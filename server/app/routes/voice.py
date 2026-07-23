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


class LockCityNodeTool(BaseModel):
    name: str
    phone: str
    city: str
    email: str | None = None
    address: str | None = None
    zip: str | None = None
    dry_run: bool = True


class AddAcquisitionNeedTool(BaseModel):
    category: str
    name: str
    description: str | None = None
    equipment_spec: str | None = None
    target_cost_cents: int = Field(default=0, ge=0)
    priority: int = Field(default=7, ge=1, le=10)
    empire_tier: int = Field(default=1, ge=1, le=5)


class StateIntentTool(BaseModel):
    intent: str = Field(min_length=3)
    auto_execute: bool = False


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
        f"{stats.uncertainty_pending} uncertainty reviews need you. "
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
    from app.escalation import route_to_human_firewall

    route = await route_to_human_firewall(db, escalation, budget=body.budget)
    await trigger_n8n(
        "human-escalation",
        {"escalation_id": escalation.id, "title": body.title, **route},
    )
    routed = route.get("routed", "firewall")
    if routed == "guardian":
        msg = f"Firewall: {route.get('guardian')}. Commander not notified."
    elif routed == "rentahuman":
        msg = "Human firewall bounty posted. Commander not notified."
    else:
        msg = "Queued in human firewall. Commander not notified."
    return VoiceToolResponse(
        success=True,
        message=msg,
        data={"escalation_id": escalation.id, "level": "human", **route},
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


@router.post("/tools/lock_city_node", response_model=VoiceToolResponse)
async def tool_lock_city_node(
    body: LockCityNodeTool, db: AsyncSession = Depends(get_db)
) -> VoiceToolResponse:
    from app.value_node.expansion import execute_city_lock

    lead = {
        "name": body.name,
        "phone": body.phone,
        "city": body.city,
        "email": body.email,
        "address": body.address,
        "zip": body.zip,
    }
    result = await execute_city_lock(db, lead, dry_run=body.dry_run)
    if result.get("success"):
        msg = f"City node locked: {body.city}."
        if result.get("dry_run"):
            msg = f"Dry run OK: {body.city}. Set live in env to deploy."
        return VoiceToolResponse(success=True, message=msg, data=result)
    return VoiceToolResponse(
        success=False,
        message=f"Node lock failed: {body.city}.",
        data=result,
    )


@router.post("/tools/get_acquisition_briefing", response_model=VoiceToolResponse)
async def tool_get_acquisition_briefing(
    db: AsyncSession = Depends(get_db),
) -> VoiceToolResponse:
    """Ammo pools, top sovereign acquisition priorities, funded-ready items."""
    from app.treasury.capability import capability_snapshot

    snap = await capability_snapshot(db)
    return VoiceToolResponse(
        success=True,
        message=snap["voice_summary"],
        data=snap,
    )


@router.post("/tools/add_acquisition_need", response_model=VoiceToolResponse)
async def tool_add_acquisition_need(
    body: AddAcquisitionNeedTool, db: AsyncSession = Depends(get_db)
) -> VoiceToolResponse:
    """Add sovereign equipment or infrastructure to the acquisition manifest."""
    from app.treasury.acquisitions import create_acquisition, sync_manifest_to_vault
    from app.treasury.categories import ACQUISITION_CATEGORIES

    if body.category not in ACQUISITION_CATEGORIES:
        return VoiceToolResponse(
            success=False,
            message=f"Unknown category {body.category}. Valid: {', '.join(ACQUISITION_CATEGORIES)}.",
        )
    acq = await create_acquisition(
        db,
        category=body.category,
        name=body.name,
        description=body.description,
        equipment_spec=body.equipment_spec,
        target_cost_cents=body.target_cost_cents,
        priority=body.priority,
        empire_tier=body.empire_tier,
        source_node="voice",
    )
    await sync_manifest_to_vault(db)
    return VoiceToolResponse(
        success=True,
        message=f"Added to sovereign manifest: {acq.name} ({acq.category}).",
        data={"acquisition_id": acq.id, "status": acq.status},
    )


@router.post("/tools/get_bridge_status", response_model=VoiceToolResponse)
async def tool_get_bridge_status() -> VoiceToolResponse:
    """How to reach the hive — GitHub, voice, email commands. Use when Commander asks how to contact or command builds."""
    from app.comms.email import comms_configured
    from app.config import settings

    lines = [
        "Primary bridge: GitHub Issue with @cursor — works from phone now, no VPS needed.",
    ]
    if settings.public_base_url and "localhost" not in settings.public_base_url:
        lines.append("Voice SARA and command deck portal are configured.")
    else:
        lines.append("Voice and portal need VPS deploy — use GitHub until then.")
    if comms_configured():
        lines.append("Email commands live — send [BUILD] subject to commander mail.")
    else:
        lines.append("Email commands need sovereign mail in dot env — not Gmail to Cursor.")
    lines.append("Do not connect Gmail to Cursor. Forward to commander mail or use GitHub.")
    return VoiceToolResponse(
        success=True,
        message=" ".join(lines),
        data={
            "github_primary": True,
            "voice_live": bool(settings.public_base_url),
            "email_commands": comms_configured(),
            "gmail_to_cursor": False,
            "doc": "docs/COMMUNICATION_BRIDGE.md",
        },
    )


@router.post("/tools/state_intent", response_model=VoiceToolResponse)
async def tool_state_intent(
    body: StateIntentTool, db: AsyncSession = Depends(get_db)
) -> VoiceToolResponse:
    """
    Commander states intent → plan + direction + human life force from treasury.
  Optional auto_execute posts RentAHuman micro-tasks and queues hive.
    """
    from app.intent.engine import execute_intent, intent_briefing, plan_intent
    from app.velocity import should_auto_execute_intent

    intent = await plan_intent(db, intent_text=body.intent, source="voice")
    briefing = await intent_briefing(db, intent.id)
    direction = briefing.get("direction", "")
    treasury = briefing.get("treasury", {})
    human = treasury.get("human_life_force", {})
    msg = direction
    if human.get("voice_summary"):
        msg += " " + human["voice_summary"]
    if should_auto_execute_intent(body.intent, body.auto_execute):
        ex = await execute_intent(db, intent.id)
        msg += f" Executing: {len(ex.get('outcomes', []))} micro-tasks queued."
    return VoiceToolResponse(
        success=True,
        message=msg,
        data={**briefing, "intent_id": intent.id},
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
            {
                "type": "function",
                "function": {
                    "name": "get_acquisition_briefing",
                    "description": "Get what the empire can afford NOW — ammo, float, ready-to-order items, closest unlocks, capability gaps. Use when Commander asks what we can buy, afford, or unlock at current capacity.",
                    "parameters": {"type": "object", "properties": {}},
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/get_acquisition_briefing"},
            },
            {
                "type": "function",
                "function": {
                    "name": "add_acquisition_need",
                    "description": "Add sovereign equipment or physical infrastructure to the acquisition manifest. Categories: compute, network, storage, comms, voice, security, physical_ops, energy.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "equipment_spec": {"type": "string", "description": "State-of-the-art sovereign options to research"},
                            "target_cost_cents": {"type": "integer"},
                            "priority": {"type": "integer", "description": "1-10, higher = more urgent"},
                            "empire_tier": {"type": "integer", "description": "1=startup through 5=full sovereign"},
                        },
                        "required": ["category", "name"],
                    },
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/add_acquisition_need"},
            },
            {
                "type": "function",
                "function": {
                    "name": "get_bridge_status",
                    "description": "How to command the empire from work — GitHub Issues, voice, email. Use when Commander asks how to reach agents, connect Gmail, or build before command deck is online.",
                    "parameters": {"type": "object", "properties": {}},
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/get_bridge_status"},
            },
            {
                "type": "function",
                "function": {
                    "name": "state_intent",
                    "description": "Commander states intent/goal. Returns plan, direction, treasury human life force capacity, micro-tasks. Set auto_execute true to auto-post RentAHuman gigs and queue hive without Commander pressing buttons.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "intent": {"type": "string", "description": "What you want, e.g. deploy command deck, start KC laundry play"},
                            "auto_execute": {"type": "boolean", "description": "If true, hive + human firewall execute immediately"},
                        },
                        "required": ["intent"],
                    },
                },
                "server": {"url": "{{PUBLIC_BASE_URL}}/voice/tools/state_intent"},
            },
        ]
    }
