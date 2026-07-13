# Overwatch (Replit) → Command Center migration

> **Status:** Replit account suspended — cannot pull live. Extract from Vapi config, GitHub export, or Replit dump.

## What Overwatch was

Commander's prior command-deck website on Replit, wired to Vapi SARA. Big-tech dependency chain:

```text
Phone (+1 971-382-0038) → Vapi → Replit Overwatch (SUSPENDED) → dead webhooks
Phone (+1 971-382-0038) → Vapi → Servury Command Center (LIVE) → hive executes
```

**Goal:** Salvage useful UX, routes, prompts, and business logic into this repo. Never depend on Replit again.

## Extraction sources (priority order)

| # | Source | How |
|---|--------|-----|
| 1 | **Vapi assistant config** | Wire SARA workflow dumps assistant JSON — tool `server.url` values may point at `*.replit.dev` |
| 2 | **GitHub** | If Repl was connected to GitHub → clone that repo |
| 3 | **Replit export** | When account unsuspended: Tools → Git → export zip, or Download as zip |
| 4 | **Commander memory** | Portal notes, screenshots, voice transcripts in vault/inbox |
| 5 | **Wayback** | If Repl had a public deployment URL |

## Map to this system

| Overwatch (likely) | Command Center (here) |
|--------------------|------------------------|
| Dashboard / status | Portal `http://157.254.194.89:3000` |
| Voice commands | SARA tools → `/voice/tools/*` |
| Tasks / decisions | `/api/intent`, portal tasks |
| Treasury / float | `/api/treasury/*` |
| Empire plays | Sovereign Stay, KC blitz, expansion nodes |
| Escalations | Human firewall + nuclear queue |

## Agent auto-execute

Commander intent (voice or GitHub Issue):

> *Migrate Overwatch from Replit — extract useful routes, UI, and logic into Command Center. Max speed.*

Triggers `overwatch_migration` template — hive researches, diffs, ports what matters.

## Anti-dependency law

- Replit: **retire** after migration
- Vapi: **bridge** until LiveKit treasury clears
- Cursor/agents: **tools** — sovereign code on Servury VPS is source of truth
