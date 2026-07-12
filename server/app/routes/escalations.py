from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.escalation import create_escalation
from app.integrations.n8n import trigger_n8n
from app.integrations.rentahuman import create_bounty, search_humans
from app.models import EscalationLevel, EscalationStatus, Guardian, HumanEscalation
from app.schemas_escalation import (
    EscalationCreate,
    EscalationOut,
    GuardianCreate,
    GuardianOut,
    RentAHumanBountyRequest,
)
from app.services import log_activity

router = APIRouter(prefix="/api", tags=["human-layer"])


@router.get("/escalations", response_model=list[EscalationOut])
async def list_escalations(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[EscalationOut]:
    result = await db.execute(
        select(HumanEscalation).order_by(desc(HumanEscalation.created_at)).limit(100)
    )
    return [EscalationOut.model_validate(e) for e in result.scalars().all()]


@router.post("/escalations", response_model=EscalationOut)
async def post_escalation(
    body: EscalationCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> EscalationOut:
    escalation = await create_escalation(
        db,
        title=body.title,
        description=body.description,
        level=body.level,
        task_id=body.task_id,
        budget=body.budget,
        nuclear_flag=body.nuclear_flag,
        source="portal",
    )
    if escalation.level == EscalationLevel.human:
        await trigger_n8n(
            "human-escalation",
            {"escalation_id": escalation.id, "title": escalation.title},
        )
    return EscalationOut.model_validate(escalation)


@router.get("/guardians", response_model=list[GuardianOut])
async def list_guardians(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[GuardianOut]:
    result = await db.execute(select(Guardian).where(Guardian.is_active.is_(True)))
    return [GuardianOut.model_validate(g) for g in result.scalars().all()]


@router.post("/guardians", response_model=GuardianOut)
async def add_guardian(
    body: GuardianCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> GuardianOut:
    guardian = Guardian(
        name=body.name,
        role=body.role,
        email=body.email,
        rentahuman_id=body.rentahuman_id,
        max_per_task=body.max_per_task,
        notes=body.notes,
    )
    db.add(guardian)
    await db.commit()
    await db.refresh(guardian)
    await log_activity(db, "guardian_added", f"Guardian onboarded: {guardian.name}")
    return GuardianOut.model_validate(guardian)


@router.post("/integrations/rentahuman/search")
async def rah_search(
    skill: str | None = None,
    city: str | None = None,
    _: str = Depends(get_current_user),
) -> dict:
    return await search_humans(skill=skill, city=city)


@router.post("/integrations/rentahuman/bounty")
async def rah_bounty(
    body: RentAHumanBountyRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    if not body.dry_run and body.compensation > settings.guardian_per_task_cap:
        raise HTTPException(
            status_code=403,
            detail=f"Compensation exceeds guardian cap (${settings.guardian_per_task_cap}). "
            "Set nuclear_flag on escalation or raise cap in manifest.",
        )

    result = await create_bounty(
        title=body.title,
        description=body.description,
        compensation=body.compensation,
        location=body.location,
        dry_run=body.dry_run,
    )

    if body.escalation_id and result.get("ok") and not body.dry_run:
        escalation = await db.get(HumanEscalation, body.escalation_id)
        if escalation:
            bounty_id = str(result.get("data", {}).get("id", ""))
            escalation.rentahuman_bounty_id = bounty_id or None
            escalation.status = EscalationStatus.in_progress
            await db.commit()

    await log_activity(
        db,
        "rentahuman_bounty",
        f"Bounty {'preview' if body.dry_run else 'posted'}: {body.title}",
        {"compensation": body.compensation, "dry_run": body.dry_run},
    )
    return result
