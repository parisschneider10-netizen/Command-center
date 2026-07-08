# Judgment Rules — What Needs Human vs Agent

> Commander configures via API or portal. Agents and firewall read these rules.

## Commander only (nuclear)

- Legal, contracts, lawsuits
- Public brand statements
- Spend above guardian cap ($25/task default)
- New vendor first payment above cap

## Human firewall (3 guardians)

- Physical presence required
- Reputation needs trusted face
- Agent exhausted 3+ attempts on same task

## Guardian (within manifest CAN list)

- Vendor information calls (no commitments)
- Routine customer replies (templates)
- Approve task completion under cap

## Agent only (hive)

- Research, drafts, code, vault
- Digital automation
- Routine email drafts (auto-send per will manifest)

## Auto-post RentAHuman when

- Physical task + no guardian available
- `physical_presence` or `agent_exhausted` rule matches
- Float covers budget (treasury human life force check)

Update via: `PATCH /api/intent/judgment-rules/{rule_key}`
