"""What the empire can afford right now — capability snapshot."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AmmoPool, SovereignAcquisition, TreasuryLedger
from app.treasury.acquisitions import list_acquisitions
from app.treasury.categories import ACQUISITION_CATEGORIES
from app.treasury.empire import detect_empire_tier, effective_treasury_rates
from app.treasury.float import float_summary

CAPABILITY_BY_CATEGORY = {
    "compute": "Deploy city nodes, n8n HA, agent workers",
    "network": "Starlink failover, multi-WAN, command uplink independence",
    "storage": "Encrypted vault mirror, ledger backups, cold archive",
    "comms": "Sovereign mail — exit Gmail dependency",
    "voice": "Self-hosted SARA path — reduce Vapi lock-in",
    "security": "Hardware 2FA, treasury approval hardening",
    "physical_ops": "Ground force scale, mobile command, KC outreach",
    "energy": "Edge node uptime through outages",
}


def _acq_payload(acq: SovereignAcquisition, *, extra: dict | None = None) -> dict:
    remaining = max(0, acq.target_cost_cents - acq.funded_cents) if acq.target_cost_cents else 0
    pct = 100 if acq.status == "funded" else (
        round(acq.funded_cents / acq.target_cost_cents * 100, 1) if acq.target_cost_cents else 0
    )
    base = {
        "id": acq.id,
        "name": acq.name,
        "category": acq.category,
        "capability": CAPABILITY_BY_CATEGORY.get(acq.category, acq.description),
        "description": acq.description,
        "empire_tier": acq.empire_tier,
        "priority": acq.priority,
        "status": acq.status,
        "target_cost_cents": acq.target_cost_cents,
        "funded_cents": acq.funded_cents,
        "remaining_cents": remaining,
        "remaining_usd": round(remaining / 100, 2),
        "funded_percent": pct,
        "equipment_spec": acq.equipment_spec,
    }
    if extra:
        base.update(extra)
    return base


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

    # Approximate ops reserve still available (cleared minus paid out)
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


async def capability_snapshot(db: AsyncSession) -> dict:
    """
    At current liquidity and empire tier: what can we buy, unlock, or scale?
    """
    empire = await detect_empire_tier(db)
    tier = empire["tier"]
    rates = effective_treasury_rates(tier)
    liquidity = await liquidity_snapshot(db)
    pool_by_cat = liquidity["pool_by_category"]

    acquisitions = await list_acquisitions(db, empire_tier=tier)
    all_acquisitions = await list_acquisitions(db)

    ready_to_order: list[dict] = []
    affordable_now: list[dict] = []
    within_liquidity: list[dict] = []
    next_unlocks: list[dict] = []
    capability_gaps: list[dict] = []

    for acq in acquisitions:
        payload = _acq_payload(acq)
        remaining = payload["remaining_cents"]
        pool_bal = pool_by_cat.get(acq.category, 0)

        if acq.status == "funded" or (
            acq.target_cost_cents > 0 and acq.funded_cents >= acq.target_cost_cents
        ):
            ready_to_order.append({**payload, "reason": "Fully funded — Commander can order now"})
        elif acq.target_cost_cents == 0 and acq.status in ("needed", "researching"):
            affordable_now.append({
                **payload,
                "reason": "Deploy-only (no hardware cost) — agents can execute now",
            })
        elif remaining > 0 and pool_bal >= remaining:
            affordable_now.append({
                **payload,
                "reason": f"Category pool has ${pool_bal / 100:.2f} — covers ${remaining / 100:.2f} remaining",
            })
        elif remaining > 0 and liquidity["total_deployable_cents"] >= remaining:
            within_liquidity.append({
                **payload,
                "reason": f"Total deployable ${liquidity['total_deployable_usd']:.2f} covers ${remaining / 100:.2f}",
            })

        if acq.status in ("needed", "researching") and acq.target_cost_cents > 0:
            next_unlocks.append(payload)

        if acq.empire_tier <= tier and acq.status in ("needed", "researching"):
            capability_gaps.append(payload)

    next_unlocks.sort(key=lambda x: (-x["funded_percent"], -x["priority"]))
    capability_gaps.sort(key=lambda x: (-x["priority"], x["remaining_cents"]))

    # Project float growth: if current holds clear, ammo incoming at effective rate
    projected_ammo_from_float = int(
        liquidity["float_hold_cents"] * rates["ammo_percent"] / 100
    )

    recommended: list[str] = []
    if ready_to_order:
        names = ", ".join(r["name"] for r in ready_to_order[:3])
        recommended.append(f"Order now: {names}")
    if affordable_now and not ready_to_order:
        names = ", ".join(a["name"] for a in affordable_now[:3])
        recommended.append(f"Affordable with current ammo: {names}")
    if next_unlocks:
        top = next_unlocks[0]
        recommended.append(
            f"Closest unlock: {top['name']} at {top['funded_percent']}% "
            f"(${top['remaining_usd']:.2f} to go)"
        )
    if liquidity["float_hold_usd"] > 0:
        recommended.append(
            f"${liquidity['float_hold_usd']:.2f} in float clears in ~{rates['hold_hours']}h — "
            f"~${projected_ammo_from_float / 100:.2f} ammo incoming at tier {tier} rates"
        )
    if not recommended:
        recommended.append("Revenue nodes active — first host payment will seed ammo pools")

    voice_summary = (
        f"Empire tier {tier} {empire['label']}. "
        f"Ammo ${liquidity['ammo_usd']:.2f}, float ${liquidity['float_hold_usd']:.2f}, "
        f"total deployable ${liquidity['total_deployable_usd']:.2f}. "
    )
    if ready_to_order:
        voice_summary += f"Ready to order: {ready_to_order[0]['name']}. "
    elif affordable_now:
        voice_summary += f"You can afford: {affordable_now[0]['name']}. "
    elif next_unlocks:
        voice_summary += (
            f"Closest unlock: {next_unlocks[0]['name']} "
            f"at {next_unlocks[0]['funded_percent']}%."
        )

    return {
        "empire": empire,
        "effective_rates": rates,
        "liquidity": liquidity,
        "ready_to_order": ready_to_order,
        "affordable_now": affordable_now,
        "within_total_liquidity": within_liquidity,
        "next_unlocks": next_unlocks[:8],
        "capability_gaps": capability_gaps[:10],
        "categories": ACQUISITION_CATEGORIES,
        "capability_by_category": CAPABILITY_BY_CATEGORY,
        "manifest_total": len(all_acquisitions),
        "tier_visible_targets": len(acquisitions),
        "float_projection": {
            "clearing_ammo_cents": projected_ammo_from_float,
            "clearing_ammo_usd": round(projected_ammo_from_float / 100, 2),
            "hold_hours": rates["hold_hours"],
            "ammo_percent_at_tier": rates["ammo_percent"],
        },
        "recommended_actions": recommended,
        "voice_summary": voice_summary.strip(),
        "how_to_add": {
            "voice": 'Say "Add [item] to acquisition list" with category and priority',
            "api": "POST /api/treasury/acquisitions",
            "portal": "Empire tab → Add Target form",
        },
    }
