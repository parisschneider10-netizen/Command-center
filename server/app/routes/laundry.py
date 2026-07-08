from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import LaundryGuestRequest, LaundryHost
from app.schemas_laundry import GuestRequest, GuestRequestOut, HostOut, HostSignup
from app.value_node.laundry import create_guest_request, register_host

router = APIRouter(prefix="/api/laundry", tags=["kc-laundry"])


@router.post("/host-signup", response_model=HostOut)
async def host_signup(body: HostSignup, db: AsyncSession = Depends(get_db)) -> HostOut:
    """Public webhook — GHL landing form posts here. No auth (add API key in prod)."""
    host = await register_host(db, body.model_dump())
    return HostOut.model_validate(host)


@router.post("/guest-request", response_model=GuestRequestOut)
async def guest_request(
    body: GuestRequest, db: AsyncSession = Depends(get_db)
) -> GuestRequestOut:
    """Guest QR / SMS flow — triggers RentAHuman via n8n."""
    req = await create_guest_request(db, body.model_dump())
    return GuestRequestOut.model_validate(req)


@router.get("/hosts", response_model=list[HostOut])
async def list_hosts(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[HostOut]:
    result = await db.execute(
        select(LaundryHost).order_by(desc(LaundryHost.created_at)).limit(200)
    )
    return [HostOut.model_validate(h) for h in result.scalars().all()]


@router.get("/requests", response_model=list[GuestRequestOut])
async def list_requests(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[GuestRequestOut]:
    result = await db.execute(
        select(LaundryGuestRequest).order_by(desc(LaundryGuestRequest.created_at)).limit(200)
    )
    return [GuestRequestOut.model_validate(r) for r in result.scalars().all()]
