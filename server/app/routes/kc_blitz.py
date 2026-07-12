from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import KcHostLead
from app.schemas_kc_blitz import CloseSaleAtDoor, DispatchCloser, KcLeadBatch, KcLeadIn
from app.value_node.kc_blitz import (
    blitz_dispatch_all_new,
    blitz_status,
    close_sale_at_door,
    dispatch_closer,
    ingest_lead,
    ingest_leads_batch,
)

router = APIRouter(prefix="/api/kc-blitz", tags=["kc-world-cup-blitz"])


@router.get("/status")
async def get_blitz_status(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """30-unit cap, slots remaining, World Cup urgency."""
    return await blitz_status(db)


@router.post("/leads")
async def post_lead(
    body: KcLeadIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """AI agent ingests one STR host lead."""
    lead = await ingest_lead(db, body.model_dump())
    return {"ok": True, "lead_id": lead.id, "status": lead.status}


@router.post("/leads/batch")
async def post_leads_batch(
    body: KcLeadBatch,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """AI bulk lead drop."""
    return await ingest_leads_batch(db, [l.model_dump() for l in body.leads])


@router.get("/leads")
async def list_leads(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[dict]:
    q = select(KcHostLead).order_by(desc(KcHostLead.created_at)).limit(200)
    if status:
        q = q.where(KcHostLead.status == status)
    result = await db.execute(q)
    return [
        {
            "id": l.id,
            "name": l.name,
            "phone": l.phone,
            "neighborhood": l.neighborhood,
            "unit_count": l.unit_count,
            "status": l.status,
            "mission_id": l.mission_id,
            "package_sku": l.package_sku,
        }
        for l in result.scalars().all()
    ]


@router.post("/leads/{lead_id}/dispatch")
async def post_dispatch_closer(
    lead_id: int,
    body: DispatchCloser | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Send RentAHuman closer to lock host ASAP."""
    opts = body or DispatchCloser()
    result = await dispatch_closer(
        db, lead_id, dry_run=opts.dry_run, pay_cents=opts.pay_cents
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "dispatch failed"))
    return result


@router.post("/close-sale")
async def post_close_sale(
    body: CloseSaleAtDoor,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """
    Host paid at door → lock unit cap → 4h sales float → instant closer payout.
    """
    result = await close_sale_at_door(db, **body.model_dump())
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "close failed"))
    return result


@router.post("/dispatch-all")
async def post_dispatch_all(
    limit: int = 10,
    dry_run: bool = True,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """World Cup speed — dispatch closers to all new leads."""
    return await blitz_dispatch_all_new(db, limit=limit, dry_run=dry_run)
