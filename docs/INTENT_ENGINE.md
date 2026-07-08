# Intent Engine — State Intent, System Plans, Hive Executes

> You state intent. System shows plan + data. Human firewall protects your time. Treasury shows what float buys in human life force.

## The loop

```text
YOU: "I want to deploy the command deck and start KC laundry"
         │
         ▼
┌─────────────────────┐
│   INTENT ENGINE     │  Plan · phases · micro-tasks · treasury capacity
└─────────┬───────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
┌────────┐  ┌──────────────────┐
│  HIVE  │  │ HUMAN FIREWALL   │  3 guardians + RentAHuman auto-post
│ agents │  │ judgment layer   │  You never post gigs manually
└────────┘  └──────────────────┘
          │
          ▼
   Commander sees NUCLEAR only
```

## Human firewall (3 slots)

Three vetted humans execute **as you would** when the hive hits judgment walls:

| Slot | Role | When activated |
|------|------|----------------|
| 1 | Primary guardian | Vendor calls, reputation, judgment in manifest |
| 2 | Ops guardian | Physical tasks, ground force oversight |
| 3 | Overflow / RAH supervisor | RentAHuman bounty quality, completion proof |

Register via `POST /api/guardians`. Empty slots → system auto-posts RentAHuman micro-tasks.

**You configure what needs judgment** via `GET/PATCH /api/intent/judgment-rules`.

## Judgment rules (defaults)

| Rule | Handler | Auto-post RAH |
|------|---------|---------------|
| Legal & contracts | Commander | No |
| Public brand | Commander | No |
| Spend over cap | Commander | No |
| Physical world | Human firewall | Yes |
| Reputation / trusted face | Guardian | Yes |
| Agent failed 3x | Human firewall | Yes |
| Routine digital | Agent only | No |

## Treasury: human life force

`GET /api/treasury/human-capital` translates float into capacity:

```json
{
  "deployable_usd": 107.0,
  "capacity": {
    "micro_gigs_20_usd": 5,
    "standard_gigs_35_usd": 3,
    "tasks_at_guardian_cap": 4,
    "guardian_day_equivalents": 1
  }
}
```

Meaning: *"With current float you can run 3 host visits without touching your wallet again."*

Included in `GET /api/treasury/capability` as `human_life_force`.

## API

| Endpoint | Purpose |
|----------|---------|
| `POST /api/intent` | State intent → plan + direction |
| `POST /api/intent` `{ "auto_execute": true }` | Plan + execute (no buttons) |
| `POST /api/intent/{id}/execute` | Execute planned micro-tasks |
| `GET /api/intent/{id}` | Full briefing |
| `GET /api/intent/firewall` | 3 guardian slots status |
| `GET /api/intent/judgment-rules` | What needs human judgment |
| `PATCH /api/intent/judgment-rules/{key}` | Commander configures rules |
| `GET /api/treasury/human-capital` | Float → gig capacity |

## Voice (SARA)

| Say | Result |
|-----|--------|
| *"My intent is deploy command deck on Servury"* | Plan + direction + human capacity |
| *"Execute intent — start KC laundry play"* | `auto_execute: true` |
| *"What can my float do for human help?"* | Treasury human life force |

## Micro-task auto-post

When you execute an intent, the system:

1. **Agent tasks** → agent competition queue + n8n
2. **Guardian tasks** → assigned round-robin to firewall slots
3. **RentAHuman tasks** → `POST /api/bounties` automatically (dry-run until key set)

You never open RentAHuman to post gigs. Intent engine does it aligned to your will.

## Example

```bash
POST /api/intent
{
  "intent": "Deploy command deck and run 5 KC host visits this week",
  "auto_execute": true
}
```

Returns:
- Phases: code → VPS deploy → voice wire → verify
- Micro-tasks: RAH deploy gig ($50), 5x host visits ($35), agent webhook tasks
- Treasury: whether float covers human budget
- Firewall: which guardian got which judgment task

## Config

```env
HUMAN_FIREWALL_SIZE=3
INTENT_AUTO_POST_RAH=true
RENTAHUMAN_API_KEY=   # VPS .env only — dry-run until set
GUARDIAN_PER_TASK_CAP=25
COMMANDER_DAILY_BUDGET_CAP=100
```

## Vault

- `vault/commander/judgment-rules.md` — human-readable rules mirror
- `vault/guardians/commander-manifest.md` — firewall permissions

See [HUMAN_LAYER.md](HUMAN_LAYER.md) · [TREASURY_LAYER.md](TREASURY_LAYER.md) · [SOVEREIGN_ACQUISITIONS.md](SOVEREIGN_ACQUISITIONS.md)
