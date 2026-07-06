# Command Center + Voice OS — Sovereign Empire

A **self-owned, agent-first empire** for one person at scale: voice command, agent hive, sovereign comms, agent wallets, A2A commerce.

**North star:** [docs/EMPIRE_VISION.md](docs/EMPIRE_VISION.md)

## The stack at a glance

| Layer | Components | Status |
|-------|-----------|--------|
| **0 — Infrastructure** | VPS, Docker, Postgres, HTTPS | Ready |
| **1 — Tools** | Brave Search, payment rails (later) | Planned |
| **2 — Memory** | Obsidian vault, Command DB, comms inbox | Built |
| **3 — Orchestration** | Voice OS, n8n, agent competition queue | Built |
| **3.5 — Human utility** | Guardians, RentAHuman (not agent gates) | Built |
| **4 — Hive agents** | AutoGen, Skyvern, competing workers | Planned |
| **4.5 — Treasury** | Agent wallets, spend ledger | Foundation |
| **4.6 — A2A commerce** | Agent-to-agent business | Foundation |
| **5 — Interfaces** | Vapi/SARA voice, Command Center portal | Built |

Full architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Quick start

```bash
cp .env.example .env
# Edit passwords, domain, n8n keys
docker compose up -d
```

| Service | URL |
|---------|-----|
| Command Center portal | http://localhost:3000 |
| Voice OS API | http://localhost:8000 |
| n8n workflows | http://localhost:5678 |
| Obsidian vault | `./vault/` folder |

## How the pieces connect

```
Phone call (Vapi)
    → Voice OS (tasks, notes, briefings)
        → Obsidian vault (markdown inbox)
        → n8n webhooks (automations)
            → Agents later (AutoGen, Skyvern, Brave)

Browser (when you have internet)
    → Command Center portal (dashboard, decisions, activity)
    → Obsidian app (synced vault notes)
    → n8n UI (workflow management)
```

## Voice commands (via Vapi)

- *"Give me a briefing"* — status of tasks, decisions, activity
- *"Create a task: build landing page, high priority"* — queues work + triggers n8n
- *"Log a note: competitor launched new pricing"* — saves to vault inbox + activity log
- *"Dump to vault: research ideas"* — structured note for agents to process later
- *"Queue a decision: Stripe vs Square"* — waiting in portal for your review

## Obsidian vault

Notes land in `vault/inbox/`. Sync to your phone/laptop via Syncthing (recommended), Git, or Obsidian Sync.

See [vault/README.md](vault/README.md)

## What you're replacing forever

| Consumer app | Empire layer |
|--------------|--------------|
| Gmail | [Comms layer](docs/COMMS_LAYER.md) — sovereign mail + agent inbox |
| Banking apps (ops) | [Treasury layer](docs/TREASURY_LAYER.md) — agent wallets + ledger |
| Manual everything | Agent hive + [A2A commerce](docs/A2A_COMMERCE.md) |

## Setup guides

- [Empire vision (start here)](docs/EMPIRE_VISION.md)
- [Agent-first philosophy](docs/AGENT_FIRST.md)
- [Comms — Gmail replacement](docs/COMMS_LAYER.md)
- [Treasury — agent wallets](docs/TREASURY_LAYER.md)
- [A2A commerce](docs/A2A_COMMERCE.md)
- [Human utility layer](docs/HUMAN_LAYER.md)
- [Vapi + SARA voice](docs/VAPI_SETUP.md)
- [GitHub command channel (primary)](docs/GITHUB_COMMAND.md)
- [Fast launch playbook](docs/FAST_LAUNCH.md)
- [Value extraction node (income, deliberate)](docs/VALUE_NODE.md)

## Project structure

```
server/           Voice OS API
portal/           Command Center web app
vault/            Obsidian markdown vault (your data)
agents/           Future agent workers (AutoGen, Skyvern)
docs/             Setup guides + workflow templates
docker-compose.yml
```

## Sovereignty checklist

- All core services self-hosted on your VPS
- Vault = plain markdown files you own
- Open-source stack (Docker, Postgres, n8n, FastAPI, React)
- External only where necessary: Vapi (voice), Brave Search (optional research)
- This repo is infrastructure-as-code — fork it, open-source it, own it

## Phases

1. **Now** — Deploy foundation, Vapi/SARA, agent queue, will manifest
2. **Live** — Domain mail, comms API → Gmail retired
3. **Money** — Treasury wallets, spend rules → banking apps for ops retired
4. **Hive** — AutoGen/Skyvern competing on queue
5. **A2A** — External agent commerce, revenue
6. **Sovereign** — LiveKit, Stalwart mail, full self-host

Don't skip phases. Each goes live before the next.
