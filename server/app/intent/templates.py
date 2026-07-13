"""Intent templates — Commander states goal, system returns plan + micro-tasks."""

from __future__ import annotations

DEPLOY_TEMPLATE = {
    "name": "deploy_command_deck",
    "phases": [
        {"phase": 1, "title": "Code ready", "owner": "agent", "detail": "Merge PR, verify health endpoints"},
        {"phase": 2, "title": "VPS deploy", "owner": "human", "detail": "SSH + docker compose OR RentAHuman gig"},
        {"phase": 3, "title": "Voice wire", "owner": "agent", "detail": "Vapi webhook → /vapi/webhook"},
        {"phase": 4, "title": "Verify", "owner": "commander", "detail": "One SARA call + portal login (2 min)"},
    ],
}

KC_LAUNDRY_TEMPLATE = {
    "name": "kc_laundry_play",
    "phases": [
        {"phase": 1, "title": "Host pipeline", "owner": "agent", "detail": "GHL form → /api/laundry/host-signup"},
        {"phase": 2, "title": "Ground force", "owner": "human", "detail": "Host visits + sticker drops via RentAHuman"},
        {"phase": 3, "title": "Guest flow", "owner": "agent", "detail": "QR → guest-request webhook"},
        {"phase": 4, "title": "Float", "owner": "treasury", "detail": "Host payment → 48h hold → ammo pools"},
    ],
}

EXPANSION_TEMPLATE = {
    "name": "expansion_node",
    "phases": [
        {"phase": 1, "title": "Lead intake", "owner": "agent", "detail": "Scrape/register leads → /api/value-node/leads"},
        {"phase": 2, "title": "City lock", "owner": "agent", "detail": "Servury VPS + GHL sub-account per city"},
        {"phase": 3, "title": "Treasury", "owner": "treasury", "detail": "Log VPS spend, ammo allocation"},
    ],
}

HUMAN_HELP_TEMPLATE = {
    "name": "human_firewall",
    "phases": [
        {"phase": 1, "title": "Firewall check", "owner": "guardian", "detail": "Route to 1 of 3 guardians by specialty"},
        {"phase": 2, "title": "Micro-task post", "owner": "system", "detail": "Auto-post RentAHuman if no guardian"},
        {"phase": 3, "title": "Commander shield", "owner": "commander", "detail": "You only see nuclear items"},
    ],
}

WIRE_SARA_TEMPLATE = {
    "name": "wire_sara",
    "phases": [
        {"phase": 1, "title": "HTTPS via sslip.io", "owner": "system", "detail": "Caddy auto-TLS — no domain purchase"},
        {"phase": 2, "title": "Vapi API wire", "owner": "system", "detail": "PATCH assistant via VAPI_API_KEY"},
        {"phase": 3, "title": "Voice live", "owner": "commander", "detail": "Call SARA — state intent, system executes"},
    ],
}

GENERIC_TEMPLATE = {
    "name": "general_expansion",
    "phases": [
        {"phase": 1, "title": "Research", "owner": "agent", "detail": "Hive researches sovereign path"},
        {"phase": 2, "title": "Execute digital", "owner": "agent", "detail": "Tasks queued for agent competition"},
        {"phase": 3, "title": "Human judgment", "owner": "human", "detail": "Firewall handles physical/judgment walls"},
        {"phase": 4, "title": "Treasury", "owner": "treasury", "detail": "Fund from float — ammo + human life force"},
    ],
}

KC_WELCOME_BASKET_TEMPLATE = {
    "name": "kc_welcome_basket_play",
    "phases": [
        {"phase": 1, "title": "Host prepay", "owner": "treasury", "detail": "GHL $249 → prepay API → 48h float"},
        {"phase": 2, "title": "Agent lock SKU", "owner": "agent", "detail": "lock-spec Costco basket list"},
        {"phase": 3, "title": "3-person crew", "owner": "human", "detail": "Shop $22 + Assemble $20 + Deliver $18 RAH"},
        {"phase": 4, "title": "Laundry upsell", "owner": "agent", "detail": "QR in basket → laundry recurring"},
    ],
}

