# Machine Speed Checklist

What to connect, where secrets go, and in what order. **Never paste API keys in chat, Issues, or GitHub.**

## Golden rule

```text
Secrets → VPS .env file ONLY (or Cursor Cloud secrets for GH_TOKEN)
Code → GitHub (no keys ever)
You → command via Issues + SARA
```

---

## TIER 0 — Tonight (empire online)

| # | What | Where | Give to me in chat? |
|---|------|-------|---------------------|
| 1 | **Merge PR #1** | GitHub | No — just merge |
| 2 | **SSH access to your Servury VPS** | You run deploy | **No password in chat** — hire DevOps or SSH yourself |
| 3 | **Clone repo on VPS** | `git clone` + `docker compose up -d` | No |
| 4 | **`.env` on VPS** | copy from `.env.example` | Fill locally on VPS, never commit |
| 5 | **GitHub → Cursor** | cursor.com settings | No |
| 6 | **`GH_TOKEN`** | Cursor Cloud Agent secrets | Create PAT yourself, paste in Cursor UI only |
| 7 | **Vapi** | dashboard.vapi.ai | Webhook URL only in docs — keys in Vapi UI |

**Result:** Call SARA + file GitHub Issues + portal live.

---

## TIER 1 — Money bot live (expansion node)

| Secret | Goes in VPS `.env` | Required when |
|--------|-------------------|---------------|
| `SERVURY_API_KEY` | ✅ VPS | Provisioning client VPS nodes |
| `SERVURY_API_URL` | ✅ VPS | Verify from Servury dashboard |
| `GHL_API_KEY` | ✅ VPS | Creating PM sub-accounts |
| `GHL_COMPANY_ID` | ✅ VPS | GHL SaaS |
| `GHL_MTR_RECON_SNAPSHOT_ID` | ✅ VPS | Snapshot flash |
| `EXPANSION_DRY_RUN=false` | ✅ VPS | Only after dry run works |

**Do NOT give me these in chat.** Put on VPS. Tell me: *"keys are in .env, test expansion dry run"*.

---

## TIER 2 — Hive brain (agents)

| Secret | Where | Notes |
|--------|-------|-------|
| `OPENAI_API_KEY` | VPS `.env` | Voice OS, agents (Vapi often uses its own) |
| `ANTHROPIC_API_KEY` | VPS `.env` | If you use Claude for workers — **optional**, not required for me in Cursor |
| `BRAVE_SEARCH_API_KEY` | VPS `.env` | Research agents — later |
| `SKYVERN_API_KEY` | VPS `.env` | Browser automation — later |

### Anthropic specifically

- **Cursor** bills you for Cloud Agent (Cursor subscription) — separate from Anthropic
- **Your VPS agents** use `ANTHROPIC_API_KEY` from `.env` if we wire Claude workers
- **You do NOT need to give me your Anthropic key** for GitHub/Issue building — I run on Cursor's stack
- **You DO need it on VPS** when AutoGen/Claude workers run 24/7 on your server

---

## TIER 3 — Humans + overflow

| Secret | Where | When |
|--------|-------|------|
| `RENTAHUMAN_API_KEY` | VPS `.env` | Physical tasks, hiring humans via API |
| Guardian contacts | `vault/guardians/` | Not API keys — roster |

RentAHuman: get key at rentahuman.ai → VPS `.env` only. Tell me when set, not the key.

---

## TIER 4 — Comms (kill Gmail)

| Secret | Where |
|--------|-------|
| `COMMS_IMAP_*` / `COMMS_SMTP_*` | VPS `.env` |

Migadu/Fastmail or self-hosted mail — after foundation live.

---

## Servury: two different things

| Thing | What it is | What you do |
|-------|-----------|-------------|
| **Your empire VPS** | The server you rent now | SSH in, deploy `docker compose`, put `.env` here |
| **Servury API** | Money bot creates MORE VPS for clients | API key in `.env` on empire VPS |

You don't "connect me to Servury" — you **deploy the repo on your Servury box** and put secrets in `.env` there.

Optional: hire someone on RentAHuman to run the deploy if you can't SSH at work.

---

## What I need from you (safe to say in chat)

✅ **Yes, tell me:**
- "Keys are set on VPS"
- Servury API docs / correct endpoint URL
- GHL company ID format (not the key)
- Domain name for HTTPS
- GitHub repo names
- What the lead scraper looks like
- Errors from logs (redact secrets)

❌ **Never tell me:**
- API keys, passwords, SSH root password
- Private tokens in Issues or chat

---

## Machine speed order (do in parallel)

```text
HOUR 1     Merge PR → deploy VPS → .env core secrets
HOUR 2     Vapi webhook → test SARA call
HOUR 3     GH_TOKEN in Cursor → first @cursor Issue
DAY 2      Expansion dry run → then GHL + Servury keys → live 1 city
DAY 3      Lead scraper wired → n8n auto pipeline
WEEK 1     RentAHuman key → income + hire for fires
WEEK 2     Document everything in vault/ for the world
```

---

## Document for the world

Your story lives in:
- `vault/` — process, decisions, manifest (Obsidian)
- GitHub Issues — public command log (can make repo public later)
- `docs/` — architecture others can fork

When ready to inspire solo entrepreneurs: open-source the template repo, keep `.env` private.

---

## Billing reality (honest)

| Service | Who bills you |
|---------|---------------|
| Cursor | Cursor (Cloud Agents) |
| Vapi | Per-minute voice |
| Servury | VPS hosting |
| GHL | Per sub-account / SaaS |
| OpenAI/Anthropic | Per token on VPS agents |
| RentAHuman | Per bounty |

Owning infrastructure reduces lock-in; it doesn't eliminate API costs. Treasury layer tracks it all.

---

## One message to send me after Tier 0

```text
Foundation deployed on Servury at [domain or IP].
Vapi webhook set. GH_TOKEN in Cursor.
Ready for expansion dry run.
Lead scraper: [paste code or repo link — no keys]
```

That's machine speed. You command. Keys stay on the machine. We build.
