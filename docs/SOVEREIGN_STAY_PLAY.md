# Sovereign Stay Systems — V1 Core (Evergreen Empire Launch)

> **40 cities × 3 units = 120 units** · $150 doorstep presale · zero Commander OOP · 24-month stealth baseline

This is the **primary evergreen play**. KC World Cup blitz is optional; this scales nationally with the same matrix logic.

## The genius (why it works)

| Mechanism | Effect |
|-----------|--------|
| **Layer 1 presale** | Cash hits pavement *before* you deliver anything — closer is paid from host money, not yours |
| **$150 wedge** | Low enough to close at door; high enough for $120 net float after $30 closer |
| **3 units/city** | Small cap = fast close per grid; no single-city saturation risk |
| **40 cities** | 120 total units — same scale as big blitz, spread for stealth |
| **Badge engine** | Digital amenity badges boost perceived listing value (velocity multiplier) |
| **Buyback algorithm** | >30% vacancy → programmatic floor buyback, risk-neutralized |
| **Checkout actuators** | RentAHuman handles turnover; partner locker hub = secondary yield |
| **DeFi ledger** | Append-only audit on VPS — DB + JSONL for investor-grade trail |

## Unit economics (per lock-in)

```text
$150 gross (Cash App / Venmo / Stripe at door)
 − $30 closer (RentAHuman, pay on proof)
 ─────────────────
 $120 net float
 − $20 Cursor Pro compute earmark (first hosts fund dev environment)
 ─────────────────
 $100 vault reserve (pure working capital)
```

**10% management fee** undercuts traditional 20% PMs — software brain does the rest.

## Architecture (your blueprint → Command Center)

```text
LAYER 1  POST /api/sovereign-stay/presale
           → sovereign_presale_close mission ($30)
           → treasury sales_close hold (4h)
           → instant closer payout

LAYER 2  POST /api/sovereign-stay/hosts/{id}/optimize
           → badge velocity multiplier
           → buyback if vacancy > 30%

LAYER 3  POST /api/sovereign-stay/hosts/{id}/checkout
           → checkout_turnover mission ($25)
           → partner kickback +$15 logged

DEFI     GET /api/sovereign-stay/ledger
           → SQLite sovereign_ledger_events
           → vault/sovereign/empire_ledger.jsonl
```

## API

| Endpoint | Layer |
|----------|-------|
| `GET /api/sovereign-stay/status` | Matrix snapshot |
| `GET /api/sovereign-stay/cities` | Per-city 3-unit caps |
| `POST /api/sovereign-stay/presale` | Layer 1 |
| `POST /api/sovereign-stay/hosts/{id}/optimize` | Layer 2 |
| `POST /api/sovereign-stay/hosts/{id}/checkout` | Layer 3 |
| `GET /api/sovereign-stay/ledger` | DeFi audit |
| `POST /api/sovereign-stay/simulate` | Day-1 KCMO sandbox |

## n8n webhooks

| Event | When |
|-------|------|
| `sovereign-presale-locked` | Layer 1 complete |
| `sovereign-optimization` | Layer 2 run |
| `sovereign-checkout` | Layer 3 dispatch |

## Config (.env)

```env
SOVEREIGN_TARGET_CITIES=40
SOVEREIGN_UNITS_PER_CITY=3
SOVEREIGN_UPFRONT_FEE_CENTS=15000
SOVEREIGN_CLOSER_BOUNTY_CENTS=3000
SOVEREIGN_RENTAHUMAN_BOUNTY_CENTS=2500
SOVEREIGN_PARTNER_KICKBACK_CENTS=1500
SOVEREIGN_CURSOR_EARMARK_CENTS=2000
SOVEREIGN_BUYBACK_VACANCY_THRESHOLD=0.30
RENTAHUMAN_API_KEY=
```

## 24-month stealth rollout → MACHINE SPEED (Commander directive)

> **Human-paced docs are obsolete.** Agents execute in parallel. Host funds upfront. Compound daily until grid locked.

| Target | Horizon | How |
|--------|---------|-----|
| **Full grid** | **≤30 days** | 40 cities × 3 units = 120 locks — parallel agent waves, not serial |
| **Daily** | Every 24h | New presales → instant treasury clear → fund next city closers + hive research |
| **Per city** | As fast as closers close | 3 locks → next city (easiest-first ranked by hive) |

**Close pitch (instant yes):** *"$150 presale. If vacancy spikes, buyback algorithm kicks in — you're not eating the loss. We take the floor risk."*

**Lead focus:** **MTR hosts/PMs first** — already think mid-term, faster yes than cold STR tourists. Expansion node MTR recon + Sovereign Stay presale stack together.

**Parallel (not sequential):**
- Hive scrapes + ranks cities simultaneously
- Multiple closers / actuators per wave (A2A + ground force)
- Treasury from host #1 funds host #2 same day — compound until 120/120

Legacy 12–24 month phasing is **retired** — see `vault/commander/operating-contract.md`.

## Voice intent

*"My intent is sovereign stay — launch the 40 city matrix"*

See [GROUND_FORCE.md](GROUND_FORCE.md) · [TREASURY_LAYER.md](TREASURY_LAYER.md)
