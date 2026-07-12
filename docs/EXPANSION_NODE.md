# Expansion Value Node — STR Property Manager SaaS

Your money bot: **scrape PM leads → deploy Servury VPS + GHL sub-account per city → sell MTR recon automation.**

## What your code does

```text
Lead (PM in city)
    ├── Servury: white-label VPS (~$3.99/mo) — recon node
    ├── GHL: SaaS sub-account + MTR snapshot flash
    └── DB: lead locked as "infrastructure_locked"

Scale: up to 40 cities in parallel (batch-capped when live)
```

## Integrated into Command Center

| Path | Purpose |
|------|---------|
| `server/app/value_node/expansion.py` | Orchestrator (fixed your bugs) |
| `server/app/integrations/servury.py` | VPS provision |
| `server/app/integrations/ghl.py` | GHL sub-account |
| `POST /api/value-node/expansion/scale` | Run batch |
| `POST /api/value-node/expansion/city-lock` | Single city |
| `POST /voice/tools/lock_city_node` | SARA voice trigger |

## Bugs fixed from your paste

1. `if response.status in:` → proper status checks `(200, 201)`
2. Parallel VPS + GHL via `asyncio.gather`
3. **Dry run default ON** — won't spin 40 real VPS without config
4. **Live batch cap** — max 5 cities per live run (configurable)
5. Treasury logs VPS spend when live
6. Leads persist in `scraped_leads` table

## Env vars

```env
SERVURY_API_KEY=
SERVURY_API_URL=https://api.servury.com
GHL_API_KEY=
GHL_COMPANY_ID=
GHL_MTR_RECON_SNAPSHOT_ID=
EXPANSION_DRY_RUN=true
EXPANSION_MAX_CITIES=40
EXPANSION_LIVE_BATCH_CAP=5
EXPANSION_VPS_COST_CENTS=399
```

Set `EXPANSION_DRY_RUN=false` only when API keys verified.

## Test dry run

```bash
curl -X POST http://localhost:8000/api/value-node/expansion/city-lock \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lead": {
      "name": "Vanguard PM",
      "phone": "+15551234567",
      "email": "ops@vanguard.com",
      "city": "Kansas City",
      "address": "100 Main St",
      "zip": "64106"
    },
    "dry_run": true
  }'
```

## Revenue model (your empire)

- GHL SaaS sub-accounts billed to PMs monthly
- Servury VPS passed through or bundled
- MTR recon automation = the product ("Unautomated-STR-Leak" crisis)

## Nuclear triggers

- Live deploy > batch cap
- Spend above treasury daily cap
- GHL/Servury API failures at scale → n8n `expansion-failure` webhook

## Next builds

- [ ] Wire lead scraper → `POST /api/value-node/leads`
- [ ] n8n workflow: new lead → auto city-lock dry run
- [ ] Portal tab: leads + city nodes map
- [ ] Verify real Servury + GHL API paths against your accounts
