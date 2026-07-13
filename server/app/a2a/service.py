"""A2A routing service — hire external agents before any human bounty."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.a2a.resolver import classify_work, human_obsoletion_snapshot
from app.config import settings
from app.integrations.n8n import trigger_n8n
from app.models import ActivityLog
from app.schemas import TaskCreate
from app.services import create_task, log_activity


async def _activity_counts(db: AsyncSession) -> tuple[int, int, int]:
    async def count_prefix(prefix: str) -> int:
        return int(
            await db.scalar(
                select(func.count())
                .select_from(ActivityLog)
                .where(ActivityLog.event_type.like(f"{prefix}%"))
            )
            or 0
        )

    a2a = await count_prefix("a2a_")
    human = await count_prefix("rentahuman") + await count_prefix("escalation_human")
    agent = await count_prefix("intent_executing") + await count_prefix("agent_")
    return a2a, agent, human


async def hire_external_agent(
    db: AsyncSession,
    *,
    capability: str,
    title: str,
    description: str,
    payload: dict | None = None,
    offered_price_cents: int | None = None,
    source: str = "hive",
) -> dict:
    """
    Outbound A2A — queue digital work to external agents before humans.
    Logs + n8n fan-out; allowlist validation expands in Phase 2.
    """
    classification = classify_work(title, description)
    if classification["human_required"] and not classification["prefer_a2a"]:
        return {
            "ok": False,
            "skipped": True,
            "reason": "human_actuator_only",
            "classification": classification,
        }

    body = {
        "capability": capability,
        "title": title,
        "description": description,
        "payload": payload or {},
        "offered_price_cents": offered_price_cents,
        "classification": classification,
        "source": source,
    }
    await log_activity(db, "a2a_outbound_hire", f"A2A hire: {capability} — {title[:80]}", body)
    n8n = await trigger_n8n("a2a-hire", body)

    return {
        "ok": True,
        "routed": "a2a",
        "message": "Digital work routed agent-to-agent — human not consulted.",
        "classification": classification,
        "n8n": n8n,
    }


async def route_digital_work(
    db: AsyncSession,
    *,
    title: str,
    description: str | None = None,
    tags: str | None = None,
    will_priority: int = 7,
    capability: str = "general_digital",
) -> dict:
    """
    Unified digital router: classify → A2A hire → agent task queue.
    Never posts RentAHuman for digital-classified work.
    """
    classification = classify_work(title, description, tags)

    if classification["human_required"] and not classification.get("digital_hits"):
        return {
            "ok": False,
            "routed": "human_only",
            "classification": classification,
            "message": "Physical work — human actuator path only after A2A/agent exhaustion.",
        }

    if classification["prefer_a2a"] and settings.a2a_prefer_over_humans:
        a2a = await hire_external_agent(
            db,
            capability=capability,
            title=title,
            description=description or "",
            source="route_digital_work",
        )
        if a2a.get("ok"):
            return {**a2a, "routed": "a2a"}

    task = await create_task(
        db,
        TaskCreate(
            title=title,
            description=description,
            priority="high" if will_priority >= 8 else "normal",
            source="a2a_router",
            will_priority=will_priority,
            open_for_agents=True,
        ),
    )
    await trigger_n8n("agent-queue", {"task_id": task.id, "title": title, "via": "a2a_router"})
    await log_activity(
        db,
        "agent_queued_a2a_fallback",
        f"Agent queue (A2A path): {title[:80]}",
        {"task_id": task.id, "classification": classification},
    )
    return {
        "ok": True,
        "routed": "agent_queue",
        "task_id": task.id,
        "classification": classification,
        "message": "Hive agent queue — humans not used.",
    }


async def obsoletion_metrics(db: AsyncSession) -> dict:
    a2a, agent, human = await _activity_counts(db)
    return human_obsoletion_snapshot(
        a2a_events=a2a,
        agent_events=agent,
        human_events=human,
    )
