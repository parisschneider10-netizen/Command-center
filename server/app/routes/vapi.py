import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, verify_token
from app.config import settings
from app.database import get_db
from app.integrations.machine_wire import machine_wire_sara, wire_readiness
from app.models import VoiceSession
from app.services import log_activity

router = APIRouter(prefix="/vapi", tags=["vapi"])
optional_bearer = HTTPBearer(auto_error=False)


async def _require_wire_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
    x_machine_wire_token: str | None = Header(None),
) -> str:
    token = x_machine_wire_token or (credentials.credentials if credentials else None)
    if token and settings.machine_wire_token and token == settings.machine_wire_token:
        return "machine"
    if credentials:
        verify_token(credentials.credentials)
        return "portal"
    raise HTTPException(
        status_code=401,
        detail="Portal bearer token or X-Machine-Wire-Token required",
    )


@router.get("/status")
async def vapi_status(_: str = Depends(get_current_user)) -> dict:
    """SARA / Vapi wire status — no dashboard needed."""
    readiness = wire_readiness()
    if settings.vapi_api_key and not readiness.get("sara_phone"):
        try:
            from app.integrations.vapi_client import list_phone_numbers, format_phone_number

            numbers = await list_phone_numbers()
            readiness["phone_numbers"] = [
                {
                    "id": row.get("id"),
                    "number": format_phone_number(row),
                    "name": row.get("name"),
                    "assistant_id": row.get("assistantId"),
                }
                for row in numbers
            ]
            if numbers:
                readiness["sara_phone"] = format_phone_number(numbers[0])
        except Exception as exc:
            readiness["phone_lookup_error"] = str(exc)
    return {"ok": True, **readiness}


@router.post("/machine-wire")
async def machine_wire(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(_require_wire_auth),
) -> dict:
    """
    Machine-speed SARA wire: PATCH Vapi assistant via API key.
    Add VAPI_API_KEY to .env or GitHub Secrets → run Wire SARA workflow.
    """
    result = await machine_wire_sara()
    await log_activity(
        db,
        "vapi_machine_wire",
        "SARA machine-wire " + ("OK" if result.get("ok") else "FAILED"),
        result,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


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
