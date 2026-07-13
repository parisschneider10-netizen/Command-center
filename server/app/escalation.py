"""Escalation logic — internal agents → A2A → humans → Commander."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import (
    EscalationLevel,
    EscalationStatus,
    HumanEscalation,
)
from app.services import log_activity


async def create_escalation(
    db: AsyncSession,
    *,
    title: str,
    description: str,
    level: EscalationLevel = EscalationLevel.human,
    task_id: int | None = None,
    budget: float | None = None,
    nuclear_flag: bool = False,
    source: str = "system",
) -> HumanEscalation:
    """Create escalation. Tries A2A/agent path before human level when digital."""
    if (
        level == EscalationLevel.human
        and not nuclear_flag
        and settings.a2a_prefer_over_humans
    ):
        from app.a2a.resolver import classify_work
        from app.a2a.service import route_digital_work

        classification = classify_work(title, description)
        if classification["prefer_a2a"] and not classification["human_required"]:
            routed = await route_digital_work(
                db,
                title=title,
                description=description,
                capability="escalation_digital",
            )
            if routed.get("ok"):
                await log_activity(
                    db,
                    "escalation_a2a_redirect",
                    f"Human escalation avoided — A2A/agent route: {title[:80]}",
                    {"routed": routed, "classification": classification},
                )
                # Synthetic escalation record for audit — not human-assigned
                esc = HumanEscalation(
                    title=title,
                    description=description,
                    level=EscalationLevel.human,
                    status=EscalationStatus.in_progress,
                    task_id=task_id,
                    budget=budget,
                    nuclear_flag=False,
                    source=f"{source}_a2a_redirect",
                )
                db.add(esc)
                await db.commit()
                await db.refresh(esc)
                return esc

    final_level = level
    final_status = EscalationStatus.open

    if nuclear_flag:
        final_level = EscalationLevel.commander
        final_status = EscalationStatus.needs_commander
    elif budget is not None and budget > settings.guardian_per_task_cap:
        final_level = EscalationLevel.commander
        final_status = EscalationStatus.needs_commander

    escalation = HumanEscalation(
        title=title,
        description=description,
        level=final_level,
        status=final_status,
        task_id=task_id,
        budget=budget,
        nuclear_flag=nuclear_flag,
        source=source,
    )
    db.add(escalation)
    await db.commit()
    await db.refresh(escalation)

    event = "escalation_commander" if final_level == EscalationLevel.commander else "escalation_human"
    await log_activity(
        db,
        event,
        f"Escalation L{final_level.value}: {title}",
        {
            "escalation_id": escalation.id,
            "level": final_level.value,
            "nuclear": nuclear_flag,
        },
    )
    return escalation
