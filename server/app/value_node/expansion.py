"""STR expansion value node — Servury VPS + GHL sub-account per PM lead."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.velocity import effective_expansion_batch_cap
from app.integrations.ghl import create_subaccount
from app.integrations.n8n import trigger_n8n
from app.integrations.servury import provision_vps
from app.models import ScrapedLead
from app.services import log_activity
from app.treasury.service import request_spend


async def register_lead(db: AsyncSession, lead: dict, *, source: str = "api") -> ScrapedLead:
    existing = await db.execute(
        select(ScrapedLead).where(ScrapedLead.phone == lead["phone"])
    )
    row = existing.scalar_one_or_none()
    if row:
        return row

    entry = ScrapedLead(
        name=lead["name"],
        phone=lead["phone"],
        email=lead.get("email"),
        address=lead.get("address"),
        zip_code=lead.get("zip") or lead.get("zip_code"),
        city=lead["city"],
        crisis_type=lead.get("crisis_type", "Unautomated-STR-Leak"),
        status="scraped",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    await log_activity(
        db,
        "lead_scraped",
        f"Lead: {entry.name} — {entry.city}",
        {"source": source, "phone": entry.phone},
    )
    await trigger_n8n(
        "lead-intake",
        {
            "id": entry.id,
            "name": entry.name,
            "phone": entry.phone,
            "city": entry.city,
            "source": source,
        },
    )
    return entry


async def update_lead_status(
    db: AsyncSession, phone: str, status: str, **fields
) -> ScrapedLead | None:
    result = await db.execute(select(ScrapedLead).where(ScrapedLead.phone == phone))
    lead = result.scalar_one_or_none()
    if not lead:
        return None
    lead.status = status
    for key, val in fields.items():
        if hasattr(lead, key) and val is not None:
            setattr(lead, key, val)
    await db.commit()
    await db.refresh(lead)
    return lead


async def execute_city_lock(
    db: AsyncSession,
    target_lead: dict,
    *,
    dry_run: bool | None = None,
    wallet_id: int | None = None,
) -> dict:
    """Deploy Servury node + GHL sub-account for one PM lead."""
    dry = settings.expansion_dry_run if dry_run is None else dry_run
    city = target_lead["city"]
    pm_name = target_lead["name"]

    if not dry and wallet_id:
        await request_spend(
            db,
            wallet_id=wallet_id,
            amount_cents=settings.expansion_vps_cost_cents,
            description=f"Servury VPS — {city} — {pm_name}",
            counterparty="servury",
        )

    vps_result, ghl_result = await asyncio.gather(
        provision_vps(city_name=city, pm_name=pm_name, dry_run=dry),
        create_subaccount(pm_data=target_lead, city_name=city, dry_run=dry),
    )

    vps_ok = vps_result and not vps_result.get("error")
    ghl_ok = ghl_result and not ghl_result.get("error")

    if vps_ok and ghl_ok:
        lead = await register_lead(db, target_lead)
        await update_lead_status(
            db,
            target_lead["phone"],
            "infrastructure_locked",
            servury_server_id=str(vps_result.get("id")),
            servury_ip=vps_result.get("ip_address"),
            ghl_account_id=str(ghl_result.get("id")),
        )
        await log_activity(
            db,
            "city_node_locked",
            f"{city}: {pm_name} — IP {vps_result.get('ip_address')}",
            {"dry_run": dry, "city": city},
        )
        return {
            "success": True,
            "city": city,
            "ip": vps_result.get("ip_address"),
            "ghl_account_id": ghl_result.get("id"),
            "dry_run": dry,
        }

    await log_activity(
        db,
        "city_node_failed",
        f"Node failure in {city}",
        {"vps": vps_result, "ghl": ghl_result},
    )
    if not dry:
        await trigger_n8n(
            "expansion-failure",
            {"city": city, "pm": pm_name, "vps": vps_result, "ghl": ghl_result},
        )
    return {
        "success": False,
        "city": city,
        "vps": vps_result,
        "ghl": ghl_result,
        "dry_run": dry,
    }


async def scale_cities(
    db: AsyncSession,
    leads: list[dict],
    *,
    dry_run: bool | None = None,
    wallet_id: int | None = None,
) -> dict:
    """Lock infrastructure across N cities (parallel)."""
    dry = settings.expansion_dry_run if dry_run is None else dry_run
    cap = settings.expansion_max_cities
    batch_cap = effective_expansion_batch_cap()
    if not dry and len(leads) > batch_cap:
        return {
            "success": False,
            "error": (
                f"Live batch capped at {batch_cap} cities. "
                f"Set EXPANSION_LIVE_BATCH_CAP or use dry_run."
            ),
            "requested": len(leads),
        }

    targets = leads[:cap]
    results = []
    for lead in targets:
        result = await execute_city_lock(
            db, lead, dry_run=dry, wallet_id=wallet_id
        )
        results.append(result)

    successes = sum(1 for r in results if r.get("success"))
    summary = {
        "total": len(targets),
        "successful": successes,
        "dry_run": dry,
        "results": results,
    }
    await log_activity(
        db,
        "expansion_scale",
        f"Expansion: {successes}/{len(targets)} nodes",
        {"dry_run": dry, "successful": successes},
    )
    await trigger_n8n("expansion-complete", summary)
    return summary
