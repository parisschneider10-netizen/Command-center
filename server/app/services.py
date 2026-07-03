import json
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActivityLog, Decision, Task, TaskStatus, VoiceSession
from app.schemas import DashboardStats, TaskCreate


async def log_activity(
    db: AsyncSession,
    event_type: str,
    message: str,
    metadata: dict | None = None,
) -> ActivityLog:
    entry = ActivityLog(
        event_type=event_type,
        message=message,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def create_task(db: AsyncSession, payload: TaskCreate) -> Task:
    task = Task(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        source=payload.source,
        will_priority=payload.will_priority,
        open_for_agents=payload.open_for_agents,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    await log_activity(
        db,
        "task_created",
        f"Task created: {task.title}",
        {"task_id": task.id, "source": task.source},
    )
    return task


async def get_dashboard_stats(db: AsyncSession) -> DashboardStats:
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    pending = await db.scalar(
        select(func.count()).select_from(Task).where(Task.status == TaskStatus.pending)
    )
    in_progress = await db.scalar(
        select(func.count())
        .select_from(Task)
        .where(Task.status == TaskStatus.in_progress)
    )
    completed = await db.scalar(
        select(func.count())
        .select_from(Task)
        .where(Task.status == TaskStatus.completed)
    )
    decisions_pending = await db.scalar(
        select(func.count()).select_from(Decision).where(Decision.status == "pending")
    )
    voice_today = await db.scalar(
        select(func.count())
        .select_from(VoiceSession)
        .where(VoiceSession.started_at >= today_start)
    )
    recent_activity = await db.scalar(select(func.count()).select_from(ActivityLog))

    return DashboardStats(
        tasks_pending=pending or 0,
        tasks_in_progress=in_progress or 0,
        tasks_completed=completed or 0,
        decisions_pending=decisions_pending or 0,
        voice_sessions_today=voice_today or 0,
        recent_activity_count=recent_activity or 0,
    )
