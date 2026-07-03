from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.integrations.n8n import trigger_n8n
from app.services import log_activity

router = APIRouter(prefix="/integrations/n8n", tags=["integrations"])


class N8nTriggerRequest(BaseModel):
    event: str
    payload: dict = {}


@router.post("/trigger")
async def n8n_trigger(
    body: N8nTriggerRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    result = await trigger_n8n(body.event, body.payload)
    await log_activity(
        db,
        "n8n_trigger",
        f"n8n event: {body.event}",
        {"event": body.event, "result": result},
    )
    return result
