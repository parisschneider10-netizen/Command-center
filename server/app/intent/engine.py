"""Intent engine — Commander states intent, system plans, hive + humans execute."""

from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.escalation import create_escalation
from app.integrations.n8n import trigger_n8n
from app.integrations.rentahuman import create_bounty
from app.intent.templates import (
    DEFAULT_JUDGMENT_RULES,
    build_micro_tasks,
    match_template,
)
from app.models import (
    CommanderIntent,
    EscalationLevel,
    EscalationStatus,
    Guardian,
    IntentMicroTask,
    JudgmentRule,
    TaskPriority,
)
from app.schemas import TaskCreate
from app.services import create_task, log_activity
from app.treasury.capability import capability_snapshot
from app.treasury.human_capital import human_life_force_snapshot


async def ensure_judgment_rules(db: AsyncSession) -> list[JudgmentRule]:
    from sqlalchemy import func

    count = await db.scalar(select(func.count()).select_from(JudgmentRule)) or 0
    if count > 0:
        existing = await db.execute(select(JudgmentRule).order_by(JudgmentRule.id))
        return list(existing.scalars().all())

    for rule in DEFAULT_JUDGMENT_RULES:
        db.add(
            JudgmentRule(
                rule_key=rule["id"],
                label=rule["label"],
                handler=rule["handler"],
                auto_post_rah=rule["auto_rah"],
            )
        )
    await db.commit()
    result = await db.execute(select(JudgmentRule).order_by(JudgmentRule.id))
    return list(result.scalars().all())


async def plan_intent(db: AsyncSession, *, intent_text: str, source: str = "commander") -> CommanderIntent:
    """Parse intent → plan + micro-tasks + treasury human capacity. No Commander buttons."""
    template = match_template(intent_text)
    template_name = template["name"]
    micro_tasks = build_micro_tasks(template_name, intent_text)
    human_cap = await human_life_force_snapshot(db)
    capability = await capability_snapshot(db)
    rules = await ensure_judgment_rules(db)

    total_human_budget = sum(
        t.get("budget_usd", 0) for t in micro_tasks if t.get("executor") in ("rentahuman", "guardian")
    )
    can_auto_execute = total_human_budget <= human_cap["deployable_usd"]

    plan = {
        "template": template_name,
        "phases": template["phases"],
        "micro_tasks": micro_tasks,
        "judgment_rules": [
            {"key": r.rule_key, "label": r.label, "handler": r.handler, "auto_rah": r.auto_post_rah}
            for r in rules
        ],
        "treasury": {
            "human_life_force": human_cap,
            "capability_summary": capability.get("voice_summary"),
            "total_human_budget_usd": total_human_budget,
            "can_fund_from_float": can_auto_execute,
        },
        "commander_touch_points": [
            p for p in template["phases"] if p.get("owner") == "commander"
        ],
        "direction": _direction_statement(template_name, intent_text, human_cap),
    }

    intent = CommanderIntent(
        intent_text=intent_text,
        source=source,
        status="planned",
        template_name=template_name,
        plan_json=_json_dump(plan),
    )
    db.add(intent)
    await db.commit()
    await db.refresh(intent)

    for i, mt in enumerate(micro_tasks):
        row = IntentMicroTask(
            intent_id=intent.id,
            title=mt["title"],
            description=mt.get("description"),
            executor=mt.get("executor", "agent"),
            budget_usd=mt.get("budget_usd"),
            will_priority=mt.get("will_priority", 6),
            status="planned",
            tags=",".join(mt.get("tags", [])) if mt.get("tags") else None,
        )
        db.add(row)
    await db.commit()

    await log_activity(
        db,
        "intent_planned",
        f"Intent planned: {intent_text[:80]}",
        {"intent_id": intent.id, "template": template_name},
    )
    return intent


def _direction_statement(template_name: str, intent_text: str, human_cap: dict) -> str:
    caps = human_cap["capacity"]
    return (
        f"Goal: {intent_text.strip()[:200]}. "
        f"Hive handles digital execution. Human firewall covers judgment/physical. "
        f"Float supports {caps['standard_gigs_35_usd']} standard gigs now. "
        f"You only intervene on nuclear items in the plan."
    )


def _json_dump(obj: dict) -> str:
    import json

    return json.dumps(obj, default=str)


def _json_load(raw: str | None) -> dict:
    import json

    if not raw:
        return {}
    return json.loads(raw)


async def get_firewall_guardians(db: AsyncSession) -> list[Guardian]:
    """Up to 3 active guardians = human firewall."""
    result = await db.execute(
        select(Guardian)
        .where(Guardian.is_active.is_(True))
        .order_by(Guardian.id)
        .limit(settings.human_firewall_size)
    )
    return list(result.scalars().all())


async def _assign_guardian(db: AsyncSession, guardians: list[Guardian], index: int) -> Guardian | None:
    if not guardians:
        return None
    return guardians[index % len(guardians)]


