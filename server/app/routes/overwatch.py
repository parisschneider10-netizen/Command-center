"""Overwatch (Replit) salvage — extract useful bones into Command Center."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.integrations.vapi_client import find_replit_urls, get_assistant
from app.services import log_activity

router = APIRouter(prefix="/api/overwatch", tags=["overwatch-migration"])


def _bones_path() -> Path:
    return Path(settings.vault_path) / "overwatch" / "bones.json"


def _snapshot_path() -> Path:
    return Path(settings.vault_path) / "commander" / "overwatch-vapi-snapshot.json"


@router.post("/extract")
async def extract_overwatch(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """
    Pull Vapi assistant config — hunt Replit URLs, map salvageable bones.
    Replit live access blocked while suspended; this captures what Vapi still knows.
    """
    if not settings.vapi_api_key:
        return {"ok": False, "error": "VAPI_API_KEY not configured"}

    assistant_id = settings.vapi_assistant_id.strip()
    wire_path = Path(settings.vault_path) / "commander" / "vapi-wire.json"
    if not assistant_id and wire_path.exists():
        assistant_id = json.loads(wire_path.read_text()).get("assistant_id", "")

    if not assistant_id:
        return {"ok": False, "error": "No assistant_id — run Wire SARA first"}

    assistant = await get_assistant(assistant_id)
    replit_urls = find_replit_urls(assistant)

    snapshot_path = _snapshot_path()
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(assistant, indent=2, default=str))

    bones = {
        "source": "vapi_assistant_snapshot",
        "assistant_id": assistant_id,
        "replit_urls": replit_urls,
        "replit_live": False,
        "salvage_map": {
            "dashboard": "portal/",
            "voice_tools": "server/app/routes/voice.py",
            "intent_engine": "server/app/intent/",
            "treasury": "server/app/treasury/",
            "sovereign_stay": "server/app/value_node/sovereign_stay.py",
            "doctrine": "vault/commander/",
        },
        "next": [
            "Clone GitHub export if Repl was synced",
            "Port unique Overwatch routes into portal + /api",
            "Retire all replit.dev tool URLs — Servury only",
        ],
    }
    bones_path = _bones_path()
    bones_path.parent.mkdir(parents=True, exist_ok=True)
    bones_path.write_text(json.dumps(bones, indent=2))

    await log_activity(
        db,
        "overwatch_extract",
        f"Overwatch bones extracted — {len(replit_urls)} Replit URL(s)",
        bones,
    )
    return {"ok": True, **bones}


@router.get("/bones")
async def get_overwatch_bones(_: str = Depends(get_current_user)) -> dict:
    path = _bones_path()
    if not path.exists():
        return {"ok": False, "error": "No extraction yet — POST /api/overwatch/extract"}
    return {"ok": True, **json.loads(path.read_text())}
