from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.comms.email import comms_configured, list_inbox, send_email, sync_inbox
from app.database import get_db
from app.models import EmailMessage
from app.schemas_agents import EmailDraft, EmailOut

router = APIRouter(prefix="/api/comms", tags=["comms"])


@router.get("/status")
async def comms_status(_: str = Depends(get_current_user)) -> dict:
    return {"configured": comms_configured(), "gmail_replacement": "agent-first inbox"}


@router.post("/sync")
async def comms_sync(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    if not comms_configured():
        raise HTTPException(status_code=503, detail="Comms not configured — set IMAP in .env")
    count = await sync_inbox(db)
    return {"synced": count}


@router.get("/inbox", response_model=list[EmailOut])
async def comms_inbox(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[EmailOut]:
    messages = await list_inbox(db)
    return [EmailOut.model_validate(m) for m in messages]


@router.get("/messages/{message_id}", response_model=EmailOut)
async def comms_message(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> EmailOut:
    msg = await db.get(EmailMessage, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return EmailOut.model_validate(msg)


@router.post("/messages/{message_id}/draft", response_model=EmailOut)
async def comms_draft(
    message_id: int,
    body: EmailDraft,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> EmailOut:
    msg = await db.get(EmailMessage, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.draft_reply = body.draft_reply
    msg.agent_summary = body.agent_summary
    msg.nuclear_flag = body.nuclear_flag
    msg.status = "draft_ready"
    await db.commit()
    await db.refresh(msg)
    return EmailOut.model_validate(msg)


@router.post("/messages/{message_id}/send")
async def comms_send(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    return await send_email(db, message_id)
