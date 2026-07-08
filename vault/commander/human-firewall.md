# Human Firewall — 3 Guardian Slots

> These humans protect Commander time. They execute with your judgment when the hive cannot.

## Slots (register in portal or POST /api/guardians)

| Slot | Name | Role | Status |
|------|------|------|--------|
| 1 | _TBD_ | Primary guardian | recruiting |
| 2 | _TBD_ | Ops / physical | recruiting |
| 3 | _TBD_ | RAH supervisor | recruiting |

## Rules

- Empty slot → Intent engine auto-posts RentAHuman micro-task
- Filled slot → judgment tasks route to guardian first
- Commander notified **only** on nuclear triggers (see judgment-rules)

## Train guardians on

- `vault/guardians/commander-manifest.md`
- `vault/commander/will-manifest.md`
- `vault/commander/judgment-rules.md`
