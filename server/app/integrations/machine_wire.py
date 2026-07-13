"""Machine-speed wire — HTTPS + Vapi API, no dashboard clicks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from app.config import settings
from app.integrations.vapi_client import wire_assistant


def ip_to_sslip_host(ip: str) -> str:
    clean = ip.strip()
    if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", clean):
        raise ValueError(f"Invalid IPv4 for sslip.io: {ip}")
    return f"{clean.replace('.', '-')}.sslip.io"


def extract_ip_from_settings() -> str | None:
    if settings.vps_public_ip:
        return settings.vps_public_ip.strip()
    for url in (settings.public_https_url, settings.public_base_url):
        if not url:
            continue
        host = urlparse(url).hostname or ""
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
            return host
        if host.endswith(".sslip.io"):
            return host.replace("-", ".").replace(".sslip.io", "")
    return None


def resolve_https_base() -> str:
    """Public HTTPS URL for Vapi webhooks — zero domain purchase via sslip.io."""
    if settings.public_https_url:
        base = settings.public_https_url.rstrip("/")
        if not base.startswith("https://"):
            base = f"https://{base.lstrip('https://').lstrip('http://')}"
        return base

    pub = settings.public_base_url.rstrip("/")
    if pub.startswith("https://"):
        return pub

    ip = extract_ip_from_settings()
    if not ip:
        raise ValueError(
            "Set VPS_PUBLIC_IP or PUBLIC_HTTPS_URL in .env (or PUBLIC_BASE_URL with IP)"
        )
    return f"https://{ip_to_sslip_host(ip)}"


def sslip_hostname() -> str:
    return urlparse(resolve_https_base()).hostname or ""


def write_wire_status(result: dict) -> Path:
    path = Path(settings.vault_path) / "commander" / "vapi-wire.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, default=str))
    return path


def read_wire_status() -> dict:
    path = Path(settings.vault_path) / "commander" / "vapi-wire.json"
    if not path.exists():
        return {"wired": False}
    return json.loads(path.read_text())


async def machine_wire_sara() -> dict:
    """
    One call: resolve HTTPS base → PATCH Vapi assistant → save status.
    Commander drops VAPI_API_KEY once; system does the rest.
    """
    if not settings.vapi_api_key:
        return {
            "ok": False,
            "error": "VAPI_API_KEY missing — add to GitHub Secrets or VPS .env",
            "next_step": "Actions → Wire SARA (machine speed)",
        }

    try:
        https_base = resolve_https_base()
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    hostname = urlparse(https_base).hostname or ""

    try:
        result = await wire_assistant(https_base)
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "hint": "Ensure docs/vapi-assistant.json exists on VPS (git pull + docs volume mount)",
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "https_base": https_base}

    status = {
        **result,
        "wired": True,
        "sslip_hostname": hostname,
        "caddy_required": True,
        "caddy_note": (
            f"Ensure Caddy serves {hostname} on ports 80/443 "
            "(run scripts/setup-sslip-https.sh on VPS)"
        ),
    }
    write_wire_status(status)
    return status


def wire_readiness() -> dict:
    status = read_wire_status()
    https_base = None
    try:
        https_base = resolve_https_base()
    except ValueError:
        pass
    phones: list[dict] = []
    primary_phone = status.get("phone_number")
    if status.get("wired") and primary_phone:
        phones = [{"number": primary_phone, "id": status.get("phone_number_id")}]
    return {
        "vapi_key_configured": bool(settings.vapi_api_key),
        "assistant_id_configured": bool(settings.vapi_assistant_id),
        "phone_id_configured": bool(settings.vapi_phone_number_id),
        "sara_phone": primary_phone or status.get("phone_number"),
        "phone_numbers": phones,
        "https_base": https_base,
        "sslip_hostname": sslip_hostname() if https_base else None,
        "last_wire": status,
        "machine_wire_endpoint": "/vapi/machine-wire",
    }
