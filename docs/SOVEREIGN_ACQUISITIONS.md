# Sovereign Acquisitions — Revenue → Ammo → Capability

Every copper penny from revenue nodes becomes **ammo** for empire expansion. Treasury does not hoard cash — it transforms inbound revenue into sovereign infrastructure targets.

## Philosophy

```text
Revenue in  →  48h float  →  cleared  →  ammo pools  →  acquisition manifest  →  capability out
```

| Revenue node | What it funds |
|--------------|---------------|
| Ground force host payments | Network kit, physical ops, Starlink |
| KC laundry | Ground force starter kit, mobile command |
| Expansion (Servury/GHL) | Compute nodes per city |
| Manual treasury inbound | Commander-directed priorities |

Agents research **state-of-the-art sovereign options** (self-hosted, vendor-independent). Commander approves `funded` → `ordered` → `acquired` (nuclear if over cap).

## Categories

| Category | Examples |
|----------|----------|
| **compute** | Servury VPS, n8n HA, Postgres replica, GPUs |
| **network** | Starlink Business, Peplink multi-WAN, sovereign mesh |
| **storage** | Encrypted NAS, cold archive, vault mirror |
| **comms** | Mailcow/Stalwart, sovereign DNS, domain control |
| **voice** | Self-hosted LiveKit, SIP bridge (Vapi exit path) |
| **security** | YubiKey fleet, HSM, IDS |
| **physical_ops** | Rugged laptop, QR/sticker kits, mobile command |
| **energy** | Solar + battery UPS for edge nodes |

## Allocation rules (defaults)

When host payment **clears** the 48h hold:

| Split | Default % | Purpose |
|-------|-----------|---------|
| **Ammo** | 70% | Split across category pools by weight |
| **Ops reserve** | 30% | Worker payouts, immediate operating costs |

**Ammo category weights** (of ammo portion):

| Category | Weight |
|----------|--------|
| compute | 25% |
| network | 20% |
| storage | 10% |
| comms | 10% |
| voice | 10% |
| security | 15% |
| physical_ops | 10% |

Configure via `.env`:

```env
TREASURY_AMMO_PERCENT=70
TREASURY_OPS_RESERVE_PERCENT=30
TREASURY_AUTO_FUND_ACQUISITIONS=true
```

## Empire tiers

Acquisitions are tagged by **empire tier** — agents filter by current expansion level:

| Tier | Scope | Example acquisitions |
|------|-------|---------------------|
| T1 | Single city / bootstrap | Mail stack, YubiKeys, ground force kit, first VPS |
| T2 | Multi-node regional | Starlink, Peplink, NAS, mobile command |
| T3 | Multi-city | Solar/UPS edge, dedicated metal |
| T4 | National | Redundant uplinks, geo-distributed compute |
| T5 | Full sovereign | Custom mesh, air-gapped backup, owned spectrum paths |

As empire expands, agents add tier-appropriate targets via API or voice.

## Living manifest

Synced automatically to:

```text
vault/commander/sovereign-acquisitions.md
```

Updated on: startup, acquisition create/update, manual manifest fetch.

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /api/treasury/acquisitions` | Full acquisition queue |
| `GET /api/treasury/acquisitions/briefing` | Ammo + top priorities summary |
| `GET /api/treasury/acquisitions/manifest` | Sync + return markdown |
| `GET /api/treasury/acquisitions/categories` | Categories + ammo weights |
| `POST /api/treasury/acquisitions` | Add new target |
| `PATCH /api/treasury/acquisitions/{id}` | Update status, vendor research |
| `POST /api/treasury/acquisitions/seed` | Seed default manifest (if empty) |
| `GET /api/treasury/ammo` | Pool balances + recent allocations |
| `GET /api/treasury/overview` | Includes ammo balance + acquisition counts |

## Voice (SARA)

| Command | Tool |
|---------|------|
| *"Acquisition briefing"* / *"What ammo do we have?"* | `get_acquisition_briefing` |
| *"Add Starlink to acquisition list"* | `add_acquisition_need` |

## Agent workflow

1. **Research** — For each `needed` item, find sovereign alternatives (open-source, self-hosted).
2. **Update** — PATCH `vendor_candidates` and `equipment_spec` with findings.
3. **Fund** — Cleared revenue auto-fills pools; auto-fund hits highest priority per category.
4. **Acquire** — When `funded`, queue Commander approval to order (nuclear if over guardian cap).
5. **Deploy** — Status `acquired` → `deployed`; log to vault + activity.

## Starlink + sovereign network stack

Target architecture for network independence:

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Starlink   │────►│   Peplink    │────►│  Servury VPS    │
│  Business   │     │  Multi-WAN   │     │  Command Center │
└─────────────┘     │  + LTE       │     └─────────────────┘
                    └──────────────┘
                           │
                    Failover if ISP/cell dies
```

Agents should continuously compare: Starlink gen, Peplink models, Tailscale vs WireGuard mesh, DNS sovereignty.

## Security

- Acquisition orders above guardian cap → nuclear queue
- Vendor payments logged in treasury ledger
- Manifest is public-safe (no API keys, no credentials)

See [TREASURY_LAYER.md](TREASURY_LAYER.md) for wallets and ledger. See [EMPIRE_VISION.md](EMPIRE_VISION.md) for north star.
