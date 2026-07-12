import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import ActivityLog, Decision, Task, TaskStatus, VoiceSession
from app.schemas import (
    ActivityOut,
    BriefingOut,
    DashboardStats,
    DecisionOut,
    TaskOut,
    VoiceSessionOut,
)
from app.services import get_dashboard_stats

router = APIRouter(prefix="/api", tags=["portal"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> DashboardStats:
    return await get_dashboard_stats(db)


@router.get("/briefing", response_model=BriefingOut)
async def briefing(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> BriefingOut:
    stats = await get_dashboard_stats(db)

    tasks_result = await db.execute(
        select(Task)
        .where(Task.status.in_([TaskStatus.pending, TaskStatus.in_progress]))
        .order_by(desc(Task.created_at))
        .limit(10)
    )
    pending_tasks = list(tasks_result.scalars().all())

    decisions_result = await db.execute(
        select(Decision)
        .where(Decision.status == "pending")
        .order_by(desc(Decision.created_at))
        .limit(10)
    )
    pending_decisions = list(decisions_result.scalars().all())

    activity_result = await db.execute(
        select(ActivityLog).order_by(desc(ActivityLog.created_at)).limit(20)
    )
    recent_activity = list(activity_result.scalars().all())

    hour = datetime.now(timezone.utc).hour
    if hour < 12:
        greeting = "Good morning, Commander."
    elif hour < 17:
        greeting = "Good afternoon, Commander."
    else:
        greeting = "Good evening, Commander."

    return BriefingOut(
        greeting=greeting,
        stats=stats,
        pending_tasks=[TaskOut.model_validate(t) for t in pending_tasks],
        pending_decisions=[DecisionOut.model_validate(d) for d in pending_decisions],
        recent_activity=[ActivityOut.model_validate(a) for a in recent_activity],
    )


@router.get("/tasks", response_model=list[TaskOut])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[TaskOut]:
    result = await db.execute(select(Task).order_by(desc(Task.created_at)).limit(100))
    return [TaskOut.model_validate(t) for t in result.scalars().all()]


@router.get("/activity", response_model=list[ActivityOut])
async def list_activity(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[ActivityOut]:
    result = await db.execute(
        select(ActivityLog).order_by(desc(ActivityLog.created_at)).limit(100)
    )
    return [ActivityOut.model_validate(a) for a in result.scalars().all()]


@router.get("/voice-sessions", response_model=list[VoiceSessionOut])
async def list_voice_sessions(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[VoiceSessionOut]:
    result = await db.execute(
        select(VoiceSession).order_by(desc(VoiceSession.started_at)).limit(50)
    )
    return [VoiceSessionOut.model_validate(v) for v in result.scalars().all()]


@router.get("/decisions", response_model=list[DecisionOut])
async def list_decisions(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[DecisionOut]:
    result = await db.execute(
        select(Decision).order_by(desc(Decision.created_at)).limit(50)
    )
    return [DecisionOut.model_validate(d) for d in result.scalars().all()]
