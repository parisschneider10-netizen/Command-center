"""Ready Room — Obsidian intent command center for the Sovereign Core."""

from __future__ import annotations

import base64
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.config import settings

READY_ROOM_FOLDERS = ("inbox", "intent", "processed", "archive", "handwritten", "chat")


def vision_api_key() -> str:
    """OPENAI_API_KEY or Commander's LLM_API_KEY — funds vision ingest when treasury clears."""
    import os

    return (settings.llm_api_key or settings.openai_api_key or os.getenv("LLM_API_KEY", "")).strip()


def ready_room_root() -> Path:
    root = Path(settings.vault_path) / "ready-room"
    root.mkdir(parents=True, exist_ok=True)
    for sub in READY_ROOM_FOLDERS:
        (root / sub).mkdir(exist_ok=True)
    (root / "chat" / "attachments").mkdir(parents=True, exist_ok=True)
    return root


def slugify(text: str, max_len: int = 50) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len] or "intent"


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse simple YAML frontmatter between --- markers."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    meta: dict[str, Any] = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if val.lower() in ("true", "false"):
            meta[key] = val.lower() == "true"
        else:
            meta[key] = val
    return meta, parts[2].strip()


def build_intent_note(
    *,
    intent: str,
    mode: str = "drill",
    auto_execute: bool = True,
    title: str | None = None,
    body: str = "",
    tags: list[str] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    tag_list = tags or ["ready-room", "intent"]
    if mode == "drill":
        tag_list = list({*tag_list, "drill", "sights-on"})
    else:
        tag_list = list({*tag_list, "live", "kill-shot"})
    title = title or intent[:60]
    return f"""---
type: intent
status: pending
mode: {mode}
auto_execute: {str(auto_execute).lower()}
intent: "{intent.replace('"', "'")}"
created: {now.isoformat()}
tags: [{", ".join(tag_list)}]
title: "{title.replace('"', "'")}"
source: ready-room
---

# {title}

## Commander intent

{intent}

## Mode

- **{mode.upper()}** — {"sights on (dry run)" if mode == "drill" else "kill shot (live)"}

{body}
"""


def write_intent_note(
    intent: str,
    *,
    mode: str = "drill",
    auto_execute: bool = True,
    title: str | None = None,
    body: str = "",
) -> Path:
    root = ready_room_root()
    now = datetime.now(timezone.utc)
    filename = f"{now.strftime('%Y-%m-%d-%H%M')}-{slugify(intent)}.md"
    path = root / "intent" / filename
    path.write_text(
        build_intent_note(
            intent=intent,
            mode=mode,
            auto_execute=auto_execute,
            title=title,
            body=body,
        ),
        encoding="utf-8",
    )
    return path


def list_ready_room_notes(folder: str = "intent", limit: int = 50) -> list[dict]:
    root = ready_room_root()
    folder_path = root / folder
    if not folder_path.exists():
        return []
    notes = sorted(folder_path.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    result = []
    for path in notes[:limit]:
        content = path.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(content)
        stat = path.stat()
        result.append(
            {
                "filename": path.name,
                "folder": folder,
                "path": str(path.relative_to(Path(settings.vault_path))),
                "status": meta.get("status", "unknown"),
                "mode": meta.get("mode", "drill"),
                "intent": meta.get("intent", ""),
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return result


def mark_note_status(path: Path, status: str, extra: dict | None = None) -> None:
    content = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(content)
    meta["status"] = status
    meta["updated"] = datetime.now(timezone.utc).isoformat()
    if extra:
        meta.update(extra)
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, bool):
            lines.append(f"{k}: {str(v).lower()}")
        else:
            lines.append(f'{k}: "{v}"' if " " in str(v) else f"{k}: {v}")
    lines.append("---")
    path.write_text("\n".join(lines) + "\n\n" + body, encoding="utf-8")


VISION_PROMPT = """You are the Ready Room ingest engine for a one-man empire command system.

Extract ALL content from this handwritten operational note into structured markdown for Obsidian vault ingestion.

Output format (start with frontmatter exactly):

---
type: intent
status: pending
mode: drill
auto_execute: true
intent: "<single clear intent sentence>"
tags: [ready-room, handwritten]
source: ready-room-handwritten
---

# <title>

## Extracted text
<all readable text>

## Rules and constraints
<bullet list of any rules written>

## Logic map
<mermaid or bullet flow if diagrams present; describe arrows and boxes>

## Suggested kill-shot phrase
<one voice command line if launch-related>

If mode cannot be determined, use mode: drill. Never invent financial numbers not on the page."""


async def extract_handwritten_note(image_bytes: bytes, mime: str = "image/jpeg") -> str:
    """Vision LLM — your process_handwritten_note step 2+3 (correct API endpoint)."""
    api_key = vision_api_key()
    if not api_key:
        raise ValueError(
            "LLM_API_KEY or OPENAI_API_KEY missing — add when treasury clears vision spend"
        )
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                ],
            }
        ],
        "max_tokens": 2000,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if response.status_code >= 400:
            raise ValueError(f"Vision API failed ({response.status_code}): {response.text}")
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def save_handwritten_extraction(
    image_bytes: bytes,
    *,
    original_name: str,
    mime: str = "image/jpeg",
) -> dict:
    root = ready_room_root()
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d-%H%M%S")
    slug = slugify(Path(original_name).stem)

    image_ext = ".jpg" if "jpeg" in mime else ".png" if "png" in mime else ".img"
    image_path = root / "handwritten" / f"{stamp}-{slug}{image_ext}"
    image_path.write_bytes(image_bytes)

    extracted = await extract_handwritten_note(image_bytes, mime=mime)
    md_path = root / "processed" / f"{stamp}-{slug}-extracted.md"
    md_path.write_text(extracted, encoding="utf-8")

    meta, _ = parse_frontmatter(extracted)
    intent_path = None
    if meta.get("type") == "intent" and meta.get("intent"):
        intent_path = root / "intent" / f"{stamp}-{slug}-from-handwritten.md"
        intent_path.write_text(extracted, encoding="utf-8")

    return {
        "image_path": str(image_path.relative_to(Path(settings.vault_path))),
        "extracted_path": str(md_path.relative_to(Path(settings.vault_path))),
        "intent_path": str(intent_path.relative_to(Path(settings.vault_path))) if intent_path else None,
        "intent": meta.get("intent", ""),
        "mode": meta.get("mode", "drill"),
    }


