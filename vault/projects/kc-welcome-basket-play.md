# KC Welcome Basket — Live Ops

> Lead offer · Laundry upsell in every basket QR

## Status: PRE-LAUNCH

## Packages (GHL)

| SKU | Price | Credits |
|-----|-------|---------|
| launch_5pack | $249 | 5 |
| bundle_laundry_intro | $199 | 3 |
| single_basket | $79 | 1 |

## Crew per basket ($60 labor, pay on completion)

| Role | $ | RAH tag |
|------|---|---------|
| Shopper | 22 | welcome-basket shop |
| Assembler | 20 | welcome-basket assemble |
| Deliver | 18 | welcome-basket deliver |

**Commander:** Register on RentAHuman → claim shopper gigs.

## Flow

1. `POST /api/welcome-basket/host-signup`
2. Agent `lock-spec`
3. Host pays → `prepay` → 48h float
4. `fulfill/{host_id}` → 3 missions
5. Complete with photo proof → payout from float

## Zero OOP rule

**Never shop before host prepay hits treasury.**

## Changelog

| Date | Note |
|------|------|
| 2026-07-09 | Welcome basket play — lead offer before laundry scale |
