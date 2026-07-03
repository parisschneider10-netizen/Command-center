# RentAHuman Setup

Connect your hive to the human marketplace when agents can't handle a task.

## What it is

[RentAHuman](https://rentahuman.ai) lets AI agents hire humans for real-world tasks via REST API or MCP. Search is free; bounties require an API key.

**In your stack:** Level 2 escalation — after agents fail, before Commander.

## Setup

1. Register at https://rentahuman.ai
2. Create an API key (Settings → API Keys)
3. Add to `.env`:
   ```
   RENTAHUMAN_API_KEY=rah_live_your_key_here
   ```
4. Restart API: `docker compose restart api`

## Escalation flow

```text
Agent blocked
  → escalate_to_human (Voice OS)
  → Check guardian roster
      → Guardian available? Assign from manifest
      → No guardian? POST /api/bounties (dry-run first)
  → Commander NOT notified (unless nuclear or over budget)
```

## API endpoints (Voice OS wraps these)

| Voice OS | RentAHuman |
|----------|------------|
| `POST /api/integrations/rentahuman/search` | `GET /api/humans` |
| `POST /api/integrations/rentahuman/bounty` | `POST /api/bounties` |

Always use `dry_run: true` first for bounties over $15.

## Budget caps (from manifest)

Default caps in `.env`:
- `GUARDIAN_PER_TASK_CAP=25` — max per bounty without Commander
- `COMMANDER_DAILY_BUDGET_CAP=100` — daily human spend

Override in `vault/guardians/commander-manifest.md`.

## n8n webhook

Create workflow: `human-escalation`
- Triggered when Voice OS escalates to Level 2
- Actions: notify guardian, search RentAHuman, post bounty if needed

## MCP alternative

For AutoGen agents later, add RentAHuman MCP server:
https://rentahuman.ai/docs

Same rules apply — manifest caps, dry-run, no Commander unless nuclear.

See [HUMAN_LAYER.md](HUMAN_LAYER.md) for the full escalation pyramid.
