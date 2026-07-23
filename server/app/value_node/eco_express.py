"""Eco-Express — D2C smart thermostat flips. No hosts. Hunters close, RAH installs."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.integrations.n8n import trigger_n8n
from app.leads.hunter import hunt_leads
from app.models import EcoExpressJob
from app.services import log_activity
from app.treasury.float import record_host_payment
from app.value_node.ground_force import complete_mission, deploy_mission

HUNTER_DOOR_PITCH = """Hi — Evergy utility crews are updating grid efficiency markers on this block this week. Your house likely has an older manual thermostat bleeding ~$180/year in wasted energy.

My company is running the Eco-Express Program right now. In 15 minutes we replace your wall unit with a brand-new Wi-Fi smart thermostat. With the local Evergy rebate, the hardware is FREE. You only pay a flat $149 for certified installation and programming.

We can put a technician on your wall right now or at 4:00 PM today. Which slot keeps your bills low?"""

INSTALLER_BRIEF = """15-minute smart thermostat swap. Photo proof REQUIRED: new unit powered on showing Wi-Fi icon. Pick up at Lowe's using barcode in this mission. Wire swap only — no HVAC duct work."""


def focus_zips() -> list[str]:
    return [z.strip() for z in settings.eco_focus_zips.split(",") if z.strip()]


def calculate_rebate_stack(
    *,
    retail_cents: int | None = None,
    evergy_rebate_cents: int | None = None,
    lowes_discount_pct: float | None = None,
) -> dict:
    """Stack Lowe's Pro volume + Evergy instant rebate → wholesale hardware cost."""
    retail = retail_cents or settings.eco_hardware_retail_cents
    rebate = evergy_rebate_cents or settings.eco_evergy_rebate_cents
    discount_pct = lowes_discount_pct if lowes_discount_pct is not None else settings.eco_lowes_pro_discount_pct
    pro_price = int(retail * (1 - discount_pct))
    out_of_pocket = max(0, pro_price - rebate)
    homeowner = settings.eco_homeowner_price_cents
    installer = settings.eco_installer_pay_cents
    net = homeowner - out_of_pocket - installer
    daily = net * settings.eco_daily_door_goal
    return {
        "retail_cents": retail,
        "lowes_pro_discount_pct": discount_pct,
        "pro_price_cents": pro_price,
        "evergy_rebate_cents": rebate,
        "hardware_out_of_pocket_cents": out_of_pocket,
        "homeowner_invoice_cents": homeowner,
        "installer_pay_cents": installer,
        "net_profit_cents": net,
        "net_profit_usd": round(net / 100, 2),
        "daily_goal_doors": settings.eco_daily_door_goal,
        "daily_profit_usd": round(daily / 100, 2),
        "monthly_profit_usd_30d": round(daily * 30 / 100, 2),
        "formula": "$149 homeowner - $50 hardware - $40 installer = $59 net/door",
    }


async def eco_status(db: AsyncSession) -> dict:
    """Dashboard snapshot for portal / SARA."""
    total = await db.scalar(select(func.count()).select_from(EcoExpressJob)) or 0
    paid = await db.scalar(
        select(func.count()).select_from(EcoExpressJob).where(EcoExpressJob.status.in_(("paid", "hardware_ordered", "install_dispatched", "completed")))
    ) or 0
    completed = await db.scalar(
        select(func.count()).select_from(EcoExpressJob).where(EcoExpressJob.status == "completed")
    ) or 0
    targeted = await db.scalar(
        select(func.count()).select_from(EcoExpressJob).where(EcoExpressJob.status == "targeted")
    ) or 0
    econ = calculate_rebate_stack()
    return {
        "program": "Eco-Express",
        "tagline": "D2C smart thermostat flips — zero hosts",
        "focus": f"{settings.eco_primary_city} metro (Evergy rebate MO)",
        "zips": focus_zips(),
        "year_built_window": [settings.eco_year_built_min, settings.eco_year_built_max],
        "economics": econ,
        "jobs": {
            "targeted": targeted,
            "paid": paid,
            "completed": completed,
            "total": total,
        },
        "hunter_pitch": HUNTER_DOOR_PITCH,
        "voice_summary": (
            f"Eco-Express: {completed} installs done, {targeted} doors on strike list. "
            f"${econ['net_profit_usd']}/door net, goal {settings.eco_daily_door_goal}/day."
        ),
    }


