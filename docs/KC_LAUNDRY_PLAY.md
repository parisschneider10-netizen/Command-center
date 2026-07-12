# KC Laundry Play — Revenue While You Build

**Parallel track:** Money flows Week 1 on the **same VPS, same API, same RentAHuman, same GHL** as the empire command stack.

World Cup + KC STR legalization = timing. You have facilities, detergent, people. Empire infra captures leads and dispatches humans.

---

## The play in one sentence

**Sign Airbnb hosts → they offer "free laundry" to guests → RentAHuman/facility partners fulfill → you sell detergent bulk + per-turn fees → add luggage valet using empty unit space.**

Revenue funds sovereign infrastructure. Command deck keeps getting better.

---

## Revenue streams (automated where possible)

| Stream | Who pays | Fulfillment |
|--------|----------|-------------|
| **Per-turn laundry** | Host (monthly or per bag) | Partner facility + RentAHuman pickup/delivery |
| **Detergent supply** | Facility partners (bulk) | You buy bulk, margin on resale |
| **Guest upsell** | Guest optional premium (express, fold) | Same pipeline |
| **Host lock-in** | Annual "amenity package" | GHL automation + your brand on listing |
| **Luggage valet** (Phase 2) | Guest daily fee | Host empty unit = storage; RentAHuman move bags |

---

## How it uses empire infrastructure (same endpoints)

```text
Marketing (GHL page / QR / World Cup ads)
        ↓
POST /api/laundry/host-signup     ← new host lead
POST /api/laundry/guest-request   ← guest needs pickup
        ↓
Voice OS logs activity + vault note
        ↓
n8n webhook "laundry-host"        ← auto welcome, assign territory
        ↓
GHL sub-account OR pipeline stage  ← existing GHL integration
        ↓
RentAHuman bounty                 ← pickup/delivery human
        ↓
Treasury ledger                   ← revenue in, supply cost out
        ↓
Command Center portal             ← you see hosts, turns, $$$ 
```

**No second stack.** Laundry IS a value node on the empire API.

---

## World Cup + KC STR angle

| Factor | Your move |
|--------|-----------|
| World Cup crowds | "Guest laundry amenity" — hosts win bookings |
| KC STR now legal | Every new host needs turnkey amenities |
| You have facilities + detergent | Undercut national linen services on price + local speed |
| RentAHuman | Scale pickup/delivery without hiring W-2 army |

**Pitch to host (one line):**  
*"Add free laundry to your listing — we handle pickup, wash, return. You look premium. We do the work."*

**Pitch to guest:**  
*"Text this number — bags picked up in 2 hours, returned fresh."*

---

## Luggage valet (Phase 2 — same hosts)

```text
Guest checks out of Airbnb but staying in KC (World Cup)
        ↓
Host has empty unit / closet / garage slot
        ↓
You pay host $X/day for storage space
        ↓
RentAHuman moves bags unit → storage → back when needed
        ↓
Guest pays valet fee · Host gets storage income · You take margin
```

Same host relationships. Upsell after laundry trust is built.

---

## Automated Week 1 (don't wait for perfect command deck)

| Day | Ship | Revenue? |
|-----|------|----------|
| 1 | VPS live + laundry API endpoints | — |
| 1 | GHL landing page + host signup form → webhook | — |
| 2 | 10 hosts manually recruited (you/Friend) | First signups |
| 3 | QR in pilot units → guest-request webhook | First turns |
| 4 | RentAHuman bounty template: "laundry pickup KC" | Fulfillment auto |
| 5 | Stripe link in GHL (or manual invoice) | **First $** |
| 7 | 20 hosts · World Cup marketing live | Recurring |

Command deck portal shows hosts/leads now. Pretty UI later. **Money first.**

---

## Unit economics (example — tune live)

| Item | $ |
|------|---|
| Host pays per turn (2 bags) | $25–40 |
| Your cost (facility + detergent + human) | $12–18 |
| Margin per turn | $10–22 |
| 20 hosts × 8 turns/mo | $1,600–3,520 gross |
| Detergent bulk to 3 facilities | +$500–1,500/mo |

Enough to fund VPS, APIs, Cursor, and next infra tier in weeks — not years.

---

## RentAHuman fulfillment flow

1. Guest request hits API → n8n fires
2. n8n POST RentAHuman bounty: pickup address, time window, pay $15–25
3. Human picks up → drops at partner facility
4. Facility scans "received" (SMS or portal tap)
5. Delivery human returns to guest
6. Treasury logs payout + revenue

Guardian/facility partner on manifest for quality — not you on every turn.

---

## What you tell SARA at work

- *"Log note: pitched 3 hosts in Brookside"*
- *"Create task: GHL landing page live today"*
- *"Escalate to human: need pickup driver tonight Crossroads"*

---

## Nuclear (only you)

- Contracts with facility partners
- Pricing below margin floor
- Public brand campaigns

Everything else: agents + n8n + RentAHuman.

---

## Files in repo

| Path | Purpose |
|------|---------|
| `docs/KC_LAUNDRY_PLAY.md` | This doc |
| `vault/projects/kc-laundry-play.md` | Living ops + pricing |
| `POST /api/laundry/*` | Lead + request capture |
| GHL snapshot | Host onboarding automation (your existing snapshot ID) |

---

## Next GitHub Issue

```markdown
[BUILD] KC laundry GHL landing webhook + host signup flow

@cursor
- Wire POST /api/laundry/host-signup to n8n laundry-host webhook
- GHL form webhook handler
- RentAHuman bounty template in docs
Ship today.
```

Build empire. Run laundry. Same machine.
