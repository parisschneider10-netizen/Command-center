"""Max velocity intent handling — auto-execute, parallel, no human timelines."""

from __future__ import annotations

from app.config import settings

MAX_SPEED_KEYWORDS = (
    "max speed",
    "machine speed",
    "warpspeed",
    "warp speed",
    "auto execute",
    "parallel",
    "full potential",
    "unleash",
    "compound",
    "30 day",
    "transhuman",
)


def should_auto_execute_intent(intent_text: str, explicit_auto_execute: bool) -> bool:
    """Default ON when empire_max_velocity — Commander states will, hive runs."""
    if explicit_auto_execute:
        return True
    if settings.intent_default_auto_execute and settings.empire_max_velocity:
        return True
    lower = intent_text.lower()
    return any(kw in lower for kw in MAX_SPEED_KEYWORDS)


def effective_expansion_batch_cap() -> int:
    """Parallel cities at max velocity — not human serial batches of 5."""
    if settings.empire_max_velocity:
        return settings.expansion_max_cities
    return settings.expansion_live_batch_cap


def velocity_snapshot() -> dict:
    return {
        "empire_max_velocity": settings.empire_max_velocity,
        "intent_default_auto_execute": settings.intent_default_auto_execute,
        "sovereign_grid_days_target": settings.sovereign_grid_days_target,
        "expansion_parallel_cap": effective_expansion_batch_cap(),
        "law": "Science and physics only — not human calendar pace.",
    }
