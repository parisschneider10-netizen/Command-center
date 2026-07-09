from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import LaundryHost
from app.schemas_welcome_basket import (
    BasketHostOut,
    BasketHostSignup,
    BasketLockSpec,
    BasketPrepay,
)
from app.value_node.welcome_basket import (
    fulfill_next_basket,
    launch_cost_summary,
    lock_basket_spec,
    record_package_prepay,
    register_basket_host,
    PACKAGE_SKUS,
)

router = APIRouter(prefix="/api/welcome-basket", tags=["kc-welcome-basket"])


@router.get("/launch-cost")
async def get_launch_cost() -> dict:
    """What you pay out-of-pocket to launch NOW — target zero."""
    return launch_cost_summary()


@router.get("/packages")
async def get_packages() -> dict:
    return {"packages": PACKAGE_SKUS}


@router.post("/host-signup", response_model=BasketHostOut)
async def basket_host_signup(
    body: BasketHostSignup, db: AsyncSession = Depends(get_db)
) -> BasketHostOut:
    host = await register_basket_host(db, body.model_dump())
    return BasketHostOut.model_validate(host)


@router.post("/hosts/{host_id}/lock-spec", response_model=BasketHostOut)
async def post_lock_spec(
    host_id: int,
    body: BasketLockSpec,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> BasketHostOut:
    try:
        host = await lock_basket_spec(db, host_id, body.spec)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return BasketHostOut.model_validate(host)


@router.post("/hosts/{host_id}/prepay")
async def post_prepay(
    host_id: int,
    body: BasketPrepay,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    try:
        return await record_package_prepay(
            db,
            host_id=host_id,
            package_sku=body.package_sku,
            amount_cents=body.amount_cents,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/fulfill/{host_id}")
async def post_fulfill(
    host_id: int,
    dry_run: bool = True,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    """Dispatch 3-person basket crew — shop, assemble, deliver. Pay on completion."""
    try:
        return await fulfill_next_basket(db, host_id, dry_run=dry_run)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/hosts", response_model=list[BasketHostOut])
async def list_basket_hosts(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[BasketHostOut]:
    result = await db.execute(
        select(LaundryHost)
        .where(LaundryHost.program == "welcome_basket")
        .order_by(desc(LaundryHost.created_at))
        .limit(100)
    )
    return [BasketHostOut.model_validate(h) for h in result.scalars().all()]