KC_WORLD_CUP_BLITZ_TEMPLATE = {
    "name": "kc_world_cup_blitz",
    "phases": [
        {"phase": 1, "title": "AI lead scrape", "owner": "agent", "detail": "POST /api/kc-blitz/leads/batch — 50 KCMO STR hosts"},
        {"phase": 2, "title": "Dispatch closers", "owner": "human", "detail": "POST dispatch-all — RentAHuman $45 pay-on-close"},
        {"phase": 3, "title": "Lock 30 units", "owner": "treasury", "detail": "Host pays $249 at door → 4h sales float → instant closer payout"},
        {"phase": 4, "title": "Replicate", "owner": "agent", "detail": "Copy locked-host playbook to remaining pipeline units"},
    ],
}

SOVEREIGN_STAY_TEMPLATE = {
    "name": "sovereign_stay_matrix",
    "phases": [
        {"phase": 1, "title": "Doorstep presale", "owner": "human", "detail": "POST /api/sovereign-stay/presale — $150 in, $30 closer, $120 float"},
        {"phase": 2, "title": "Badge + buyback brain", "owner": "agent", "detail": "POST optimize — badges boost velocity, buyback if vacancy >30%"},
        {"phase": 3, "title": "Checkout actuators", "owner": "human", "detail": "POST checkout — RentAHuman turnover + partner kickback"},
        {"phase": 4, "title": "Scale grid", "owner": "agent", "detail": "3 units × 40 cities = 120 evergreen units"},
    ],
}

OVERWATCH_MIGRATION_TEMPLATE = {
    "name": "overwatch_replit_migration",
    "phases": [
        {"phase": 1, "title": "Extract", "owner": "agent", "detail": "Dump Vapi assistant + hunt replit.dev URLs; clone GitHub export if linked"},
        {"phase": 2, "title": "Inventory", "owner": "agent", "detail": "Map Overwatch routes/UI to portal + /api/* in Command Center"},
        {"phase": 3, "title": "Port", "owner": "agent", "detail": "Migrate useful logic — vault/projects/overwatch-replit-migration.md"},
        {"phase": 4, "title": "Retire Replit", "owner": "system", "detail": "Point Vapi tools at Servury only; Replit dependency zero"},
    ],
}

INTENT_MATCHERS: list[dict] = [
    {"keywords": ["wire sara", "connect vapi", "connect sara", "vapi key", "voice live", "machine wire", "obsolete click"], "template": WIRE_SARA_TEMPLATE},
    {"keywords": ["overwatch", "replit", "migrate overwatch", "command center website"], "template": OVERWATCH_MIGRATION_TEMPLATE},
    {"keywords": ["sovereign stay", "sovereign", "v1_core", "egoist", "40 cities", "3 units"], "template": SOVEREIGN_STAY_TEMPLATE},
    {"keywords": ["deploy", "vps", "servury", "command deck", "online", "docker"], "template": DEPLOY_TEMPLATE},
    {"keywords": ["welcome basket", "basket", "new host", "welcome kit"], "template": KC_WELCOME_BASKET_TEMPLATE},
    {"keywords": ["world cup", "blitz", "lock 30", "kcmo", "close sale"], "template": KC_WORLD_CUP_BLITZ_TEMPLATE},
    {"keywords": ["laundry", "kc", "host", "detergent", "world cup"], "template": KC_LAUNDRY_TEMPLATE},
    {"keywords": ["expand", "city", "str", "property manager", "ghl"], "template": EXPANSION_TEMPLATE},
    {"keywords": ["hire", "human", "help", "firewall", "guardian", "physical"], "template": HUMAN_HELP_TEMPLATE},
    {"keywords": ["ground", "sticker", "visit", "rentahuman", "rah"], "template": KC_LAUNDRY_TEMPLATE},
    {"keywords": ["starlink", "network", "acquire", "infra"], "template": GENERIC_TEMPLATE},
]

# Default judgment triggers — Commander can override via API / vault
DEFAULT_JUDGMENT_RULES: list[dict] = [
    {"id": "legal", "label": "Legal & contracts", "handler": "commander", "auto_rah": False},
    {"id": "brand_public", "label": "Public statements / brand", "handler": "commander", "auto_rah": False},
    {"id": "spend_over_cap", "label": "Spend above guardian cap", "handler": "commander", "auto_rah": False},
    {"id": "physical_presence", "label": "Physical world task", "handler": "human_firewall", "auto_rah": True},
    {"id": "vendor_commitment", "label": "Vendor commitments / pricing", "handler": "guardian", "auto_rah": False},
    {"id": "reputation_face", "label": "Reputation requires trusted face", "handler": "guardian", "auto_rah": True},
    {"id": "agent_exhausted", "label": "Agent failed 3+ attempts", "handler": "human_firewall", "auto_rah": True},
    {"id": "routine_ops", "label": "Routine digital ops", "handler": "agent", "auto_rah": False},
]

