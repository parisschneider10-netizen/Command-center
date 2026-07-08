from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.intent.engine import (
    ensure_judgment_rules,
    execute_intent,
    get_firewall_guardians,
    intent_briefing,
    plan_intent,
)
from app.models import CommanderIntent, JudgmentRule
from app.schemas_intent import IntentExecute, IntentIn, IntentOut, JudgmentRuleUpdate
from app.treasury.human_capital import human_life_force_snapshot

router = APIRouter(prefix="/api/intent", tags=["intent-engine"])


@router.post("", response_model=dict)
async def state_intent(
    body: IntentIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """
    Commander states intent → system returns plan, data, human capacity.
    Optional auto_execute queues hive + firewall without manual gig posting.
    """
    intent = await plan_intent(db, intent_text=body.intent, source=body.source)
    briefing = await intent_briefing(db, intent.id)
    result = {"ok": True, **briefing}
    if body.auto_execute:
        exec_result = await execute_intent(db, intent.id)
        result["execution"] = exec_result
        briefing = await intent_briefing(db, intent.id)
        result.update(briefing)
    return result


@router.get("/human-capital")
async def get_human_capital(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """What float/cash can buy in human life force — gigs, guardians, firewall capacity."""
    return await human_life_force_snapshot(db)


@router.get("/firewall")
async def get_firewall(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Human firewall — 3 guardians who protect Commander time."""
    guardians = await get_firewall_guardians(db)
    from app.config import settings

    return {
        "slots": settings.human_firewall_size,
        "guardians": [
            {
                "id": g.id,
                "name": g.name,
                "role": g.role,
                "max_per_task": g.max_per_task,
                "rentahuman_id": g.rentahuman_id,
            }
            for g in guardians
        ],
        "open_slots": max(0, settings.human_firewall_size - len(guardians)),
        "purpose": "Execute with your judgment. Commander sees nuclear only.",
    }


@router.get("/judgment-rules")
async def get_judgment_rules(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[dict]:
    rules = await ensure_judgment_rules(db)
    return [
        {
            "id": r.id,
            "rule_key": r.rule_key,
            "label": r.label,
            "handler": r.handler,
            "auto_post_rah": r.auto_post_rah,
            "is_active": r.is_active,
        }
        for r in rules
    ]


@router.patch("/judgment-rules/{rule_key}")
async def patch_judgment_rule(
    rule_key: str,
    body: JudgmentRuleUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    result = await db.execute(select(JudgmentRule).where(JudgmentRule.rule_key == rule_key))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await db.commit()
    return {"ok": True, "rule_key": rule_key}


@router.get("", response_model=list[IntentOut])
async def list_intents(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[IntentOut]:
    result = await db.execute(
        select(CommanderIntent).order_by(desc(CommanderIntent.created_at)).limit(50)
    )
    return [IntentOut.model_validate(i) for i in result.scalars().all()]


@router.get("/{intent_id}")
async def get_intent(
    intent_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    return await intent_briefing(db, intent_id)


@router.post("/{intent_id}/execute")
async def post_execute_intent(
    intent_id: int,
    body: IntentExecute | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Auto-post micro-tasks: agent queue + guardian assign + RentAHuman bounties."""
    opts = body or IntentExecute()
    return await execute_intent(
        db,
        intent_id,
        auto_post_rah=opts.auto_post_rah,
        dry_run_rah=opts.dry_run_rah,
    )
