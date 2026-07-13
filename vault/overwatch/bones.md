# Overwatch salvage — useful bones

> Extracted from Vapi assistant snapshot. Replit live blocked while suspended.

## Mapped to Command Center

| Overwatch function | Lives here now |
|--------------------|----------------|
| Command dashboard | `portal/` |
| Voice orders | SARA + `/voice/tools/*` |
| Intent → execution | `/api/intent` + auto-execute |
| Treasury / float | `/api/treasury` |
| Human tasks | Human firewall + RentAHuman |
| Empire plays | Sovereign Stay, expansion, KC blitz |

## Extraction

```bash
# After deploy — portal auth
POST /api/overwatch/extract
GET  /api/overwatch/bones
```

Or: **Actions → Wire SARA** saves `vault/commander/overwatch-vapi-snapshot.json`

## Replit URLs found

Run extract to populate. All must point to `https://157-254-194-89.sslip.io` after migration.
