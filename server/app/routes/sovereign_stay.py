from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import SovereignHost
from app.schemas_sovereign_stay import (
    CheckoutLogistics,
    CryptoPresale,
    OnboardingPresale,
    OptimizationRun,
)
from app.value_node.sovereign_stay import (
    city_grid_status,
    crypto_receive_brief,
    execute_ai_optimization_engine,
    list_ledger_events,
    matrix_status,
    process_crypto_presale,
    process_onboarding_presale,
    run_simulation,
    trigger_checkout_logistics,
)

router = APIRouter(prefix="/api/sovereign-stay", tags=["sovereign-stay-systems"])


@router.get("/status")
async def get_matrix_status(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """40 cities × 3 units — empire matrix snapshot."""
    return await matrix_status(db)


@router.get("/cities")
async def get_city_grids(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[dict]:
    return await city_grid_status(db)


@router.get("/hosts")
async def list_hosts(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[dict]:
    result = await db.execute(
        select(SovereignHost).order_by(desc(SovereignHost.created_at)).limit(200)
    )
    return [
        {
            "id": h.id,
            "external_id": h.external_id,
            "host_name": h.host_name,
            "property_address": h.property_address,
            "city_grid": h.city_grid,
            "status": h.status,
            "net_float_usd": round(h.net_float_cents / 100, 2),
            "vault_reserve_usd": round(h.vault_reserve_cents / 100, 2),
        }
        for h in result.scalars().all()
    ]


@router.get("/ledger")
async def get_defi_ledger(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[dict]:
    """Append-only audit trail — DB + JSONL on VPS."""
    return await list_ledger_events(db)


@router.get("/crypto/receive")
async def get_crypto_receive(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Closer briefing — bootstrap fuel play 1, then host-paid split."""
    return await crypto_receive_brief(db)


@router.post("/presale")
async def post_presale(
    body: OnboardingPresale,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Layer 1: doorstep presale — $150 in, $30 closer, float locked."""
    result = await process_onboarding_presale(db, **body.model_dump())
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "presale failed"))
    return result


@router.post("/presale-crypto")
async def post_presale_crypto(
    body: CryptoPresale,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Layer 1 crypto — host USDC direct to treasury, closer paid in crypto."""
    result = await process_crypto_presale(db, **body.model_dump())
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "crypto presale failed"))
    return result


@router.post("/hosts/{host_id}/optimize")
async def post_optimize(
    host_id: int,
    body: OptimizationRun,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Layer 2: badge velocity + buyback engine."""
    result = await execute_ai_optimization_engine(
        db, host_id, body.current_vacancy_pct
    )
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error", "not found"))
    return result


@router.post("/hosts/{host_id}/checkout")
async def post_checkout(
    host_id: int,
    body: CheckoutLogistics,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Layer 3: RentAHuman turnover + partner kickback."""
    result = await trigger_checkout_logistics(
        db, host_id, body.guest_name, dry_run=body.dry_run
    )
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error", "not found"))
    return result


@router.post("/simulate")
async def post_simulate(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Run blueprint Day-1 KCMO sandbox simulation."""
    return await run_simulation(db)
