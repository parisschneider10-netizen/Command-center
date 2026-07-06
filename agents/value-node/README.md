# Value Extraction Node

**Status:** Decision required before code.

## Do not build until

1. [ ] Foundation deployed (Voice OS + portal on VPS)
2. [ ] `vault/commander/value-node-decision.md` completed
3. [ ] Rules added to `will-manifest.md`

## When approved

This folder will contain:

- `workflow.json` — n8n export for the chosen node
- `agent.py` — agent logic (lead qualify, API handler, etc.)
- `Dockerfile` — optional worker container

## See

- [docs/VALUE_NODE.md](../../docs/VALUE_NODE.md) — full design
- [docs/GITHUB_WORKFLOW.md](../../docs/GITHUB_WORKFLOW.md) — build from work

**No impulse launches.** One node. Manifest-governed.
