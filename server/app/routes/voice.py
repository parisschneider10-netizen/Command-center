from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.escalation import create_escalation
from app.integrations.n8n import trigger_n8n
from app.models import Decision, EscalationLevel, Task, TaskPriority, TaskStatus, VoiceSession
from app.schemas import TaskCreate
from app.services import create_task, get_dashboard_stats, log_activity
from app.vault import write_inbox_note

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


class DumpToVaultTool(BaseModel):
    title: str
    body: str


class TriggerWorkflowTool(BaseModel):
    event: str
    payload: dict = Field(default_factory=dict)


class IssueWillTool(BaseModel):
    title: str
    description: str | None = None
    will_priority: int = Field(default=8, ge=1, le=10)


class EscalateToHumanTool(BaseModel):
    title: str
    description: str
    budget: float | None = None


class NuclearEscalationTool(BaseModel):
    title: str
    context: str


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
    will_map = {"low": 3, "normal": 5, "high": 7, "urgent": 9}
    task = await create_task(
        db,
        TaskCreate(
            title=body.title,
            description=body.description,
            priority=priority_map.get(body.priority, TaskPriority.normal),
            source="voice",
            will_priority=will_map.get(body.priority, 5),
        ),
    )
    await trigger_n8n(
        "task-created",
        {"task_id": task.id, "title": task.title, "priority": task.priority.value},
    )
    await trigger_n8n(
        "agent-queue",
        {"task_id": task.id, "title": task.title, "will_priority": task.will_priority},
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
    title = body.message[:80] + ("..." if len(body.message) > 80 else "")
    path = write_inbox_note(title, body.message, source="voice")
    await log_activity(
        db,
        "vault_note_created",
        f"Vault inbox: {path.name}",
        {"path": path.name},
    )
    return VoiceToolResponse(
        success=True,
        message="Note logged to command center and Obsidian vault inbox.",
        data={"vault_file": path.name},
    )


@router.post("/tools/dump_to_vault", response_model=VoiceToolResponse)
async def tool_dump_to_vault(
    body: DumpToVaultTool, db: AsyncSession = Depends(get_db)
) -> VoiceToolResponse:
    path = write_inbox_note(body.title, body.body, source="voice")
    await log_activity(
        db,
        "vault_note_created",
        f"Vault dump: {body.title}",
        {"path": path.name},
    )
    await trigger_n8n(
        "vault-inbox",
        {"title": body.title, "path": path.name, "folder": "inbox"},
    )
    return VoiceToolResponse(
        success=True,
        message=f"Dumped to Obsidian vault inbox as {path.name}.",
        data={"vault_file": path.name},
    )


@router.post("/tools/trigger_workflow", response_model=VoiceToolResponse)
async def tool_trigger_workflow(
    body: TriggerWorkflowTool, db: AsyncSession = Depends(get_db)
) -> VoiceToolResponse:
    result = await trigger_n8n(body.event, body.payload)
    await log_activity(
        db,
        "n8n_trigger",
        f"Workflow triggered: {body.event}",
        {"event": body.event, "result": result},
    )
    if result.get("triggered"):
        return VoiceToolResponse(
            success=True,
            message=f"Workflow '{body.event}' triggered.",
            data=result,
        )
    return VoiceToolResponse(
        success=False,
        message=f"Could not trigger workflow '{body.event}'. {result.get('reason') or result.get('error', 'Unknown error')}",
        data=result,
    )


@router.post("/tools/issue_will", response_model=VoiceToolResponse)
async def tool_issue_will(
    body: IssueWillTool, db: AsyncSession = Depends(get_db)
) -> VoiceToolResponse:
    """Commander's will — high priority task for competing agents."""
    task = await create_task(
        db,
        TaskCreate(
            title=body.title,
            description=body.description,
            priority=TaskPriority.urgent,
            source="will",
            will_priority=body.will_priority,
            open_for_agents=True,
        ),
    )
    await trigger_n8n(
        "agent-queue",
        {"task_id": task.id, "title": task.title, "will_priority": task.will_priority, "will": True},
    )
    return VoiceToolResponse(
        success=True,
        message=f"Will issued. Priority {task.will_priority}. Agents competing.",
        data={"task_id": task.id, "will_priority": task.will_priority},
    )


@router.post("/tools/escalate_to_human", response_model=VoiceToolResponse)
async def tool_escalate_to_human(
    body: EscalateToHumanTool, db: AsyncSession = Depends(get_db)
) -> VoiceToolResponse:
    escalation = await create_escalation(
        db,
        title=body.title,
        description=body.description,
        level=EscalationLevel.human,
        budget=body.budget,
        nuclear_flag=False,
        source="voice",
    )
    if escalation.level == EscalationLevel.commander:
        return VoiceToolResponse(
            success=True,
            message="Over budget. Queued for Commander review. Not calling.",
            data={"escalation_id": escalation.id, "level": "commander"},
        )
    await trigger_n8n(
        "human-escalation",
        {"escalation_id": escalation.id, "title": body.title},
    )
    return VoiceToolResponse(
        success=True,
        message="Human layer engaged. Commander not notified.",
        data={"escalation_id": escalation.id, "level": "human"},
    )


@router.post("/tools/nuclear_escalation", response_model=VoiceToolResponse)
async def tool_nuclear_escalation(
    body: NuclearEscalationTool, db: AsyncSession = Depends(get_db)
) -> VoiceToolResponse:
    escalation = await create_escalation(
        db,
        title=body.title,
        description=body.context,
        level=EscalationLevel.commander,
        nuclear_flag=True,
        source="voice",
    )
    decision = Decision(
        title=f"NUCLEAR: {body.title}",
        context=body.context,
        recommendation="Commander decision required — last resort escalation.",
    )
    db.add(decision)
    await db.commit()
    return VoiceToolResponse(
        success=True,
        message="Nuclear flag set. Queued for Commander portal review.",
        data={"escalation_id": escalation.id, "level": "commander"},
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
                    "description": "Log a note or idea. Saves to command center AND Obsidian vault inbox for agent processing.",
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
            {
                "type": "function",
                "function": {
                    "name": "dump_to_vault",
                    "description": "Dump a structured note to the Obsidian vault inbox with a title and body. Use for longer captures, research dumps, or brain dumps.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string", "description": "Full note content"},
                        },
                        "required": ["title", "body"],
                    },
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/dump_to_vault"},
            },
            {
                "type": "function",
                "function": {
                    "name": "trigger_workflow",
                    "description": "Trigger an n8n automation workflow by event name. Use for starting research, processing queues, or custom automations.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "event": {"type": "string", "description": "Workflow event name, e.g. task-created, vault-inbox, research"},
                            "payload": {"type": "object", "description": "Optional data to pass to the workflow"},
                        },
                        "required": ["event"],
                    },
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/trigger_workflow"},
            },
            {
                "type": "function",
                "function": {
                    "name": "escalate_to_human",
                    "description": "Escalate to human layer (guardians or RentAHuman). Commander is NOT notified. Use when agents cannot handle.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "budget": {"type": "number", "description": "Max budget in USD"},
                        },
                        "required": ["title", "description"],
                    },
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/escalate_to_human"},
            },
            {
                "type": "function",
                "function": {
                    "name": "nuclear_escalation",
                    "description": "LAST RESORT ONLY. Queue decision for Commander. Use only for legal, large money, or explicit Commander request.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "context": {"type": "string"},
                        },
                        "required": ["title", "context"],
                    },
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/nuclear_escalation"},
            },
        ]
    }
