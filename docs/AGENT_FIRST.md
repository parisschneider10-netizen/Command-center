# Agent-First Empire

**Agents are unlimited. They are extensions of your will. Humans are utilities — not governors.**

## The hierarchy (correct mental model)

```text
                    COMMANDER (you)
                         │
                    WILL MANIFEST
                    (vault/commander/will-manifest.md)
                         │
              ┌──────────┴──────────┐
              │   AGENT HIVE        │  ← PRIMARY. Do everything possible.
              │   compete · execute │     No artificial limits.
              └──────────┬──────────┘
                         │ only when agents literally cannot:
              ┌──────────┴──────────┐
              │   HUMAN UTILITIES   │  ← reputation · physical · legal identity
              │   guardians · RAH   │     NOT permission gatekeepers on agents
              └──────────┬──────────┘
                         │ nuclear only:
                    COMMANDER REVIEW
                    (portal queue, not interruptions)
```

## Agent-first rules

1. **Agents try everything** — research, email, browser, code, comms, wallets, A2A
2. **No human approval for agent scope** — if an agent can do it, it does it
3. **Humans when agents hit hard walls** — physical, reputation, legal identity
4. **Commander is not in the loop** unless nuclear manifest trigger
5. **Agents compete** — race to claim and execute will-aligned tasks
6. **Agents spend** — within wallet caps; nuclear for big money
7. **Agents transact** — A2A commerce with allowlisted external agents

## Agent competition

Tasks from your will enter the **open queue**. Agents:

1. Poll `GET /api/agent-queue/open`
2. Claim: `POST /api/agent-queue/{task_id}/claim`
3. Execute autonomously
4. Complete: `POST /api/agent-queue/{task_id}/complete`
5. Score updates — best performers get priority on future claims

This creates internal competition to carry your will out fastest.

## Will manifest

`vault/commander/will-manifest.md` is the source of truth:

- Current empire priorities (ranked)
- What "carrying out will" means this week
- Agent autonomy boundaries (legal/safety — not human convenience)
- Success metrics agents optimize for

Voice OS and SARA read tasks against the manifest. n8n routes high-priority will to agent queue first.

## Gmail is dead (comms layer)

You don't need Gmail. You need **agent-readable comms**:

```text
Inbound email → your domain → Stalwart (self-hosted) → Voice OS inbox API
                                                      → agents triage/draft/reply
Outbound      ← agents draft ← Commander approve (nuclear) or auto-send per manifest
```

See [COMMS_LAYER.md](COMMS_LAYER.md).

## Hybrid system summary

| Capability | Who handles it |
|------------|----------------|
| Research, drafts, code, browser | **Agents** (always first) |
| Email triage, reply drafts | **Agents** |
| Send email (routine, in manifest) | **Agents** auto |
| Send email (nuclear: legal, large deals) | **Agent drafts → Commander queue** |
| Physical tasks | **RentAHuman / guardians** |
| Public reputation moments | **Humans** (guardians) |
| Strategy, nuclear decisions | **Commander** (portal only) |

## What we're building

| Phase | Focus |
|-------|-------|
| **Now** | Will manifest, agent queue, competition API, comms foundation |
| **Next** | AutoGen + Skyvern workers claiming from queue |
| **Later** | Self-hosted mail live, agents fully replace Gmail workflow |

Humans don't limit agents. Agents limit how much anyone bothers you.
