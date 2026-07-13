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


async def route_to_human_firewall(
    db: AsyncSession,
    escalation: HumanEscalation,
    *,
    budget: float | None = None,
) -> dict:
    """
    Human firewall hole — assign guardian or auto-post RentAHuman.
    Commander is NOT notified unless escalation is nuclear/commander level.
    """
    from app.intent.engine import get_firewall_guardians
    from app.integrations.n8n import trigger_n8n
    from app.integrations.rentahuman import create_bounty

    if escalation.level == EscalationLevel.commander:
        return {"routed": "commander", "escalation_id": escalation.id}

    guardians = await get_firewall_guardians(db)
    if guardians:
        guardian = guardians[escalation.id % len(guardians)]
        escalation.guardian_id = guardian.id
        escalation.status = EscalationStatus.in_progress
        await db.commit()
        await trigger_n8n(
            "human-firewall-guardian",
            {
                "escalation_id": escalation.id,
                "guardian_id": guardian.id,
                "title": escalation.title,
            },
        )
        return {
            "routed": "guardian",
            "escalation_id": escalation.id,
            "guardian": guardian.name,
        }

    bounty_usd = budget or settings.guardian_per_task_cap
    rah_result = None
    if settings.intent_auto_post_rah and settings.rentahuman_api_key:
        rah_result = await create_bounty(
            title=escalation.title,
            description=escalation.description,
            compensation=bounty_usd,
            tags=["human-firewall", "launch-ready"],
        )
        if rah_result.get("ok"):
            data = rah_result.get("data") or {}
            escalation.rentahuman_bounty_id = str(data.get("id", ""))
            escalation.status = EscalationStatus.in_progress
            await db.commit()

    await trigger_n8n(
        "human-firewall-hole",
        {
            "escalation_id": escalation.id,
            "title": escalation.title,
            "rah_posted": bool(rah_result and rah_result.get("ok")),
            "budget_usd": bounty_usd,
        },
    )
    return {
        "routed": "rentahuman" if rah_result and rah_result.get("ok") else "firewall_queue",
        "escalation_id": escalation.id,
        "rah": rah_result,
        "note": "Guardian slots empty — bounty queued when RAH key live",
    }
