"""GoHighLevel sub-account provisioning — SaaS snapshot flash."""

import httpx

from app.config import settings


async def create_subaccount(
    *,
    pm_data: dict,
    city_name: str,
    dry_run: bool | None = None,
) -> dict | None:
    dry = settings.expansion_dry_run if dry_run is None else dry_run

    if dry:
        return {
            "dry_run": True,
            "id": f"dry-ghl-{city_name.lower().replace(' ', '-')}",
        }

    if not settings.ghl_api_key or not settings.ghl_company_id:
        return {"error": "GHL_API_KEY or GHL_COMPANY_ID not configured"}

    endpoint = f"{settings.ghl_api_url.rstrip('/')}/locations/"
    headers = {
        "Authorization": f"Bearer {settings.ghl_api_key}",
        "Content-Type": "application/json",
        "Version": "2021-07-28",
    }
    payload = {
        "companyId": settings.ghl_company_id,
        "name": pm_data.get("name"),
        "email": pm_data.get("email"),
        "phone": pm_data.get("phone"),
        "address": pm_data.get("address"),
        "city": city_name,
        "snapshotId": settings.ghl_mtr_recon_snapshot_id or None,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(endpoint, json=payload, headers=headers)
        if response.status_code in (200, 201):
            data = response.json()
            loc_id = data.get("id") or data.get("locationId")
            return {"id": loc_id}
        return {"error": f"GHL HTTP {response.status_code}", "body": response.text[:200]}
