# Command Center + Voice OS — Sovereign Stack

A **self-owned, layered system** for running a one-man empire: voice command by phone, command deck by browser, markdown memory in Obsidian, workflows in n8n.

## The stack at a glance

| Layer | Components | Status |
|-------|-----------|--------|
| **0 — Infrastructure** | VPS, Docker, Postgres, HTTPS | Ready |
| **1 — Tools** | Brave Search (optional, later) | Planned |
| **2 — Memory** | Obsidian vault, Command DB | Built |
| **3 — Orchestration** | Voice OS, n8n | Built |
| **4 — Agents** | AutoGen, Skyvern | Planned (stubs ready) |
| **5 — Interfaces** | Vapi voice, Command Center portal | Built |

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

## Setup guides

- [Vapi phone setup](docs/VAPI_SETUP.md) — Phase 1 (now)
- [Voice stack & LiveKit migration](docs/VOICE_STACK.md) — Phase 2 (sovereign)
- [Human layer & escalation pyramid](docs/HUMAN_LAYER.md)
- [RentAHuman setup](docs/RENTAHUMAN_SETUP.md)
- [n8n workflow setup](docs/N8N_SETUP.md)
- [Full architecture & roadmap](docs/ARCHITECTURE.md)

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

1. **Now** — Deploy foundation, connect Vapi, set up n8n webhooks, sync Obsidian
2. **Next** — n8n automations for inbox processing, Syncthing, HTTPS
3. **Later** — AutoGen + Skyvern + Brave Search agent layer

Don't skip Phase 1. Solid foundation first, agents second.
