# Value Extraction Node — STR Expansion

**Status:** Integrated into Command Center.

## Business

Property manager leads → Servury VPS + GHL sub-account per city → MTR recon SaaS revenue.

See [docs/EXPANSION_NODE.md](../../docs/EXPANSION_NODE.md)

## Dry run

```bash
cd agents/value-node
python run_dry.py
```

Or via API: `POST /api/value-node/expansion/scale` with `"dry_run": true`

## Live deploy

1. Set API keys in `.env`
2. `EXPANSION_DRY_RUN=false`
3. Start with `EXPANSION_LIVE_BATCH_CAP=1`, verify, scale up
