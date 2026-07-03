from datetime import datetime

from pydantic import BaseModel, Field

from app.models import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.normal
    source: str = "voice"


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActivityOut(BaseModel):
    id: int
    event_type: str
    message: str
    metadata_json: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class VoiceSessionOut(BaseModel):
    id: int
    vapi_call_id: str | None
    summary: str | None
    transcript: str | None
    duration_seconds: int | None
    started_at: datetime
    ended_at: datetime | None

    model_config = {"from_attributes": True}


class DecisionCreate(BaseModel):
    title: str
    context: str
    recommendation: str | None = None


class DecisionResolve(BaseModel):
    status: str = Field(pattern="^(approved|rejected|deferred)$")


class DecisionOut(BaseModel):
    id: int
    title: str
    context: str
    recommendation: str | None
    status: str
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    tasks_pending: int
    tasks_in_progress: int
    tasks_completed: int
    decisions_pending: int
    voice_sessions_today: int
    recent_activity_count: int


class BriefingOut(BaseModel):
    greeting: str
    stats: DashboardStats
    pending_tasks: list[TaskOut]
    pending_decisions: list[DecisionOut]
    recent_activity: list[ActivityOut]