def _ingested_marker(image_path: Path) -> Path:
    return image_path.with_suffix(image_path.suffix + ".ingested")


def append_layer1_ledger(event: dict) -> Path:
    """Layer 1 database ledger — append-only JSONL (your step 3 population target)."""
    import json

    ledger = Path(settings.sovereign_ledger_path)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "layer": 1,
        "source": "ready-room",
        **event,
    }
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")
    return ledger


async def process_handwritten_note(image_path: str | Path) -> dict:
    """
    Commander's process_handwritten_note — Ready Room vault ingest.

    1. Encode image base64 (internal)
    2. Vision LLM extract → structured markdown
    3. Save Obsidian archive + Layer 1 ledger line + intent queue
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Ready Room image not found: {path}")

    suffix = path.suffix.lower()
    mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png" if suffix == ".png" else "image/jpeg"
    data = path.read_bytes()

    extracted = await extract_handwritten_note(data, mime=mime)

    # Obsidian archive — note_extracted.md beside the scan (your output_path pattern)
    obsidian_out = path.parent / f"{path.stem}_extracted.md"
    obsidian_out.write_text(extracted, encoding="utf-8")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    slug = slugify(path.stem)
    root = ready_room_root()
    md_path = root / "processed" / f"{stamp}-{slug}-extracted.md"
    md_path.write_text(extracted, encoding="utf-8")

    meta, _ = parse_frontmatter(extracted)
    intent_path = None
    if meta.get("type") == "intent" and meta.get("intent"):
        intent_path = root / "intent" / f"{stamp}-{slug}-from-handwritten.md"
        intent_path.write_text(extracted, encoding="utf-8")

    ledger_path = append_layer1_ledger(
        {
            "event": "handwritten_ingest",
            "image": str(path.name),
            "extracted": str(md_path.name),
            "intent": meta.get("intent", ""),
            "mode": meta.get("mode", "drill"),
        }
    )
    _ingested_marker(path).write_text(md_path.name, encoding="utf-8")

    return {
        "image_path": str(path),
        "obsidian_extracted": str(obsidian_out),
        "extracted_path": str(md_path.relative_to(Path(settings.vault_path))),
        "intent_path": str(intent_path.relative_to(Path(settings.vault_path))) if intent_path else None,
        "ledger_path": str(ledger_path),
        "intent": meta.get("intent", ""),
        "mode": meta.get("mode", "drill"),
    }


async def scan_handwritten_inbox() -> dict:
    """Auto-ingest new images in ready-room/handwritten/ (Obsidian drop folder)."""
    root = ready_room_root() / "handwritten"
    outcomes = []
    for path in sorted(root.glob("*")):
        if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        if _ingested_marker(path).exists():
            continue
        try:
            result = await process_handwritten_note(path)
            outcomes.append({"file": path.name, "ok": True, **result})
        except Exception as exc:
            outcomes.append({"file": path.name, "ok": False, "error": str(exc)})
    return {
        "handwritten_scanned": len(outcomes),
        "ok": sum(1 for o in outcomes if o.get("ok")),
        "outcomes": outcomes,
    }
