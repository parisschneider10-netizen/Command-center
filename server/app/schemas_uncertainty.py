from datetime import datetime

from pydantic import BaseModel, Field


class UncertaintyReviewOut(BaseModel):
    id: int
    source_node: str
    payload_json: str
    confidence_score: float
    reason: str | None
    vault_path: str | None
    status: str
    commander_resolution: str | None
    resolved_intent: str | None
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class UncertaintyResolveIn(BaseModel):
    action: str = Field(pattern="^(approve|override|reject)$")
    corrected_intent: str | None = None
    notes: str | None = None
    mode: str = Field(default="live", pattern="^(drill|live|dry_run|test)$")
