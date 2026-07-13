"""Agent-to-agent commerce — prefer over humans; obsoletion is the goal."""

from app.a2a.resolver import classify_work, human_obsoletion_snapshot
from app.a2a.service import hire_external_agent, route_digital_work

__all__ = [
    "classify_work",
    "human_obsoletion_snapshot",
    "hire_external_agent",
    "route_digital_work",
]
