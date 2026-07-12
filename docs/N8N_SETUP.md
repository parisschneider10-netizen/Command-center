# n8n Setup

n8n is your **workflow glue** — it connects Voice OS, the Obsidian vault, and future agents (AutoGen, Skyvern, Brave Search).

## Access n8n

After `docker compose up -d`:

- Local: http://localhost:5678
- Production: https://your-domain.com/n8n (via Caddy reverse proxy)

First visit: create your n8n owner account.

## Required webhooks (create these workflows)

Create one n8n workflow per event. Each uses a **Webhook** trigger node.

| Event name | Triggered when | Suggested action |
|------------|----------------|------------------|
| `task-created` | Voice creates a task | Log, notify, queue for agent |
| `vault-inbox` | Note dumped to Obsidian inbox | Summarize, tag, move to research/ |
| `research` | Manual voice trigger | Call AutoGen + Brave Search (Phase 3) |

### Example: task-created workflow

1. Add **Webhook** node
   - HTTP Method: POST
   - Path: `task-created`
   - Response: immediately
2. Add **HTTP Request** node (optional)
   - Log to external service or send yourself an email
3. Activate workflow

Webhook URL will be: `https://your-domain.com/webhook/task-created`

Set in `.env`:
```
N8N_WEBHOOK_BASE_URL=https://your-domain.com/webhook
```

Voice OS calls: `POST {N8N_WEBHOOK_BASE_URL}/task-created`

## Starter workflow export

Import `docs/n8n-starter-workflow.json` into n8n as a starting template.

## Connecting future agents

### AutoGen (Phase 3)
- n8n HTTP Request → AutoGen worker API
- Worker reads vault, writes results back

### Skyvern (Phase 3)
- n8n triggers Skyvern for browser tasks
- Results logged to vault + Command Center

### Brave Search (Phase 3)
- n8n HTTP Request → Brave Search API
- Results appended to vault note

**Rule:** Agents never call each other directly. Everything routes through n8n or Voice OS.

## Security

- Put n8n behind HTTPS
- Use n8n credentials store for API keys
- Don't expose n8n port 5678 publicly without auth
- Use Caddy basic auth or VPN for admin UIs

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full layer map.
