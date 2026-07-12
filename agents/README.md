# Agent Workers (Layer 4)

Placeholder for future agent services. **Do not enable until Layer 0–3 are stable.**

## Planned workers

| Agent | Purpose | Status |
|-------|---------|--------|
| **AutoGen** | Multi-agent reasoning, complex task execution | Phase 3 |
| **Skyvern** | Browser automation (forms, logins, web tasks) | Phase 3 |
| **Brave Search** | Web research tool (via n8n, not standalone) | Phase 3 |

## How they'll connect

```
Voice OS / n8n webhook
        ↓
   Agent worker (Docker service)
        ↓
   Reads vault/ · Writes results · Updates Command Center
```

## When you're ready

1. Uncomment agent services in `docker-compose.yml`
2. Add API keys to `.env`
3. Create n8n workflows that call agent endpoints
4. Test with one simple task before going live

See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for the full roadmap.
