"""One-button launch — hunt leads + fire kill-shot intent."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.integrations.machine_wire import read_wire_status
from app.intent.engine import execute_intent, plan_intent
from app.leads.hunter import hunt_leads
from app.services import log_activity
from app.velocity import should_auto_execute_intent, velocity_snapshot

router = APIRouter(prefix="/api/launch", tags=["launch"])


class KillShotIn(BaseModel):
    city: str = Field(default_factory=lambda: settings.sovereign_focus_city)
    hunt_leads: bool = Field(default=True, description="Auto-hunt leads before launch")
    max_leads: int = Field(default=15, ge=1, le=50)
    drill: bool = Field(default=False, description="Drill only — no live closer payouts")


@router.get("/status")
async def launch_status(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Launch deck snapshot for portal."""
    from sqlalchemy import func, select

    from app.models import ScrapedLead

    total = await db.scalar(select(func.count()).select_from(ScrapedLead)) or 0
    wire = read_wire_status()
    return {
        "ok": True,
        "sara_wired": wire.get("wired", False),
        "sara_phone": settings.sara_phone_e164,
        "leads_in_pipeline": total,
        "focus_city": settings.sovereign_focus_city,
        "max_hosts": settings.sovereign_target_cities * settings.sovereign_units_per_city,
        "auto_hunt": True,
        "kill_shot_endpoint": "POST /api/launch/kill-shot",
        "hunt_endpoint": "POST /api/leads/hunt",
        "velocity": velocity_snapshot(),
    }


@router.post("/kill-shot")
async def kill_shot(
    body: KillShotIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """
    One button: auto-hunt leads → launch Sovereign Stay MTR live.
    """
    hunt_result = None
    if body.hunt_leads:
        from app.value_node.eco_express import generate_strike_list

        hunt_result = await generate_strike_list(db)

    mode = "drill" if body.drill else "live"
    intent_text = (
        f"Launch Eco-Express D2C smart thermostat program. {mode}. Max speed. "
        f"Kansas City suburbs. Strike list → hunter close $149 → RAH install. "
        f"No hosts. Net $59/door."
    )
    intent = await plan_intent(db, intent_text=intent_text, source="kill_shot")
    execution = None
    if should_auto_execute_intent(intent_text, True):
        execution = await execute_intent(db, intent.id)

    await log_activity(
        db,
        "kill_shot",
        f"Kill shot {mode} — {body.city}",
        {"hunted": hunt_result, "intent_id": intent.id},
    )

    return {
        "ok": True,
        "mode": mode,
        "city": body.city,
        "hunt": hunt_result,
        "intent_id": intent.id,
        "execution": execution,
        "next": [
            "Hunters close $149 at door (Evergy rebate pitch)",
            "Payment confirmed → Lowe's pickup + RAH install",
            f"Call SARA: {settings.sara_phone_e164}",
        ],
    }
