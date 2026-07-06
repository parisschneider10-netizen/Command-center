"""Servury VPS provisioning — white-label node per city."""

import httpx

from app.config import settings


async def provision_vps(
    *,
    city_name: str,
    pm_name: str,
    dry_run: bool | None = None,
) -> dict | None:
    dry = settings.expansion_dry_run if dry_run is None else dry_run
    label = f"apex-node-{city_name.lower().replace(' ', '-')}"

    if dry:
        return {
            "dry_run": True,
            "id": f"dry-srv-{label}",
            "ip_address": "203.0.113.10",
            "label": label,
        }

    if not settings.servury_api_key:
        return {"error": "SERVURY_API_KEY not configured"}

    endpoint = f"{settings.servury_api_url.rstrip('/')}/servers"
    headers = {
        "Authorization": f"Bearer {settings.servury_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "plan": "vps-micro-1",
        "region": "us-central",
        "os": "ubuntu-24-04-lts",
        "label": label,
        "tags": ["recon-node", pm_name.lower().replace(" ", "-")],
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(endpoint, json=payload, headers=headers)
        if response.status_code in (200, 201):
            data = response.json()
            return {
                "id": data.get("id"),
                "ip_address": data.get("ip_address"),
                "root_password": data.get("root_password"),
            }
        return {"error": f"Servury HTTP {response.status_code}", "body": response.text[:200]}
