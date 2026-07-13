# Your Code → Ready Room System (intent map)

> Commander's `process_handwritten_note` — what each step means and where it lives now.

## Your original flow

```python
def process_handwritten_note(image_path):
    # 1. base64 encode image
    # 2. vision LLM (LLM_API_KEY) — extract text, rules, logic maps
    # 3. POST to populate Layer 1 database ledger
    # 4. save _extracted.md to Obsidian archive
```

**Intent:** Paper/diagram in Ready Room → structured strategy → database + Obsidian → hive executes when money allows fast build.

---

## Line-by-line mapping

| Your step | Was (sketch) | Is now (production) |
|-----------|--------------|---------------------|
| **1. base64** | `base64.b64encode` | `server/app/ready_room/service.py` → `extract_handwritten_note()` |
| **2. LLM vision** | `LLM_API_KEY` + gpt-4o | `LLM_API_KEY` **or** `OPENAI_API_KEY` in `.env` |
| **2b. API URL** | `https://openai.com` ❌ | `https://api.openai.com/v1/chat/completions` ✅ |
| **3. Layer 1 ledger** | "database ingestion" | `append_layer1_ledger()` → `vault/sovereign/empire_ledger.jsonl` |
| **4. Obsidian save** | `*_extracted.md` | Same folder: `note_extracted.md` + `ready-room/processed/` |
| **5. Intent queue** | (implied) | `ready-room/intent/*-from-handwritten.md` → scan → intent engine |

---

## How to run (Obsidian only)

1. Photo/diagram → save to `vault/ready-room/handwritten/my-plan.jpg`
2. Sync vault to VPS
3. **Auto:** `POST /api/ready-room/scan` (or doctor cron) picks up new images
4. **Manual:** `python scripts/process-ready-room-note.py vault/ready-room/handwritten/my-plan.jpg`

Output:
- `my-plan_extracted.md` (Obsidian — open immediately)
- `ready-room/processed/...-extracted.md`
- `vault/sovereign/empire_ledger.jsonl` (+1 line)
- Intent note if vision found an `intent:` in frontmatter

---

## Money gate (cheap until funded)

| Item | Cost | When |
|------|------|------|
| Typed intents in Obsidian | **$0** | Now |
| Scan / intent engine | **$0** | Now |
| Handwritten vision | ~$0.01–0.05/image | When `LLM_API_KEY` set |

No key = typed Ready Room still works. Handwritten waits for treasury — not blocked.

---

## Fast build when money lands

1. Set `LLM_API_KEY` in `.env`
2. Set `RENTAHUMAN_API_KEY` for closers
3. Ready Room `mode: live` → scan → presale wave
4. Layer 1 ledger already receiving ingest events — revenue lines append same file

---

## Function name preserved

```python
# server/app/ready_room/service.py
async def process_handwritten_note(image_path: str | Path) -> dict: ...
```

Same name. Same intent. Wired to empire stack.
