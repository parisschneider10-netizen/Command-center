# Sovereign Empire Architecture

A layered, self-owned system. Each layer does one job. You turn layers on as you need them — nothing is required on day one except Layer 0–2.

## Design principles

1. **Sovereign first** — self-hosted on your VPS, open-source core, you own the data
2. **Layered** — each layer is independent; swap parts without rebuilding everything
3. **Voice-first command** — phone is your remote control when you're on the clock
4. **Markdown as memory** — Obsidian vault = human-readable, agent-readable knowledge
5. **Orchestration, not spaghetti** — n8n connects pieces; agents don't call each other randomly

## The stack (bottom to top)

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 5 — INTERFACES                                   │
│  Vapi/SARA · Command Center portal · Obsidian app         │
├─────────────────────────────────────────────────────────┤
│  LAYER 4.6 — A2A COMMERCE                               │
│  Agent-to-agent business · allowlist · settlement       │
├─────────────────────────────────────────────────────────┤
│  LAYER 4.5 — TREASURY                                   │
│  Agent wallets · spend ledger · no banking apps for ops │
├─────────────────────────────────────────────────────────┤
│  LAYER 4 — HIVE AGENTS                                  │
│  AutoGen · Skyvern · competing workers                  │
├─────────────────────────────────────────────────────────┤
│  LAYER 3.5 — HUMAN UTILITY                              │
│  Guardians · RentAHuman · physical/reputation only      │
├─────────────────────────────────────────────────────────┤
│  LAYER 3 — ORCHESTRATION                                │
│  n8n · Voice OS · agent competition queue               │
├─────────────────────────────────────────────────────────┤
│  LAYER 2 — MEMORY & COMMS                               │
│  Obsidian vault · Command DB · agent inbox (no Gmail)   │
├─────────────────────────────────────────────────────────┤
│  LAYER 1 — TOOLS (external, optional)                   │
│  Brave Search · payment rails · A2A networks            │
├─────────────────────────────────────────────────────────┤
│  LAYER 0 — INFRASTRUCTURE                               │
│  VPS · Docker · Postgres · HTTPS (Caddy)                │
└─────────────────────────────────────────────────────────┘
```

## What each piece does

| Component | Layer | Role | Sovereign? |
|-----------|-------|------|------------|
| **VPS (Servury)** | 0 | Your land. Everything runs here. | ✅ Yours |
| **Docker Compose** | 0 | Runs all services consistently | ✅ Open source |
| **Postgres** | 0 | n8n state + future shared DB | ✅ Open source |
| **Caddy** | 0 | HTTPS reverse proxy | ✅ Open source |
| **Obsidian vault** | 2 | Markdown notes — you dump, agents read | ✅ Plain files you own |
| **Command DB** | 2 | Tasks, decisions, voice logs | ✅ SQLite/Postgres on your VPS |
| **n8n** | 3 | Workflow glue — "when X, do Y" | ✅ Self-hosted |
| **Voice OS** | 3 | Phone → actions (tasks, notes, triggers) | ✅ This repo |
| **Command Center** | 5 | Your dashboard when you have internet | ✅ This repo |
| **AutoGen** | 4 | Multi-agent teams for complex work | ✅ Open source (add later) |
| **Skyvern** | 4 | Browser automation (forms, sites) | ✅ Open source (add later) |
| **Brave Search** | 1 | Web research when agents need it | ⚠️ External API (optional) |
| **Vapi** | 5 | Voice phone interface | ⚠️ External (replace with LiveKit later) |
| **LiveKit** | 5 | Self-hosted voice (Phase 2) | ✅ Open source |
| **RentAHuman** | 3.5 | On-demand humans for physical/judgment tasks | ⚠️ External API |
| **Guardians** | 3.5 | Vetted humans for utility/reputation | ✅ Your roster |
| **Agent wallets** | 4.5 | Per-agent spend limits, ledger | ✅ Foundation |
| **A2A commerce** | 4.6 | Agent-to-agent business | ✅ Foundation |

See [EMPIRE_VISION.md](EMPIRE_VISION.md) for the full north star.

## Data flow examples

### Voice note dump (works now)

```
You call Vapi → Voice OS → writes markdown to vault/ + logs to DB
                         → optional: triggers n8n webhook
Obsidian (on your phone/laptop) syncs vault → you see the note
Agent (later) reads vault → processes → creates task
```

### Research task (Phase 2+)

```
Voice: "Research competitor pricing"
  → Voice OS creates task
  → n8n picks up new task
  → AutoGen agent team plans research
  → Brave Search API gathers data
  → Results written to vault/Research/competitor-pricing.md
  → Decision queued in Command Center
You review in portal → approve → Skyvern posts update (if needed)
```

## Obsidian on VPS — how it actually works

Obsidian is a **local app**. The vault is just a folder of `.md` files. You don't run Obsidian on the server — you run the **vault folder** on the server and sync it.

**Recommended sync options (pick one):**

| Method | Best for | Sovereign? |
|--------|----------|------------|
| **Syncthing** | Real-time sync phone ↔ VPS | ✅ Fully self-hosted |
| **Obsidian Sync** | Easiest, paid | ⚠️ Their servers |
| **Git** | Version history, open source friendly | ✅ If private repo |

Voice OS writes notes to `/vault/inbox/` — you process them in Obsidian when you sync.

## n8n — the glue layer

n8n sits between Voice OS and your agents. It handles:

- New task created → notify you / start workflow
- Vault note added → trigger agent processing
- Scheduled briefings → email or webhook
- AutoGen / Skyvern calls → wrapped in retry + logging

**Rule:** Voice OS and agents talk to n8n via webhooks. n8n talks to everything else. No direct agent-to-agent chaos.

## What to add and when

### Phase 1 — Foundation (built now)
- [x] Voice OS + Command Center
- [x] Obsidian vault folder + write API
- [x] n8n in Docker Compose
- [x] Postgres for n8n

### Phase 2 — Automation (next)
- [ ] n8n workflow: new task → process queue
- [ ] n8n workflow: vault inbox → summarize
- [ ] Syncthing for vault sync
- [ ] HTTPS + domain on VPS

### Phase 3 — Agents (when foundation is stable)
- [ ] AutoGen worker service (Docker)
- [ ] Skyvern for browser tasks
- [ ] Brave Search in research workflows

### Phase 4 — Empire scale
- [ ] Approval gates for sensitive actions
- [ ] Multi-agent specialization (sales, ops, content)
- [ ] Open-source release of your stack template

## What NOT to do early

- Don't wire AutoGen + Skyvern + Brave all at once — you'll debug four systems simultaneously
- Don't use 5 sync methods for Obsidian — pick one
- Don't skip HTTPS — Vapi and n8n webhooks need it
- Don't store secrets in the vault — use `.env` only

## Ownership checklist

Before calling it "sovereign," verify:

- [ ] VPS is in your account, your SSH keys
- [ ] Domain DNS points to your VPS
- [ ] All `.env` secrets are yours, rotated
- [ ] Vault folder is backed up (restic or btrfs snapshots)
- [ ] Postgres dumps scheduled
- [ ] You can rebuild from this repo + backups alone

This repo is your **infrastructure-as-code** for the empire. Fork it, open-source it, own it.
