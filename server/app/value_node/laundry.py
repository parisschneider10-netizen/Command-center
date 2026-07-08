"""KC Laundry play — revenue node on empire infrastructure."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.n8n import trigger_n8n
from app.models import LaundryGuestRequest, LaundryHost
from app.services import log_activity


async def register_host(db: AsyncSession, data: dict) -> LaundryHost:
    host = LaundryHost(
        name=data["name"],
        phone=data["phone"],
        email=data.get("email"),
        address=data.get("address"),
        neighborhood=data.get("neighborhood"),
        unit_count=data.get("unit_count", 1),
        offers_luggage_valet=data.get("offers_luggage_valet", False),
        storage_units_available=data.get("storage_units_available", 0),
        status="lead",
    )
    db.add(host)
    await db.commit()
    await db.refresh(host)
    await log_activity(
        db,
        "laundry_host_signup",
        f"Host lead: {host.name} — {host.neighborhood or 'KC'}",
        {"host_id": host.id},
    )
    await trigger_n8n(
        "laundry-host",
        {
            "host_id": host.id,
            "name": host.name,
            "phone": host.phone,
            "neighborhood": host.neighborhood,
            "units": host.unit_count,
        },
    )
    return host


async def create_guest_request(db: AsyncSession, data: dict) -> LaundryGuestRequest:
    req = LaundryGuestRequest(
        host_id=data.get("host_id"),
        guest_phone=data.get("guest_phone"),
        pickup_address=data["pickup_address"],
        service_type=data.get("service_type", "laundry_turn"),
        notes=data.get("notes"),
        status="requested",
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    await log_activity(
        db,
        "laundry_guest_request",
        f"{req.service_type}: {req.pickup_address[:80]}",
        {"request_id": req.id},
    )
    await trigger_n8n(
        "laundry-guest-request",
        {
            "request_id": req.id,
            "service_type": req.service_type,
            "pickup_address": req.pickup_address,
            "guest_phone": req.guest_phone,
        },
    )
    return req