async def generate_strike_list(
    db: AsyncSession,
    *,
    max_targets: int = 30,
) -> dict:
    """Loop A — hunt KCMO homeowners in focus zips, queue as targeted jobs."""
    zips = focus_zips()
    hunt = await hunt_leads(
        db,
        city=settings.eco_primary_city,
        max_leads=max_targets,
        source="eco_strike",
        profile="eco_homeowner",
        focus_zips=zips,
    )
    created = []
    zip_idx = 0
    for item in hunt.get("leads", []):
        phone = item.get("phone", "")
        if phone.startswith("pending-"):
            continue
        existing = await db.execute(
            select(EcoExpressJob).where(EcoExpressJob.phone == phone)
        )
        if existing.scalar_one_or_none():
            continue
        zip_code = zips[zip_idx % len(zips)] if zips else "64111"
        zip_idx += 1
        job = EcoExpressJob(
            homeowner_name=item.get("name", "Homeowner")[:255],
            phone=phone,
            address=(item.get("address") or f"{item.get('name', 'Residential')} — {zip_code} KCMO")[:500],
            zip_code=zip_code,
            neighborhood="KCMO",
            year_built=1985,
            status="targeted",
            hardware_cost_cents=calculate_rebate_stack()["hardware_out_of_pocket_cents"],
            homeowner_paid_cents=settings.eco_homeowner_price_cents,
            installer_pay_cents=settings.eco_installer_pay_cents,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        created.append({"id": job.id, "name": job.homeowner_name, "phone": job.phone})
    await log_activity(db, "eco_strike_list", f"Strike list: {len(created)} doors", {"created": created})
    await trigger_n8n("eco-express-strike", {"count": len(created), "jobs": created})
    return {"ok": True, "strike_list": created, "hunt": hunt}


async def dispatch_hunter(db: AsyncSession, job_id: int, *, dry_run: bool = True) -> dict:
    """Arm hunter with doorstep pitch + address (field close — no RAH until paid)."""
    job = await db.get(EcoExpressJob, job_id)
    if not job:
        return {"ok": False, "error": "Job not found"}
    job.status = "hunter_ready"
    job.notes = (job.notes or "") + f"\nHunter briefed dry_run={dry_run}"
    await db.commit()
    await log_activity(db, "eco_hunter_ready", job.address, {"job_id": job_id})
    return {
        "ok": True,
        "job_id": job_id,
        "pitch": HUNTER_DOOR_PITCH,
        "address": job.address,
        "phone": job.phone,
        "collect_cents": job.homeowner_paid_cents,
    }


async def confirm_homeowner_payment(
    db: AsyncSession,
    job_id: int,
    *,
    payment_proof: str,
    scheduled_slot: str = "ASAP",
    dry_run: bool = False,
) -> dict:
    """Loop B — homeowner paid $149 → treasury + Lowe's pickup + installer dispatch."""
    job = await db.get(EcoExpressJob, job_id)
    if not job:
        return {"ok": False, "error": "Job not found"}

    ledger = await record_host_payment(
        db,
        amount_cents=job.homeowner_paid_cents,
        host_id=job.id,
        description=f"Eco-Express homeowner — {job.address}",
        payment_category="sales_close",
        hold_hours=settings.treasury_hold_hours,
    )
    job.payment_ledger_id = ledger.id
    job.payment_proof = payment_proof
    job.scheduled_slot = scheduled_slot
    job.paid_at = datetime.now(timezone.utc)
    job.status = "paid"
    await db.commit()

    barcode = await _place_lowes_pickup_order(job)
    job.lowes_pickup_barcode = barcode
    job.status = "hardware_ordered"
    await db.commit()

    install = await deploy_mission(
        db,
        mission_type="eco_thermostat_install",
        neighborhood=job.neighborhood or job.zip_code,
        target_address=job.address,
        pay_cents=job.installer_pay_cents,
        dry_run=dry_run,
    )
    if install.get("ok"):
        job.install_mission_id = install["mission_id"]
        job.status = "install_dispatched"
        await db.commit()

    await trigger_n8n(
        "eco-express-paid",
        {"job_id": job.id, "barcode": barcode, "install_mission_id": job.install_mission_id},
    )
    return {
        "ok": True,
        "job_id": job.id,
        "ledger_id": ledger.id,
        "lowes_pickup_barcode": barcode,
        "install": install,
        "net_profit_cents": job.homeowner_paid_cents - job.hardware_cost_cents - job.installer_pay_cents,
    }


async def _place_lowes_pickup_order(job: EcoExpressJob) -> str:
    """Lowe's Pro Extended Aisle + Evergy rebate validation (stub until API keys wired)."""
    token = secrets.token_hex(6).upper()
    barcode = f"LOWES-ECO-{job.id}-{token}"
    await trigger_n8n(
        "eco-lowes-pickup",
        {
            "job_id": job.id,
            "barcode": barcode,
            "address": job.address,
            "zip": job.zip_code,
            "hardware_cost_cents": job.hardware_cost_cents,
            "evergy_rebate_cents": settings.eco_evergy_rebate_cents,
            "lowes_pro_account": settings.lowes_pro_account_id or "configure LOWES_PRO_ACCOUNT_ID",
        },
    )
    return barcode


def _photo_proof_valid(proof: str) -> bool:
    lower = (proof or "").lower()
    if not lower.strip():
        return False
    if "http" in lower or "wifi" in lower or "wi-fi" in lower or "photo" in lower:
        return True
    return len(lower) > 40


async def complete_install(
    db: AsyncSession,
    job_id: int,
    *,
    thermostat_photo_proof: str,
    worker_ref: str = "rah:installer",
) -> dict:
    """Loop C — photo proof or freeze installer payout (net-48)."""
    job = await db.get(EcoExpressJob, job_id)
    if not job:
        return {"ok": False, "error": "Job not found"}
    if not job.install_mission_id:
        return {"ok": False, "error": "No install mission dispatched"}

    job.thermostat_photo_proof = thermostat_photo_proof
    if not _photo_proof_valid(thermostat_photo_proof):
        job.payout_frozen = True
        job.status = "payout_frozen"
        await db.commit()
        await log_activity(
            db,
            "eco_payout_frozen",
            f"Job {job.id} — missing Wi-Fi photo proof",
            {"job_id": job.id},
        )
        return {
            "ok": False,
            "error": "Photo proof required — thermostat powered on with Wi-Fi icon visible",
            "payout_frozen": True,
            "job_id": job.id,
        }

    payout = await complete_mission(
        db,
        job.install_mission_id,
        proof_notes=f"Eco-Express install verified. {thermostat_photo_proof}",
        worker_ref=worker_ref,
        ledger_id=job.payment_ledger_id,
    )
    job.status = "completed"
    job.completed_at = datetime.now(timezone.utc)
    job.payout_frozen = False
    await db.commit()
    await trigger_n8n("eco-express-complete", {"job_id": job.id, "payout": payout})
    return {
        "ok": True,
        "job_id": job.id,
        "payout": payout,
        "net_profit_cents": job.homeowner_paid_cents - job.hardware_cost_cents - job.installer_pay_cents,
    }


async def list_jobs(db: AsyncSession, limit: int = 50) -> list[dict]:
    result = await db.execute(
        select(EcoExpressJob).order_by(desc(EcoExpressJob.created_at)).limit(limit)
    )
    rows = []
    for j in result.scalars().all():
        rows.append(
            {
                "id": j.id,
                "homeowner_name": j.homeowner_name,
                "phone": j.phone,
                "address": j.address,
                "zip_code": j.zip_code,
                "status": j.status,
                "scheduled_slot": j.scheduled_slot,
                "net_profit_cents": j.homeowner_paid_cents - j.hardware_cost_cents - j.installer_pay_cents,
                "payout_frozen": j.payout_frozen,
            }
        )
    return rows


async def hunter_close_sheet(db: AsyncSession) -> dict:
    """Printable strike sheet for field closer — phones + pitch."""
    jobs = await list_jobs(db, limit=50)
    ready = [j for j in jobs if j["status"] in ("targeted", "hunter_ready")]
    return {
        "city": settings.eco_primary_city,
        "why_this_city": (
            "Kansas City MO — Evergy rebate stack, 1970–2005 housing stock, "
            "suburban doors without host/STR complexity."
        ),
        "pitch": HUNTER_DOOR_PITCH,
        "collect_usd": settings.eco_homeowner_price_cents / 100,
        "doors": ready,
        "count": len(ready),
        "with_phone": sum(1 for j in ready if j.get("phone") and not str(j["phone"]).startswith("pending")),
    }
