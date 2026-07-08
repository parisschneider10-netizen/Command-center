"""Human life force — what float/cash buys in guardian + RentAHuman capacity."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.treasury.liquidity import liquidity_snapshot

# Typical micro-task costs (align with ground force + RAH gigs)
MICRO_TASK_TIERS = [
    {"label": "Micro gig", "cost_usd": 20, "examples": "Sticker drop, simple errand"},
    {"label": "Standard gig", "cost_usd": 35, "examples": "Host visit, vendor call"},
    {"label": "Skilled gig", "cost_usd": 50, "examples": "VPS deploy, photo proof campaign"},
    {"label": "Guardian block", "cost_usd": 100, "examples": "Half-day judgment coverage"},
]


async def human_life_force_snapshot(db: AsyncSession) -> dict:
    """
    Translate treasury liquidity into human capacity the empire can deploy.
    Commander never posts gigs manually — system uses this to auto-post micro-tasks.
    """
    liquidity = await liquidity_snapshot(db)
    deployable_cents = liquidity["total_deployable_cents"]
    deployable_usd = liquidity["total_deployable_usd"]
    cap = settings.guardian_per_task_cap
    daily_cap = settings.commander_daily_budget_cap

    micro_at_20 = int(deployable_usd // 20) if deployable_usd >= 20 else 0
    micro_at_35 = int(deployable_usd // 35) if deployable_usd >= 35 else 0
    micro_at_cap = int(deployable_usd // cap) if deployable_usd >= cap else 0
    guardian_days = int(deployable_usd // daily_cap) if deployable_usd >= daily_cap else 0

    recommendations: list[str] = []
    if deployable_usd < 20:
        recommendations.append(
            "Low float — focus agent-only work until first host payment clears."
        )
    elif deployable_usd < 100:
        recommendations.append(
            f"Can deploy {micro_at_35} ground-force mission(s) at $35 each."
        )
    else:
        recommendations.append(
            f"Can deploy {micro_at_cap} micro-tasks at ${cap} cap + "
            f"{guardian_days} guardian-day equivalent at ${daily_cap}/day."
        )
    if liquidity["float_hold_usd"] > 0:
        recommendations.append(
            f"${liquidity['float_hold_usd']:.2f} in float clearing — "
            "human capacity increases when holds release."
        )

    return {
        "deployable_usd": deployable_usd,
        "deployable_cents": deployable_cents,
        "guardian_per_task_cap_usd": cap,
        "daily_human_budget_cap_usd": daily_cap,
        "capacity": {
            "micro_gigs_20_usd": micro_at_20,
            "standard_gigs_35_usd": micro_at_35,
            "tasks_at_guardian_cap": micro_at_cap,
            "guardian_day_equivalents": guardian_days,
        },
        "tiers": MICRO_TASK_TIERS,
        "firewall_slots": settings.human_firewall_size,
        "recommendations": recommendations,
        "voice_summary": (
            f"${deployable_usd:.2f} deployable. "
            f"Human life force: up to {micro_at_35} standard gigs "
            f"or {micro_at_cap} tasks at ${cap} cap. "
            f"Firewall has {settings.human_firewall_size} guardian slots."
        ),
    }
