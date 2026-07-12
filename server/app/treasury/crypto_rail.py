"""Crypto treasury rail — bootstrap fuel first, then host-paid split. Zero Commander OOP."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import SovereignCloserPayout, SovereignHost, TreasuryLedger
from app.services import log_activity
from app.treasury.float import record_host_payment


async def empire_bootstrapped(db: AsyncSession) -> bool:
    """True after first host fuel secured — switches payment mode."""
    count = await db.scalar(select(func.count()).select_from(SovereignHost)) or 0
    return count > 0


async def current_payment_mode(db: AsyncSession) -> str:
    """
    bootstrap — first play: 100% USDC to treasury (empire fuel). Closer deferred.
    split — play 2+: host sends treasury + closer directly. Zero Commander wallet funding.
    """
    if settings.sovereign_payment_mode in ("bootstrap", "split"):
        return settings.sovereign_payment_mode
    return "split" if await empire_bootstrapped(db) else "bootstrap"


async def treasury_receive_instructions(db: AsyncSession) -> dict:
    """Closer door script — mode-aware, zero Commander OOP."""
    mode = await current_payment_mode(db)
    addr = settings.treasury_usdc_address
    gross = settings.sovereign_upfront_fee_cents
    closer = settings.sovereign_closer_bounty_cents
    treasury_part = gross - closer
    configured = bool(addr)

    if mode == "bootstrap":
        script = (
            f"FIRST FUEL PLAY — host sends 100% ${gross / 100:.0f} {settings.treasury_crypto_asset} "
            f"to treasury {addr or '[set address]'}. "
            f"NO Commander money. Closer paid from host fuel on play 2+. "
            f"Submit treasury tx hash only."
        )
        return {
            "payment_mode": "bootstrap",
            "commander_oop": 0,
            "asset": settings.treasury_crypto_asset,
            "chain": settings.treasury_crypto_chain,
            "treasury_address": addr or "SET_TREASURY_USDC_ADDRESS_IN_ENV",
            "treasury_amount_usd": gross / 100,
            "treasury_amount_cents": gross,
            "closer_payout_usd": closer / 100,
            "closer_paid_by": "deferred_until_play_2_host_fuel",
            "closer_script": script,
            "configured": configured,
        }

    script = (
        f"Host sends TWO transfers on {settings.treasury_crypto_chain}: "
        f"1) ${treasury_part / 100:.0f} {settings.treasury_crypto_asset} → treasury {addr}. "
        f"2) ${closer / 100:.0f} {settings.treasury_crypto_asset} → closer wallet DIRECT. "
        f"Commander never funds wallet — host pays closer at door. Submit both tx hashes."
    )
    return {
        "payment_mode": "split",
        "commander_oop": 0,
        "asset": settings.treasury_crypto_asset,
        "chain": settings.treasury_crypto_chain,
        "treasury_address": addr or "SET_TREASURY_USDC_ADDRESS_IN_ENV",
        "treasury_amount_usd": treasury_part / 100,
        "treasury_amount_cents": treasury_part,
        "closer_payout_usd": closer / 100,
        "closer_payout_cents": closer,
        "closer_paid_by": "host_direct_at_door",
        "closer_script": script,
        "configured": configured,
    }


async def _tx_hash_used(db: AsyncSession, tx_hash: str) -> bool:
    result = await db.execute(
        select(TreasuryLedger).where(TreasuryLedger.a2a_ref == tx_hash)
    )
    if result.scalar_one_or_none():
        return True
    result = await db.execute(
        select(SovereignCloserPayout).where(SovereignCloserPayout.payout_tx_hash == tx_hash)
    )
    return result.scalar_one_or_none() is not None


async def record_crypto_treasury_inbound(
    db: AsyncSession,
    *,
    amount_cents: int,
    host_id: int,
    tx_hash: str,
    description: str,
    payment_mode: str,
) -> TreasuryLedger:
    if await _tx_hash_used(db, tx_hash):
        raise ValueError(f"Tx hash already recorded: {tx_hash}")

    entry = await record_host_payment(
        db,
        amount_cents=amount_cents,
        host_id=host_id,
        description=description,
        payment_category="crypto_instant",
    )
    entry.a2a_ref = tx_hash
    entry.counterparty = f"crypto:treasury:{host_id}:{payment_mode}"
    await db.commit()
    await db.refresh(entry)
    await log_activity(
        db,
        "crypto_treasury_inbound",
        f"${amount_cents / 100:.2f} {settings.treasury_crypto_asset} — {payment_mode}",
        {"ledger_id": entry.id, "tx_hash": tx_hash, "mode": payment_mode},
    )
    return entry


async def defer_closer_payout(
    db: AsyncSession,
    *,
    mission_id: int,
    host_id: int,
    closer_wallet: str,
    amount_cents: int,
) -> SovereignCloserPayout:
    """Bootstrap play — closer owed, paid from host-funded treasury on play 2+."""
    row = SovereignCloserPayout(
        mission_id=mission_id,
        host_id=host_id,
        closer_wallet=closer_wallet,
        amount_cents=amount_cents,
        status="deferred",
        payment_mode="bootstrap",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def record_closer_paid_by_host(
    db: AsyncSession,
    *,
    mission_id: int,
    host_id: int,
    closer_wallet: str,
    amount_cents: int,
    closer_tx_hash: str,
) -> SovereignCloserPayout:
    """Split play — host sent USDC directly to closer. Zero treasury outbound."""
    if await _tx_hash_used(db, closer_tx_hash):
        raise ValueError(f"Closer tx hash already used: {closer_tx_hash}")

    row = SovereignCloserPayout(
        mission_id=mission_id,
        host_id=host_id,
        closer_wallet=closer_wallet,
        amount_cents=amount_cents,
        status="paid_host_direct",
        payment_mode="split",
        payout_tx_hash=closer_tx_hash,
        paid_at=datetime.now(timezone.utc),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    entry = TreasuryLedger(
        wallet_id=None,
        amount_cents=amount_cents,
        direction="outbound",
        description=f"Closer paid by host at door — mission {mission_id}",
        status="disbursed",
        counterparty=f"crypto:host_paid:{closer_wallet}",
        linked_mission_id=mission_id,
        a2a_ref=f"closer:{closer_tx_hash[:64]}",
        payment_category="host_direct_closer",
        resolved_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.commit()

    await log_activity(
        db,
        "closer_paid_host_direct",
        f"${amount_cents / 100:.2f} USDC host→closer — zero Commander OOP",
        {"mission_id": mission_id, "tx_hash": closer_tx_hash},
    )
    return row


async def settle_deferred_closers(db: AsyncSession) -> list[dict]:
    """
    Pay deferred closers from HOST-FUNDED treasury balance (bootstrap fuel).
    Commander still puts $0 in — play 1 USDC funds play 1 closer payout.
  Logs send instruction; treasury wallet already holds host money.
    """
    result = await db.execute(
        select(SovereignCloserPayout).where(SovereignCloserPayout.status == "deferred")
    )
    settled = []
    for row in result.scalars().all():
        entry = TreasuryLedger(
            wallet_id=None,
            amount_cents=row.amount_cents,
            direction="outbound",
            description=(
                f"Deferred closer payout — mission {row.mission_id} — "
                f"send from HOST-FUNDED treasury USDC to {row.closer_wallet}"
            ),
            status="disbursed",
            counterparty=f"crypto:deferred:{row.closer_wallet}",
            linked_mission_id=row.mission_id,
            payment_category="deferred_from_host_fuel",
            resolved_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        row.status = "paid_from_host_fuel"
        row.paid_at = datetime.now(timezone.utc)
        await db.commit()
        settled.append(
            {
                "payout_id": row.id,
                "closer_wallet": row.closer_wallet,
                "amount_usd": row.amount_cents / 100,
                "action": f"Send ${row.amount_cents / 100:.2f} USDC from treasury (host-funded) to closer",
            }
        )
    return settled
