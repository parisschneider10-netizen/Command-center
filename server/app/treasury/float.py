"""48-hour float + worker payout after host payment clears."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import TreasuryLedger
from app.services import log_activity


async def record_host_payment(
    db: AsyncSession,
    *,
    amount_cents: int,
    host_id: int,
    description: str,
) -> TreasuryLedger:
    """
    Host pays upfront. Funds enter 48h hold before ground force / workers paid.
    Float window = treasury_hold_hours (default 48).
    """
    release_at = datetime.now(timezone.utc) + timedelta(hours=settings.treasury_hold_hours)
    entry = TreasuryLedger(
        wallet_id=None,
        amount_cents=amount_cents,
        direction="inbound",
        description=description,
        status="hold_48h",
        counterparty=f"host:{host_id}",
        release_at=release_at,
        nuclear_required=False,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    await log_activity(
        db,
        "host_payment_hold",
        f"${amount_cents / 100:.2f} held until {release_at.isoformat()}",
        {"ledger_id": entry.id, "host_id": host_id, "float_hours": settings.treasury_hold_hours},
    )
    return entry


async def release_cleared_holds(db: AsyncSession) -> list[TreasuryLedger]:
    """Release holds past release_at — ready for worker payout."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(TreasuryLedger).where(
            TreasuryLedger.status == "hold_48h",
            TreasuryLedger.release_at <= now,
        )
    )
    released = []
    for entry in result.scalars().all():
        entry.status = "cleared"
        entry.resolved_at = now
        released.append(entry)
    if released:
        await db.commit()
        await log_activity(
            db,
            "float_cleared",
            f"{len(released)} payment(s) cleared for worker payout",
        )
    return released


async def payout_worker(
    db: AsyncSession,
    *,
    amount_cents: int,
    mission_id: int,
    worker_ref: str,
    from_ledger_id: int | None = None,
) -> TreasuryLedger:
    """Pay RentAHuman worker after mission complete + hold cleared."""
    if from_ledger_id:
        parent = await db.get(TreasuryLedger, from_ledger_id)
        if not parent or parent.status not in ("cleared", "hold_48h"):
            raise ValueError("Parent payment not cleared for payout")

    entry = TreasuryLedger(
        wallet_id=None,
        amount_cents=amount_cents,
        direction="outbound",
        description=f"Ground force payout — mission {mission_id}",
        status="disbursed",
        counterparty=worker_ref,
        linked_mission_id=mission_id,
        resolved_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    await log_activity(
        db,
        "ground_force_payout",
        f"${amount_cents / 100:.2f} → {worker_ref}",
        {"mission_id": mission_id},
    )
    return entry


async def float_summary(db: AsyncSession) -> dict:
    """Active fiat float in 48h hold window."""
    result = await db.execute(
        select(TreasuryLedger).where(TreasuryLedger.status == "hold_48h")
    )
    holds = list(result.scalars().all())
    total = sum(h.amount_cents for h in holds)
    return {
        "hold_hours": settings.treasury_hold_hours,
        "active_holds": len(holds),
        "float_cents": total,
        "float_usd": round(total / 100, 2),
    }
