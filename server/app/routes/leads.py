"""Public lead intake — GHL forms, Telegram, n8n. No portal login required."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas_expansion import LeadIn, LeadOut
from app.value_node.expansion import register_lead

router = APIRouter(prefix="/api/leads", tags=["lead-intake"])


class LeadBatchIn(BaseModel):
    leads: list[LeadIn] = Field(min_length=1, max_length=100)


def _verify_lead_secret(x_lead_secret: str | None) -> None:
    if not settings.lead_webhook_secret:
        return
    if x_lead_secret != settings.lead_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid lead webhook secret")


@router.get("/intake/status")
async def intake_status() -> dict:
    """Public — copy this URL into GHL / n8n / Telegram tonight."""
    base = settings.public_base_url.rstrip("/")
    return {
        "ok": True,
        "endpoint": f"{base}/api/leads/intake",
        "batch": f"{base}/api/leads/intake/batch",
        "auth": "optional X-Lead-Secret header when LEAD_WEBHOOK_SECRET is set",
        "fields": ["name", "phone", "city", "email?", "address?", "zip?", "crisis_type?"],
        "portal": "http://157.254.194.89:3000 — Launch tab",
        "voice": settings.sara_phone_e164,
    }


@router.post("/intake", response_model=LeadOut)
async def intake_lead(
    body: LeadIn,
    db: AsyncSession = Depends(get_db),
    x_lead_secret: str | None = Header(default=None),
) -> LeadOut:
    """GHL form / mobile / scrape tool → MTR lead pipeline."""
    _verify_lead_secret(x_lead_secret)
    lead = await register_lead(db, body.model_dump(), source="webhook")
    return LeadOut.model_validate(lead)


@router.post("/intake/batch")
async def intake_batch(
    body: LeadBatchIn,
    db: AsyncSession = Depends(get_db),
    x_lead_secret: str | None = Header(default=None),
) -> dict:
    """Bulk lead drop — paste scrape results tonight."""
    _verify_lead_secret(x_lead_secret)
    created = []
    for item in body.leads:
        lead = await register_lead(db, item.model_dump(), source="webhook")
        created.append(LeadOut.model_validate(lead))
    return {"ok": True, "count": len(created), "leads": created}
