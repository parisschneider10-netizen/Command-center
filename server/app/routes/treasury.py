from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import AgentWallet, TreasuryLedger
from app.schemas_treasury import LedgerOut, SpendRequest, WalletCreate, WalletOut
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
    return {
        "wallets": wallets or 0,
        "pending_approvals": pending or 0,
        "approved_spend_cents_today": approved_today or 0,
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
