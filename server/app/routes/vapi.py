import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import VoiceSession
from app.services import log_activity

router = APIRouter(prefix="/vapi", tags=["vapi"])


@router.post("/webhook")
async def vapi_webhook(
    request: Request, db: AsyncSession = Depends(get_db)
) -> dict:
    payload = await request.json()
    message = payload.get("message", {})
    msg_type = message.get("type", "")

    if msg_type == "status-update":
        status = message.get("status", "")
        call = message.get("call", {})
        call_id = call.get("id")

        if status == "in-progress":
            session = VoiceSession(vapi_call_id=call_id)
            db.add(session)
            await db.commit()
            await log_activity(
                db,
                "voice_call_started",
                "Voice session started",
                {"call_id": call_id},
            )

        elif status == "ended":
            call_id = call.get("id")
            result = await db.execute(
                select(VoiceSession).where(VoiceSession.vapi_call_id == call_id)
            )
            session = result.scalar_one_or_none()
            if session:
                session.ended_at = datetime.now(timezone.utc)
                await db.commit()
            await log_activity(
                db,
                "voice_call_ended",
                "Voice session ended",
                {"call_id": call_id},
            )

    elif msg_type == "end-of-call-report":
        call = message.get("call", {})
        call_id = call.get("id")
        summary = message.get("summary", "")
        transcript = message.get("transcript", "")
        duration = message.get("durationSeconds")

        result = await db.execute(
            select(VoiceSession).where(VoiceSession.vapi_call_id == call_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            session = VoiceSession(vapi_call_id=call_id)
            db.add(session)

        session.summary = summary
        session.transcript = (
            json.dumps(transcript) if isinstance(transcript, (list, dict)) else str(transcript)
        )
        session.duration_seconds = duration
        session.ended_at = datetime.now(timezone.utc)
        await db.commit()

        await log_activity(
            db,
            "voice_call_summary",
            summary or "Voice call completed",
            {"call_id": call_id},
        )

    elif msg_type == "function-call":
        pass

    return {"ok": True}
