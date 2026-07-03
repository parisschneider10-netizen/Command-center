# Treasury Layer — Agent Wallets

Replace your need to open **banking apps** for day-to-day empire operations. Agents hold wallets. You hold treasury. Everything is logged.

## Philosophy

```text
You don't check balances on your phone.
Agents spend within rules.
Ledger is truth.
Nuclear queue for big money.
```

Banking apps become **archive + funding source** — money flows into Commander treasury, agents operate from sub-wallets, you only look at the portal for anomalies or nuclear approvals.

## Architecture

```text
┌─────────────────────────────────────────┐
│  FUNDING SOURCES (Phase 1 bridge)       │
│  Business bank · Mercury · Wise · Crypto│
└──────────────────┬──────────────────────┘
                   │ manual or API fund
                   ▼
┌─────────────────────────────────────────┐
│  COMMANDER TREASURY                     │
│  Master balance · daily empire cap      │
└──────────────────┬──────────────────────┘
                   │ allocate
         ┌─────────┼─────────┐
         ▼         ▼         ▼
    Agent A    Agent B    Agent A2A
    wallet     wallet     wallet
    $50/day    $20/day    $200/day
```

## Agent wallet rules

| Rule | Default |
|------|---------|
| Per-agent daily cap | Set in manifest |
| Auto-approve under | $25/transaction |
| Commander queue above | $25/transaction |
| Daily empire cap | $100/day total |
| A2A wallet | Separate cap, separate ledger |

Agents request spend → ledger checks caps → auto-approve or nuclear queue.

## What agents pay for

- RentAHuman bounties
- API credits (Brave, OpenAI, etc.)
- Domain/services renewals (within cap)
- A2A purchases from other agents
- SaaS tools the hive needs

## Phased rollout

### Phase 1 — Ledger only (foundation now)

- Log all spend requests in Command DB
- Agents POST `/api/treasury/spend-request`
- Auto-approve/deny by rules
- You manually execute approved spends (bank app) until Phase 2

**You stop living in banking apps for ops — agents propose, ledger tracks, you batch-approve nuclear.**

### Phase 2 — Programmatic rails

Pick one or more based on your entity:

| Rail | Best for |
|------|----------|
| **Mercury API** | US business, developer-friendly |
| **Stripe Issuing** | Virtual cards per agent |
| **Privacy.com** | Virtual cards with caps |
| **USDC/Crypto wallet** | Agent-native, A2A friendly |
| **Wise API** | International |

Connect one rail → approved ledger entries auto-execute.

### Phase 3 — Full agent autonomy

Agents spend without you. Commander sees weekly treasury report in portal. Nuclear only for anomalies.

## Nuclear money triggers (always queue, never auto)

- Any single transaction above manifest cap
- Daily empire cap exceeded
- New vendor first payment
- Legal/contract payments
- A2A counterparty not on allowlist

## API (Voice OS)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/treasury/overview` | Balances, caps, today's spend |
| `GET /api/treasury/wallets` | All agent wallets |
| `POST /api/treasury/wallets` | Create agent wallet |
| `POST /api/treasury/spend-request` | Agent requests spend |
| `GET /api/treasury/ledger` | Full transaction log |
| `POST /api/treasury/approve/{id}` | Commander approves nuclear |

## Voice (SARA)

- *"Treasury status"* → today's spend, pending approvals
- *"Approve spend 47"* → nuclear approval from phone (yes/no)

## Security

- Agent wallets are **limits**, not bank accounts
- Real money stays in regulated rails you control
- API keys for payment rails in `.env` only, never vault
- Every transaction immutable in ledger

## Sovereignty note

Full sovereign money (self-custody crypto, private rails) is possible in Phase 3+. Start with regulated business banking + programmatic layer — legality and audit trail matter for a real empire.

See [EMPIRE_VISION.md](EMPIRE_VISION.md) for the full north star.
