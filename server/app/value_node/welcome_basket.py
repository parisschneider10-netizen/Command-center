"""KC Welcome Basket play — host pays upfront, agents lock spec, humans shop + deliver."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.n8n import trigger_n8n
from app.models import LaundryHost, WelcomeBasketFulfillment
from app.services import log_activity
from app.treasury.float import record_host_payment

# Agent-locked standard KC new-host basket (Costco/Sams bulk pricing)
DEFAULT_BASKET_SPEC = """
KC New STR Host Welcome Basket (agent-locked SKU v1)
- Kirkland bottled water 24pk
- Local KC snack (Joe's KC bbq sauce OR Roasterie coffee sample)
- Travel tissues + hand sanitizer
- Printed welcome card w/ QR (laundry + host support)
- Single-serve detergent pods x3 (laundry upsell path)
- World Cup / KC visitor guide printout
Est. supply COGS at bulk: $14–18 per basket
"""

PACKAGE_SKUS: dict[str, dict] = {
    "launch_5pack": {
        "label": "New Host Launch Kit — 5 welcome baskets",
        "price_cents": 24900,
        "basket_credits": 5,
        "revenue_per_basket_cents": 4980,
        "pitch": "Every new guest feels premium. We shop, assemble, place in unit.",
    },
    "single_basket": {
        "label": "Single welcome basket",
        "price_cents": 7900,
        "basket_credits": 1,
        "revenue_per_basket_cents": 7900,
        "pitch": "One-time turn before your next booking.",
    },
    "bundle_laundry_intro": {
        "label": "Welcome 3-pack + laundry amenity intro",
        "price_cents": 19900,
        "basket_credits": 3,
        "revenue_per_basket_cents": 6633,
        "pitch": "Baskets now, laundry amenity QR for ongoing revenue.",
    },
}

# Per-basket unit economics (pay-on-completion labor from host float)
UNIT_ECONOMICS = {
    "supply_cogs_cents": 1600,
    "labor_team_cents": 6000,
    "labor_breakdown": {
        "shopper": 2200,
        "assembler": 2000,
        "deliver_place": 1800,
    },
    "margin_at_launch_5pack_cents": 4980 - 1600 - 6000,
    "note": "Positive margin when host prepays launch_5pack; labor paid only on photo proof.",
}


def launch_cost_summary() -> dict:
    """What Commander pays out-of-pocket to launch NOW."""
    return {
        "commander_cash_required_day_1_usd": 0,
        "why_zero_oop": [
            "Host pays BEFORE shopping (GHL/Stripe → treasury hold)",
            "RentAHuman paid ON COMPLETION from host float",
            "Supplies bought AFTER host payment clears hold window",
            "You can be shopper #1 on RentAHuman — pay yourself from host revenue",
        ],
        "optional_costs": {
            "servury_vps_if_not_live_usd": "4–20/mo",
            "ghl_if_new_account_usd": "97/mo or existing",
            "stripe_per_transaction": "2.9% + 30¢ on host prepay",
            "first_marketing_usd": "0 — guerrilla + host referrals",
        },
        "first_host_prepay_target_usd": 249,
        "first_host_covers": "5 baskets · ~$75 supplies · ~$60 labor · treasury margin + ammo",
        "packages": PACKAGE_SKUS,
        "unit_economics": UNIT_ECONOMICS,
        "scale_path": [
            "Host 1–3: You + 2 RentAHuman (shop / assemble / deliver)",
            "Host 4–10: Firewall guardians + RAH overflow",
            "Host 10+: Bulk Costco run · dedicated assembler · laundry upsell",
        ],
    }


async def register_basket_host(db: AsyncSession, data: dict) -> LaundryHost:
    host = LaundryHost(
        name=data["name"],
        phone=data["phone"],
        email=data.get("email"),
        address=data.get("address"),
        neighborhood=data.get("neighborhood"),
        unit_count=data.get("unit_count", 1),
        program="welcome_basket",
        status="lead",
    )
    db.add(host)
    await db.commit()
    await db.refresh(host)
    await log_activity(db, "welcome_basket_host", f"Host lead: {host.name}")
    await trigger_n8n("welcome-basket-host", {"host_id": host.id, "name": host.name})
    return host


async def lock_basket_spec(
    db: AsyncSession, host_id: int, spec: str | None = None
) -> LaundryHost:
    """Agent locks shopping list — no human shops until this is set."""
    host = await db.get(LaundryHost, host_id)
    if not host:
        raise ValueError("Host not found")
    host.locked_basket_spec = spec or DEFAULT_BASKET_SPEC.strip()
    host.status = "spec_locked"
    await db.commit()
    await db.refresh(host)
    await log_activity(db, "basket_spec_locked", f"Host {host_id} basket SKU locked")
    return host


async def record_package_prepay(
    db: AsyncSession,
    *,
    host_id: int,
    package_sku: str,
    amount_cents: int | None = None,
) -> dict:
    """Host pays upfront → 48h treasury float → funds labor + supplies."""
    pkg = PACKAGE_SKUS.get(package_sku)
    if not pkg:
        raise ValueError(f"Unknown package: {package_sku}")

    host = await db.get(LaundryHost, host_id)
    if not host:
        raise ValueError("Host not found")

    pay = amount_cents or pkg["price_cents"]
    host.prepaid_balance_cents += pay
    host.welcome_basket_credits += pkg["basket_credits"]
    host.program = "welcome_basket"
    host.status = "funded"
    if not host.locked_basket_spec:
        host.locked_basket_spec = DEFAULT_BASKET_SPEC.strip()

    ledger = await record_host_payment(
        db,
        amount_cents=pay,
        host_id=host_id,
        description=f"Welcome basket {package_sku} — {host.name}",
    )
    await db.commit()
    await trigger_n8n(
        "welcome-basket-funded",
        {
            "host_id": host_id,
            "package": package_sku,
            "credits": pkg["basket_credits"],
            "ledger_id": ledger.id,
        },
    )
    return {
        "ok": True,
        "host_id": host_id,
        "package": package_sku,
        "paid_cents": pay,
        "basket_credits": host.welcome_basket_credits,
        "float_ledger_id": ledger.id,
        "hold_hours": 48,
        "next_step": "POST /api/welcome-basket/fulfill/{host_id} after spec locked",
    }


async def fulfill_next_basket(db: AsyncSession, host_id: int, *, dry_run: bool = True) -> dict:
    """Deploy 3-person team: shop + assemble + deliver. Pay on completion from float."""
    from app.value_node.ground_force import deploy_basket_crew

    host = await db.get(LaundryHost, host_id)
    if not host:
        raise ValueError("Host not found")
    if host.welcome_basket_credits <= 0:
        raise ValueError("No basket credits — host must prepay first")
    if not host.locked_basket_spec:
        raise ValueError("Agent must lock basket spec first")

    fulfillment = WelcomeBasketFulfillment(
        host_id=host_id,
        basket_spec=host.locked_basket_spec,
        revenue_cents=UNIT_ECONOMICS["supply_cogs_cents"] + UNIT_ECONOMICS["labor_team_cents"],
        labor_budget_cents=UNIT_ECONOMICS["labor_team_cents"],
        status="dispatching",
    )
    db.add(fulfillment)
    await db.commit()
    await db.refresh(fulfillment)

    crew = await deploy_basket_crew(
        db,
        host_id=host_id,
        neighborhood=host.neighborhood or "KCMO",
        target_address=host.address,
        basket_spec=host.locked_basket_spec,
        dry_run=dry_run,
    )

    host.welcome_basket_credits -= 1
    fulfillment.status = "crew_dispatched"
    await db.commit()

    await log_activity(
        db,
        "welcome_basket_fulfill",
        f"Basket crew for host {host_id}",
        {"fulfillment_id": fulfillment.id, "crew": crew},
    )
    return {
        "ok": True,
        "fulfillment_id": fulfillment.id,
        "credits_remaining": host.welcome_basket_credits,
        "crew_missions": crew,
        "dry_run": dry_run,
    }
