"""Ready Room API — Obsidian-only intent operations."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.integrations.n8n import trigger_n8n
from app.ready_room.scanner import scan_pending_intents
from app.ready_room.service import (
    list_ready_room_notes,
    ready_room_root,
    save_handwritten_extraction,
    write_intent_note,
)
from app.services import log_activity

router = APIRouter(prefix="/api/ready-room", tags=["ready-room"])


class ReadyRoomIntentIn(BaseModel):
    intent: str
    mode: str = Field(default="drill", pattern="^(drill|live|dry_run|test)$")
    auto_execute: bool = True
    title: str | None = None
    body: str = ""


@router.get("/status")
async def ready_room_status(_: str = Depends(get_current_user)) -> dict:
    """Ready Room snapshot — pending intents, folders, Obsidian paths."""
    root = ready_room_root()
    pending = [n for n in list_ready_room_notes("intent") if n.get("status") == "pending"]
    return {
        "ok": True,
        "vault_path": str(root.relative_to(Path(settings.vault_path).parent)),
        "obsidian_root": "ready-room/",
        "folders": {
            "intent": "Type intents here (Obsidian template)",
            "handwritten": "Drop photo scans of handwritten notes",
            "processed": "System extractions",
            "archive": "Executed intents",
        },
        "pending_intents": len(pending),
        "pending": pending[:20],
        "manual": "vault/commander/ready-room-manual.md",
    }


@router.post("/intent")
async def create_ready_room_intent(
    body: ReadyRoomIntentIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Create intent note in ready-room/intent/ — same as Obsidian template save."""
    path = write_intent_note(
        body.intent,
        mode=body.mode if body.mode != "dry_run" else "drill",
        auto_execute=body.auto_execute,
        title=body.title,
        body=body.body,
    )
    await log_activity(db, "ready_room_intent_created", body.intent[:80], {"path": path.name})
    await trigger_n8n("ready-room-intent", {"path": path.name, "intent": body.intent, "mode": body.mode})
    return {
        "ok": True,
        "path": str(path.relative_to(Path(settings.vault_path))),
        "next": "Sync Obsidian → POST /api/ready-room/scan to execute",
    }


@router.post("/scan")
async def scan_ready_room(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """
    Process pending ready-room/intent notes → intent engine.
    Wire n8n cron: POST /api/ready-room/scan every 5 min.
    """
    result = await scan_pending_intents(db)
    return {"ok": True, **result}


@router.post("/handwritten")
async def ingest_handwritten(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """
    Upload handwritten note image → vision extract → ready-room/processed + intent queue.
    Obsidian: drop image in ready-room/handwritten/ then call this API or use CLI script.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload an image (jpeg/png)")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

    try:
        result = await save_handwritten_extraction(
            data,
            original_name=file.filename or "note.jpg",
            mime=file.content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await log_activity(db, "ready_room_handwritten", "Handwritten note ingested", result)
    await trigger_n8n("ready-room-handwritten", result)
    return {"ok": True, **result, "next": "POST /api/ready-room/scan to process intent"}


@router.get("/notes/{folder}")
async def list_notes(
    folder: str,
    limit: int = 50,
    _: str = Depends(get_current_user),
) -> list[dict]:
    allowed = {"intent", "processed", "archive", "inbox"}
    if folder not in allowed:
        raise HTTPException(status_code=400, detail=f"Folder must be one of: {allowed}")
    return list_ready_room_notes(folder, limit)
