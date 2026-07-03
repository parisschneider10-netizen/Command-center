"""Agent competition queue — agents race to carry Commander's will."""

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentWorker, Task, TaskStatus
from app.services import log_activity


async def get_open_tasks(db: AsyncSession, limit: int = 50) -> list[Task]:
    result = await db.execute(
        select(Task)
        .where(
            Task.open_for_agents.is_(True),
            Task.status == TaskStatus.pending,
            Task.claimed_by_agent_id.is_(None),
        )
        .order_by(desc(Task.will_priority), desc(Task.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def claim_task(
    db: AsyncSession, task_id: int, agent: AgentWorker
) -> Task | None:
    task = await db.get(Task, task_id)
    if not task or task.claimed_by_agent_id or task.status != TaskStatus.pending:
        return None

    task.claimed_by_agent_id = agent.id
    task.status = TaskStatus.in_progress
    await db.commit()
    await db.refresh(task)
    await log_activity(
        db,
        "agent_claim",
        f"{agent.name} claimed: {task.title}",
        {"task_id": task.id, "agent_id": agent.id},
    )
    return task


async def complete_task(
    db: AsyncSession,
    task_id: int,
    agent: AgentWorker,
    *,
    success: bool = True,
    notes: str | None = None,
) -> Task | None:
    task = await db.get(Task, task_id)
    if not task or task.claimed_by_agent_id != agent.id:
        return None

    if success:
        task.status = TaskStatus.completed
        agent.wins += 1
        agent.score += 2 if task.will_priority >= 8 else 1
    else:
        task.status = TaskStatus.pending
        task.claimed_by_agent_id = None
        task.blocked_reason = notes
        agent.losses += 1
        agent.score = max(0, agent.score - 1)

    await db.commit()
    await db.refresh(task)
    await log_activity(
        db,
        "agent_complete" if success else "agent_failed",
        f"{agent.name} {'completed' if success else 'released'}: {task.title}",
        {"task_id": task.id, "agent_id": agent.id},
    )
    return task


async def get_leaderboard(db: AsyncSession, limit: int = 10) -> list[AgentWorker]:
    result = await db.execute(
        select(AgentWorker)
        .where(AgentWorker.is_active.is_(True))
        .order_by(desc(AgentWorker.score))
        .limit(limit)
    )
    return list(result.scalars().all())
