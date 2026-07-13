"""
Binding doctrine — machine-readable operating contract for all agents.
Source of truth: vault/commander/operating-contract.md
"""

from __future__ import annotations

from pathlib import Path

DOCTRINE_VERSION = "1.2"

# Max velocity — only physics/science/nuclear limit the hive. No human-paced timelines.
MAX_VELOCITY_LAW = (
    "Execute at maximum lawful speed. Parallel by default. "
    "Compound treasury same-day. Never suggest calendar rollouts to Commander."
)
MAX_VELOCITY_GOALS = frozenset(
    {
        "parallel_by_default",
        "intent_auto_execute",
        "same_day_treasury_compound",
        "science_is_only_limit",
        "no_human_pace_timelines",
        "transhumanist_execution",
    }
)

# Phrases that imply human-paced thinking — agents must NOT emit these.
FORBIDDEN_TIMELINE_PHRASES = (
    "12 month",
    "12-month",
    "24 month",
    "24-month",
    "over the next year",
    "take your time",
    "when you have time",
    "no rush",
    "weeks to months",
    "human timeline",
    "phased rollout over",
    "gradually over",
)

# Commander-only actions (founder custody). Agents must NOT substitute humans for these.
COMMANDER_ONLY = frozenset(
    {
        "hold_api_keys",
        "hold_secrets",
        "state_will_intent",
        "nuclear_legal",
        "nuclear_big_money",
        "nuclear_public_brand",
    }
)

# Agents MUST handle via API/automation — never instruct Commander to click dashboards.
AGENT_AUTOMATES = frozenset(
    {
        "vps_deploy",
        "vapi_wire",
        "https_provision",
        "github_build",
        "intent_execute",
        "treasury_clear",
        "hive_research",
        "doctor_scan",
        "n8n_trigger",
        "a2a_hire",
        "a2a_sell",
    }
)

# A2A-first — system design goal: obsolete human dependency for digital work.
A2A_FIRST_GOALS = frozenset(
    {
        "obsolete_human_dependency",
        "agent_to_agent_before_humans",
        "zero_humans_for_digital",
        "humans_actuators_not_employees",
        "scale_via_composed_agents",
    }
)

# Humans (RentAHuman) ONLY for these walls — never for setup/DevOps.
HUMAN_ACTUATOR_ONLY = frozenset(
    {
        "physical_presence",
        "reputation_face",
        "legal_identity",
        "platform_human_verification",
        "agent_exhausted_3x",
        "a2a_exhausted_3x",
    }
)

# Phrases agents must NOT emit in suggestions to Commander (anti-patterns).
FORBIDDEN_SUGGESTIONS = (
    "open the vapi dashboard",
    "click the vapi dashboard",
    "ssh into servury",
    "hire someone to deploy",
    "hire devops",
    "configure dns manually",
    "paste this in the vapi ui",
    "go to dashboard.vapi",
    "hire a human for research",
    "use rentahuman for code",
    "get a person to deploy",
    "human employee",
) + FORBIDDEN_TIMELINE_PHRASES

EXECUTION_ORDER = [
    "intent",
    "internal_agents",
    "a2a_external_agents",
    "machine_apis",
    "human_actuators_last_resort",
    "commander_nuclear",
]


def contract_path(vault_path: str = "./vault") -> Path:
    return Path(vault_path) / "commander" / "operating-contract.md"


def contract_exists(vault_path: str = "./vault") -> bool:
    return contract_path(vault_path).exists()


def load_contract_text(vault_path: str = "./vault") -> str:
    path = contract_path(vault_path)
    if path.exists():
        return path.read_text()
    return ""


def doctrine_snapshot(vault_path: str = "./vault") -> dict:
    """Returned by /health, /api/bridge/status — agents read this first."""
    return {
        "version": DOCTRINE_VERSION,
        "law": "Commander states intent. Hive executes. Commander holds keys and sees nuclear only.",
        "a2a_goal": "Obsolete human dependency — agent-to-agent before any human actuator.",
        "max_velocity": MAX_VELOCITY_LAW,
        "max_velocity_goals": sorted(MAX_VELOCITY_GOALS),
        "max_velocity_file": "vault/commander/max-velocity.md",
        "launch_manual": "vault/commander/launch-manual.md",
        "launch_cheat_sheet": "vault/commander/launch-cheat-sheet.md",
        "budget_law": "vault/commander/budget-law.md",
        "sovereign_grid_days_target": 30,
        "contract_file": "vault/commander/operating-contract.md",
        "a2a_allowlist": "vault/commander/a2a-allowlist.md",
        "contract_present": contract_exists(vault_path),
        "execution_order": EXECUTION_ORDER,
        "a2a_first_goals": sorted(A2A_FIRST_GOALS),
        "commander_only": sorted(COMMANDER_ONLY),
        "agent_automates": sorted(AGENT_AUTOMATES),
        "human_actuator_only": sorted(HUMAN_ACTUATOR_ONLY),
        "anti_patterns": list(FORBIDDEN_SUGGESTIONS),
    }


def violates_doctrine(suggestion: str) -> str | None:
    """Return matched anti-pattern if text suggests forbidden Commander/human-default work."""
    lower = suggestion.lower()
    for phrase in FORBIDDEN_SUGGESTIONS:
        if phrase in lower:
            return phrase
    return None
