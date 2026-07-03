from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Decision, Task, TaskPriority, TaskStatus, VoiceSession
from app.schemas import TaskCreate
from app.services import create_task, get_dashboard_stats, log_activity

router = APIRouter(prefix="/voice", tags=["voice-os"])


class VoiceToolResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None


class CreateTaskTool(BaseModel):
    title: str
    description: str | None = None
    priority: str = "normal"


class QueueDecisionTool(BaseModel):
    title: str
    context: str
    recommendation: str | None = None


class UpdateTaskTool(BaseModel):
    task_id: int
    status: str | None = None
    title: str | None = None


class LogNoteTool(BaseModel):
    message: str


@router.post("/tools/create_task", response_model=VoiceToolResponse)
async def tool_create_task(
    body: CreateTaskTool, db: AsyncSession = Depends(get_db)
) -> VoiceToolResponse:
    priority_map = {
        "low": TaskPriority.low,
        "normal": TaskPriority.normal,
        "high": TaskPriority.high,
        "urgent": TaskPriority.urgent,
    }
    task = await create_task(
        db,
        TaskCreate(
            title=body.title,
            description=body.description,
            priority=priority_map.get(body.priority, TaskPriority.normal),
            source="voice",
        ),
    )
    return VoiceToolResponse(
        success=True,
        message=f"Task '{task.title}' created and queued.",
        data={"task_id": task.id, "status": task.status.value},
    )


@router.post("/tools/get_briefing", response_model=VoiceToolResponse)
async def tool_get_briefing(db: AsyncSession = Depends(get_db)) -> VoiceToolResponse:
    stats = await get_dashboard_stats(db)

    tasks_result = await db.execute(
        select(Task)
        .where(Task.status.in_([TaskStatus.pending, TaskStatus.in_progress]))
        .order_by(desc(Task.created_at))
        .limit(5)
    )
    tasks = tasks_result.scalars().all()

    decisions_result = await db.execute(
        select(Decision).where(Decision.status == "pending").limit(5)
    )
    decisions = decisions_result.scalars().all()

    task_lines = [f"- {t.title} ({t.status.value})" for t in tasks]
    decision_lines = [f"- {d.title}" for d in decisions]

    summary = (
        f"You have {stats.tasks_pending} pending tasks, "
        f"{stats.tasks_in_progress} in progress, and "
        f"{stats.decisions_pending} decisions waiting. "
        f"{stats.voice_sessions_today} voice sessions today."
    )
    if task_lines:
        summary += " Active tasks: " + "; ".join(task_lines)
    if decision_lines:
        summary += " Decisions needed: " + "; ".join(decision_lines)

    return VoiceToolResponse(
        success=True,
        message=summary,
        data=stats.model_dump(),
    )


@router.post("/tools/queue_decision", response_model=VoiceToolResponse)
async def tool_queue_decision(
    body: QueueDecisionTool, db: AsyncSession = Depends(get_db)
) -> VoiceToolResponse:
    decision = Decision(
        title=body.title,
        context=body.context,
        recommendation=body.recommendation,
    )
    db.add(decision)
    await db.commit()
    await db.refresh(decision)
    await log_activity(
        db,
        "decision_queued",
        f"Decision queued: {decision.title}",
        {"decision_id": decision.id},
    )
    return VoiceToolResponse(
        success=True,
        message=f"Decision '{decision.title}' queued for your review in the command center.",
        data={"decision_id": decision.id},
    )


@router.post("/tools/update_task", response_model=VoiceToolResponse)
async def tool_update_task(
    body: UpdateTaskTool, db: AsyncSession = Depends(get_db)
) -> VoiceToolResponse:
    task = await db.get(Task, body.task_id)
    if not task:
        return VoiceToolResponse(success=False, message=f"Task {body.task_id} not found.")

    if body.title:
        task.title = body.title
    if body.status:
        try:
            task.status = TaskStatus(body.status)
        except ValueError:
            return VoiceToolResponse(
                success=False,
                message=f"Invalid status '{body.status}'. Use pending, in_progress, completed, blocked, or cancelled.",
            )

    await db.commit()
    await log_activity(
        db,
        "task_updated",
        f"Task updated: {task.title}",
        {"task_id": task.id, "status": task.status.value},
    )
    return VoiceToolResponse(
        success=True,
        message=f"Task '{task.title}' is now {task.status.value}.",
        data={"task_id": task.id, "status": task.status.value},
    )


@router.post("/tools/log_note", response_model=VoiceToolResponse)
async def tool_log_note(
    body: LogNoteTool, db: AsyncSession = Depends(get_db)
) -> VoiceToolResponse:
    await log_activity(db, "voice_note", body.message)
    return VoiceToolResponse(
        success=True,
        message="Note logged to command center.",
    )


@router.get("/tools/schema")
async def tool_schema() -> dict:
    """OpenAPI-style tool definitions for Vapi assistant configuration."""
    return {
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Create a new task or build request for the empire. Use when the commander wants something done, built, researched, or scheduled.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Short task title"},
                            "description": {"type": "string", "description": "Full details of what to do"},
                            "priority": {
                                "type": "string",
                                "enum": ["low", "normal", "high", "urgent"],
                                "description": "Task priority",
                            },
                        },
                        "required": ["title"],
                    },
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/create_task"},
            },
            {
                "type": "function",
                "function": {
                    "name": "get_briefing",
                    "description": "Get a status briefing of the command center — tasks, decisions, activity.",
                    "parameters": {"type": "object", "properties": {}},
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/get_briefing"},
            },
            {
                "type": "function",
                "function": {
                    "name": "queue_decision",
                    "description": "Queue a decision for the commander to review later in the portal when they have internet access.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "context": {"type": "string", "description": "Full context for the decision"},
                            "recommendation": {"type": "string", "description": "Your recommended action"},
                        },
                        "required": ["title", "context"],
                    },
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/queue_decision"},
            },
            {
                "type": "function",
                "function": {
                    "name": "update_task",
                    "description": "Update an existing task status or title.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "integer"},
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "completed", "blocked", "cancelled"],
                            },
                            "title": {"type": "string"},
                        },
                        "required": ["task_id"],
                    },
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/update_task"},
            },
            {
                "type": "function",
                "function": {
                    "name": "log_note",
                    "description": "Log a note, idea, or observation to the command center activity feed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "The note to log"},
                        },
                        "required": ["message"],
                    },
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/log_note"},
            },
        ]
    }
