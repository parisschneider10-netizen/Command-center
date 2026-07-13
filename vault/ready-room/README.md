# Ready Room — Obsidian Intent Command Center

> **Operate the empire from Obsidian only.** Type intent here. Hive executes when you scan.

## Folders

| Folder | You do | System does |
|--------|--------|-------------|
| `intent/` | Create intent notes from template | Scans → intent engine |
| `handwritten/` | Drop photo of handwritten ops notes | Vision extract → `processed/` |
| `processed/` | Read extractions | Auto-queued intents |
| `archive/` | Review history | Moved after execute |
| `inbox/` | Quick captures | Triage to intent |

## Workflow (sights on → kill shot)

### 1. Type intent (Obsidian)

Use template: `templates/ready-room-intent.md`

- `mode: drill` — sights on, no live spend
- `mode: live` — kill shot

Save to `ready-room/intent/`. Sync vault (Syncthing/Git).

### 2. Fire the hive

**Option A — API (n8n cron every 5 min):**
```
POST /api/ready-room/scan
```

**Option B — Voice:**
> *"Scan ready room. Max speed."*

**Option C — Portal** (future button) — scan now

### 3. Handwritten notes

1. Photo your diagram → save to `ready-room/handwritten/note.jpg`
2. Run: `python scripts/process-ready-room-note.py vault/ready-room/handwritten/note.jpg`
3. Or: `POST /api/ready-room/handwritten` with image upload
4. `POST /api/ready-room/scan`

## Status

```
GET /api/ready-room/status
```

## Manual

`vault/commander/ready-room-manual.md`
