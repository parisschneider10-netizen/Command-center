"""Ready Room scan — pending Obsidian intents → intent engine."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.integrations.n8n import trigger_n8n
from app.intent.engine import execute_intent, plan_intent
from app.ready_room.service import (
    mark_note_status,
    parse_frontmatter,
    ready_room_root,
    scan_handwritten_inbox,
)
from app.services import log_activity
from app.velocity import should_auto_execute_intent


async def scan_pending_intents(db: AsyncSession) -> dict:
    """
    Process all ready-room/intent/*.md with status: pending.
    Also ingests new handwritten images first (Obsidian drop folder).
    """
    handwritten = await scan_handwritten_inbox()

    root = ready_room_root()
    intent_dir = root / "intent"
    outcomes = []

    for path in sorted(intent_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(content)
        if meta.get("type") != "intent":
            continue
        if meta.get("status", "pending") != "pending":
            continue

        intent_text = meta.get("intent") or body
        if not intent_text or len(intent_text.strip()) < 3:
            outcomes.append({"file": path.name, "ok": False, "error": "empty intent"})
            continue

        mode = str(meta.get("mode", "drill")).lower()
        drill = mode in ("drill", "dry_run", "sights-on", "test")
        auto_flag = bool(meta.get("auto_execute", True))
        if drill:
            intent_text = f"{intent_text.strip()} — drill only, dry run, sights on"

        try:
            intent = await plan_intent(db, intent_text=intent_text, source="ready-room")
            result: dict = {
                "file": path.name,
                "ok": True,
                "intent_id": intent.id,
                "mode": mode,
                "drill": drill,
            }
            if should_auto_execute_intent(intent_text, auto_flag) and not drill:
                ex = await execute_intent(db, intent.id)
                result["execution"] = ex
            elif should_auto_execute_intent(intent_text, auto_flag) and drill:
                result["note"] = "Drill mode — planned only, no live execution"

            from app.ready_room.service import mark_note_status

            mark_note_status(
                path,
                "executed" if not drill else "drilled",
                {"intent_id": str(intent.id), "mode": mode},
            )
            archive_path = ready_room_root() / "archive" / path.name
            archive_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

            await log_activity(
                db,
                "ready_room_intent",
                f"Ready Room: {intent_text[:80]}",
                result,
            )
            outcomes.append(result)
        except Exception as exc:
            outcomes.append({"file": path.name, "ok": False, "error": str(exc)})

    summary = {
        "handwritten": handwritten,
        "scanned": len(outcomes),
        "ok": sum(1 for o in outcomes if o.get("ok")),
        "outcomes": outcomes,
    }
    if outcomes:
        await trigger_n8n("ready-room-scan", summary)
    return summary
