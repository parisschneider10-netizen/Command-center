from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.hive.empire_research import list_research_tasks

router = APIRouter(prefix="/api/hive", tags=["hive"])


@router.get("/research")
async def get_research_queue(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[dict]:
    """Research tasks auto-queued when treasury fuel arrives."""
    return await list_research_tasks(db)
