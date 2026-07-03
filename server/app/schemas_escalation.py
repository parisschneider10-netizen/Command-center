from datetime import datetime

from pydantic import BaseModel, Field

from app.models import EscalationLevel, EscalationStatus


class EscalationCreate(BaseModel):
    title: str
    description: str
    level: EscalationLevel = EscalationLevel.human
    task_id: int | None = None
    budget: float | None = None
    nuclear_flag: bool = False


class EscalationOut(BaseModel):
    id: int
    title: str
    description: str
    level: EscalationLevel
    status: EscalationStatus
    task_id: int | None
    guardian_id: int | None
    rentahuman_bounty_id: str | None
    budget: float | None
    nuclear_flag: bool
    source: str
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class GuardianCreate(BaseModel):
    name: str
    role: str = "guardian"
    email: str | None = None
    rentahuman_id: str | None = None
    max_per_task: float = 25.0
    notes: str | None = None


class GuardianOut(BaseModel):
    id: int
    name: str
    role: str
    email: str | None
    rentahuman_id: str | None
    max_per_task: float
    is_active: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RentAHumanBountyRequest(BaseModel):
    title: str
    description: str
    compensation: float = Field(gt=0)
    location: str | None = None
    escalation_id: int | None = None
    dry_run: bool = True
