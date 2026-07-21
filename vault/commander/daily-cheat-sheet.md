# Commander Daily Cheat Sheet

> **Pin this in Obsidian.** One page. Phone + portal. No SSH. No chat dependency.

---

## Your operating model

```
READY ROOM (think)     →  Obsidian + handwritten + chat
        ↓
HIVE (execute)         →  VPS while you're at work
        ↓
COMMAND CENTER (see)   →  Portal — operate only when you must
        ↓
SARA (voice)           →  Call when hands are busy
```

**You state will. Machine executes. You see nuclear only.**

---

## Two controls (daily)

| Control | URL / number |
|---------|----------------|
| **Portal** | http://157.254.194.89:3000 → **Launch** tab |
| **SARA** | **+1 (971) 382-0038** |

**Login:** `commander` (lowercase) + password from deploy log  
**Health:** https://157-254-194-89.sslip.io/health → `sara_wired: true`

---

## Current mission: Eco-Express (no hosts)

**D2C smart thermostat installs — Kansas City suburbs**

| Line | $ |
|------|---|
| Homeowner pays (before work) | **149** |
| Hardware (~rebate stack) | **~50** |
| RentAHuman installer | **40** |
| **Your net / door** | **59** |

**Goal:** 4 doors/day → **$236/day** → land-acquisition vault → **your** properties later

---

## Morning (5 min — before day shift)

1. GitHub Actions → **Deploy Servury VPS** (if code changed)
2. Portal → **Launch** tab → check door count
3. Optional: **Wire SARA** if voice badge says not wired

---

## Portal buttons (Launch tab)

| Button | Does what |
|--------|-----------|
| **LAUNCH ECO-EXPRESS LIVE** | Strike list + live intent — hunters go |
| **BUILD STRIKE LIST (Loop A)** | Auto-hunt KCMO doors → queue jobs |
| **Sights on (drill)** | Rehearse — no live installer pay |
| **Loop B form** | Job ID + payment proof → Lowe's barcode + RAH install |

---

## Hunter pitch (at the door)

> *"Evergy is updating grid efficiency on this block. Your manual thermostat is bleeding ~$180/year. Eco-Express: we swap in a Wi-Fi smart thermostat in 15 minutes. Rebate makes hardware **free** — you pay **$149** for install and programming. Right now or 4 PM — which slot?"*

Full text: `vault/commander/eco-express-play.md` or `GET /api/eco-express/pitch`

---

## The three loops

```
Loop A   BUILD STRIKE LIST     → doors queued
Loop B   Homeowner pays $149  → portal: Job ID + proof → install dispatched
Loop C   Installer done        → Wi-Fi photo on unit or payout FROZEN
```

---

## Say to SARA

| When | Say |
|------|-----|
| Briefing | *"Give me a briefing."* |
| Go live | *"Launch eco express live. Max speed. Auto execute."* |
| Strike only | *"Run eco express strike list."* |
| Drill | *"Eco express drill — dry run."* |

---

## Ready Room (when you think, not operate)

| Action | Where |
|--------|--------|
| Typed intent | Obsidian → `ready-room/intent/` → `mode: live` or `drill` |
| Handwritten | Photo → `ready-room/handwritten/` → scan |
| Chat | Portal Launch or Telegram: `launch eco express live` |

Sync vault → VPS → scan runs intent.

**Claude vision:** `ANTHROPIC_API_KEY` on VPS `.env` (handwritten notes)

---

## Keys on VPS only (never paste in chat)

| Key | Why |
|-----|-----|
| `ANTHROPIC_API_KEY` | Handwritten Ready Room |
| `RENTAHUMAN_API_KEY` | Live installer $40 payouts |
| `BRAVE_SEARCH_API_KEY` | Better strike list (optional) |
| `VAPI_API_KEY` | SARA (GitHub Secrets + Wire SARA) |

File: `/opt/Command-center/.env`

---

## Budget guards

| Cap | Limit |
|-----|-------|
| Per human task | **$25** → nuclear |
| Commander daily | **$100** |
| Installer | **$40** per job (built-in) |

**Rule:** Homeowner pays before work. Commander $0 OOP.

---

## Deploy / fix (no SSH)

| Need | Action |
|------|--------|
| New code on VPS | GitHub → **Deploy Servury VPS** |
| Voice brain | GitHub → **Wire SARA (machine speed)** |
| Big build | GitHub Issue → `@cursor [BUILD] …` |

---

## Nuclear only (you)

- Legal / contracts  
- Spend over cap  
- Public brand  

**Not nuclear:** deploy, strike list, hunters, installers, payment confirm.

---

## Paused (not deleted)

| Play | Status |
|------|--------|
| Sovereign Stay (hosts) | Paused — 3 hosts KC was prior focus |
| GHL forms | Not needed |
| 40-city matrix | Scale later — after Eco-Express cash |

---

## Endgame

```
Eco-Express cash  →  vault  →  master lease YOUR 3 units  →  sovereign grid
```

Suburbs fund the empire. Hosts are obsolete.

---

## Deep manuals

| Topic | File |
|-------|------|
| Eco-Express full | `vault/commander/eco-express-play.md` |
| Ready Room | `vault/commander/ready-room-manual.md` |
| Launch ops | `vault/commander/launch-manual.md` |
| 3-host focus (old) | `vault/commander/focus-3-hosts.md` |

---

*Chat can reset. This sheet + vault + VPS do not.*
