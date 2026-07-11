"""Crypto treasury rail — host USDC direct to empire wallet, instant ledger, closer paid in crypto."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import TreasuryLedger
from app.services import log_activity
from app.treasury.float import record_host_payment


def treasury_receive_instructions() -> dict:
    """What closers show host at door — pay treasury directly, no Cash App middleman."""
    addr = settings.treasury_usdc_address
    gross = settings.sovereign_upfront_fee_cents / 100
    closer = settings.sovereign_closer_bounty_cents / 100
    configured = bool(addr)
    return {
        "payment_rail": "crypto_direct",
        "asset": settings.treasury_crypto_asset,
        "chain": settings.treasury_crypto_chain,
        "treasury_address": addr or "SET_TREASURY_USDC_ADDRESS_IN_ENV",
        "amount_usd": gross,
        "amount_cents": settings.sovereign_upfront_fee_cents,
        "closer_payout_usd": closer,
        "split_at_door": {
            "option_a": f"Host sends ${gross:.0f} {settings.treasury_crypto_asset} to treasury address — fastest",
            "option_b": f"Host sends ${gross - closer:.0f} treasury + ${closer:.0f} to closer wallet (2 txs)",
        },
        "closer_script": (
            f"Show host QR for {settings.treasury_crypto_asset} on {settings.treasury_crypto_chain}. "
            f"Send exactly ${gross:.0f} to empire treasury BEFORE you leave. "
            f"Paste tx hash in mission app. You receive ${closer:.0f} USDC instantly after confirm."
        ),
        "configured": configured,
        "warpspeed": configured,
    }


async def _tx_hash_used(db: AsyncSession, tx_hash: str) -> bool:
    result = await db.execute(
        select(TreasuryLedger).where(TreasuryLedger.a2a_ref == tx_hash)
    )
    return result.scalar_one_or_none() is not None


async def record_crypto_presale_inbound(
    db: AsyncSession,
    *,
    amount_cents: int,
    host_id: int,
    tx_hash: str,
    description: str,
) -> TreasuryLedger:
    if await _tx_hash_used(db, tx_hash):
        raise ValueError(f"Tx hash already recorded: {tx_hash}")
    if amount_cents < settings.sovereign_upfront_fee_cents:
        raise ValueError(
            f"Amount below presale minimum ${settings.sovereign_upfront_fee_cents / 100:.2f}"
        )

    entry = await record_host_payment(
        db,
        amount_cents=amount_cents,
        host_id=host_id,
        description=description,
        payment_category="crypto_instant",
    )
    entry.a2a_ref = tx_hash
    entry.counterparty = f"crypto:host:{host_id}"
    await db.commit()
    await db.refresh(entry)
    await log_activity(
        db,
        "crypto_presale_inbound",
        f"${amount_cents / 100:.2f} {settings.treasury_crypto_asset} — {tx_hash[:16]}…",
        {"ledger_id": entry.id, "tx_hash": tx_hash, "chain": settings.treasury_crypto_chain},
    )
    return entry


async def payout_closer_crypto(
    db: AsyncSession,
    *,
    amount_cents: int,
    mission_id: int,
    closer_wallet: str,
    from_ledger_id: int,
    inbound_tx_hash: str,
) -> TreasuryLedger:
    """Log instant USDC closer payout — send from treasury hot wallet."""
    parent = await db.get(TreasuryLedger, from_ledger_id)
    if not parent:
        raise ValueError("Parent inbound not found")
    if parent.amount_cents < amount_cents:
        raise ValueError("Inbound insufficient for closer payout")

    entry = TreasuryLedger(
        wallet_id=None,
        amount_cents=amount_cents,
        direction="outbound",
        description=(
            f"Closer crypto payout — mission {mission_id} — "
            f"send {settings.treasury_crypto_asset} to {closer_wallet}"
        ),
        status="disbursed",
        counterparty=f"crypto:{closer_wallet}",
        linked_mission_id=mission_id,
        a2a_ref=f"out:{inbound_tx_hash[:32]}",
        payment_category="crypto_payout",
        resolved_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    await log_activity(
        db,
        "crypto_closer_payout",
        f"${amount_cents / 100:.2f} USDC → {closer_wallet[:12]}…",
        {"mission_id": mission_id, "inbound_tx": inbound_tx_hash},
    )
    return entry
