"""Eco-Express API — D2C thermostat flips."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.value_node.eco_express import (
    HUNTER_DOOR_PITCH,
    calculate_rebate_stack,
    complete_install,
    confirm_homeowner_payment,
    dispatch_hunter,
    eco_status,
    generate_strike_list,
    hunter_close_sheet,
    list_jobs,
)

router = APIRouter(prefix="/api/eco-express", tags=["eco-express"])


class PaymentConfirmIn(BaseModel):
    payment_proof: str = Field(description="Stripe/Cash App screenshot ref or tx id")
    scheduled_slot: str = "ASAP"
    dry_run: bool = False


class InstallCompleteIn(BaseModel):
    thermostat_photo_proof: str = Field(description="URL or description — must show Wi-Fi icon on unit")
    worker_ref: str = "rah:installer"


class HunterDispatchIn(BaseModel):
    dry_run: bool = True


@router.get("/status")
async def get_eco_status(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    return await eco_status(db)


@router.get("/economics")
async def get_economics(_: str = Depends(get_current_user)) -> dict:
    return calculate_rebate_stack()


@router.get("/pitch")
async def get_hunter_pitch(_: str = Depends(get_current_user)) -> dict:
    return {"pitch": HUNTER_DOOR_PITCH}


@router.get("/jobs")
async def get_jobs(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[dict]:
    return await list_jobs(db)


@router.get("/hunter-sheet")
async def get_hunter_sheet(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Field closer sheet — targeted doors with phone + pitch."""
    return await hunter_close_sheet(db)


@router.post("/strike-list")
async def post_strike_list(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Loop A — auto-hunt KCMO doors, push strike sheet."""
    return await generate_strike_list(db)


@router.post("/jobs/{job_id}/dispatch-hunter")
async def post_dispatch_hunter(
    job_id: int,
    body: HunterDispatchIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    result = await dispatch_hunter(db, job_id, dry_run=body.dry_run)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "dispatch failed"))
    return result


@router.post("/jobs/{job_id}/payment-confirmed")
async def post_payment_confirmed(
    job_id: int,
    body: PaymentConfirmIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Loop B — $149 collected → Lowe's barcode + installer."""
    result = await confirm_homeowner_payment(
        db,
        job_id,
        payment_proof=body.payment_proof,
        scheduled_slot=body.scheduled_slot,
        dry_run=body.dry_run,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "payment flow failed"))
    return result


@router.post("/jobs/{job_id}/install-complete")
async def post_install_complete(
    job_id: int,
    body: InstallCompleteIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Loop C — Wi-Fi photo proof or freeze payout."""
    result = await complete_install(
        db,
        job_id,
        thermostat_photo_proof=body.thermostat_photo_proof,
        worker_ref=body.worker_ref,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "QC failed"))
    return result
