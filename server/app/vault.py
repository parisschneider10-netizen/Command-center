"""Obsidian vault — markdown file operations."""

import re
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings


def vault_root() -> Path:
    root = Path(settings.vault_path)
    root.mkdir(parents=True, exist_ok=True)
    for sub in ("inbox", "tasks", "research", "decisions", "projects", "templates"):
        (root / sub).mkdir(exist_ok=True)
    # Ready Room — Obsidian intent command center
    rr = root / "ready-room"
    rr.mkdir(exist_ok=True)
    for sub in ("inbox", "intent", "processed", "archive", "handwritten"):
        (rr / sub).mkdir(exist_ok=True)
    return root


def slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len] or "note"


def write_inbox_note(title: str, body: str, source: str = "voice") -> Path:
    root = vault_root()
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M")
    slug = slugify(title)
    filename = f"{date_str}-{time_str}-{slug}.md"
    path = root / "inbox" / filename

    content = f"""---
created: {now.isoformat()}
source: {source}
tags: [inbox]
title: "{title.replace('"', "'")}"
---

# {title}

{body}
"""
    path.write_text(content, encoding="utf-8")
    return path


def list_notes(folder: str = "inbox", limit: int = 50) -> list[dict]:
    root = vault_root()
    folder_path = root / folder
    if not folder_path.exists():
        return []

    notes = sorted(folder_path.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    result = []
    for path in notes[:limit]:
        stat = path.stat()
        result.append(
            {
                "filename": path.name,
                "folder": folder,
                "path": str(path.relative_to(root)),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return result


def read_note(folder: str, filename: str) -> str | None:
    root = vault_root()
    path = root / folder / filename
    if not path.exists() or not path.is_file():
        return None
    if ".." in filename or "/" in filename:
        return None
    return path.read_text(encoding="utf-8")
