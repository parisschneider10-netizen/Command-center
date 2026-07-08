from datetime import datetime

from pydantic import BaseModel, Field


class IntentIn(BaseModel):
    intent: str = Field(min_length=3, description="What you want the empire to achieve")
    source: str = "portal"
    auto_execute: bool = False


class IntentExecute(BaseModel):
    auto_post_rah: bool | None = None
    dry_run_rah: bool | None = None


class JudgmentRuleUpdate(BaseModel):
    handler: str | None = None
    auto_post_rah: bool | None = None
    is_active: bool | None = None


class IntentOut(BaseModel):
    id: int
    intent_text: str
    source: str
    status: str
    template_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
