# A2A Commerce — Agent-to-Agent Business

Your hive doesn't operate alone. Agents **transact with other agents** — buying capability, selling output, participating in an agent economy.

## What A2A means here

```text
Your Agent A2A-1                    External Agent Service
        │                                    │
        │  "Need market research report"     │
        ├────────── A2A request ────────────►│
        │                                    │
        │◄──────── deliverable + invoice ────┤
        │                                    │
        ▼                                    ▼
   Treasury wallet                    Their wallet
   (logged, capped)                   (their problem)
```

A2A is how a **one-man company scales past one VPS** — you compose other agents' capabilities without hiring employees.

## A2A vs human layer

| | A2A | Humans (RentAHuman) |
|---|-----|---------------------|
| **What** | Digital agent services | Physical/reputation meatspace |
| **Speed** | Seconds to minutes | Hours to days |
| **Pay** | Agent wallet, micropayments | Bounty, higher friction |
| **When** | Research, data, code, analysis | Pickups, in-person, phone trees |

Agents try A2A first for digital work. Humans for what agents literally cannot touch.

## Commerce flows

### Your agents BUY (inbound capability)

- Research agents (market, competitor, legal scan)
- Code generation / review agents
- Data enrichment agents
- Other empire agents on RentAHuman-style marketplaces for **digital** work

### Your agents SELL (outbound revenue)

- Your hive exposes APIs/MCP endpoints other agents call
- Packaged research, content, leads — priced in manifest
- Revenue → Commander treasury

This is your business model container — specifics come when you're ready to open-source or productize.

## Protocol stack (phased)

| Phase | Protocol |
|-------|----------|
| **1** | HTTP webhooks + n8n (agent calls your Voice OS tools) |
| **2** | MCP servers exposed from your VPS |
| **3** | Structured A2A messages in `server/app/a2a/` |
| **4** | Payment settlement via agent wallets + allowlist |
| **5** | Open protocol participation (AP2, custom, etc.) |

## Allowlist security

Not every external agent gets wallet access.

```yaml
# vault/commander/a2a-allowlist.md
trusted:
  - name: research-bot.example
    max_per_call: 10
    capabilities: [research]
blocked:
  - unknown agents default DENY
```

Unknown A2A requests → log + queue for Commander or guardian review.

## API foundation (Voice OS)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/a2a/status` | Hive open for business? |
| `POST /api/a2a/request` | Inbound request from external agent |
| `POST /api/a2a/outbound` | Your agent hires external agent |
| `GET /api/a2a/ledger` | A2A transaction log |

## n8n workflows

- `a2a-inbound` → validate allowlist → create task → agent claims
- `a2a-outbound` → spend request → wallet check → call external API
- `a2a-settle` → log completion → update treasury

## Buzzing hive

A2A + competition queue + wallets = hive that never sleeps:

```text
Will issued → agents compete → winner executes
           → needs external data → A2A buy
           → needs physical → human utility
           → needs money → wallet auto or nuclear
           → completes → score + revenue logged
```

You wake up to portal summary, not 47 app notifications.

## Open source angle

When you open-source this stack, others run compatible A2A endpoints — your hive joins a network of sovereign one-man empires trading agent services.

See [EMPIRE_VISION.md](EMPIRE_VISION.md) and [TREASURY_LAYER.md](TREASURY_LAYER.md).