# Micro-task templates per intent type
MICRO_TASK_LIBRARY: dict[str, list[dict]] = {
    "deploy_command_deck": [
        {
            "title": "Machine-wire SARA via Vapi API",
            "description": "POST /api/vapi/machine-wire with VAPI_API_KEY — no dashboard clicks.",
            "executor": "system",
            "will_priority": 10,
            "tags": ["vapi", "machine-wire"],
        },
        {
            "title": "Verify health + portal login",
            "description": "curl /health, login portal, confirm tasks load.",
            "executor": "agent",
            "will_priority": 7,
        },
    ],
    "wire_sara": [
        {
            "title": "Machine-wire SARA (HTTPS + Vapi API)",
            "description": "Auto sslip.io HTTPS + PATCH Vapi assistant. Requires VAPI_API_KEY in .env.",
            "executor": "system",
            "will_priority": 10,
            "tags": ["vapi", "machine-wire", "sara"],
        },
        {
            "title": "Verify SARA voice loop",
            "description": "Call Vapi number, say briefing, confirm portal activity.",
            "executor": "agent",
            "will_priority": 8,
        },
    ],
    "kc_laundry_play": [
        {
            "title": "KC host visit — pitch laundry amenity",
            "description": "Visit STR host, pitch complimentary laundry. Photo proof. PAY ON COMPLETION.",
            "executor": "rentahuman",
            "budget_usd": 35.0,
            "tags": ["ground-force", "host-visit", "kcmo"],
        },
        {
            "title": "KC sticker drop — QR placement",
            "description": "Place QR stickers at approved host properties. Photo each. PAY ON COMPLETION.",
            "executor": "rentahuman",
            "budget_usd": 20.0,
            "tags": ["ground-force", "stickers", "kcmo"],
        },
        {
            "title": "Wire GHL host signup to laundry API",
            "description": "Connect GHL form webhook to POST /api/laundry/host-signup",
            "executor": "agent",
            "will_priority": 8,
        },
    ],
    "expansion_node": [
        {
            "title": "Register PM lead batch",
            "description": "POST leads to /api/value-node/leads, verify in portal.",
            "executor": "agent",
            "will_priority": 7,
        },
        {
            "title": "Dry-run city lock for first lead",
            "description": "POST /api/value-node/expansion/city-lock with dry_run=true",
            "executor": "agent",
            "will_priority": 8,
        },
    ],
    "human_firewall": [
        {
            "title": "Guardian judgment — intent review",
            "description": "Review Commander intent against manifest. Execute within CAN list or escalate.",
            "executor": "guardian",
            "budget_usd": 0,
        },
    ],
    "kc_laundry_play": [
        {
            "title": "KC host visit — pitch laundry amenity",
            "description": "Visit STR host, pitch complimentary laundry. Photo proof. PAY ON COMPLETION.",
            "executor": "rentahuman",
            "budget_usd": 35.0,
            "tags": ["ground-force", "host-visit", "kcmo"],
        },
        {
            "title": "Wire GHL host signup to laundry API",
            "description": "Connect GHL form webhook to POST /api/laundry/host-signup",
            "executor": "agent",
            "will_priority": 8,
        },
    ],
    "sovereign_stay_matrix": [
        {
            "title": "Layer 1 — Doorstep presale closer",
            "description": "RentAHuman collects $150 upfront. POST /api/sovereign-stay/presale on payment proof.",
            "executor": "rentahuman",
            "budget_usd": 30.0,
            "tags": ["sovereign-stay", "presale", "layer-1"],
        },
        {
            "title": "Layer 2 — Badge + buyback optimization",
            "description": "Agent monitors vacancy. POST /api/sovereign-stay/hosts/{id}/optimize when >30%.",
            "executor": "agent",
            "will_priority": 8,
        },
        {
            "title": "Layer 3 — Checkout turnover dispatch",
            "description": "RentAHuman turnover + locker hub routing. POST checkout endpoint.",
            "executor": "rentahuman",
            "budget_usd": 25.0,
            "tags": ["sovereign-stay", "checkout", "layer-3"],
        },
        {
            "title": "DeFi ledger audit export",
            "description": "GET /api/sovereign-stay/ledger — JSONL on VPS for investor pitch trail.",
            "executor": "agent",
            "will_priority": 6,
        },
    ],
    "kc_world_cup_blitz": [
        {
            "title": "AI scrape KCMO STR host leads",
            "description": "Bulk POST /api/kc-blitz/leads/batch — target 50 leads before World Cup week.",
            "executor": "agent",
            "will_priority": 10,
        },
        {
            "title": "Dispatch closers to all new leads",
            "description": "POST /api/kc-blitz/dispatch-all — host_close_sale $45 pay when host prepays at door.",
            "executor": "rentahuman",
            "budget_usd": 45.0,
            "tags": ["kc-blitz", "host-close", "kcmo"],
        },
        {
            "title": "GHL $249 Stripe link for closers at door",
            "description": "Mobile payment link closers pull up on visit. Webhook → close-sale API.",
            "executor": "agent",
            "will_priority": 9,
        },
        {
            "title": "Welcome basket crew per locked host",
            "description": "Shop $22 + Assemble $20 + Deliver $18 after each close-sale lock.",
            "executor": "rentahuman",
            "budget_usd": 60.0,
            "tags": ["welcome-basket", "kcmo"],
        },
    ],
    "kc_welcome_basket_play": [
        {
            "title": "GHL welcome basket page + $249 prepay link",
            "description": "Landing page for launch_5pack. Webhook to POST /api/welcome-basket/host-signup + prepay.",
            "executor": "agent",
            "will_priority": 9,
        },
        {
            "title": "Lock default KC basket spec for first host",
            "description": "POST lock-spec with Costco SKU list. No shopping until locked.",
            "executor": "agent",
            "will_priority": 8,
        },
        {
            "title": "KC Welcome Basket — Shop run",
            "description": "Shop agent-locked list. Receipt photo. Commander may claim this gig.",
            "executor": "rentahuman",
            "budget_usd": 22.0,
            "tags": ["welcome-basket", "shop", "kcmo"],
        },
        {
            "title": "KC Welcome Basket — Assemble + Deliver crew",
            "description": "Assembler $20 + Deliver $18. Photo proof in unit.",
            "executor": "rentahuman",
            "budget_usd": 38.0,
            "tags": ["welcome-basket", "kcmo"],
        },
    ],
    "overwatch_replit_migration": [
        {
            "title": "Dump Vapi assistant config for Replit URLs",
            "description": "GET assistant from Vapi API; save vault/commander/overwatch-vapi-snapshot.json",
            "executor": "system",
            "will_priority": 10,
            "tags": ["overwatch", "replit", "vapi", "migration"],
        },
        {
            "title": "Inventory Overwatch vs Command Center",
            "description": "Diff routes/UI against portal + /api. Document gaps in vault/projects/overwatch-replit-migration.md",
            "executor": "agent",
            "will_priority": 9,
            "tags": ["overwatch", "migration"],
        },
        {
            "title": "Port high-value Overwatch features",
            "description": "Migrate useful dashboards, tools, prompts into this repo — Servury is source of truth.",
            "executor": "agent",
            "will_priority": 8,
            "tags": ["overwatch", "port"],
        },
    ],
    "general_expansion": [
        {
            "title": "Research sovereign path for intent",
            "description": "Hive researches options, updates vault + acquisition manifest if hardware needed.",
            "executor": "agent",
            "will_priority": 7,
        },
    ],
}


def match_template(intent_text: str) -> dict:
    lower = intent_text.lower()
    for matcher in INTENT_MATCHERS:
        if any(kw in lower for kw in matcher["keywords"]):
            return matcher["template"]
    return GENERIC_TEMPLATE


def build_micro_tasks(template_name: str, intent_text: str) -> list[dict]:
    base = MICRO_TASK_LIBRARY.get(template_name, MICRO_TASK_LIBRARY["general_expansion"])
    tasks = []
    for i, t in enumerate(base):
        tasks.append({
            **t,
            "id": i + 1,
            "intent_context": intent_text[:500],
            "status": "planned",
        })
    return tasks
