"""Hive research — auto-queued when treasury fuel arrives."""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.n8n import trigger_n8n
from app.models import Task, TaskPriority
from app.schemas import TaskCreate
from app.services import create_task, log_activity
from app.treasury.capability import capability_snapshot
from app.treasury.empire import detect_empire_tier


RESEARCH_PROMPT = """
Empire fuel received. Research the BEST upgrades available right now for this sovereign stay empire.
Focus: compute/VPS, network/Starlink, voice stack, crypto rails, automation, ground force scale.
Return top 3 recommendations with cost, ROI, and priority for 40-city × 3-unit sandbox.
Cross-check acquisition manifest gaps.
"""


async def trigger_empire_research_on_fuel(
    db: AsyncSession,
    *,
    amount_cents: int,
    source_ledger_id: int | None,
    trigger: str = "treasury_clear",
) -> dict:
    """Queue hive research task + n8n when money flows in — Commander gets best-in-class suggestions."""
    empire = await detect_empire_tier(db)
    capability = await capability_snapshot(db)
    gaps = capability.get("capability_gaps", [])[:5]
    affordable = capability.get("affordable_now", [])[:3]

    title = f"RESEARCH: Best empire upgrades for ${amount_cents / 100:.0f} new fuel"
    description = (
        f"{RESEARCH_PROMPT.strip()}\n\n"
        f"Empire tier: {empire['tier']} ({empire['label']})\n"
        f"Trigger: {trigger}\n"
        f"Source ledger: {source_ledger_id}\n"
        f"Capability gaps: {gaps}\n"
        f"Affordable now: {affordable}\n"
        f"Commander rule: ZERO out-of-pocket — recommend only host-funded paths."
    )

    task = await create_task(
        db,
        TaskCreate(
            title=title,
            description=description,
            priority=TaskPriority.high,
            source="treasury_fuel",
            will_priority=9,
            open_for_agents=True,
        ),
    )

    payload = {
        "task_id": task.id,
        "amount_cents": amount_cents,
        "empire_tier": empire["tier"],
        "source_ledger_id": source_ledger_id,
        "capability_gaps": gaps,
        "affordable_now": affordable,
        "trigger": trigger,
    }
    await log_activity(
        db,
        "empire_research_queued",
        title,
        payload,
    )
    await trigger_n8n("empire-fuel-research", payload)

    return {
        "ok": True,
        "task_id": task.id,
        "title": title,
        "voice_summary": (
            f"Research queued. Hive scouting best upgrades for ${amount_cents / 100:.0f} new fuel."
        ),
    }


async def list_research_tasks(db: AsyncSession, limit: int = 20) -> list[dict]:
    result = await db.execute(
        select(Task)
        .where(Task.source == "treasury_fuel")
        .order_by(desc(Task.created_at))
        .limit(limit)
    )
    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status.value,
            "priority": t.priority.value,
            "created_at": t.created_at.isoformat(),
        }
        for t in result.scalars().all()
    ]
