from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import ScrapedLead
from app.schemas_expansion import (
    CityLockRequest,
    ExpansionRunRequest,
    ExpansionStatus,
    LeadIn,
    LeadOut,
)
from app.value_node.expansion import execute_city_lock, register_lead, scale_cities

router = APIRouter(prefix="/api/value-node", tags=["value-node"])


@router.get("/expansion/status", response_model=ExpansionStatus)
async def expansion_status(_: str = Depends(get_current_user)) -> ExpansionStatus:
    return ExpansionStatus(
        dry_run_default=settings.expansion_dry_run,
        max_cities=settings.expansion_max_cities,
        live_batch_cap=settings.expansion_live_batch_cap,
        vps_cost_cents=settings.expansion_vps_cost_cents,
        servury_configured=bool(settings.servury_api_key),
        ghl_configured=bool(settings.ghl_api_key and settings.ghl_company_id),
    )


@router.get("/leads", response_model=list[LeadOut])
async def list_leads(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[LeadOut]:
    result = await db.execute(
        select(ScrapedLead).order_by(desc(ScrapedLead.created_at)).limit(200)
    )
    return [LeadOut.model_validate(l) for l in result.scalars().all()]


@router.post("/leads", response_model=LeadOut)
async def add_lead(
    body: LeadIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> LeadOut:
    lead = await register_lead(db, body.model_dump())
    return LeadOut.model_validate(lead)


@router.post("/expansion/city-lock")
async def city_lock(
    body: CityLockRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    return await execute_city_lock(
        db,
        body.lead.model_dump(),
        dry_run=body.dry_run,
        wallet_id=body.wallet_id,
    )


@router.post("/expansion/scale")
async def expansion_scale(
    body: ExpansionRunRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    return await scale_cities(
        db,
        [l.model_dump() for l in body.leads],
        dry_run=body.dry_run,
        wallet_id=body.wallet_id,
    )
