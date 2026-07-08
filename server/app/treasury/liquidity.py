"""Treasury liquidity — deployable cash across ammo, float, and reserve."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AmmoPool, TreasuryLedger
from app.treasury.float import float_summary


async def liquidity_snapshot(db: AsyncSession) -> dict:
    """All deployable capital: ammo pools + float + cleared inbound reserve."""
    pools = list((await db.execute(select(AmmoPool))).scalars().all())
    ammo_cents = sum(p.balance_cents for p in pools)
    pool_by_cat = {p.category: p.balance_cents for p in pools}

    float_data = await float_summary(db)
    float_cents = float_data["float_cents"]

    cleared_cents = await db.scalar(
        select(func.coalesce(func.sum(TreasuryLedger.amount_cents), 0))
        .where(
            TreasuryLedger.direction == "inbound",
            TreasuryLedger.status == "cleared",
        )
    ) or 0

    disbursed_from_cleared = await db.scalar(
        select(func.coalesce(func.sum(TreasuryLedger.amount_cents), 0))
        .where(
            TreasuryLedger.direction == "outbound",
            TreasuryLedger.status == "disbursed",
        )
    ) or 0

    cleared_reserve = max(0, cleared_cents - disbursed_from_cleared)
    total_deployable = ammo_cents + float_cents + cleared_reserve

    return {
        "ammo_cents": ammo_cents,
        "ammo_usd": round(ammo_cents / 100, 2),
        "float_hold_cents": float_cents,
        "float_hold_usd": float_data["float_usd"],
        "float_active_holds": float_data["active_holds"],
        "cleared_reserve_cents": cleared_reserve,
        "cleared_reserve_usd": round(cleared_reserve / 100, 2),
        "total_deployable_cents": total_deployable,
        "total_deployable_usd": round(total_deployable / 100, 2),
        "pool_by_category": pool_by_cat,
    }
