from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import GroundForceMission
from app.schemas_ground_force import (
    CompleteMission,
    DeployMission,
    HostPayment,
    MissionOut,
)
from app.treasury.float import float_summary, record_host_payment, release_cleared_holds
from app.value_node.ground_force import complete_mission, deploy_mission

router = APIRouter(prefix="/api/ground-force", tags=["ground-force"])


@router.post("/deploy")
async def ground_force_deploy(
    body: DeployMission,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    return await deploy_mission(db, **body.model_dump())


@router.post("/missions/{mission_id}/complete")
async def mission_complete(
    mission_id: int,
    body: CompleteMission,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    return await complete_mission(
        db,
        mission_id,
        body.proof_notes,
        body.worker_ref,
        body.ledger_id,
    )


@router.get("/missions", response_model=list[MissionOut])
async def list_missions(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[MissionOut]:
    result = await db.execute(
        select(GroundForceMission).order_by(desc(GroundForceMission.created_at)).limit(200)
    )
    return [MissionOut.model_validate(m) for m in result.scalars().all()]


@router.post("/host-payment")
async def host_payment(
    body: HostPayment,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    entry = await record_host_payment(
        db,
        amount_cents=body.amount_cents,
        host_id=body.host_id,
        description=body.description,
    )
    return {
        "ledger_id": entry.id,
        "status": entry.status,
        "release_at": entry.release_at.isoformat() if entry.release_at else None,
        "float_message": "48h fiat window before worker payout",
    }


@router.get("/float")
async def get_float(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    await release_cleared_holds(db)
    return await float_summary(db)
