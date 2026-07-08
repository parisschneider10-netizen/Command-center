from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import AgentWallet, TreasuryLedger
from app.schemas_acquisitions import AcquisitionCreate, AcquisitionOut, AcquisitionUpdate
from app.schemas_treasury import LedgerOut, SpendRequest, WalletCreate, WalletOut
from app.treasury.acquisitions import (
    acquisition_briefing,
    create_acquisition,
    list_acquisitions,
    seed_default_acquisitions,
    sync_manifest_to_vault,
    update_acquisition,
)
from app.treasury.allocation import ammo_summary
from app.treasury.capability import capability_snapshot
from app.treasury.categories import ACQUISITION_CATEGORIES, DEFAULT_AMMO_WEIGHTS
from app.treasury.service import request_spend

router = APIRouter(prefix="/api/treasury", tags=["treasury"])


@router.get("/overview")
async def treasury_overview(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    wallets = await db.scalar(select(func.count()).select_from(AgentWallet))
    pending = await db.scalar(
        select(func.count())
        .select_from(TreasuryLedger)
        .where(TreasuryLedger.status == "needs_commander")
    )
    approved_today = await db.scalar(
        select(func.coalesce(func.sum(TreasuryLedger.amount_cents), 0))
        .where(TreasuryLedger.status == "approved")
    )
    briefing = await acquisition_briefing(db)
    return {
        "wallets": wallets or 0,
        "pending_approvals": pending or 0,
        "approved_spend_cents_today": approved_today or 0,
        "ammo_balance_usd": briefing["ammo_balance_usd"],
        "acquisitions_needed": briefing["needed_count"],
        "acquisitions_funded_ready": briefing["funded_ready_count"],
    }


@router.get("/wallets", response_model=list[WalletOut])
async def list_wallets(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[WalletOut]:
    result = await db.execute(select(AgentWallet).where(AgentWallet.is_active.is_(True)))
    return [WalletOut.model_validate(w) for w in result.scalars().all()]


@router.post("/wallets", response_model=WalletOut)
async def create_wallet(
    body: WalletCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> WalletOut:
    wallet = AgentWallet(
        name=body.name,
        agent_id=body.agent_id,
        daily_limit_cents=body.daily_limit_cents,
    )
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return WalletOut.model_validate(wallet)


@router.post("/spend-request", response_model=LedgerOut)
async def spend_request(
    body: SpendRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> LedgerOut:
    try:
        entry = await request_spend(
            db,
            wallet_id=body.wallet_id,
            amount_cents=body.amount_cents,
            description=body.description,
            counterparty=body.counterparty,
            a2a_ref=body.a2a_ref,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return LedgerOut.model_validate(entry)


@router.get("/ledger", response_model=list[LedgerOut])
async def ledger(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[LedgerOut]:
    result = await db.execute(
        select(TreasuryLedger).order_by(desc(TreasuryLedger.created_at)).limit(200)
    )
    return [LedgerOut.model_validate(e) for e in result.scalars().all()]


@router.post("/approve/{ledger_id}", response_model=LedgerOut)
async def approve_spend(
    ledger_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> LedgerOut:
    entry = await db.get(TreasuryLedger, ledger_id)
    if not entry or entry.status != "needs_commander":
        raise HTTPException(status_code=404, detail="Pending entry not found")
    entry.status = "approved"
    entry.resolved_at = datetime.now(timezone.utc)
    if entry.wallet_id:
        wallet = await db.get(AgentWallet, entry.wallet_id)
        if wallet:
            wallet.daily_spent_cents += entry.amount_cents
    await db.commit()
    await db.refresh(entry)
    return LedgerOut.model_validate(entry)


@router.get("/acquisitions/categories")
async def acquisition_categories(
    _: str = Depends(get_current_user),
) -> dict:
    return {"categories": ACQUISITION_CATEGORIES, "ammo_weights": DEFAULT_AMMO_WEIGHTS}


@router.get("/acquisitions", response_model=list[AcquisitionOut])
async def get_acquisitions(
    category: str | None = None,
    status: str | None = None,
    empire_tier: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[AcquisitionOut]:
    items = await list_acquisitions(
        db, category=category, status=status, empire_tier=empire_tier
    )
    return [AcquisitionOut.model_validate(a) for a in items]


@router.post("/acquisitions", response_model=AcquisitionOut)
async def post_acquisition(
    body: AcquisitionCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> AcquisitionOut:
    if body.category not in ACQUISITION_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Unknown category: {body.category}")
    acq = await create_acquisition(db, **body.model_dump())
    await sync_manifest_to_vault(db)
    return AcquisitionOut.model_validate(acq)


@router.patch("/acquisitions/{acq_id}", response_model=AcquisitionOut)
async def patch_acquisition(
    acq_id: int,
    body: AcquisitionUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> AcquisitionOut:
    acq = await update_acquisition(db, acq_id, **body.model_dump(exclude_unset=True))
    if not acq:
        raise HTTPException(status_code=404, detail="Acquisition not found")
    await sync_manifest_to_vault(db)
    return AcquisitionOut.model_validate(acq)


@router.post("/acquisitions/seed")
async def post_seed_acquisitions(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    result = await seed_default_acquisitions(db)
    await sync_manifest_to_vault(db)
    return result


@router.get("/acquisitions/briefing")
async def get_acquisition_briefing(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    return await acquisition_briefing(db)


@router.get("/acquisitions/manifest")
async def get_acquisition_manifest(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    path = await sync_manifest_to_vault(db)
    return {"path": str(path), "content": path.read_text(encoding="utf-8")}


@router.get("/ammo")
async def get_ammo(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    return await ammo_summary(db)


@router.get("/capability")
async def get_capability(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """What the empire can afford and unlock at current liquidity + tier."""
    return await capability_snapshot(db)
