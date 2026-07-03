from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.services import log_activity

router = APIRouter(prefix="/api/a2a", tags=["a2a-commerce"])


class A2AInboundRequest(BaseModel):
    from_agent: str
    capability: str
    payload: dict = {}
    offered_price_cents: int | None = None


@router.get("/status")
async def a2a_status() -> dict:
    return {
        "open_for_business": True,
        "protocol_version": "0.1.0",
        "message": "Foundation ready — configure allowlist in vault/commander/a2a-allowlist.md",
    }


@router.post("/request")
async def a2a_inbound(
    body: A2AInboundRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Inbound A2A request — validate allowlist in Phase 2."""
    await log_activity(
        db,
        "a2a_inbound",
        f"A2A from {body.from_agent}: {body.capability}",
        body.model_dump(),
    )
    return {
        "accepted": True,
        "message": "Logged. Allowlist validation and task creation in Phase 2.",
    }


@router.post("/outbound")
async def a2a_outbound(
    body: A2AInboundRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Your agent hiring an external agent — wallet + allowlist in Phase 2."""
    await log_activity(
        db,
        "a2a_outbound",
        f"A2A hire {body.from_agent} for {body.capability}",
        body.model_dump(),
    )
    return {
        "queued": True,
        "message": "Outbound A2A logged. Connect treasury + allowlist in Phase 2.",
    }
