from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.doctor.empire_doctor import doctor_scan, doctor_status

router = APIRouter(prefix="/api/doctor", tags=["empire-doctor"])


@router.get("/status")
async def get_doctor_status(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Preventive snapshot — warp speed clear or not."""
    return await doctor_status(db)


@router.post("/scan")
async def post_doctor_scan(
    auto_repair: bool = True,
    escalate_on_critical: bool = True,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """
    Full doctor pass — auto-repair + human firewall escalation on critical.
    Wire n8n cron: POST /api/doctor/scan every 5 minutes.
    """
    return await doctor_scan(
        db, auto_repair=auto_repair, escalate_on_critical=escalate_on_critical
    )
