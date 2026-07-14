"""Ready Room chat — text + files like a messaging UI, sovereign on your VPS."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.n8n import trigger_n8n
from app.ready_room.scanner import scan_pending_intents
from app.ready_room.service import (
    ready_room_root,
    write_intent_note,
)
from app.services import log_activity


def _append_chat_transcript(source: str, text: str) -> Path:
    """Append chat line to daily transcript in vault (sovereign record)."""
    chat_dir = ready_room_root() / "chat"
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = chat_dir / f"{day}.md"
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%SZ")
    line = f"\n- **{stamp}** [{source}] {text.strip()}\n"
    if not path.exists():
        path.write_text(f"# Ready Room chat — {day}\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
    return path


def parse_chat_message(text: str) -> dict:
    """
    Parse Commander chat line into intent parameters.
    Examples:
      "launch sovereign stay live"
      "drill: expansion one city"
      "scan"
      "note: competitor pricing idea"
    """
    raw = (text or "").strip()
    lower = raw.lower()

    if lower in ("scan", "scan ready room", "execute", "fire"):
        return {"action": "scan"}

    if lower.startswith("lead:") or lower.startswith("lead "):
        body = raw.split(":", 1)[-1].strip() if ":" in raw else raw[5:].strip()
        parts = [p.strip() for p in body.replace("|", ",").split(",") if p.strip()]
        if len(parts) >= 3:
            return {
                "action": "lead",
                "name": parts[0],
                "phone": parts[1],
                "city": parts[2],
                "email": parts[3] if len(parts) > 3 else None,
            }
        return {"action": "note", "body": body, "title": "Lead parse failed — use: lead: Name, phone, city"}

    if lower.startswith("note:") or lower.startswith("note "):
        body = raw.split(":", 1)[-1].strip() if ":" in raw else raw[5:].strip()
        return {"action": "note", "body": body, "title": body[:60]}

    mode = "drill"
    if any(k in lower for k in ("launch", "kill shot", "killshot", " live", "live ")):
        mode = "live"
    if any(k in lower for k in ("drill", "dry run", "sights on", "test")):
        mode = "drill"

    intent = raw
    for prefix in ("launch:", "drill:", "intent:", "live:"):
        if lower.startswith(prefix):
            intent = raw[len(prefix) :].strip()
            break

    return {
        "action": "intent",
        "intent": intent,
        "mode": mode,
        "auto_execute": True,
    }


async def handle_chat_message(
    db: AsyncSession,
    text: str,
    *,
    source: str = "chat",
    auto_scan: bool = False,
) -> dict:
    """One chat line → Ready Room intent, note, or scan."""
    parsed = parse_chat_message(text)
    _append_chat_transcript(source, text)

    if parsed["action"] == "scan":
        result = await scan_pending_intents(db)
        await log_activity(db, "ready_room_chat_scan", "Chat: scan", result, source=source)
        return {"ok": True, "action": "scan", **result}

    if parsed["action"] == "note":
        from app.vault import write_inbox_note

        path = write_inbox_note(parsed["title"], parsed["body"], source=source)
        return {"ok": True, "action": "note", "path": str(path.name)}

    if parsed["action"] == "lead":
        from app.value_node.expansion import register_lead

        lead = await register_lead(
            db,
            {
                "name": parsed["name"],
                "phone": parsed["phone"],
                "city": parsed["city"],
                "email": parsed.get("email"),
            },
            source=source,
        )
        return {
            "ok": True,
            "action": "lead",
            "id": lead.id,
            "name": lead.name,
            "city": lead.city,
        }

    path = write_intent_note(
        parsed["intent"],
        mode=parsed["mode"],
        auto_execute=parsed.get("auto_execute", True),
    )
    await log_activity(
        db,
        "ready_room_chat_intent",
        parsed["intent"][:80],
        {"path": path.name, "mode": parsed["mode"], "source": source},
    )
    await trigger_n8n(
        "ready-room-chat",
        {"intent": parsed["intent"], "mode": parsed["mode"], "path": path.name},
    )

    result: dict = {
        "ok": True,
        "action": "intent",
        "path": str(path.relative_to(ready_room_root().parent)),
        "mode": parsed["mode"],
        "auto_scan": auto_scan,
    }
    if auto_scan:
        result["scan"] = await scan_pending_intents(db)
    return result


async def save_chat_attachment(
    db: AsyncSession,
    data: bytes,
    filename: str,
    mime: str,
    *,
    source: str = "chat",
    caption: str = "",
    auto_scan: bool = True,
) -> dict:
    """File/photo upload in chat → handwritten ingest + optional caption intent."""
    from app.ready_room.service import process_handwritten_note, save_handwritten_extraction

    attach_dir = ready_room_root() / "chat" / "attachments"
    safe = re.sub(r"[^a-zA-Z0-9._-]", "-", filename)[:80]
    dest = attach_dir / safe
    dest.write_bytes(data)
    handwritten = ready_room_root() / "handwritten" / safe
    handwritten.write_bytes(data)

    try:
        ingest = await process_handwritten_note(handwritten)
    except ValueError:
        ingest = await save_handwritten_extraction(data, original_name=filename, mime=mime)

    result = {"ok": True, "action": "file", "path": str(dest.relative_to(ready_room_root().parent)), **ingest}

    if caption.strip():
        chat = await handle_chat_message(db, caption, source=source, auto_scan=False)
        result["caption"] = chat

    if auto_scan:
        result["scan"] = await scan_pending_intents(db)

    await log_activity(db, "ready_room_chat_file", filename, result)
    return result
