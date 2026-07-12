"""KC World Cup blitz — AI leads, humans close, 30-unit cap, fast float payout."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.integrations.n8n import trigger_n8n
from app.models import CityCap, GroundForceMission, KcHostLead, LaundryHost
from app.services import log_activity
from app.treasury.float import record_host_payment
from app.value_node.ground_force import deploy_mission
from app.value_node.welcome_basket import PACKAGE_SKUS, lock_basket_spec

LOCKED_HOST_STATUSES = ("locked", "funded", "active", "spec_locked")

CLOSE_SCRIPT = """
WORLD CUP KC — HOST CLOSE (read at door)
1. "We place premium welcome baskets before every guest — hosts book faster."
2. Show sample photo + QR (laundry upsell later).
3. CAP: Only {slots_remaining} unit slots left in KCMO at launch pricing.
4. Close: $249 launch_5pack (5 baskets) OR $79 single — pay NOW on phone (Stripe/GHL link).
5. Photo: signed one-pager OR payment confirmation screenshot.
PAY ON COMPLETION — you get paid when host pays at visit.
"""


async def ensure_kcmo_cap(db: AsyncSession) -> CityCap:
    result = await db.execute(select(CityCap).where(CityCap.city_code == "kcmo"))
    cap = result.scalar_one_or_none()
    if not cap:
        cap = CityCap(
            city_code="kcmo",
            city_name="Kansas City, MO",
            max_units=settings.kcmo_max_units,
            program="welcome_basket",
        )
        db.add(cap)
        await db.commit()
        await db.refresh(cap)
    return cap


async def count_locked_units(db: AsyncSession, city_code: str = "kcmo") -> int:
    """Units committed across locked welcome-basket hosts."""
    result = await db.execute(
        select(func.coalesce(func.sum(LaundryHost.unit_count), 0)).where(
            LaundryHost.program == "welcome_basket",
            LaundryHost.status.in_(LOCKED_HOST_STATUSES),
        )
    )
    return int(result.scalar() or 0)


async def blitz_status(db: AsyncSession) -> dict:
    cap = await ensure_kcmo_cap(db)
    locked = await count_locked_units(db)
    remaining = max(0, cap.max_units - locked)
    new_leads = await db.scalar(
        select(func.count()).select_from(KcHostLead).where(KcHostLead.status == "new")
    ) or 0
    closing = await db.scalar(
        select(func.count()).select_from(KcHostLead).where(KcHostLead.status == "closing")
    ) or 0
    won = await db.scalar(
        select(func.count()).select_from(KcHostLead).where(KcHostLead.status == "locked")
    ) or 0
    return {
        "city": cap.city_name,
        "city_code": cap.city_code,
        "max_units": cap.max_units,
        "locked_units": locked,
        "slots_remaining": remaining,
        "cap_full": remaining <= 0,
        "world_cup_urgency": "LOCK 30 HOSTS ASAP — KCMO",
        "leads": {"new": new_leads, "closing": closing, "locked": won},
        "close_pay_cents": 4500,
        "sales_hold_hours": settings.treasury_sales_close_hold_hours,
        "packages": {k: v["label"] for k, v in PACKAGE_SKUS.items()},
        "voice_summary": (
            f"KCMO blitz: {locked}/{cap.max_units} units locked, "
            f"{remaining} slots left. {new_leads} new leads ready. "
            f"Closers paid ${45} on host prepay at door."
        ),
    }


async def ingest_lead(db: AsyncSession, data: dict) -> KcHostLead:
    """AI or manual lead intake."""
    existing = await db.execute(
        select(KcHostLead).where(KcHostLead.phone == data["phone"])
    )
    row = existing.scalar_one_or_none()
    if row:
        return row
    lead = KcHostLead(
        name=data["name"],
        phone=data["phone"],
        email=data.get("email"),
        address=data.get("address"),
        neighborhood=data.get("neighborhood"),
        listing_url=data.get("listing_url"),
        unit_count=data.get("unit_count", 1),
        source=data.get("source", "ai_scrape"),
        package_sku=data.get("package_sku", "launch_5pack"),
        notes=data.get("notes"),
        status="new",
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    await log_activity(db, "kc_lead_ingested", f"Lead: {lead.name} — {lead.neighborhood}")
    await trigger_n8n("kc-blitz-lead", {"lead_id": lead.id, "neighborhood": lead.neighborhood})
    return lead


async def ingest_leads_batch(db: AsyncSession, leads: list[dict]) -> dict:
    created = []
    for data in leads:
        lead = await ingest_lead(db, data)
        created.append(lead.id)
    return {"ingested": len(created), "lead_ids": created}


async def dispatch_closer(
    db: AsyncSession,
    lead_id: int,
    *,
    dry_run: bool = True,
    pay_cents: int = 4500,
) -> dict:
    """Assign ground force closer — host_close_sale mission."""
    lead = await db.get(KcHostLead, lead_id)
    if not lead:
        return {"ok": False, "error": "Lead not found"}
    if lead.status == "locked":
        return {"ok": False, "error": "Lead already locked"}

    status = await blitz_status(db)
    if status["cap_full"]:
        return {"ok": False, "error": "KCMO cap full — 30 units locked"}

    slots = status["slots_remaining"]
    script = CLOSE_SCRIPT.format(slots_remaining=slots)
    pkg = PACKAGE_SKUS.get(lead.package_sku or "launch_5pack", PACKAGE_SKUS["launch_5pack"])

    result = await deploy_mission(
        db,
        mission_type="host_close_sale",
        neighborhood=lead.neighborhood or "KCMO",
        target_address=lead.address,
        pay_cents=pay_cents,
        dry_run=dry_run,
    )
    if not result.get("ok"):
        return result

    mission_id = result["mission_id"]
    mission = await db.get(GroundForceMission, mission_id)
    if mission:
        mission.lead_id = lead_id
        await db.commit()

    lead.status = "closing"
    lead.mission_id = mission_id
    await db.commit()

    await trigger_n8n(
        "kc-blitz-dispatch",
        {"lead_id": lead_id, "mission_id": mission_id, "package": lead.package_sku},
    )
    return {
        "ok": True,
        "lead_id": lead_id,
        "mission_id": mission_id,
        "pay_on_close_cents": pay_cents,
        "package_pitch": pkg["label"],
        "close_script": script,
        "slots_remaining": slots,
        "rentahuman": result.get("rentahuman"),
    }


async def close_sale_at_door(
    db: AsyncSession,
    *,
    lead_id: int,
    mission_id: int,
    host_prepay_cents: int,
    package_sku: str,
    proof_notes: str,
    worker_ref: str,
) -> dict:
    """
    Host paid on phone at visit → lock cap slot → instant closer payout from sales float.
    """
    from app.models import GroundForceMission
    from app.value_node.ground_force import complete_mission

    lead = await db.get(KcHostLead, lead_id)
    if not lead:
        return {"ok": False, "error": "Lead not found"}

    from app.models import GroundForceMission

    cap = await ensure_kcmo_cap(db)
    locked_units = await count_locked_units(db)
    units = lead.unit_count or 1
    if locked_units + units > cap.max_units:
        return {
            "ok": False,
            "error": f"Cap exceeded — only {cap.max_units - locked_units} units left",
        }

    pkg = PACKAGE_SKUS.get(package_sku, PACKAGE_SKUS["launch_5pack"])
    host = LaundryHost(
        name=lead.name,
        phone=lead.phone,
        email=lead.email,
        address=lead.address,
        neighborhood=lead.neighborhood,
        unit_count=units,
        program="welcome_basket",
        status="locked",
        welcome_basket_credits=pkg["basket_credits"],
        prepaid_balance_cents=host_prepay_cents,
    )
    db.add(host)
    await db.commit()
    await db.refresh(host)

    await lock_basket_spec(db, host.id)
    host.status = "funded"

    ledger = await record_host_payment(
        db,
        amount_cents=host_prepay_cents,
        host_id=host.id,
        description=f"KCMO blitz close — {package_sku} — {lead.name}",
        payment_category="sales_close",
    )
    await db.commit()

    mission = await db.get(GroundForceMission, mission_id)
    if mission:
        mission.host_payment_ledger_id = ledger.id
        mission.host_id = host.id
        await db.commit()

    payout = await complete_mission(
        db,
        mission_id,
        proof_notes,
        worker_ref,
        ledger_id=ledger.id,
    )

    lead.status = "locked"
    lead.host_id = host.id
    lead.closed_at = datetime.now(timezone.utc)
    lead.package_sku = package_sku
    await db.commit()

    new_status = await blitz_status(db)
    await log_activity(
        db,
        "kc_blitz_close",
        f"LOCKED {lead.name} — {units} units — ${host_prepay_cents/100:.2f}",
        {"lead_id": lead_id, "host_id": host.id, "ledger_id": ledger.id},
    )
    await trigger_n8n(
        "kc-blitz-locked",
        {
            "lead_id": lead_id,
            "host_id": host.id,
            "units_locked": new_status["locked_units"],
            "slots_remaining": new_status["slots_remaining"],
        },
    )

    return {
        "ok": True,
        "host_id": host.id,
        "ledger_id": ledger.id,
        "hold_hours": settings.treasury_sales_close_hold_hours,
        "instant_payout": "Closer paid — host prepay secured at door",
        "payout": payout,
        "blitz": new_status,
        "replicate": "Copy locked host playbook to remaining units in pipeline",
    }


async def blitz_dispatch_all_new(
    db: AsyncSession, *, limit: int = 10, dry_run: bool = True
) -> dict:
    """Dispatch closers to all new leads — World Cup speed."""
    result = await db.execute(
        select(KcHostLead).where(KcHostLead.status == "new").limit(limit)
    )
    dispatched = []
    for lead in result.scalars().all():
        r = await dispatch_closer(db, lead.id, dry_run=dry_run)
        if r.get("ok"):
            dispatched.append(r)
    return {"dispatched": len(dispatched), "missions": dispatched}
