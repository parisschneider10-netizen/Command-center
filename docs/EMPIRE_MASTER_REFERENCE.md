# Empire Master Reference — Everything We Built & Decided

> Commander cheat sheet. One place for the full vision, plays, APIs, and how to command the hive.

---

## 1. How to build via GitHub (your primary channel)

**Works from phone. No Gmail. No VPS required to command builds.**

```text
GitHub app → Command-center repo → Issues → New issue OR comment
Body MUST include: @cursor
```

### Verify it works (5 min)

1. [cursor.com](https://cursor.com) → Settings → Integrations → **GitHub** → Connected to `Command-center`
2. Open Issue **#3** → add **comment** (not just title):

```markdown
@cursor

Servury IP: 157.254.194.89
Branch: cursor/sovereign-stay-matrix-1894
Merge PR #2 and confirm deploy steps.
```

3. Watch issue for agent reply or new PR (15–30 min)
4. **Backup:** [cursor.com/agents](https://cursor.com/agents) → paste same text

### Optional: fix Issues token gap

GitHub → Settings → Developer settings → Fine-grained PAT → Issues + Contents + PRs  
Add to Cursor Cloud Agent secrets as `GH_TOKEN`

### Daily build loop

| When | Action |
|------|--------|
| Work break | GitHub Issue `@cursor build X` |
| After merge | SSH VPS: `git pull && docker compose up -d --build` |
| Stuck | Issue comment `@cursor [BLOCKED] error: ___` (no passwords) |

**Docs:** [GITHUB_COMMAND.md](GITHUB_COMMAND.md) · [COMMUNICATION_BRIDGE.md](COMMUNICATION_BRIDGE.md)

---

## 2. Your infrastructure (what runs where)

| Piece | Role | Status |
|-------|------|--------|
| **GitHub** | Command me (`@cursor`) — builds PRs | Use now |
| **Cursor Cloud Agent** | Writes code on branches | Connect GitHub |
| **Servury VPS** | `157.254.194.89` — 24/7 empire runtime | Deploy pending |
| **SARA / Vapi** | Voice hotline → Command Center | After VPS deploy |
| **Portal** | `http://157.254.194.89:3000` | After deploy |
| **n8n** | Automations, doctor cron, research | After deploy |

**NOT used:** Gmail → Cursor (forward to sovereign mail later if wanted)

---

## 3. Primary money play — Sovereign Stay (evergreen)

**This is the launch play.** Not World Cup. 40 cities × 3 units = **120 units**.

### Your blueprint (SovereignStayMatrix)

| Layer | What | API |
|-------|------|-----|
| **1 — Upfront extraction** | $150 at door → treasury | `POST /api/sovereign-stay/presale-crypto` |
| **2 — Badge + buyback** | Listing velocity, vacancy buyback | `POST /api/sovereign-stay/hosts/{id}/optimize` |
| **3 — RentAHuman actuators** | Checkout turnover | `POST /api/sovereign-stay/hosts/{id}/checkout` |
| **DeFi ledger** | Immutable audit | `GET /api/sovereign-stay/ledger` + `vault/sovereign/empire_ledger.jsonl` |

### Unit economics

- **Gross:** $150/host presale
- **Closer:** $30
- **Net float:** $120 → $20 Cursor earmark + $100 vault reserve
- **Management fee:** 10% (undercut 20% PMs)
- **Commander OOP:** **$0**

### Zero-OOP crypto payment (two phases)

**Play 1 — Bootstrap (first host ever):**
- Host → **100% $150 USDC → treasury** (first fuel)
- Closer → **deferred** (paid from host fuel on play 2)
- Commander → $0

**Play 2+ — Split at door:**
- Host → **$120 USDC → treasury**
- Host → **$30 USDC → closer wallet** (direct — host pays closer)
- Commander wallet → **never funded by you**
- Play 1 deferred closer settled from **host-funded** treasury USDC

`GET /api/sovereign-stay/crypto/receive` — shows current mode + closer script

### Config (.env on VPS)

```env
TREASURY_USDC_ADDRESS=your_wallet
TREASURY_CRYPTO_CHAIN=base
TREASURY_CRYPTO_ASSET=USDC
TREASURY_SANDBOX_INSTANT_CLEAR=true
SOVEREIGN_TARGET_CITIES=40
SOVEREIGN_UNITS_PER_CITY=3
SOVEREIGN_PAYMENT_MODE=auto
RENTAHUMAN_API_KEY=
```

**Doc:** [SOVEREIGN_STAY_PLAY.md](SOVEREIGN_STAY_PLAY.md)

---

## 4. Treasury — instant fuel + recursive expansion

When presale clears:
```text
$ in → CLEARED instantly (sandbox_instant / crypto_instant)
  → 70% ammo pools (compute, network, storage, voice…)
  → auto-fund sovereign acquisitions
  → hive RESEARCH task queued
```

**Hive research:** `GET /api/hive/research` — agents scout best upgrades when money lands

**Capability:** `GET /api/treasury/capability` — what empire can afford now

**Doc:** [TREASURY_LAYER.md](TREASURY_LAYER.md) · [SOVEREIGN_ACQUISITIONS.md](SOVEREIGN_ACQUISITIONS.md)

---

## 5. Human firewall + Empire Doctor (no stops)

### Human firewall (3 guardian slots)
- Physical tasks, reputation, agent failures → **humans/RentAHuman**
- Empty slots → **auto-post RentAHuman**
- You see **nuclear only** (legal, brand, over cap)

`GET /api/intent/firewall` · **Doc:** [INTENT_ENGINE.md](INTENT_ENGINE.md)

### Empire Doctor (24/7 preventive)
- `GET /api/doctor/status` — warp speed clear?
- `POST /api/doctor/scan` — auto-repair + escalate critical
- n8n cron every 5 min recommended

---

## 6. Communication channels (all three)

| Channel | Use for |
|---------|---------|
| **GitHub Issues `@cursor`** | Build orders, PRs, code |
| **SARA voice** | Tasks, intents, briefings, dispatch |
| **Portal** | Dashboard, treasury, empire tab |

Voice build: SARA creates tasks + intents; GitHub `@cursor` writes code. Both 24/7 after VPS live.

**Doc:** [LAUNCH_NOW.md](LAUNCH_NOW.md) · [SARA_PERSONA.md](SARA_PERSONA.md) · [VAPI_SETUP.md](VAPI_SETUP.md)

---

## 7. Parallel plays (optional, not primary)

| Play | Scale | Doc |
|------|-------|-----|
| **KC World Cup blitz** | 30 units KCMO, $249 basket | [KC_WORLD_CUP_BLITZ.md](KC_WORLD_CUP_BLITZ.md) |
| **Welcome basket** | $249 5-pack, 3-person crew | [KC_WELCOME_BASKET_PLAY.md](KC_WELCOME_BASKET_PLAY.md) |
| **KC laundry** | Upsell after basket trust | [KC_LAUNDRY_PLAY.md](KC_LAUNDRY_PLAY.md) |
| **Expansion node** | Servury + GHL per city | [EXPANSION_NODE.md](EXPANSION_NODE.md) |

**n8n replaces GHL** for payments/automation at launch. Stripe/Cash App/crypto at door. GHL optional later.

---

## 8. Ground force (RentAHuman)

| Mission | Pay | When |
|---------|-----|------|
| `sovereign_presale_close` | $30 | Host pays at door |
| `checkout_turnover` | $25 | Checkout logistics |
| `basket_shop/assemble/deliver` | $22/$20/$18 | Welcome basket crew |

Pay on completion. Host money first. **Doc:** [GROUND_FORCE.md](GROUND_FORCE.md) · [RENTAHUMAN_SETUP.md](RENTAHUMAN_SETUP.md)

---

## 9. Key API endpoints (quick index)

```
GET  /health
GET  /api/bridge/status
GET  /api/sovereign-stay/status
GET  /api/sovereign-stay/crypto/receive
POST /api/sovereign-stay/presale-crypto
GET  /api/sovereign-stay/ledger
GET  /api/treasury/capability
GET  /api/treasury/human-capital
GET  /api/hive/research
GET  /api/doctor/status
POST /api/doctor/scan
POST /api/intent          { "intent": "...", "auto_execute": true }
```

---

## 10. Git branches & PRs

| PR | Branch | Contents |
|----|--------|----------|
| **#1** | `cursor/voice-os-command-center-1894` | Foundation: voice, portal, treasury, bridge, intent |
| **#2** | `cursor/sovereign-stay-matrix-1894` | **Deploy this** — Sovereign Stay, crypto rails, doctor, hive research |

**Deploy branch:** `cursor/sovereign-stay-matrix-1894`

---

## 11. Deploy checklist (Servury 157.254.194.89)

```bash
ssh root@157.254.194.89
curl -fsSL https://get.docker.com | sh
git clone https://github.com/parisschneider10-netizen/Command-center.git
cd Command-center
git checkout cursor/sovereign-stay-matrix-1894
cp .env.example .env
nano .env   # SECRET_KEY, PORTAL_PASSWORD, PUBLIC_BASE_URL, TREASURY_USDC_ADDRESS
docker compose up -d --build
curl http://localhost:8000/health
```

Portal: `http://157.254.194.89:3000`  
SARA webhook: `http://157.254.194.89:8000/vapi/webhook`

**Doc:** [BEGINNER_SETUP.md](BEGINNER_SETUP.md) · [LAUNCH_NOW.md](LAUNCH_NOW.md)

---

## 12. Decisions we locked in

| Decision | Why |
|----------|-----|
| GitHub `@cursor` = primary build channel | Works at work, no VPS needed |
| Sovereign Stay > World Cup blitz | Evergreen, 40×3 stealth scale |
| Zero Commander OOP | Host funds treasury; bootstrap then split |
| Crypto direct to treasury | No Cash App middleman delay |
| n8n + Stripe/crypto, not GHL day 1 | $0 vs $97/mo; you have Servury |
| Instant treasury clear on presale | Ammo + research same second |
| Human firewall + Doctor | No stops at warpspeed |
| 3 units/city, 40 cities | 120-unit funded sandbox |
| Laundry = upsell after basket trust | QR in basket |
| Commander sees nuclear only | Firewall absorbs judgment walls |

---

## 13. Voice commands to try (after SARA wired)

- *"Give me a briefing"*
- *"Doctor status — warp speed clear?"*
- *"My intent is sovereign stay — Kansas City sandbox, auto execute"*
- *"Create task: wire n8n doctor cron, urgent"*
- *"How do I command builds?"* (bridge status)

---

## 14. Recursive empire loop (the big picture)

```text
GitHub @cursor builds code
  ↓
VPS runs Command Center 24/7
  ↓
SARA + portal command empire
  ↓
AI/leads → closer → host pays USDC
  ↓
Treasury instant clear → ammo → acquisitions
  ↓
Hive researches best upgrades
  ↓
Doctor + firewall keep machine running
  ↓
Copy play to next city (3 units × 40)
  ↓
Empire tier rises → more ammo per dollar
  ↓
(repeat)
```

---

*Last updated: conversation through Sovereign Stay crypto bootstrap/split + hive research + Empire Doctor. Repo: parisschneider10-netizen/Command-center.*
