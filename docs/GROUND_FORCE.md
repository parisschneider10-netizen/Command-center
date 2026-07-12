# Ground Force + 48h Float — Game Theory Revenue Engine

RentAHuman army. Zero upfront to workers. Host pays first. 48-hour fiat float. AI commands deployment.

## The loop

```text
HOST pays upfront (full package)
        ↓
Treasury: hold_48h (48-hour float — your working capital)
        ↓
AI deploys ground force (RentAHuman bounty — pay ON COMPLETION)
        ├── host_visit      — pitch STR hosts in person
        ├── sticker_post    — QR stickers on approved properties
        └── guerrilla_guest — World Cup corridor QR handouts
        ↓
Worker completes + proof → payout after hold clears
        ↓
Chargeback window protected · workers protected · you keep margin
```

## Game theory (why it works)

| Player | Incentive |
|--------|-----------|
| **Host** | Premium listing amenity, more bookings |
| **Guest** | Free/cheap laundry via QR |
| **Ground force** | Paid only on verified completion — they hustle |
| **You** | Host cash upfront, 48h before worker payout, margin on every turn |
| **Empire AI** | Commands bounties via API — no W-2 army |

**Zero out of pocket for labor until revenue lands.** Workers eat risk short-term; you share upside when host pays.

## 48-hour float

```text
T+0   Host charged $299 monthly package
T+0   Ledger: status=hold_48h, release_at=T+48h
T+0–48  Float available for infra, detergent bulk, VPS, APIs
T+48  Auto-clear → worker payouts authorized
```

API:
- `POST /api/ground-force/host-payment` — record upfront host payment
- `GET /api/ground-force/float` — active float summary
- `POST /api/ground-force/deploy` — RentAHuman bounty
- `POST /api/ground-force/missions/{id}/complete` — proof + payout

Env: `TREASURY_HOLD_HOURS=48`

## Mission types

### host_visit
In-person STR host pitch. Signed agreement or QR placement. **$35 default** on completion.

### sticker_post
QR stickers on **host-approved** properties only. Photo proof. **$20 default**.

### guerrilla_guest
World Cup / STR corridors. Hand QR cards to guests. Count report. **$25 default**.

## Voice / GitHub command

SARA: *"Deploy ground force host visit Brookside"*

GitHub Issue:
```markdown
@cursor deploy 5 guerrilla_guest missions Westport + Plaza
```

n8n webhook: `ground-force-deploy`

## Stickers + guerrilla rules

- **Host property only** with written OK — no random public vandalism
- QR → `POST /api/laundry/guest-request`
- Photo proof → mission complete → payout

## Fund sovereign infra from float

48h window cash flow buys:
- Servury VPS upgrades
- Domain + mail
- API credits
- Detergent bulk orders
- Command deck iteration

Revenue engine funds the OS. OS automates the engine. Flywheel.

## Full stack map

```text
KC Laundry Play
    ├── host-signup API
    ├── guest-request API
    ├── ground-force API      ← this
    ├── 48h treasury float    ← this
    ├── RentAHuman fulfillment
    └── Command Center portal
```

Same endpoints. Same VPS. Machine speed.
