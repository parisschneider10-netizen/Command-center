---
type: intent
status: pending
mode: drill
auto_execute: true
intent: "REPLACE WITH YOUR INTENT — one clear sentence"
created: {{date}}
tags: [ready-room, intent, drill, sights-on]
title: "Ready Room intent"
source: ready-room
---

# Ready Room intent

## Commander intent

REPLACE WITH YOUR INTENT — one clear sentence.

## Mode

- **DRILL** — sights on (change `mode: live` for kill shot)

## Notes

- Logic maps, rules, constraints below
- Sync vault → system scans pending intents

## Operational notes

-

## Logic map

```mermaid
flowchart LR
  A[Intent] --> B[Scan]
  B --> C[Hive]
```
