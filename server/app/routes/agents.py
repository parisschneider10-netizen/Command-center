from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.queue import claim_task, complete_task, get_leaderboard, get_open_tasks
from app.auth import get_current_user
from app.database import get_db
from app.integrations.n8n import trigger_n8n
from app.models import AgentWorker, Task, TaskPriority, TaskStatus
from app.schemas import TaskCreate, TaskOut
from app.schemas_agents import AgentOut, AgentRegister, IssueWillTool, TaskClaimResult
from app.services import create_task, log_activity

router = APIRouter(prefix="/api/agent-queue", tags=["agent-hive"])


async def get_agent_by_key(
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: AsyncSession = Depends(get_db),
) -> AgentWorker:
    """Simple agent auth via name as key for now — use proper tokens in production."""
    result = await db.execute(
        select(AgentWorker).where(
            AgentWorker.name == x_agent_key, AgentWorker.is_active.is_(True)
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=401, detail="Unknown or inactive agent")
    return agent


@router.post("/register", response_model=AgentOut)
async def register_agent(
    body: AgentRegister,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> AgentWorker:
    agent = AgentWorker(
        name=body.name,
        agent_type=body.agent_type,
        capabilities=body.capabilities,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    await log_activity(db, "agent_registered", f"Agent joined hive: {agent.name}")
    return agent


@router.get("/open", response_model=list[TaskOut])
async def open_queue(
    db: AsyncSession = Depends(get_db),
    agent: AgentWorker = Depends(get_agent_by_key),
) -> list[TaskOut]:
    tasks = await get_open_tasks(db)
    return [TaskOut.model_validate(t) for t in tasks]


@router.get("/leaderboard", response_model=list[AgentOut])
async def leaderboard(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[AgentOut]:
    agents = await get_leaderboard(db)
    return [AgentOut.model_validate(a) for a in agents]


@router.post("/{task_id}/claim", response_model=TaskClaimResult)
async def claim(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    agent: AgentWorker = Depends(get_agent_by_key),
) -> TaskClaimResult:
    task = await claim_task(db, task_id, agent)
    if not task:
        return TaskClaimResult(ok=False, message="Task unavailable or already claimed.")
    return TaskClaimResult(ok=True, task_id=task.id, message=f"{agent.name} claimed task.")


@router.post("/{task_id}/complete", response_model=TaskClaimResult)
async def complete(
    task_id: int,
    success: bool = True,
    notes: str | None = None,
    db: AsyncSession = Depends(get_db),
    agent: AgentWorker = Depends(get_agent_by_key),
) -> TaskClaimResult:
    task = await complete_task(db, task_id, agent, success=success, notes=notes)
    if not task:
        return TaskClaimResult(ok=False, message="Task not yours or not found.")
    if not success:
        await trigger_n8n("agent-blocked", {"task_id": task_id, "notes": notes})
    return TaskClaimResult(
        ok=True,
        task_id=task.id,
        message="Completed." if success else "Released to queue.",
    )
