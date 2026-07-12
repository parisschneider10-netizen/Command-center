"""RentAHuman API client — human-in-the-loop layer."""

import httpx

from app.config import settings

BASE_URL = "https://rentahuman.ai/api"


def _headers() -> dict[str, str]:
    if not settings.rentahuman_api_key:
        return {}
    return {
        "X-API-Key": settings.rentahuman_api_key,
        "Authorization": f"Bearer {settings.rentahuman_api_key}",
    }


async def search_humans(
    *,
    skill: str | None = None,
    city: str | None = None,
    location: str | None = None,
    max_rate: float | None = None,
    limit: int = 10,
) -> dict:
    """Search humans — free, no API key required."""
    params: dict = {"limit": limit}
    if skill:
        params["skill"] = skill
    if city:
        params["city"] = city
    if location:
        params["location"] = location
    if max_rate is not None:
        params["maxRate"] = max_rate

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/humans", params=params)
        response.raise_for_status()
        return response.json()


async def create_bounty(
    *,
    title: str,
    description: str,
    compensation: float,
    location: str | None = None,
    tags: list[str] | None = None,
    dry_run: bool = False,
) -> dict:
    """Post a task bounty for humans to apply."""
    if not settings.rentahuman_api_key:
        return {
            "ok": False,
            "error": "RENTAHUMAN_API_KEY not configured",
            "dry_run": dry_run,
        }

    payload: dict = {
        "title": title,
        "description": description,
        "compensation": compensation,
        "price": compensation,
        "priceType": "fixed",
    }
    if location:
        payload["location"] = location
    if tags:
        payload["tags"] = tags
    if dry_run:
        payload["dryRun"] = True

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/bounties",
            json=payload,
            headers={**_headers(), "Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        return {"ok": True, "dry_run": dry_run, "data": data}


async def get_bounty(bounty_id: str) -> dict:
    if not settings.rentahuman_api_key:
        return {"ok": False, "error": "RENTAHUMAN_API_KEY not configured"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/bounties/{bounty_id}",
            headers=_headers(),
        )
        response.raise_for_status()
        return {"ok": True, "data": response.json()}
