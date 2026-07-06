# Value Extraction Node

Automated income for the empire **while** you build the foundation — deliberately, not impulsively.

## Philosophy

```text
WRONG:  Rush a "money bot" before foundation → technical debt + bad decisions
RIGHT:  Foundation first → one value node → manifest-governed → compound
```

The value node is **Layer 4.7** — it runs alongside the hive but does not override will manifest or nuclear rules.

## What it is

A **single automated system** that:
- Runs 24/7 on your VPS (n8n + agents)
- Produces measurable revenue or leads
- Logs everything to Command Center + treasury
- Escalates to you only per manifest (not every sale, not every error)

It is NOT:
- A get-rich-quick scheme
- Built in one impulsive session
- Allowed to spend unlimited money or post publicly without rules

## Decision framework (read before choosing)

Answer these in `vault/commander/value-node-decision.md` before going live:

1. **What skill/asset do you already have?** (domain knowledge beats random affiliate spam)
2. **Can agents run 90% of it?** (if not, humans are utility — not failure)
3. **Startup cost under wallet cap?** (default $100 empire daily cap)
4. **Legal and boring?** (if it feels sketchy, don't)
5. **Revenue in 30 days realistic?** (honest, not hype)
6. **Does it distract from foundation?** (if yes, defer)

**Rule:** No value node goes live until foundation Phase 1 is deployed (Voice OS + portal + VPS).

## Candidate nodes (ranked for agent-first empires)

| Node | Agent fit | Startup | Risk | Notes |
|------|-----------|---------|------|-------|
| **A — Lead gen + qualify** | High | Low | Low | Agents scrape/qualify leads, you/sales close nuclear only |
| **B — Micro API / MCP service** | High | Low | Low | Sell agent-callable capability (research, format, validate) |
| **C — Content + SEO arbitrage** | Medium | Low | Medium | Agents write, human-quality review in manifest |
| **D — Digital product (template, course)** | Medium | Low | Low | Build once, agents sell/deliver |
| **E — Service arbitrage (A2A)** | High | Medium | Medium | Your agents buy low, deliver high via hive |
| **F — E-commerce / dropship** | Medium | Medium | High | More ops, more impulse risk — defer |

**Recommendation for Phase 1 income:** Start with **A or B** — agent-native, low capital, clean logs.

## Architecture (when chosen)

```text
Value Node (n8n workflow)
    ├── Trigger: schedule / webhook / inbound lead
    ├── Agent: research · draft · qualify · deliver
    ├── Output: revenue event → treasury ledger
    ├── Log: vault/value-node/ + Command Center activity
    └── Nuclear: deals > cap · public posts · new vendors
```

## Treasury integration

All node revenue and spend flows through treasury:

- **Inbound:** `POST /api/treasury/ledger` (direction: inbound) — log revenue
- **Outbound:** agent wallet spend request — auto under cap
- **Profit:** weekly summary in portal (Phase 2 dashboard)

## Manifest gates (anti-impulse)

Add to `vault/commander/will-manifest.md`:

```markdown
## Value node rules
- Node type: [chosen after decision doc complete]
- Max daily ad/tool spend: $X
- Auto-publish content: no (draft → agent review → optional Commander)
- Revenue goal month 1: $X (sanity check, not pressure)
- Kill switch: Commander portal → disable value-node workflow
```

## Rollout phases

| Phase | Action |
|-------|--------|
| **0** | Foundation live (VPS, Voice OS, portal) |
| **1** | Complete `value-node-decision.md` — pick ONE node |
| **2** | Scaffold `agents/value-node/` + n8n workflow stub |
| **3** | Dry-run 7 days — log fake revenue, fix breaks |
| **4** | Live with $25/day spend cap |
| **5** | Scale only after 30 days stable metrics |

## Repo location

```
agents/value-node/     ← workflow + agent code (when chosen)
docs/VALUE_NODE.md     ← this doc
vault/commander/value-node-decision.md  ← your deliberate choice
```

## What to tell SARA at work

- *"Log note: value node leaning toward lead gen for [niche]"* → vault inbox
- *"Issue will: complete value node decision doc, priority 6"* → task queue
- **Do not** say *"launch money bot now"* — foundation first

Income feeds the empire. It does not rush the empire.
