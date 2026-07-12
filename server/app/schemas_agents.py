from datetime import datetime

from pydantic import BaseModel, Field


class AgentRegister(BaseModel):
    name: str
    agent_type: str = "custom"
    capabilities: str | None = None


class AgentOut(BaseModel):
    id: int
    name: str
    agent_type: str
    capabilities: str | None
    score: int
    wins: int
    losses: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskClaimResult(BaseModel):
    ok: bool
    task_id: int | None = None
    message: str


class IssueWillTool(BaseModel):
    title: str
    description: str | None = None
    will_priority: int = Field(default=7, ge=1, le=10)


class EmailOut(BaseModel):
    id: int
    direction: str
    from_addr: str
    to_addr: str
    subject: str
    body_text: str | None
    status: str
    agent_summary: str | None
    draft_reply: str | None
    nuclear_flag: bool
    received_at: datetime

    model_config = {"from_attributes": True}


class EmailDraft(BaseModel):
    draft_reply: str
    agent_summary: str | None = None
    nuclear_flag: bool = False
