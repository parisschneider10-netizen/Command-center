"""Empire Doctor — preventive checks, auto-repair, human firewall escalation."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.escalation import create_escalation
from app.integrations.n8n import trigger_n8n
from app.intent.engine import ensure_judgment_rules, get_firewall_guardians
from app.models import EscalationLevel, TreasuryLedger
from app.services import log_activity
from app.treasury.float import release_cleared_holds


async def _check_database(db: AsyncSession) -> dict:
    try:
        await db.scalar(select(func.count()).select_from(TreasuryLedger))
        return {"ok": True, "name": "database", "detail": "SQLite/Postgres reachable"}
    except Exception as exc:
        return {"ok": False, "name": "database", "detail": str(exc)}


def _check_vault() -> dict:
    path = Path(settings.vault_path)
    sovereign = path / "sovereign"
    ok = path.exists()
    return {
        "ok": ok,
        "name": "vault",
        "detail": f"vault={'ok' if ok else 'missing'} sovereign_dir={'ok' if sovereign.exists() else 'will_create'}",
    }


def _check_public_url() -> dict:
    url = settings.public_base_url
    localhost = "localhost" in url or "127.0.0.1" in url
    return {
        "ok": not localhost,
        "name": "public_url",
        "severity": "warn" if localhost else "ok",
        "detail": url if not localhost else f"{url} — SARA needs public IP or HTTPS domain",
    }


def _check_n8n() -> dict:
    configured = bool(settings.n8n_webhook_base_url)
    return {
        "ok": configured,
        "name": "n8n",
        "severity": "warn" if not configured else "ok",
        "detail": "webhook configured" if configured else "set N8N_WEBHOOK_BASE_URL for automations",
    }


def _check_rentahuman() -> dict:
    configured = bool(settings.rentahuman_api_key)
    return {
        "ok": configured,
        "name": "rentahuman",
        "severity": "warn" if not configured else "ok",
        "detail": "live bounties ready" if configured else "dry_run only until RENTAHUMAN_API_KEY set",
    }


async def _check_firewall(db: AsyncSession) -> dict:
    guardians = await get_firewall_guardians(db)
    active = [g for g in guardians if g.is_active]
    slots = settings.human_firewall_size
    return {
        "ok": True,
        "name": "human_firewall",
        "severity": "warn" if len(active) < slots else "ok",
        "detail": f"{len(active)}/{slots} guardian slots filled — empty slots auto-post RentAHuman",
        "active_guardians": len(active),
        "slots": slots,
    }


async def doctor_status(db: AsyncSession) -> dict:
    """Quick health snapshot for portal and SARA."""
    checks = [
        await _check_database(db),
        _check_vault(),
        _check_public_url(),
        _check_n8n(),
        _check_rentahuman(),
        await _check_firewall(db),
    ]
    critical = [c for c in checks if not c["ok"] and c.get("severity") != "warn"]
    warnings = [c for c in checks if not c["ok"] or c.get("severity") == "warn"]
    warpspeed = len(critical) == 0
    return {
        "doctor": "empire_doctor_v1",
        "warpspeed_clear": warpspeed,
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "checks": checks,
        "voice_summary": (
            "All systems go. Warp speed clear."
            if warpspeed
            else f"{len(critical)} critical issue(s). Human firewall may be needed."
        ),
    }


async def doctor_scan(
    db: AsyncSession,
    *,
    auto_repair: bool = True,
    escalate_on_critical: bool = True,
) -> dict:
    """
    Full scan: auto-repair safe issues, escalate critical to human firewall.
    Run via n8n cron every 5 min on VPS for 24/7 coverage.
    """
    repairs: list[str] = []
    if auto_repair:
        Path(settings.vault_path).mkdir(parents=True, exist_ok=True)
        Path(settings.sovereign_ledger_path).parent.mkdir(parents=True, exist_ok=True)
        repairs.append("vault_paths_ensured")

        await ensure_judgment_rules(db)
        repairs.append("judgment_rules_seeded")

        released = await release_cleared_holds(db)
        if released:
            repairs.append(f"float_cleared_{len(released)}_holds")

    status = await doctor_status(db)
    escalations: list[int] = []

    for check in status["checks"]:
        if check["ok"] or check.get("severity") == "warn":
            continue
        if not escalate_on_critical:
            continue
        esc = await create_escalation(
            db,
            title=f"Doctor alert: {check['name']}",
            description=check["detail"],
            level=EscalationLevel.human,
            source="empire_doctor",
        )
        escalations.append(esc.id)

    await log_activity(
        db,
        "doctor_scan",
        status["voice_summary"],
        {
            "warpspeed_clear": status["warpspeed_clear"],
            "repairs": repairs,
            "escalations": escalations,
        },
    )
    await trigger_n8n(
        "empire-doctor-scan",
        {
            "warpspeed_clear": status["warpspeed_clear"],
            "repairs": repairs,
            "escalations": escalations,
            "checks": status["checks"],
        },
    )

    return {
        "ok": status["warpspeed_clear"],
        **status,
        "repairs": repairs,
        "escalations_created": escalations,
        "human_firewall": "Empty guardian slots still auto-post RentAHuman on judgment walls",
    }
