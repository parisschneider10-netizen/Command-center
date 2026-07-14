"""Public lead intake — GHL forms, Telegram, n8n. No portal login required."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.leads.hunter import hunt_leads
from app.models import ScrapedLead
from app.schemas_expansion import LeadIn, LeadOut
from app.value_node.expansion import register_lead

router = APIRouter(prefix="/api/leads", tags=["lead-intake"])


class LeadBatchIn(BaseModel):
    leads: list[LeadIn] = Field(min_length=1, max_length=100)


class LeadHuntIn(BaseModel):
    city: str = Field(default="Kansas City")
    max_leads: int = Field(default=25, ge=1, le=50)


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


@router.post("/hunt")
async def hunt_leads_now(
    body: LeadHuntIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Automated lead hunt — no manual entry. Searches web, registers pipeline."""
    return await hunt_leads(db, city=body.city, max_leads=body.max_leads)


@router.get("/pipeline")
async def lead_pipeline(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Lead counts for portal."""
    total = await db.scalar(select(func.count()).select_from(ScrapedLead)) or 0
    with_phone = await db.scalar(
        select(func.count())
        .select_from(ScrapedLead)
        .where(ScrapedLead.phone.notlike("pending-%"))
    ) or 0
    result = await db.execute(
        select(ScrapedLead).order_by(desc(ScrapedLead.created_at)).limit(30)
    )
    recent = [
        {
            "id": l.id,
            "name": l.name,
            "phone": l.phone,
            "city": l.city,
            "status": l.status,
            "has_phone": not l.phone.startswith("pending-"),
        }
        for l in result.scalars().all()
    ]
    return {
        "ok": True,
        "total": total,
        "with_phone": with_phone,
        "needs_lookup": total - with_phone,
        "recent": recent,
        "auto_hunt": "POST /api/leads/hunt",
    }
