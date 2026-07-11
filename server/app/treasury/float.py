"""48-hour float + worker payout after host payment clears."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import TreasuryLedger
from app.services import log_activity
from app.treasury.empire import detect_empire_tier, effective_treasury_rates


async def record_host_payment(
    db: AsyncSession,
    *,
    amount_cents: int,
    host_id: int,
    description: str,
    hold_hours: int | None = None,
    payment_category: str = "standard",
) -> TreasuryLedger:
    """
    Host pays upfront. Funds enter hold before worker payout.
    sales_close: 4h hold — ground force closer paid fast after on-site prepay.
    sandbox_instant: cleared immediately — ammo pools funded in real time (40×3 sandbox).
    """
    from app.treasury.allocation import allocate_cleared_revenue

    empire = await detect_empire_tier(db)
    rates = effective_treasury_rates(empire["tier"])
    now = datetime.now(timezone.utc)
    hours = hold_hours
    if hours is None:
        if payment_category in ("sandbox_instant", "crypto_instant") and settings.treasury_sandbox_instant_clear:
            hours = 0
        elif payment_category == "sales_close":
            hours = settings.treasury_sales_close_hold_hours
        else:
            hours = rates["hold_hours"]

    if hours <= 0:
        status = "cleared"
        release_at = now
    elif hours <= settings.treasury_sales_close_hold_hours:
        status = "hold_4h"
        release_at = now + timedelta(hours=hours)
    else:
        status = "hold_48h"
        release_at = now + timedelta(hours=hours)

    entry = TreasuryLedger(
        wallet_id=None,
        amount_cents=amount_cents,
        direction="inbound",
        description=description,
        status=status,
        counterparty=f"host:{host_id}",
        release_at=release_at,
        resolved_at=now if status == "cleared" else None,
        nuclear_required=False,
        payment_category=payment_category,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    if status == "cleared":
        await allocate_cleared_revenue(db, entry)
        await log_activity(
            db,
            "sandbox_instant_clear",
            f"${amount_cents / 100:.2f} cleared instantly → ammo pools",
            {"ledger_id": entry.id, "host_id": host_id, "category": payment_category},
        )
    else:
        await log_activity(
            db,
            "host_payment_hold",
            f"${amount_cents / 100:.2f} held until {release_at.isoformat()}",
            {"ledger_id": entry.id, "host_id": host_id, "float_hours": hours, "category": payment_category},
        )
    return entry


async def release_cleared_holds(db: AsyncSession) -> list[TreasuryLedger]:
    """Release holds past release_at — ready for worker payout."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(TreasuryLedger).where(
            TreasuryLedger.status.in_(("hold_48h", "hold_4h")),
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
        from app.treasury.allocation import allocate_cleared_revenue

        for entry in released:
            await allocate_cleared_revenue(db, entry)
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
    """Pay worker after mission complete. Sales-close: instant if host prepaid at door."""
    if from_ledger_id:
        parent = await db.get(TreasuryLedger, from_ledger_id)
        if not parent:
            raise ValueError("Parent payment not found")
        allowed = parent.status in ("cleared", "hold_48h", "hold_4h")
        if parent.payment_category in ("sales_close", "sandbox_instant", "crypto_instant") and parent.status in (
            "hold_4h",
            "hold_48h",
            "cleared",
        ):
            allowed = parent.amount_cents >= amount_cents
        if not allowed:
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
    """Active fiat float in hold window — scales with empire tier."""
    empire = await detect_empire_tier(db)
    rates = effective_treasury_rates(empire["tier"])
    result = await db.execute(
        select(TreasuryLedger).where(TreasuryLedger.status.in_(("hold_48h", "hold_4h")))
    )
    holds = list(result.scalars().all())
    total = sum(h.amount_cents for h in holds)
    projected_ammo = int(total * rates["ammo_percent"] / 100)
    return {
        "empire_tier": empire["tier"],
        "hold_hours": rates["hold_hours"],
        "ammo_percent": rates["ammo_percent"],
        "active_holds": len(holds),
        "float_cents": total,
        "float_usd": round(total / 100, 2),
        "projected_ammo_on_clear_usd": round(projected_ammo / 100, 2),
    }
