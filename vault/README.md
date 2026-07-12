# Obsidian Vault

This folder is your **sovereign knowledge base**. Voice OS writes here. Agents read here. You edit in Obsidian on your devices.

## Folder structure

```
vault/
├── inbox/        ← Voice dumps, quick captures (agents process these)
├── tasks/        ← Task-related notes linked from Command Center
├── research/     ← Agent research output (Brave, AutoGen, etc.)
├── decisions/    ← Decision context and outcomes
├── projects/     ← One folder per empire project
└── templates/    ← Note templates for consistency
```

## Sync to your devices

Obsidian is an app on your phone/laptop. The vault lives on your VPS. Sync it:

### Option A: Syncthing (recommended — fully sovereign)

```bash
# On VPS
apt install syncthing
# Share /path/to/command-center/vault with your phone/laptop
```

### Option B: Git (good for open-source workflow)

```bash
# Private repo, push vault changes daily
cd vault && git init && git remote add origin your-private-repo
```

### Option C: Obsidian Sync (easiest, not fully sovereign)

Point Obsidian Sync at this vault folder.

## How agents use this

1. You call Voice OS: *"Log a note: competitor X launched new pricing"*
2. Voice OS writes `inbox/2026-07-03-competitor-x-pricing.md`
3. n8n workflow detects new file → triggers processing
4. Agent reads note → moves to `research/` with summary
5. Decision queued in Command Center for your review

## Note format

Voice OS creates notes like:

```markdown
---
created: 2026-07-03T18:00:00Z
source: voice
tags: [inbox]
---

Your note content here.
```

You can add Obsidian plugins, tags, links — it's standard markdown.
