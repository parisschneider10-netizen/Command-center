"""Empire tier detection — treasury rates scale as you expand."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import AmmoPool, GroundForceMission, LaundryHost, ScrapedLead

TIER_LABELS = {
    1: "Bootstrap",
    2: "Regional",
    3: "Multi-city",
    4: "National",
    5: "Full sovereign",
}

# Extra ammo % and hold-hour reduction as empire grows
TIER_AMMO_BONUS: dict[int, int] = {1: 0, 2: 5, 3: 10, 4: 15, 5: 20}
TIER_HOLD_REDUCTION_HOURS: dict[int, int] = {1: 0, 2: 0, 3: 6, 4: 12, 5: 24}


async def detect_empire_tier(db: AsyncSession) -> dict:
    """Infer empire tier from locked nodes, hosts, missions, and ammo velocity."""
    if settings.empire_tier_override:
        tier = min(5, max(1, settings.empire_tier_override))
        return {
            "tier": tier,
            "label": TIER_LABELS[tier],
            "override": True,
            "signals": {},
        }

    locked_cities = await db.scalar(
        select(func.count())
        .select_from(ScrapedLead)
        .where(ScrapedLead.status == "infrastructure_locked")
    ) or 0
    laundry_hosts = await db.scalar(
        select(func.count()).select_from(LaundryHost)
    ) or 0
    completed_missions = await db.scalar(
        select(func.count())
        .select_from(GroundForceMission)
        .where(GroundForceMission.status == "completed")
    ) or 0
    lifetime_ammo = await db.scalar(
        select(func.coalesce(func.sum(AmmoPool.allocated_total_cents), 0))
    ) or 0

    tier = 1
    if locked_cities >= 25 or lifetime_ammo >= 500_000:
        tier = 5
    elif locked_cities >= 10 or lifetime_ammo >= 200_000:
        tier = 4
    elif locked_cities >= 3 or lifetime_ammo >= 50_000:
        tier = 3
    elif locked_cities >= 1 or laundry_hosts >= 3 or completed_missions >= 5:
        tier = 2

    return {
        "tier": tier,
        "label": TIER_LABELS[tier],
        "override": False,
        "signals": {
            "locked_cities": locked_cities,
            "laundry_hosts": laundry_hosts,
            "completed_ground_missions": completed_missions,
            "lifetime_ammo_cents": lifetime_ammo,
            "lifetime_ammo_usd": round(lifetime_ammo / 100, 2),
        },
    }


def effective_treasury_rates(empire_tier: int) -> dict:
    """Ammo % and hold hours scale up/down with empire tier."""
    tier = min(5, max(1, empire_tier))
    ammo = min(90, settings.treasury_ammo_percent + TIER_AMMO_BONUS[tier])
    ops = 100 - ammo
    hold = max(12, settings.treasury_hold_hours - TIER_HOLD_REDUCTION_HOURS[tier])
    return {
        "empire_tier": tier,
        "ammo_percent": ammo,
        "ops_reserve_percent": ops,
        "hold_hours": hold,
        "tier_ammo_bonus": TIER_AMMO_BONUS[tier],
        "tier_hold_reduction_hours": TIER_HOLD_REDUCTION_HOURS[tier],
    }
