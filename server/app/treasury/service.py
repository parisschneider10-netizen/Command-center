"""Treasury — agent wallets and spend ledger."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import AgentWallet, TreasuryLedger
from app.services import log_activity


async def request_spend(
    db: AsyncSession,
    *,
    wallet_id: int,
    amount_cents: int,
    description: str,
    counterparty: str | None = None,
    a2a_ref: str | None = None,
) -> TreasuryLedger:
    wallet = await db.get(AgentWallet, wallet_id)
    if not wallet or not wallet.is_active:
        raise ValueError("Wallet not found or inactive")

    cap_cents = int(settings.guardian_per_task_cap * 100)
    nuclear = amount_cents > cap_cents
    daily_ok = (wallet.daily_spent_cents + amount_cents) <= wallet.daily_limit_cents

    if nuclear or not daily_ok:
        status = "needs_commander"
    else:
        status = "approved"
        wallet.daily_spent_cents += amount_cents

    entry = TreasuryLedger(
        wallet_id=wallet_id,
        amount_cents=amount_cents,
        direction="outbound",
        description=description,
        status=status,
        counterparty=counterparty,
        a2a_ref=a2a_ref,
        nuclear_required=nuclear,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    await log_activity(
        db,
        "treasury_spend_request",
        f"${amount_cents / 100:.2f} — {description}",
        {"ledger_id": entry.id, "status": status},
    )
    return entry
