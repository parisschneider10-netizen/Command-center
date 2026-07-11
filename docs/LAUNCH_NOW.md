# Launch Now — Communicate, Deploy, Fund the Sandbox

> **40 cities × 3 units = your funded sandbox.** Treasury clears presale cash **instantly** into ammo pools for expansion.

You do **not** need Gmail connected to Cursor. You need **three pipes** and one VPS.

---

## Step 0 — Talk to me TODAY (no VPS required)

### Primary: GitHub Issues from your phone

1. Install **GitHub** app
2. Repo: `parisschneider10-netizen/Command-center`
3. **Issues → New issue**

```markdown
Title: [BUILD] Deploy Command Center on Servury

@cursor

Merge PR #2. Give me copy-paste SSH deploy steps for Servury IP ___.
Wire SARA Vapi webhook after deploy.
```

This works at work, on break, anywhere with internet. **This is your build channel.**

### Backup: cursor.com/agents

Same text, paste into Cloud Agent if GitHub Issues glitch.

### NOT this

| ❌ | ✅ |
|----|-----|
| Gmail password to Cursor | GitHub Issue `@cursor` |
| Expect me to read your inbox | Forward mail → sovereign domain later |

---

## Step 1 — Launch Command Center on Servury ($20 balance)

**One VPS runs everything 24/7:**

```text
docker compose up -d
  ├── api (Command Center)
  ├── portal (your dashboard)
  ├── n8n (automations)
  └── postgres
```

### Copy-paste deploy (SSH into Servury)

```bash
curl -fsSL https://get.docker.com | sh
git clone https://github.com/parisschneider10-netizen/Command-center.git
cd Command-center
git checkout cursor/sovereign-stay-matrix-1894
cp .env.example .env
nano .env   # set SECRET_KEY, PORTAL_PASSWORD, PUBLIC_BASE_URL=http://YOUR_IP:8000
docker compose up -d --build
curl http://localhost:8000/health
```

**Can't SSH?** RentAHuman gig (~$25–50): *"Deploy docker compose on my VPS at IP ___"*

When live:
- Portal: `http://YOUR_IP:3000`
- API health: `http://YOUR_IP:8000/health`
- Bridge status: `GET /api/bridge/status` (after login)

---

## Step 2 — Wire SARA (voice hotline)

1. [dashboard.vapi.ai](https://dashboard.vapi.ai) → your assistant
2. Set webhook: `http://YOUR_IP:8000/vapi/webhook` (HTTPS when domain ready)
3. Call SARA → *"Sovereign stay status"* / *"Create task: deploy next city"*

SARA needs VPS. GitHub Issues work **before** VPS.

---

## Step 3 — Your communication stack (100% uptime goal)

```text
┌─────────────────────────────────────────────────────────┐
│  YOU (phone, work, anywhere)                             │
└───────┬─────────────────┬─────────────────┬─────────────┘
        │                 │                 │
   GitHub Issue      Call SARA         Portal login
   @cursor builds    voice tasks       tasks · treasury
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
              Command Center API (Servury 24/7)
                          │
              Cursor Cloud Agent (builds PRs)
```

| Channel | Uptime | When to use |
|---------|--------|-------------|
| **GitHub Issues** | GitHub's | Build orders, `@cursor`, PR review |
| **SARA / Vapi** | After VPS deploy | Hands-free commands, briefings |
| **Portal** | Your VPS | Empire tab, treasury, tasks |
| **Bridge webhook** | Your VPS + n8n | Stripe paid → auto presale |

**100% uptime** = Servury VPS always on + `restart: unless-stopped` in Docker (already set). You command through GitHub even if VPS blips — builds keep happening on GitHub.

---

## Step 4 — Real-time treasury (sandbox)

When a **Sovereign Stay presale** hits (`POST /api/sovereign-stay/presale`):

```text
$150 host payment
    → ledger status: CLEARED (instant — no 48h wait)
    → 70% → ammo pools (compute, network, storage…)
    → auto-fund top sovereign acquisitions
    → $30 closer paid from same inbound (host money, not yours)
```

Config on VPS:

```env
TREASURY_SANDBOX_INSTANT_CLEAR=true
SOVEREIGN_TARGET_CITIES=40
SOVEREIGN_UNITS_PER_CITY=3
```

**Every presale expands empire power the same second it lands.**

---

## Step 5 — The funded sandbox (40 × 3)

| Metric | Value |
|--------|-------|
| Cities | 40 grids |
| Units per city | 3 max |
| Total sandbox | **120 units** |
| Presale each | $150 |
| Full grid gross | $18,000 presale float |

This is **not** World Cup. This is evergreen — one city at a time, copy the matrix.

```text
City 1: lock 3 hosts → treasury ammo → fund next VPS / Starlink / closer batch
City 2: repeat
…
City 40: empire tier rises → more ammo % per dollar
```

---

## Your order of operations (do this in order)

| # | Action | Time |
|---|--------|------|
| 1 | GitHub Issue: `@cursor help me deploy Servury` | **Today** |
| 2 | Deploy docker on Servury (you or RentAHuman) | Day 1 |
| 3 | Wire Vapi → SARA | Day 1 |
| 4 | `POST /api/sovereign-stay/simulate` — verify sandbox | Day 1 |
| 5 | First real presale in Kansas City sandbox | Day 2–3 |
| 6 | n8n: Stripe webhook → presale API | When Stripe ready |

---

## Daily loop once live

```text
Morning (work)  → GitHub Issue @cursor
Break           → Call SARA or check portal treasury
Evening         → git pull on VPS if new PR merged
Weekend         → Dispatch closers, lock sandbox units
```

You command. I build on GitHub. VPS runs empire. Treasury funds expansion instantly.

See [GITHUB_COMMAND.md](GITHUB_COMMAND.md) · [BEGINNER_SETUP.md](BEGINNER_SETUP.md) · [SOVEREIGN_STAY_PLAY.md](SOVEREIGN_STAY_PLAY.md)
