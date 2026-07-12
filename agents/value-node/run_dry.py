#!/usr/bin/env python3
"""Dry-run the expansion orchestrator against local Voice OS API or in-process."""

import asyncio
import os
import sys

# Allow running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

from app.database import SessionLocal, init_db
from app.value_node.expansion import scale_cities


async def main() -> None:
    await init_db()
    mock_leads = [
        {
            "name": f"Vanguard Property Management C-{i}",
            "email": f"ops@pmNode{i}.com",
            "phone": f"+155500040{i:02d}",
            "address": "100 Main St",
            "zip": "64106",
            "city": f"TargetCity_{i}",
        }
        for i in range(1, 4)  # start with 3 in dry run, not 40
    ]

    async with SessionLocal() as db:
        result = await scale_cities(db, mock_leads, dry_run=True)
        print(f"\n[=] DRY RUN: {result['successful']}/{result['total']} nodes")


if __name__ == "__main__":
    asyncio.run(main())
