# Ready Room Manual — Obsidian-Only Operations

> The Ready Room is where you **organize intent** before the kill shot. Obsidian is your only interface — no portal required for daily command.

---

## What it is

```text
Your brain (handwritten or typed)
        ↓
Obsidian vault/ready-room/
        ↓
Scan → Intent engine → Hive executes
        ↓
Commander sees nuclear only
```

Voice and GitHub still work — but **Ready Room is the sovereign intent queue**.

---

## Folder map (in Obsidian)

Open vault folder: `ready-room/`

| Path | Purpose |
|------|---------|
| `intent/` | **Primary** — one file per intent, `status: pending` |
| `handwritten/` | Drop JPG/PNG of handwritten ops notes |
| `processed/` | Vision-extracted markdown |
| `archive/` | Completed intents (system moves here) |

---

## Create an intent (typed)

1. In Obsidian: **Templates** → `ready-room-intent`
2. Edit `intent:` line — one clear sentence
3. Set `mode:` 
   - `drill` = sights on (default, safe)
   - `live` = kill shot
4. Save into `ready-room/intent/`
5. Sync vault to VPS (Syncthing / Git push)

---

## Handwritten notes (your code, fixed)

Your diagram on paper → photo → ingest:

```bash
# On VPS (after sync) or local with OPENAI_API_KEY
python scripts/process-ready-room-note.py vault/ready-room/handwritten/my-note.jpg
```

Requires `OPENAI_API_KEY` in `.env` (vision extract).

Output:
- `ready-room/processed/*-extracted.md`
- `ready-room/intent/*-from-handwritten.md` (if intent detected)

---

## Fire execution (scan)

After sync, trigger scan **once**:

```bash
# Portal login token
curl -X POST https://157-254-194-89.sslip.io/api/ready-room/scan \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Or wire **n8n** cron: `POST /api/ready-room/scan` every 5 minutes.

**Voice:** *"Scan ready room. Auto execute."*

---

## Intent note format (frontmatter)

```yaml
---
type: intent
status: pending        # system sets executed/drilled after scan
mode: drill             # drill | live
auto_execute: true
intent: "Sovereign stay MTR leads — drill only"
tags: [ready-room, intent]
---
```

---

## Sights on vs kill shot (from Ready Room)

| mode | Ready Room | System |
|------|------------|--------|
| `drill` | You type intent + drill | Plans only, appends dry run |
| `live` | You type intent + live | Auto-executes hive + firewall |

---

## Check queue

```
GET /api/ready-room/status
```

Shows `pending_intents` count.

---

## Budget law (Ready Room)

- **Drill first** — default template uses `mode: drill`
- Scan does **not** cost money — vision ingest uses OpenAI only when you upload handwritten
- Live mode respects treasury caps ($25/task, $100/day)

---

## Sync setup (pick one)

| Method | Commander effort |
|--------|------------------|
| **Syncthing** | One-time VPS + phone setup |
| **Git** | Push vault from laptop, pull on VPS |
| **Obsidian Sync** | Easiest, paid |

Vault path on VPS: `/opt/Command-center/vault/ready-room/`

---

## Daily rhythm (Obsidian only)

1. Open Obsidian → `ready-room/intent/`
2. New note from template OR photo → handwritten folder
3. Sync
4. Scan fires (manual or n8n)
5. Check `archive/` for what executed
6. Nuclear queue in portal **only if needed**

---

## Related

- `vault/commander/launch-manual.md`
- `vault/commander/launch-cheat-sheet.md`
- `vault/ready-room/README.md`
