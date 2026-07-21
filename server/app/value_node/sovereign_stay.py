"""Sovereign Stay Systems V1 — asset-light egoist arbitrage matrix."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.integrations.n8n import trigger_n8n
from app.models import CityCap, SovereignHost, SovereignLedgerEvent
from app.services import log_activity
from app.treasury.float import record_host_payment
from app.treasury.crypto_rail import (
    current_payment_mode,
    defer_closer_payout,
    record_closer_paid_by_host,
    record_crypto_treasury_inbound,
    settle_deferred_closers,
    treasury_receive_instructions,
)
from app.value_node.ground_force import complete_mission, deploy_mission

DEFAULT_BADGES = ["FREE_CHECKOUT_RIDE", "VERIFIED_MATCHDAY_WASH"]

MATRIX_CONFIG = {
    "target_cities": lambda: settings.sovereign_target_cities,
    "units_per_city": lambda: settings.sovereign_units_per_city,
    "focus_city": lambda: settings.sovereign_focus_city,
    "max_hosts": lambda: settings.sovereign_target_cities * settings.sovereign_units_per_city,
    "upfront_fee_usd": lambda: settings.sovereign_upfront_fee_cents / 100,
    "closer_bounty_usd": lambda: settings.sovereign_closer_bounty_cents / 100,
    "management_fee_pct": lambda: settings.sovereign_management_fee_pct,
    "rentahuman_bounty_usd": lambda: settings.sovereign_rentahuman_bounty_cents / 100,
}


def _city_code(city_grid: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", city_grid.lower()).strip("_")
    return slug[:32] or "unknown"


def _resolve_config() -> dict:
    return {k: fn() for k, fn in MATRIX_CONFIG.items()}


async def ensure_city_grid(db: AsyncSession, city_grid: str) -> CityCap:
    code = _city_code(city_grid)
    result = await db.execute(
        select(CityCap).where(
            CityCap.city_code == code,
            CityCap.program == "sovereign_stay",
        )
    )
    cap = result.scalar_one_or_none()
    if not cap:
        cap = CityCap(
            city_code=code,
            city_name=city_grid,
            max_units=settings.sovereign_units_per_city,
            program="sovereign_stay",
        )
        db.add(cap)
        await db.commit()
        await db.refresh(cap)
    return cap


async def count_city_units(db: AsyncSession, city_code: str) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(SovereignHost)
        .where(SovereignHost.city_code == city_code, SovereignHost.status == "ACTIVE_LOCK_IN")
    )
    return int(result.scalar() or 0)


async def matrix_status(db: AsyncSession) -> dict:
    cfg = _resolve_config()
    cities = await db.scalar(
        select(func.count())
        .select_from(CityCap)
        .where(CityCap.program == "sovereign_stay")
    ) or 0
    locked_hosts = await db.scalar(
        select(func.count())
        .select_from(SovereignHost)
        .where(SovereignHost.status == "ACTIVE_LOCK_IN")
    ) or 0
    max_units = cfg["target_cities"] * cfg["units_per_city"]
    float_cents = await db.scalar(
        select(func.coalesce(func.sum(SovereignHost.net_float_cents), 0)).select_from(SovereignHost)
    ) or 0
    vault_cents = await db.scalar(
        select(func.coalesce(func.sum(SovereignHost.vault_reserve_cents), 0)).select_from(SovereignHost)
    ) or 0
    return {
        "system": "SOVEREIGN_STAY_SYSTEMS_V1_CORE",
        "purpose": f"Focus play — {cfg['max_hosts']} hosts in {cfg['focus_city']}. Scale cities later.",
        "config": cfg,
        "scale": {
            "target_cities": cfg["target_cities"],
            "units_per_city": cfg["units_per_city"],
            "focus_city": cfg["focus_city"],
            "max_units": max_units,
            "cities_initialized": cities,
            "hosts_locked": locked_hosts,
            "slots_remaining": max(0, max_units - locked_hosts),
        },
        "float_usd": round(float_cents / 100, 2),
        "vault_reserve_usd": round(vault_cents / 100, 2),
        "badges_default": DEFAULT_BADGES,
        "voice_summary": (
            f"Sovereign Stay: {locked_hosts}/{max_units} hosts locked in {cfg['focus_city']}. "
            f"${float_cents/100:.0f} net float. Scale to more cities when these 3 are cash-flowing."
        ),
    }


async def commit_to_private_ledger(
    db: AsyncSession,
    *,
    event_type: str,
    payload: dict,
    host_id: int | None = None,
) -> SovereignLedgerEvent:
    """DeFi recording layer — DB + append-only JSONL on VPS disk."""
    row = SovereignLedgerEvent(
        event_type=event_type,
        host_id=host_id,
        payload_json=json.dumps(payload, default=str),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    ledger_path = Path(settings.sovereign_ledger_path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {"id": row.id, "event_type": event_type, "host_id": host_id, **payload},
        default=str,
    )
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return row


async def process_onboarding_presale(
    db: AsyncSession,
    *,
    host_name: str,
    property_address: str,
    city_grid: str,
    worker_ref: str,
    proof_notes: str,
    dry_run_closer: bool = True,
) -> dict:
    """
    Layer 1: Same-day upfront cash extraction at doorstep.
    $150 collected → $30 closer → $120 net float → $20 Cursor earmark → $100 vault.
    """
    cap = await ensure_city_grid(db, city_grid)
    locked = await count_city_units(db, cap.city_code)
    if locked >= cap.max_units:
        return {
            "ok": False,
            "error": f"City grid full — {cap.max_units} units max in {city_grid}",
        }

    gross = settings.sovereign_upfront_fee_cents
    closer_cut = settings.sovereign_closer_bounty_cents
    net_float = gross - closer_cut
    cursor_earmark = settings.sovereign_cursor_earmark_cents
    vault_reserve = net_float - cursor_earmark

    dispatch = await deploy_mission(
        db,
        mission_type="sovereign_presale_close",
        neighborhood=city_grid,
        target_address=property_address,
        pay_cents=closer_cut,
        dry_run=dry_run_closer,
    )
    if not dispatch.get("ok"):
        return dispatch

    mission_id = dispatch["mission_id"]
    external_id = f"HOST_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    host = SovereignHost(
        external_id=external_id,
        host_name=host_name,
        property_address=property_address,
        city_grid=city_grid,
        city_code=cap.city_code,
        badges_json=json.dumps(DEFAULT_BADGES),
        status="ACTIVE_LOCK_IN",
        gross_collected_cents=gross,
        closer_cut_cents=closer_cut,
        net_float_cents=net_float,
        cursor_earmark_cents=cursor_earmark,
        vault_reserve_cents=vault_reserve,
        closer_mission_id=mission_id,
    )
    db.add(host)
    await db.commit()
    await db.refresh(host)

    ledger = await record_host_payment(
        db,
        amount_cents=gross,
        host_id=host.id,
        description=f"Sovereign Stay presale — {host_name} — {city_grid}",
        payment_category="sandbox_instant",
    )
    host.inbound_ledger_id = ledger.id
    await db.commit()

    payout = await complete_mission(
        db,
        mission_id,
        proof_notes,
        worker_ref,
        ledger_id=ledger.id,
    )

    host_profile = {
        "id": external_id,
        "host_id": host.id,
        "timestamp": host.created_at.isoformat(),
        "host_name": host_name,
        "property_address": property_address,
        "city_grid": city_grid,
        "badges_deployed": DEFAULT_BADGES,
        "status": host.status,
        "financials": {
            "gross_collected": gross / 100,
            "closer_cut": closer_cut / 100,
            "net_float_generated": net_float / 100,
            "earmarked_cursor_pro_compute": cursor_earmark / 100,
            "net_vault_reserve": vault_reserve / 100,
        },
        "ledger_id": ledger.id,
        "payout": payout,
    }

    await commit_to_private_ledger(
        db,
        event_type="LAYER_1_EXTRACTION",
        payload=host_profile,
        host_id=host.id,
    )
    await log_activity(
        db,
        "sovereign_presale",
        f"LAYER 1: {host_name} — ${gross/100:.0f} — {city_grid}",
        {"host_id": host.id, "ledger_id": ledger.id},
    )
    await trigger_n8n("sovereign-presale-locked", host_profile)

    status = await matrix_status(db)
    return {"ok": True, "layer": 1, "host_profile": host_profile, "matrix": status}


async def crypto_receive_brief(db: AsyncSession) -> dict:
    """Closer door script — bootstrap first fuel, then host-paid split."""
    return await treasury_receive_instructions(db)


async def process_crypto_presale(
    db: AsyncSession,
    *,
    host_name: str,
    property_address: str,
    city_grid: str,
    treasury_tx_hash: str,
    closer_wallet: str,
    worker_ref: str,
    closer_tx_hash: str | None = None,
    proof_notes: str = "",
    dry_run_closer: bool = True,
    mission_id: int | None = None,
) -> dict:
    """
    Zero Commander OOP crypto presale.
    bootstrap: host → 100% treasury (first fuel). Closer deferred.
    split: host → treasury + closer direct (2 txs). Commander wallet untouched.
    """
    from app.hive.empire_research import trigger_empire_research_on_fuel
    from app.models import GroundForceMission

    cap = await ensure_city_grid(db, city_grid)
    locked = await count_city_units(db, cap.city_code)
    if locked >= cap.max_units:
        return {"ok": False, "error": f"City grid full — {cap.max_units} units max in {city_grid}"}

    if not settings.treasury_usdc_address:
        return {"ok": False, "error": "TREASURY_USDC_ADDRESS not set in VPS .env"}

    mode = await current_payment_mode(db)
    gross = settings.sovereign_upfront_fee_cents
    closer_cut = settings.sovereign_closer_bounty_cents
    treasury_cents = gross if mode == "bootstrap" else gross - closer_cut

    if not mission_id:
        dispatch = await deploy_mission(
            db,
            mission_type="sovereign_presale_close",
            neighborhood=city_grid,
            target_address=property_address,
            pay_cents=closer_cut,
            dry_run=dry_run_closer,
        )
        if not dispatch.get("ok"):
            return dispatch
        mission_id = dispatch["mission_id"]

    try:
        external_id = f"HOST_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        host = SovereignHost(
            external_id=external_id,
            host_name=host_name,
            property_address=property_address,
            city_grid=city_grid,
            city_code=cap.city_code,
            badges_json=json.dumps(DEFAULT_BADGES),
            status="ACTIVE_LOCK_IN",
            gross_collected_cents=gross,
            closer_cut_cents=closer_cut,
            net_float_cents=treasury_cents if mode == "bootstrap" else treasury_cents,
            cursor_earmark_cents=min(settings.sovereign_cursor_earmark_cents, treasury_cents),
            vault_reserve_cents=max(0, treasury_cents - settings.sovereign_cursor_earmark_cents),
            closer_mission_id=mission_id,
        )
        db.add(host)
        await db.commit()
        await db.refresh(host)

        ledger = await record_crypto_treasury_inbound(
            db,
            amount_cents=treasury_cents,
            host_id=host.id,
            tx_hash=treasury_tx_hash,
            description=f"Crypto presale ({mode}) — {host_name} — {city_grid}",
            payment_mode=mode,
        )
        host.inbound_ledger_id = ledger.id
        await db.commit()

        closer_result: dict = {}
        if mode == "bootstrap":
            deferred = await defer_closer_payout(
                db,
                mission_id=mission_id,
                host_id=host.id,
                closer_wallet=closer_wallet,
                amount_cents=closer_cut,
            )
            closer_result = {
                "status": "deferred",
                "payout_id": deferred.id,
                "message": (
                    "First fuel secured. Closer paid from host-funded treasury on play 2+. "
                    "Zero Commander OOP."
                ),
            }
        else:
            if not closer_tx_hash:
                raise ValueError("split mode requires closer_tx_hash — host pays closer at door")
            paid = await record_closer_paid_by_host(
                db,
                mission_id=mission_id,
                host_id=host.id,
                closer_wallet=closer_wallet,
                amount_cents=closer_cut,
                closer_tx_hash=closer_tx_hash,
            )
            closer_result = {
                "status": "paid_host_direct",
                "payout_id": paid.id,
                "closer_tx_hash": closer_tx_hash,
                "message": "Host paid closer directly. Commander wallet not used.",
            }
            deferred_settled = await settle_deferred_closers(db)
            if deferred_settled:
                closer_result["deferred_settled"] = deferred_settled

        mission = await db.get(GroundForceMission, mission_id)
        if mission:
            mission.status = "completed"
            mission.proof_notes = proof_notes or f"Treasury tx: {treasury_tx_hash}"
            mission.completed_at = datetime.now(timezone.utc)
            mission.host_payment_ledger_id = ledger.id
            mission.host_id = host.id
            await db.commit()

        research = await trigger_empire_research_on_fuel(
            db,
            amount_cents=treasury_cents,
            source_ledger_id=ledger.id,
            trigger=f"crypto_{mode}",
        )

        host_profile = {
            "id": external_id,
            "host_id": host.id,
            "payment_mode": mode,
            "commander_oop_usd": 0,
            "treasury_tx_hash": treasury_tx_hash,
            "treasury_inbound_usd": treasury_cents / 100,
            "closer": closer_result,
            "research_task_id": research.get("task_id"),
        }

        await commit_to_private_ledger(
            db,
            event_type=f"LAYER_1_CRYPTO_{mode.upper()}",
            payload=host_profile,
            host_id=host.id,
        )
        await trigger_n8n("sovereign-crypto-presale", host_profile)

        next_mode = await current_payment_mode(db)
        return {
            "ok": True,
            "layer": 1,
            "payment_mode": mode,
            "next_mode": next_mode,
            "commander_oop": 0,
            "host_profile": host_profile,
            "research": research,
            "matrix": await matrix_status(db),
            "warpspeed": (
                "Bootstrap fuel locked." if mode == "bootstrap"
                else "Split pay — host funded treasury + closer."
            ),
        }
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}


async def execute_ai_optimization_engine(
    db: AsyncSession,
    host_id: int,
    current_vacancy_pct: float,
) -> dict:
    """
    Layer 2: Badge velocity + programmatic buyback on high vacancy.
    """
    host = await db.get(SovereignHost, host_id)
    if not host:
        return {"ok": False, "error": "Host not found"}

    badges = json.loads(host.badges_json or "[]")
    velocity_multiplier = len(badges) * 1.5
    host.vacancy_pct = current_vacancy_pct
    await db.commit()

    if current_vacancy_pct > settings.sovereign_buyback_vacancy_threshold:
        result = {
            "ok": True,
            "layer": 2,
            "action": "EXECUTE_BUYBACK_LIQUIDATION",
            "risk_neutralized": True,
            "vacancy_pct": current_vacancy_pct,
            "algorithm": "Floor buyback → fire-sale to transit travelers → salvage margin",
        }
    else:
        result = {
            "ok": True,
            "layer": 2,
            "action": "MONITOR_STATIONARY_FLOW",
            "risk_neutralized": False,
            "booking_velocity_multiplier": velocity_multiplier,
            "badges_deployed": badges,
            "vacancy_pct": current_vacancy_pct,
        }

    await commit_to_private_ledger(
        db,
        event_type="LAYER_2_OPTIMIZATION",
        payload=result,
        host_id=host.id,
    )
    await trigger_n8n("sovereign-optimization", {"host_id": host_id, **result})
    return result


async def trigger_checkout_logistics(
    db: AsyncSession,
    host_id: int,
    guest_name: str,
    *,
    dry_run: bool = True,
) -> dict:
    """
    Layer 3: RentAHuman checkout turnover + partner locker hub kickback.
    """
    host = await db.get(SovereignHost, host_id)
    if not host:
        return {"ok": False, "error": "Host not found"}

    bounty_cents = settings.sovereign_rentahuman_bounty_cents
    partner_kickback = settings.sovereign_partner_kickback_cents

    dispatch = await deploy_mission(
        db,
        mission_type="checkout_turnover",
        neighborhood=host.city_grid,
        target_address=host.property_address,
        host_id=host.id,
        pay_cents=bounty_cents,
        dry_run=dry_run,
    )

    result = {
        "ok": True,
        "layer": 3,
        "task_deployed": dispatch.get("ok", False),
        "guest_name": guest_name,
        "rentahuman_bounty": {
            "title": f"STR Turnover & Transport: {host.host_name}",
            "location": host.property_address,
            "bounty_amount_usd": bounty_cents / 100,
            "mission_id": dispatch.get("mission_id"),
            "rentahuman": dispatch.get("rentahuman"),
        },
        "partner_kickback_usd": partner_kickback / 100,
        "partner_funnel": "Guest routed to Locker Hub — secondary yield",
    }

    await commit_to_private_ledger(
        db,
        event_type="LAYER_3_CHECKOUT",
        payload=result,
        host_id=host.id,
    )
    await trigger_n8n("sovereign-checkout", {"host_id": host_id, **result})
    return result


async def list_ledger_events(db: AsyncSession, limit: int = 200) -> list[dict]:
    result = await db.execute(
        select(SovereignLedgerEvent)
        .order_by(SovereignLedgerEvent.created_at.desc())
        .limit(limit)
    )
    rows = []
    for row in result.scalars().all():
        try:
            payload = json.loads(row.payload_json)
        except json.JSONDecodeError:
            payload = {"raw": row.payload_json}
        rows.append(
            {
                "id": row.id,
                "event_type": row.event_type,
                "host_id": row.host_id,
                "created_at": row.created_at.isoformat(),
                "payload": payload,
            }
        )
    return rows


async def city_grid_status(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(CityCap).where(CityCap.program == "sovereign_stay").order_by(CityCap.city_name)
    )
    grids = []
    for cap in result.scalars().all():
        locked = await count_city_units(db, cap.city_code)
        grids.append(
            {
                "city_code": cap.city_code,
                "city_grid": cap.city_name,
                "max_units": cap.max_units,
                "locked_units": locked,
                "slots_remaining": max(0, cap.max_units - locked),
            }
        )
    return grids


async def run_simulation(db: AsyncSession) -> dict:
    """Blueprint Day-1 sandbox — KCMO underdog activation."""
    presale = await process_onboarding_presale(
        db,
        host_name="KCMO Underdog Rentals LLC",
        property_address="412 W 12th St, Kansas City, MO",
        city_grid="Kansas City",
        worker_ref="rah:sim-closer-1",
        proof_notes="Simulation — Cash App/Venmo screenshot",
        dry_run_closer=True,
    )
    if not presale.get("ok"):
        return presale
    host_id = presale["host_profile"]["host_id"]
    optimize = await execute_ai_optimization_engine(db, host_id, 0.15)
    checkout = await trigger_checkout_logistics(
        db, host_id, "Traveler Anonymous", dry_run=True
    )
    return {
        "ok": True,
        "simulation": True,
        "layer_1": presale,
        "layer_2": optimize,
        "layer_3": checkout,
        "matrix": await matrix_status(db),
    }
