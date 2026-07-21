"""Automated MTR/STR lead hunter — no manual entry."""

from __future__ import annotations

import hashlib
import re
from html import unescape
from urllib.parse import quote_plus

import httpx

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.integrations.n8n import trigger_n8n
from app.services import log_activity
from app.value_node.expansion import register_lead

PHONE_RE = re.compile(
    r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}"
)
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

HUNT_QUERIES = [
    "{city} short term rental property management phone",
    "{city} Airbnb property manager contact",
    "{city} vacation rental management company",
    "{city} STR co-host property manager",
]


def _normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return digits
    return raw.strip()


def _pending_phone(name: str, city: str) -> str:
    digest = hashlib.sha1(f"{name}|{city}".encode()).hexdigest()[:10]
    return f"pending-{digest}"


def _parse_result(title: str, snippet: str, url: str, city: str) -> dict | None:
    text = unescape(f"{title} {snippet}")
    phones = [_normalize_phone(p) for p in PHONE_RE.findall(text)]
    phones = [p for p in phones if len(re.sub(r"\D", "", p)) >= 10]
    emails = EMAIL_RE.findall(text)
    name = re.sub(r"\s*[-|•].*$", "", title).strip()[:120]
    if not name or len(name) < 3:
        return None
    if any(skip in name.lower() for skip in ("wikipedia", "reddit", "youtube", "indeed")):
        return None
    phone = phones[0] if phones else _pending_phone(name, city)
    return {
        "name": name,
        "phone": phone,
        "email": emails[0] if emails else None,
        "address": url[:500] if url else None,
        "city": city,
        "crisis_type": "Auto-Hunt-STR-MTR",
    }


async def _brave_search(query: str, count: int = 10) -> list[dict]:
    if not settings.brave_search_api_key:
        return []
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": count},
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": settings.brave_search_api_key,
            },
        )
        response.raise_for_status()
        data = response.json()
    results = []
    for item in data.get("web", {}).get("results", []):
        results.append(
            {
                "title": item.get("title", ""),
                "snippet": item.get("description", ""),
                "url": item.get("url", ""),
            }
        )
    return results


async def _duckduckgo_search(query: str) -> list[dict]:
    """No API key — fallback hunter for tonight."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {"User-Agent": "CommandCenter-LeadHunter/1.0"}
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.post(url, headers=headers, data={"q": query})
        response.raise_for_status()
        html = response.text
    results = []
    for block in re.findall(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</',
        html,
        re.DOTALL,
    ):
        link, title, snippet = block
        title = re.sub(r"<[^>]+>", "", title).strip()
        snippet = re.sub(r"<[^>]+>", "", snippet).strip()
        if title:
            results.append({"title": title, "snippet": snippet, "url": link})
    return results[:15]


async def hunt_leads(
    db: AsyncSession,
    *,
    city: str | None = None,
    max_leads: int = 15,
    source: str = "auto_hunt",
) -> dict:
    """Search web → parse contacts → register leads. Fully automated."""
    city = city or settings.sovereign_focus_city
    seen_phones: set[str] = set()
    seen_names: set[str] = set()
    created: list[dict] = []
    skipped = 0
    engine = "duckduckgo"

    for template in HUNT_QUERIES:
        if len(created) >= max_leads:
            break
        query = template.format(city=city)
        try:
            if settings.brave_search_api_key:
                engine = "brave"
                raw = await _brave_search(query, count=10)
            else:
                raw = await _duckduckgo_search(query)
        except Exception as exc:
            await log_activity(db, "lead_hunt_error", query, {"error": str(exc)})
            continue

        for item in raw:
            if len(created) >= max_leads:
                break
            parsed = _parse_result(
                item.get("title", ""),
                item.get("snippet", ""),
                item.get("url", ""),
                city,
            )
            if not parsed:
                skipped += 1
                continue
            key = parsed["phone"]
            name_key = parsed["name"].lower()
            if key in seen_phones or name_key in seen_names:
                skipped += 1
                continue
            seen_phones.add(key)
            seen_names.add(name_key)
            lead = await register_lead(db, parsed, source=source)
            created.append(
                {
                    "id": lead.id,
                    "name": lead.name,
                    "phone": lead.phone,
                    "city": lead.city,
                    "has_phone": not lead.phone.startswith("pending-"),
                }
            )

    summary = {
        "ok": True,
        "engine": engine,
        "city": city,
        "hunted": len(created),
        "skipped_duplicates": skipped,
        "leads": created,
        "with_phone": sum(1 for l in created if l["has_phone"]),
        "needs_lookup": sum(1 for l in created if not l["has_phone"]),
    }
    await log_activity(
        db,
        "lead_hunt_complete",
        f"Hunted {len(created)} leads in {city}",
        summary,
    )
    await trigger_n8n("lead-hunt-complete", summary)
    return summary
