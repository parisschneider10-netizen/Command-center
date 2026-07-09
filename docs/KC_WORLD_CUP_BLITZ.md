# KC World Cup Blitz — Lock 30 Units FAST

> AI finds leads · Humans close at door · Host pays upfront · Closer paid instant via 4h sales float

## The machine

```text
AI ingests STR leads (Airbnb new hosts KCMO)
        ↓
POST /api/kc-blitz/leads/batch
        ↓
POST /api/kc-blitz/leads/{id}/dispatch  →  RentAHuman CLOSER ($45)
        ↓
Closer visits → host pays $249 on phone (Stripe/GHL)
        ↓
POST /api/kc-blitz/close-sale  →  unit LOCKED in cap
        ↓
4h sales float (not 48h) → closer paid INSTANT (host $ secured)
        ↓
Welcome basket crew fulfills · laundry QR upsell
        ↓
Copy playbook to next host in pipeline
```

## 30-unit cap (KCMO)

| Metric | Value |
|--------|-------|
| **Max units** | 30 STR units in KCMO |
| **Tracks** | `unit_count` per locked host |
| **Urgency pitch** | "Only {N} slots left at launch price" |
| **When full** | Cap blocks new locks — waitlist or next city |

`GET /api/kc-blitz/status` — live slots remaining.

## Closer pay — instant via sales float

| Step | Timing |
|------|--------|
| Host pays $249 at door | Second 0 |
| Treasury records `sales_close` hold | **4 hours** (not 48) |
| Closer completes + payment screenshot | Same visit |
| `close-sale` API | **Instant payout** — host money secured |

**Game theory:** Closer only gets paid when host pays. Zero out of your pocket.

| Role | Pay | When |
|------|-----|------|
| **Sales closer** | $45 | Host prepay confirmed at door |
| Shopper | $22 | After basket spec locked |
| Assembler | $20 | Photo proof |
| Deliver | $18 | In unit photo |

## Close script (on bounty)

1. World Cup crowds — guests expect premium touch
2. Welcome baskets before every booking
3. **Only X slots left** in KCMO at $249/5-pack
4. Pay NOW on phone (Stripe link you pull up)
5. Screenshot = mission complete = you get paid

## API

| Endpoint | Who |
|----------|-----|
| `GET /api/kc-blitz/status` | Cap + urgency |
| `POST /api/kc-blitz/leads` | AI single lead |
| `POST /api/kc-blitz/leads/batch` | AI bulk scrape |
| `POST /api/kc-blitz/leads/{id}/dispatch` | Send closer |
| `POST /api/kc-blitz/close-sale` | Host paid → lock → payout |
| `POST /api/kc-blitz/dispatch-all` | Blast all new leads |

## World Cup week plan

| Day | Action |
|-----|--------|
| 1 | AI scrape 50 KC STR leads → `leads/batch` |
| 1 | `dispatch-all` — 10 closers live |
| 2–5 | Target **6–8 locks/day** → 30 units in 4–5 days |
| Each lock | $249 × 30 = **$7,470 treasury** |
| After 30 | Clone model to next neighborhood / city |

## Replicate model

Each locked host record includes:
- Locked basket spec (agent SKU)
- Unit count toward cap
- Prepay ledger (sales_close 4h)
- Mission chain for fulfillment

Next 30 units = same API flow, new lead batch, copy playbook from vault.

## Voice / Intent

*"My intent is KC World Cup blitz — lock 30 hosts now"*

`POST /api/intent` + `auto_execute: true`

## Config

```env
KCMO_MAX_UNITS=30
TREASURY_SALES_CLOSE_HOLD_HOURS=4
RENTAHUMAN_API_KEY=   # VPS .env only
```

See [KC_WELCOME_BASKET_PLAY.md](KC_WELCOME_BASKET_PLAY.md) · [GROUND_FORCE.md](GROUND_FORCE.md)
