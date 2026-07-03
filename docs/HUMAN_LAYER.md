# Human Layer — Escalation & Guardians

The hive is **agent-first**. Agents do everything they can — without artificial limits. Humans are utilities for reputation, physical world, and hard walls agents cannot cross. **You are the nuclear option — last call only.**

Humans do NOT gate what agents are allowed to try digitally. See [AGENT_FIRST.md](AGENT_FIRST.md).

## Escalation pyramid

```text
                    ┌─────────────┐
                    │  COMMANDER  │  ← You. Nuclear. Last resort only.
                    │  (Level 3)  │
                    └──────▲──────┘
                           │ only if:
                           │ • guardian permissions exceeded
                           │ • budget cap hit
                           │ • nuclear flag set
                    ┌──────┴──────┐
                    │   HUMAN     │  ← Guardians + RentAHuman hires
                    │   LAYER     │     Act as you within permission bounds
                    │  (Level 2)  │
                    └──────▲──────┘
                           │ when:
                           │ • agents blocked
                           │ • physical-world task
                           │ • judgment call in guardian scope
                    ┌──────┴──────┐
                    │    HIVE     │  ← AutoGen, Skyvern, n8n, Voice OS
                    │   AGENTS    │     Try everything autonomously first
                    │  (Level 1)  │
                    └─────────────┘
```

## Core concepts

### Guardian
A vetted human who operates **as you** within a defined permission manifest. They train on your logic (stored in the vault). They are not generic hires — they are your delegated authority.

### RentAHuman
Marketplace for **on-demand humans** when no guardian is available or the task needs local/physical execution. API + MCP integration. Search is free; bounties require API key.

### Escalation
Every problem gets a level. The hive **must exhaust Level 1** before touching Level 2. Level 3 (you) requires explicit triggers — never automatic nagging.

## When each level activates

| Level | Who handles | Examples |
|-------|-------------|----------|
| **1 — Agents** | n8n, AutoGen, Skyvern, Voice OS | Research, drafts, browser tasks, logging |
| **2 — Humans** | Guardians, RentAHuman bounties | Physical tasks, phone calls, judgment in scope, agent stuck |
| **3 — Commander** | You | Payments above cap, legal, firing, strategy, nuclear flags |

## Guardian permission manifest

Stored at: `vault/guardians/commander-manifest.md`

Guardians read this. Agents read this. It defines:
- What guardians CAN approve alone
- What requires another guardian
- What requires Commander (you)
- Budget caps per task/day
- Tone and decision logic ("what would Commander do?")

Update the manifest as your logic evolves. Guardians train off it + your vault notes.

## RentAHuman integration

```text
Agent blocked at Level 1
    → Voice OS / n8n creates HumanEscalation (level 2)
    → Check: guardian available?
        YES → assign guardian, notify via manifest rules
        NO  → POST /api/bounties on RentAHuman (dry-run first)
    → Human completes task
    → Result logged to vault + Command Center
    → Commander NOT notified unless nuclear trigger
```

### API flow (when enabled)

1. `GET /api/humans` — search (free, no key)
2. `POST /api/bounties` with `dryRun=true` — preview cost
3. `POST /api/bounties` — post after guardian/auto-approval rules pass
4. Webhook back → update escalation status in Command Center

Set `RENTAHUMAN_API_KEY` in `.env` when ready.

## Nuclear triggers (only these bother you)

Configure in `vault/guardians/commander-manifest.md`:

- Spend above daily cap
- Legal, contracts, lawsuits
- Public statements / brand
- Firing or hiring guardians
- Account access you haven't pre-authorized
- Guardian explicitly flags `needs_commander`

Everything else stays in the hive or human layer.

## One-man company → scale

This structure lets you operate solo today:

| Today | At scale |
|-------|----------|
| You = Commander | You = Commander (unchanged) |
| RentAHuman for ad-hoc tasks | Standing guardians + RentAHuman overflow |
| Manifest in vault | Manifest + guardian training docs |
| Manual guardian pick | n8n auto-assigns by skill/availability |

You're building **org chart as code**. The hierarchy exists before the humans do.

## Voice commands (SARA)

- *"Escalate to human: need someone to pick up package downtown"* → Level 2
- *"Assign guardian for vendor call"* → Level 2, guardian pool
- *"Nuclear flag: need my approval on contract"* → Level 3, queues decision for you

SARA confirms yes/no before any escalation. She never auto-pages you.

## Files in this repo

| Path | Purpose |
|------|---------|
| `vault/guardians/commander-manifest.md` | Your permission bible |
| `docs/HUMAN_LAYER.md` | This doc |
| `server/app/integrations/rentahuman.py` | RentAHuman API client |
| `server/app/routes/escalations.py` | Escalation API |
| `docs/RENTAHUMAN_SETUP.md` | API key + bounty setup |

## Phase rollout

1. **Now** — Manifest + escalation models + API stubs
2. **Next** — n8n workflow: blocked task → auto-escalate Level 2
3. **Later** — RentAHuman API key, guardian roster, auto-bounty
4. **Never automatic** — Level 3 without nuclear trigger
