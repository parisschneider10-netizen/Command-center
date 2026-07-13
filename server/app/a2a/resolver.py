"""
A2A-first resolver — digital work NEVER defaults to humans.
System design goal: obsolete human dependency.
"""

from __future__ import annotations

import re

# Physical / judgment walls — ONLY cases where humans may be used.
HUMAN_REQUIRED_KEYWORDS = frozenset(
    {
        "physical",
        "in-person",
        "in person",
        "door knock",
        "host visit",
        "host-visit",
        "sticker",
        "stickers",
        "deliver",
        "delivery",
        "shop run",
        "assemble",
        "pickup",
        "pick up",
        "ground-force",
        "ground force",
        "guerrilla",
        "meatspace",
        "photo proof at property",
        "plaza",
        "westport",
    }
)

# Digital work — route A2A → internal agents; never RentAHuman first.
A2A_DIGITAL_KEYWORDS = frozenset(
    {
        "research",
        "scrape",
        "api",
        "code",
        "build",
        "deploy",
        "wire",
        "digital",
        "analysis",
        "data",
        "enrich",
        "automation",
        "browser",
        "email draft",
        "github",
        "n8n",
        "webhook",
        "ledger",
        "treasury",
        "intent",
        "agent",
        "hive",
        "a2a",
    }
)

# Suggesting humans for these violates doctrine.
FORBIDDEN_HUMAN_FOR = frozenset(
    {
        "deploy",
        "devops",
        "dns",
        "dashboard",
        "vapi setup",
        "docker",
        "research",
        "code",
        "api wire",
    }
)


def _text_blob(*parts: str | None) -> str:
    return " ".join(p for p in parts if p).lower()


def classify_work(
    title: str,
    description: str | None = None,
    tags: str | None = None,
) -> dict:
    """
    Decide routing: a2a_first | agent_queue | human_actuator_only.
    Default for unknown work: A2A + agents (NOT humans).
    """
    blob = _text_blob(title, description, tags)

    human_hits = [k for k in HUMAN_REQUIRED_KEYWORDS if k in blob]
    digital_hits = [k for k in A2A_DIGITAL_KEYWORDS if k in blob]
    forbidden_human = [k for k in FORBIDDEN_HUMAN_FOR if k in blob]

    human_required = len(human_hits) > 0
    digital = len(digital_hits) > 0 or not human_required

    if forbidden_human and not human_required:
        return {
            "route": "a2a_first",
            "prefer_a2a": True,
            "human_required": False,
            "agent_queue_fallback": True,
            "human_hits": human_hits,
            "digital_hits": digital_hits,
            "doctrine_note": "Humans forbidden for this digital work — A2A or hive only.",
        }

    if human_required and not digital:
        return {
            "route": "human_actuator_only",
            "prefer_a2a": False,
            "human_required": True,
            "agent_queue_fallback": False,
            "human_hits": human_hits,
            "digital_hits": digital_hits,
            "doctrine_note": "Physical/judgment wall — human actuator permitted as last resort.",
        }

    if human_required and digital:
        return {
            "route": "a2a_first_then_split",
            "prefer_a2a": True,
            "human_required": True,
            "agent_queue_fallback": True,
            "human_hits": human_hits,
            "digital_hits": digital_hits,
            "doctrine_note": "Digital slice → A2A/agents first; physical slice → actuator only if A2A fails.",
        }

    return {
        "route": "a2a_first",
        "prefer_a2a": True,
        "human_required": False,
        "agent_queue_fallback": True,
        "human_hits": human_hits,
        "digital_hits": digital_hits,
        "doctrine_note": "Default: agent-to-agent and hive — humans not considered.",
    }


def human_obsoletion_snapshot(
    *,
    a2a_events: int = 0,
    agent_events: int = 0,
    human_events: int = 0,
) -> dict:
    """Metrics toward zero human dependency for digital work."""
    total = a2a_events + agent_events + human_events
    human_pct = round(100 * human_events / total, 1) if total else 0.0
    a2a_pct = round(100 * a2a_events / total, 1) if total else 0.0
    return {
        "goal": "obsolete_human_dependency",
        "target_human_pct_digital": 0,
        "current_human_pct": human_pct,
        "current_a2a_pct": a2a_pct,
        "a2a_events": a2a_events,
        "agent_events": agent_events,
        "human_events": human_events,
        "on_track": human_pct == 0 or a2a_events + agent_events > human_events,
        "law": "A2A and hive first. Humans are actuators being phased out — not staff.",
    }
