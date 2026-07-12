"""Escalation logic — agents first, humans second, Commander last."""

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
    """Create escalation. Auto-promotes to commander if nuclear or over budget."""
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
