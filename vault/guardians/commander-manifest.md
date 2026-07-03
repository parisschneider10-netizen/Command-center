# Commander Permission Manifest

> This document defines how the hive operates when Commander is unavailable.
> Guardians act as Commander within these bounds. Agents escalate per these rules.
> **Commander is the nuclear option — last call only.**

## Identity

- **Commander:** [Your name / handle]
- **Company:** One-man empire (scaling via hive + human layer)
- **Default posture:** Agents handle it → humans if stuck → Commander only if nuclear

---

## Level 1 — Agents (try first, always)

Agents MUST attempt before escalating:

- Research and summaries (Brave Search, vault notes)
- Drafts (content, emails, docs) — do not send without guardian if external
- Browser tasks within Skyvern scope
- Task logging, vault dumps, n8n workflows
- Status briefings

**Never escalate to Commander for Level 1 failures.** Escalate to Level 2.

---

## Level 2 — Human Guardians

### Guardians CAN (without Commander)

- [ ] Reply to routine customer inquiries (use vault templates)
- [ ] Schedule meetings under $0 cost
- [ ] Complete physical-world tasks via RentAHuman under budget cap
- [ ] Approve task completions under **$25 per task**
- [ ] Daily spend cap: **$100/day** across all human hires
- [ ] Make judgment calls documented in `vault/guardians/playbook/`
- [ ] Call vendors for information (not commitments)

### Guardians CANNOT (escalate to Commander or senior guardian)

- [ ] Spend above $25/task or $100/day
- [ ] Sign contracts or legal documents
- [ ] Post publicly on Commander's behalf (social, press)
- [ ] Grant account access or share credentials
- [ ] Fire or hire standing guardians
- [ ] Refunds or payment disputes
- [ ] Anything marked `nuclear` in a task

### RentAHuman rules

1. Always `dryRun=true` first if bounty > $15
2. Search humans free; post bounty only when guardian pool empty
3. Prefer guardians over marketplace when available
4. Log every hire to vault + Command Center

---

## Level 3 — Commander (nuclear / last call)

Commander is notified ONLY when:

1. **Budget exceeded** — task needs more than guardian cap
2. **Permission denied** — action outside guardian manifest
3. **Nuclear flag** — task or human explicitly sets `needs_commander: true`
4. **Guardian deadlock** — two guardians disagree (rare)
5. **Legal / brand / money** — contracts, public statements, large payments

### Commander is NEVER notified for:

- Routine task updates
- Agent failures (escalate to human first)
- RentAHuman tasks under cap that guardians approved
- Vault inbox dumps
- Briefings

---

## Decision logic (train guardians on this)

When unsure, ask:

1. Can an agent do this? → Level 1
2. Is it under budget and in the CAN list? → Guardian decides
3. Is it in the CANNOT list? → Queue decision for Commander (do not call)
4. Is it urgent physical-world? → RentAHuman bounty, guardian supervises

**Bias:** Handle it without Commander. Commander's time is nuclear.

---

## Guardian roster

| Name | Role | RentAHuman ID | Max/task | Status |
|------|------|---------------|----------|--------|
| _TBD_ | Primary guardian | — | $25 | recruiting |

Add rows as you onboard humans.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-07-03 | Initial manifest — one-man company structure |