async def execute_intent(
    db: AsyncSession,
    intent_id: int,
    *,
    auto_post_rah: bool | None = None,
    dry_run_rah: bool | None = None,
) -> dict:
    """
    Execute planned intent — agent tasks, guardian assignments, RentAHuman auto-post.
    Commander does not press buttons. Firewall protects time.
    """
    intent = await db.get(CommanderIntent, intent_id)
    if not intent:
        return {"ok": False, "error": "Intent not found"}

    plan = _json_load(intent.plan_json)
    if not plan.get("treasury", {}).get("can_fund_from_float") and plan.get("treasury", {}).get("total_human_budget_usd", 0) > 0:
        intent.status = "needs_commander_budget"
        await db.commit()
        return {
            "ok": False,
            "error": "Human task budget exceeds deployable float — nuclear budget approval required",
            "intent_id": intent_id,
        }

    auto_rah = settings.intent_auto_post_rah if auto_post_rah is None else auto_post_rah
    dry = settings.expansion_dry_run if dry_run_rah is None else dry_run_rah

    result = await db.execute(
        select(IntentMicroTask).where(IntentMicroTask.intent_id == intent_id).order_by(IntentMicroTask.id)
    )
    micro_tasks = list(result.scalars().all())
    guardians = await get_firewall_guardians(db)
    guardian_idx = 0
    outcomes: list[dict] = []

    for mt in micro_tasks:
        if mt.executor == "agent":
            priority = TaskPriority.urgent if mt.will_priority >= 8 else TaskPriority.high
            task = await create_task(
                db,
                TaskCreate(
                    title=mt.title,
                    description=mt.description,
                    priority=priority,
                    source="intent",
                    will_priority=mt.will_priority,
                    open_for_agents=True,
                ),
            )
            mt.status = "agent_queued"
            mt.linked_task_id = task.id
            await trigger_n8n(
                "agent-queue",
                {"task_id": task.id, "intent_id": intent_id, "title": mt.title},
            )
            outcomes.append({"micro_task_id": mt.id, "action": "agent_task", "task_id": task.id})

        elif mt.executor == "guardian":
            guardian = await _assign_guardian(db, guardians, guardian_idx)
            guardian_idx += 1
            esc = await create_escalation(
                db,
                title=mt.title,
                description=mt.description or "",
                level=EscalationLevel.human,
                budget=mt.budget_usd,
                source="intent_firewall",
            )
            if guardian:
                esc.guardian_id = guardian.id
                esc.status = EscalationStatus.assigned
            mt.status = "guardian_assigned"
            mt.linked_escalation_id = esc.id
            await trigger_n8n("human-escalation", {"escalation_id": esc.id, "intent_id": intent_id})
            outcomes.append({
                "micro_task_id": mt.id,
                "action": "guardian",
                "escalation_id": esc.id,
                "guardian": guardian.name if guardian else "pool_empty",
            })

        elif mt.executor == "rentahuman":
            budget = mt.budget_usd or settings.guardian_per_task_cap
            if auto_rah:
                rah = await create_bounty(
                    title=mt.title,
                    description=mt.description or "",
                    compensation=budget,
                    location="Kansas City, MO" if "kc" in (mt.tags or "").lower() else None,
                    tags=(mt.tags or "").split(",") if mt.tags else ["intent-engine"],
                    dry_run=dry,
                )
                mt.status = "rah_posted" if rah.get("ok") else "rah_failed"
                if rah.get("ok") and not dry:
                    bounty_id = str(rah.get("data", {}).get("id", ""))
                    mt.rentahuman_bounty_id = bounty_id or None
                outcomes.append({
                    "micro_task_id": mt.id,
                    "action": "rentahuman",
                    "dry_run": dry,
                    "result": rah,
                })
            else:
                mt.status = "rah_skipped"
                outcomes.append({"micro_task_id": mt.id, "action": "rah_disabled"})

        await db.commit()

    intent.status = "executing"
    await db.commit()
    await log_activity(
        db,
        "intent_executing",
        f"Intent {intent_id} executing — {len(outcomes)} micro-tasks",
        {"outcomes": outcomes},
    )
    await trigger_n8n("intent-executed", {"intent_id": intent_id, "outcomes": outcomes})

    return {
        "ok": True,
        "intent_id": intent_id,
        "status": intent.status,
        "outcomes": outcomes,
        "commander_required": False,
        "message": "Hive + human firewall executing. Commander notified only on nuclear triggers.",
    }


async def intent_briefing(db: AsyncSession, intent_id: int) -> dict:
    intent = await db.get(CommanderIntent, intent_id)
    if not intent:
        return {"ok": False, "error": "Not found"}
    plan = _json_load(intent.plan_json)
    tasks = list(
        (
            await db.execute(
                select(IntentMicroTask).where(IntentMicroTask.intent_id == intent_id)
            )
        )
        .scalars()
        .all()
    )
    guardians = await get_firewall_guardians(db)
    return {
        "intent_id": intent.id,
        "intent_text": intent.intent_text,
        "status": intent.status,
        "template": intent.template_name,
        "direction": plan.get("direction"),
        "phases": plan.get("phases"),
        "treasury": plan.get("treasury"),
        "micro_tasks": [
            {
                "id": t.id,
                "title": t.title,
                "executor": t.executor,
                "status": t.status,
                "budget_usd": t.budget_usd,
            }
            for t in tasks
        ],
        "firewall": {
            "slots": settings.human_firewall_size,
            "active_guardians": [{"id": g.id, "name": g.name, "role": g.role} for g in guardians],
            "open_slots": max(0, settings.human_firewall_size - len(guardians)),
        },
    }
