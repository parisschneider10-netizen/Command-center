"""Transform cleared revenue into ammo — every penny funds empire expansion."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import AmmoAllocation, AmmoPool, TreasuryLedger
from app.services import log_activity
from app.treasury.acquisitions import auto_fund_top_priorities, ensure_ammo_pools
from app.treasury.categories import DEFAULT_AMMO_WEIGHTS


async def allocate_cleared_revenue(
    db: AsyncSession,
    ledger_entry: TreasuryLedger,
) -> list[AmmoAllocation]:
    """
    When host payment clears hold, split revenue:
    - ops_reserve_percent → stays as cleared fiat (worker payouts)
    - ammo_percent → category ammo pools → auto-fund acquisitions
    """
    if ledger_entry.direction != "inbound" or ledger_entry.status != "cleared":
        return []

    existing = await db.execute(
        select(AmmoAllocation).where(AmmoAllocation.source_ledger_id == ledger_entry.id)
    )
    if existing.scalar_one_or_none():
        return []

    total = ledger_entry.amount_cents
    ammo_total = int(total * settings.treasury_ammo_percent / 100)
    if ammo_total <= 0:
        return []

    await ensure_ammo_pools(db)
    allocations: list[AmmoAllocation] = []
    weight_sum = sum(DEFAULT_AMMO_WEIGHTS.values())

    for category, weight in DEFAULT_AMMO_WEIGHTS.items():
        amount = int(ammo_total * weight / weight_sum)
        if amount <= 0:
            continue

        pool_result = await db.execute(select(AmmoPool).where(AmmoPool.category == category))
        pool = pool_result.scalar_one()
        pool.balance_cents += amount
        pool.allocated_total_cents += amount

        alloc = AmmoAllocation(
            source_ledger_id=ledger_entry.id,
            category=category,
            amount_cents=amount,
            description=(
                f"Ammo from {ledger_entry.description} "
                f"(${ledger_entry.amount_cents / 100:.2f} inbound, "
                f"{settings.treasury_ammo_percent}% ammo split)"
            ),
        )
        db.add(alloc)
        allocations.append(alloc)

    await db.commit()
    await log_activity(
        db,
        "revenue_to_ammo",
        f"${ammo_total / 100:.2f} ammo from ledger {ledger_entry.id}",
        {
            "ledger_id": ledger_entry.id,
            "ammo_cents": ammo_total,
            "categories": len(allocations),
        },
    )

    await auto_fund_top_priorities(db)
    return allocations


async def ammo_summary(db: AsyncSession) -> dict:
    """Ammo pool balances and recent allocations."""
    pools = list(
        (await db.execute(select(AmmoPool).order_by(AmmoPool.category))).scalars().all()
    )
    recent = list(
        (
            await db.execute(
                select(AmmoAllocation).order_by(AmmoAllocation.created_at.desc()).limit(50)
            )
        )
        .scalars()
        .all()
    )
    total_balance = sum(p.balance_cents for p in pools)
    total_lifetime = sum(p.allocated_total_cents for p in pools)
    return {
        "total_balance_cents": total_balance,
        "total_balance_usd": round(total_balance / 100, 2),
        "lifetime_allocated_cents": total_lifetime,
        "pools": [
            {
                "category": p.category,
                "balance_cents": p.balance_cents,
                "allocated_total_cents": p.allocated_total_cents,
            }
            for p in pools
        ],
        "recent_allocations": [
            {
                "id": a.id,
                "category": a.category,
                "amount_cents": a.amount_cents,
                "source_ledger_id": a.source_ledger_id,
                "description": a.description,
                "created_at": a.created_at.isoformat(),
            }
            for a in recent
        ],
        "rules": {
            "ammo_percent": settings.treasury_ammo_percent,
            "ops_reserve_percent": settings.treasury_ops_reserve_percent,
            "category_weights": DEFAULT_AMMO_WEIGHTS,
        },
    }
