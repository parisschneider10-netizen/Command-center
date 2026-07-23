# Operate Tonight — Eco-Express KCMO

> **Best city:** Kansas City MO (Evergy rebate geography). Not Johnson County KS — rebate is MO-side.

---

## Before you leave (5 min)

1. GitHub → **Actions** → **Deploy Servury VPS** → branch **`cursor/uncertainty-fallback-1894`** (or `main` after merge)
2. Portal → http://157.254.194.89:3000 → login **`commander`** (lowercase)
3. Confirm **Launch** tab shows Eco-Express buttons

---

## Get real leads on the strike list

| Step | Portal |
|------|--------|
| 1 | **Launch** → **BUILD STRIKE LIST** |
| 2 | Scroll **Closer sheet** — names, phones, pitch |
| 3 | Send hunter / RentAHuman closer to doors **with phone numbers** |
| 4 | Skip `pending-*` phones — no dialable number |

**Manual add:** Launch tab lead form OR `POST /api/value-node/leads` with name + phone + city `Kansas City`

---

## Close at the door ($149 before work)

Pitch is on **Closer sheet** panel. Collect payment first.

| After payment | Portal |
|---------------|--------|
| Loop B | Job ID + payment proof (Cash App / Venmo / Stripe ref) |
| System | Lowe's barcode stub + RAH installer dispatch |

---

## Keys you need on VPS `.env`

| Key | Required for |
|-----|----------------|
| `RENTAHUMAN_API_KEY` | Live installer $40 payouts |
| `BRAVE_SEARCH_API_KEY` | Better strike list (optional — DuckDuckGo works) |
| `ANTHROPIC_API_KEY` | Handwritten Ready Room vision |
| `VAPI_API_KEY` | SARA (GitHub Secrets + Wire SARA) |

---

## Uncertainty tab (new)

If handwritten note OCR confidence &lt; 85% → **Uncertainty** tab → approve or correct → auto-scan.

---

## What's still stub (money works, automation partial)

| Piece | Status |
|-------|--------|
| Lowe's Pro auto-order | Barcode stub + n8n event |
| Evergy rebate API | Math in economics; manual rebate paperwork |
| Web hunt quality | Real phones vary — verify before dispatch |
| Crypto/NOWPayments | Not wired — cash/Cash App tonight |

---

## SARA shortcuts

- *"Give me a briefing."*
- *"Run eco express strike list."*
- *"Launch eco express live."*

**Phone:** +1 (971) 382-0038
