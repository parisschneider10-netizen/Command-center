#!/usr/bin/env python3
"""
Ready Room — process handwritten operational note (CLI).

Usage (on VPS or laptop with vault synced):
  export OPENAI_API_KEY=sk-...
  python scripts/process-ready-room-note.py vault/ready-room/handwritten/my-note.jpg

Or pipe to API:
  curl -X POST https://YOUR_DOMAIN/api/ready-room/handwritten \\
    -H "Authorization: Bearer $TOKEN" \\
    -F "file=@my-note.jpg"
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Allow running from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from app.config import settings  # noqa: E402
from app.ready_room.service import save_handwritten_extraction  # noqa: E402


def _mime(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    return "image/jpeg"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest handwritten Ready Room note")
    parser.add_argument("image_path", type=Path, help="Path to jpg/png scan")
    args = parser.parse_args()

    if not args.image_path.exists():
        print(f"ERROR: file not found: {args.image_path}", file=sys.stderr)
        sys.exit(1)

    key = os.getenv("OPENAI_API_KEY") or settings.openai_api_key
    if not key:
        print("ERROR: set OPENAI_API_KEY in environment or .env", file=sys.stderr)
        sys.exit(1)

    data = args.image_path.read_bytes()
    result = await save_handwritten_extraction(
        data,
        original_name=args.image_path.name,
        mime=_mime(args.image_path),
    )
    print(f"SYSTEM DATA INGESTED: Ready Room updated")
    print(f"  image:     {result['image_path']}")
    print(f"  extracted: {result['extracted_path']}")
    if result.get("intent_path"):
        print(f"  intent:    {result['intent_path']}")
    print("Next: POST /api/ready-room/scan or run scan from Obsidian workflow")


if __name__ == "__main__":
    asyncio.run(main())
