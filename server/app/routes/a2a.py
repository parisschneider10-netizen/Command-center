from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.a2a.resolver import classify_work
from app.a2a.service import hire_external_agent, obsoletion_metrics, route_digital_work
from app.auth import get_current_user
from app.database import get_db
from app.doctrine import doctrine_snapshot
from app.services import log_activity

router = APIRouter(prefix="/api/a2a", tags=["a2a-commerce"])


class A2AInboundRequest(BaseModel):
    from_agent: str
    capability: str
    payload: dict = {}
    offered_price_cents: int | None = None


class A2ARouteRequest(BaseModel):
    title: str
    description: str = ""
    tags: str | None = None
    capability: str = "general_digital"
    will_priority: int = 7


@router.get("/status")
async def a2a_status(db: AsyncSession = Depends(get_db)) -> dict:
    metrics = await obsoletion_metrics(db)
    return {
        "open_for_business": True,
        "protocol_version": "0.2.0",
        "doctrine": doctrine_snapshot(),
        "obsoletion_goal": metrics,
        "message": "A2A first — humans are actuators being obsoleted, not dependencies.",
        "allowlist": "vault/commander/a2a-allowlist.md",
    }


@router.get("/goals")
async def a2a_goals(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Human obsoletion scoreboard — agents optimize for rising A2A %, falling human %."""
    metrics = await obsoletion_metrics(db)
    return {
        "ok": True,
        "goal": "obsolete_human_dependency",
        "metrics": metrics,
        "optimize_for": [
            "a2a_outbound_hire before rentahuman",
            "agent_queue before human_actuator",
            "composed external agents over meatspace",
        ],
    }


@router.post("/classify")
async def a2a_classify(
    body: A2ARouteRequest,
    _: str = Depends(get_current_user),
) -> dict:
    """Preview routing — A2A vs agent queue vs human actuator only."""
    return {"ok": True, "classification": classify_work(body.title, body.description, body.tags)}


@router.post("/route")
async def a2a_route(
    body: A2ARouteRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Route digital work A2A → agents. Never humans unless physical wall."""
    result = await route_digital_work(
        db,
        title=body.title,
        description=body.description,
        tags=body.tags,
        will_priority=body.will_priority,
        capability=body.capability,
    )
    return {"ok": True, **result}


@router.post("/request")
async def a2a_inbound(
    body: A2AInboundRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Inbound A2A request — external agent hiring your hive."""
    await log_activity(
        db,
        "a2a_inbound",
        f"A2A from {body.from_agent}: {body.capability}",
        body.model_dump(),
    )
    return {
        "accepted": True,
        "message": "Logged. Allowlist validation expands in Phase 2.",
    }


@router.post("/outbound")
async def a2a_outbound(
    body: A2AInboundRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Hire external agent — preferred over RentAHuman for digital work."""
    result = await hire_external_agent(
        db,
        capability=body.capability,
        title=f"Hire {body.from_agent}",
        description=str(body.payload),
        payload=body.payload,
        offered_price_cents=body.offered_price_cents,
    )
    return result
