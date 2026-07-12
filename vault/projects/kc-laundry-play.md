# KC Laundry + Luggage Valet — Live Ops

> Empire value node · Kansas City · World Cup window

## Status: PRE-LAUNCH

## Offers

### 1. Host Laundry Amenity
- Host adds "Complimentary laundry" to Airbnb listing
- Guest texts/calls → pickup → partner facility → return
- Host pays upfront: $______ per turn OR $______/month package*

### 2. Detergent supply (B2B)
- Partner facilities buy bulk from us

### 3. Luggage valet (Phase 2)
- Guest storage · host paid for empty unit space

## Ground force (RentAHuman army)

| Mission | Default pay | On completion |
|---------|-------------|---------------|
| host_visit | $35 | Signed host or QR agreement |
| sticker_post | $20 | Photo proof per placement |
| guerrilla_guest | $25 | 20+ QR cards + location report |

**Rule:** Pay on completion only. `POST /api/ground-force/deploy`

## 48-hour float

- Host pays **upfront** → treasury `hold_48h` → float for infra → worker payout after clear
- `GET /api/ground-force/float`

## Stickers / guerrilla

- **Host-approved properties ONLY**
- QR → `POST /api/laundry/guest-request`
- World Cup corridors — guest handouts

## Pricing (edit live)

| SKU | Price |
|-----|-------|
| Monthly host package (upfront) | $ |
| Standard turn (2 bags) | $ |
| Luggage valet / day | $ |

## RentAHuman bounty — laundry pickup

```
Title: KC Laundry Pickup — {neighborhood}
Pay: $20 on completion
Task: Pick up bags from {address}. Deliver to {facility}. Photo confirm.
```

## Changelog

| Date | Note |
|------|------|
| 2026-07-08 | Play created |
| 2026-07-08 | Ground force + 48h float added |
