# A2A Allowlist

> External agents your hive will do business with.
> **Default: DENY all unknown agents.**
>
> **System goal:** Obsolete human dependency. Buy capability agent-to-agent first.

## Obsoletion mandate

| Work type | Route | Never |
|-----------|-------|-------|
| Research, code, data, deploy, API | A2A → hive agents | RentAHuman |
| Physical (door knock, delivery) | A2A try first → human actuator last | Employees |

Scoreboard: `GET /api/a2a/goals` — target `human_pct = 0` for digital.

## Trusted agents

| Agent ID | Capability | Max/call | Status |
|----------|------------|----------|--------|
| _example-research-bot_ | research | $10 | template |

## Blocked patterns

- Unknown agents (default)
- Requests without price quote
- Wallet spend above daily A2A cap
- **Routing digital work to humans when A2A available**

## Your hive's outbound services (what you sell)

Other agents hire your hive — revenue → treasury:

- Voice OS tool APIs (`/voice/tools/*`)
- Sovereign stay presale rails
- Research + lead enrichment (when productized)

## Changelog

| Date | Change |
|------|--------|
| 2026-07-03 | Initial allowlist template |
| 2026-07-13 | Obsoletion mandate — A2A before humans encoded as law |
