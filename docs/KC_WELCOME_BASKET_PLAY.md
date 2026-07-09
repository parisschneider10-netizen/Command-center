# KC Welcome Basket Play — Zero Out-of-Pocket Launch

**Better front door than laundry alone.** New STR hosts in KC need listings that pop. You deliver **welcome baskets** — agent locks the SKU, host pays **upfront**, you + 2 humans shop/assemble/deliver via RentAHuman. Treasury fuels the empire.

Laundry becomes the **upsell after trust** (QR in every basket).

---

## What you pay to launch NOW

| Item | Your cash Day 1 | Notes |
|------|-----------------|-------|
| **Basket supplies** | **$0** | Bought AFTER host prepays |
| **RentAHuman labor** | **$0** | Pay on completion only |
| **Servury VPS** | $4–20/mo | Only if command deck not live yet |
| **GHL** | $0 if you have it | Landing + payment link |
| **Stripe** | 2.9% + 30¢ | Deducted from host payment, not your pocket |

### **Target: $0 out of your pocket**

Host money arrives **before** Costco run. Float hits treasury **before** workers get paid.

`GET /api/welcome-basket/launch-cost` — live numbers in API.

---

## The pitch (one line)

*"New KC Airbnb host? We place premium welcome baskets in your unit before every guest — you look 5-star, we handle shopping and delivery."*

**World Cup + new STR laws** = hosts need turnkey amenities **today**.

---

## Packages (host pays upfront)

| SKU | Price | Baskets | Best for |
|-----|-------|---------|----------|
| **launch_5pack** | **$249** | 5 | Launch promo — fuels treasury fast |
| **bundle_laundry_intro** | $199 | 3 | Basket + laundry QR upsell |
| **single_basket** | $79 | 1 | Trial / one-off turn |

**Early bird:** First 10 hosts at $249 — you trade margin for **treasury ammo + reviews**. Laundry recurring is the profit engine.

---

## Per-basket unit economics

| Line | $ |
|------|---|
| Host revenue (5-pack) | ~$50/basket |
| Supplies (Costco bulk) | $14–18 |
| Labor team (3 people, pay on completion) | $60 |
| | |
| Shopper | $22 |
| Assembler | $20 |
| Deliver + place in unit | $18 |

**At $249/5-pack:** Thin per-basket margin — **strategic**. One host prepay = **$249 in treasury float** → ammo pools → VPS, Starlink path.

**At $79 single:** ~$5–15 margin per basket after labor.

**Real profit:** Host converts to **$29/turn laundry** + detergent supply after basket trust.

---

## Zero-OOP cash flow (one host)

```text
Day 0   Host signs GHL → pays $249 (Stripe)
           ↓
        POST /api/welcome-basket/hosts/{id}/prepay
           ↓
        Treasury: 48h hold ($249 float)
           ↓
Day 1   Agent locks basket spec (Costco list)
        POST /api/welcome-basket/hosts/{id}/lock-spec
           ↓
Day 2   Dispatch 3-person crew (dry-run → live)
        POST /api/welcome-basket/fulfill/{host_id}
           ↓
        RentAHuman: Shop $22 · Assemble $20 · Deliver $18
        (YOU can claim Shopper gig — pay yourself from host float)
           ↓
Day 4   Hold clears → 70% ammo ($174) · 30% ops ($75)
        Workers paid on photo proof
           ↓
        4 basket credits remain · laundry QR in basket
```

---

## 3-person crew (you + 2 RentAHuman)

| Role | Pay | Who |
|------|-----|-----|
| **Shopper** | $22 | You (RentAHuman profile) OR hire #1 |
| **Assembler** | $20 | Hire #2 |
| **Deliver** | $18 | Hire #3 |

**One bounty per role.** Photo proof each step. System auto-posts via intent engine or fulfill endpoint.

Register on RentAHuman as a worker → claim your own shopper gigs → **legal pay yourself from host revenue** logged in treasury.

---

## Agent-locked basket spec (default SKU)

```
- Kirkland water 24pk
- KC local snack (Joe's KC / Roasterie)
- Tissues + sanitizer
- Welcome card + QR (laundry upsell)
- Detergent pods x3
- KC visitor guide
COGS ~$16 at Costco bulk
```

Agent locks via API — humans never improvise shopping.

---

## API flow

| Step | Endpoint |
|------|----------|
| 1. Host lead | `POST /api/welcome-basket/host-signup` |
| 2. Agent lock SKU | `POST /api/welcome-basket/hosts/{id}/lock-spec` |
| 3. Host prepay | `POST /api/welcome-basket/hosts/{id}/prepay` |
| 4. Dispatch crew | `POST /api/welcome-basket/fulfill/{id}` |
| 5. Complete missions | `POST /api/ground-force/missions/{id}/complete` |

---

## Week 1 launch plan (zero OOP)

| Day | Action | Cost to you |
|-----|--------|-------------|
| 1 | GHL page: "KC New Host Welcome Kit — $249" | $0 |
| 1 | `host-signup` webhook live | $0 |
| 2 | Pitch 5 new STR hosts (Facebook groups, PM meetups) | $0 |
| 3 | **First host pays $249** | **-$0** (you receive money) |
| 3 | Lock spec + fulfill basket #1 (you shop) | $0 until host $ clears |
| 4 | 2 RAH workers assemble + deliver | Paid from float |
| 5 | Basket #2–3 from same host credits | Same float |
| 7 | Upsell laundry amenity on host call | Recurring revenue |

**Goal Week 1:** 3 hosts × $249 = **$747 treasury inbound** before you spend on infra.

---

## Scale path

| Stage | Hosts | Crew | Treasury |
|-------|-------|------|----------|
| Bootstrap | 1–5 | You + 2 RAH | Float → ammo |
| Growth | 5–20 | Firewall guardians + RAH | Laundry upsell |
| Scale | 20+ | Dedicated assembler · bulk Costco | Expansion node |

---

## Voice / Intent

*"My intent is launch KC welcome basket play with 3 hosts"*

→ `POST /api/intent` with `auto_execute: true`  
→ Agent tasks + RAH crew templates + treasury capacity check

---

## vs Laundry-first

| Welcome basket | Laundry |
|----------------|---------|
| Instant visual host value | Operational complexity |
| New host hook (STR legalization) | Recurring revenue king |
| $249 upfront treasury fuel | Per-turn margins |
| **Lead with basket** | **Upsell laundry in basket QR** |

**Do both. Lead with basket.**

---

## Nuclear (only you)

- Host contracts below $249 floor
- Public marketing spend
- New facility partner agreements

---

## Next GitHub Issue

```markdown
[BUILD] GHL welcome basket payment → prepay webhook

@cursor
- Stripe/GHL payment success → POST /api/welcome-basket/hosts/{id}/prepay
- n8n welcome-basket-funded workflow
Ship today.
```

See [KC_LAUNDRY_PLAY.md](KC_LAUNDRY_PLAY.md) · [INTENT_ENGINE.md](INTENT_ENGINE.md) · [GROUND_FORCE.md](GROUND_FORCE.md)
