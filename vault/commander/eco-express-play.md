# Eco-Express — D2C Smart Thermostat Flips

> **Pivot locked:** No hosts. No STR. Extract cash from suburban homeowners → fund your own properties later.

---

## The play

| Line | Amount |
|------|--------|
| Homeowner pays (before work) | **$149** |
| Hardware (retail $100 − Evergy rebate − Lowe's Pro) | **~$50** |
| RentAHuman installer (15 min swap) | **$40** |
| **Your net / door** | **$59** |

**Goal:** 4 doors/day → **$236/day** → land-acquisition vault

---

## The three loops (automated)

### Loop A — Strike list
`POST /api/eco-express/strike-list`  
Hunts KCMO homeowners in focus zips → `eco_express_jobs` status `targeted`

### Loop B — Payment → hardware → install
`POST /api/eco-express/jobs/{id}/payment-confirmed`  
Homeowner paid → treasury hold → Lowe's pickup barcode → RAH install dispatched

### Loop C — Photo QC (net-48)
`POST /api/eco-express/jobs/{id}/install-complete`  
Must include Wi-Fi icon photo — else **payout frozen**

---

## Hunter doorstep pitch

```
Hi — Evergy utility crews are updating grid efficiency markers on this block this week.
Your house likely has an older manual thermostat bleeding ~$180/year in wasted energy.

My company is running the Eco-Express Program right now. In 15 minutes we replace your
wall unit with a brand-new Wi-Fi smart thermostat. With the local Evergy rebate, the
hardware is FREE. You only pay a flat $149 for certified installation and programming.

We can put a technician on your wall right now or at 4:00 PM today.
Which slot keeps your bills low?
```

`GET /api/eco-express/pitch` — same text for mobile

---

## Rebate stack math

`GET /api/eco-express/economics`

```
$100 retail → 10% Lowe's Pro → $90 → $50 Evergy rebate → $40-50 out of pocket
```

Wire `LOWES_PRO_ACCOUNT_ID` + `EVERGY_REBATE_PROGRAM_ID` when APIs ready.

---

## Focus geography

**Kansas City metro** — zips in `ECO_FOCUS_ZIPS`  
Housing **1970–2005** — legacy manual thermostats

---

## Path to sovereign properties

```
Eco-Express D2C → $10k+ float (45 days) → master lease 3 nurse recovery suites under YOUR LLC
```

No hosts. No permission. Your cash. Your grid.

---

## Portal / voice

- Portal Launch tab → **Eco-Express** buttons
- SARA: *"Run eco express strike list"* / *"Launch eco express live"*

---

*Suburbs fund the empire. Hosts are obsolete.*
