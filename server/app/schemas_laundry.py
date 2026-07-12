from datetime import datetime

from pydantic import BaseModel, Field


class HostSignup(BaseModel):
    name: str
    phone: str
    email: str | None = None
    address: str | None = None
    neighborhood: str | None = None
    unit_count: int = Field(default=1, ge=1)
    offers_luggage_valet: bool = False
    storage_units_available: int = Field(default=0, ge=0)


class GuestRequest(BaseModel):
    pickup_address: str
    guest_phone: str | None = None
    host_id: int | None = None
    service_type: str = "laundry_turn"
    notes: str | None = None


class HostOut(BaseModel):
    id: int
    name: str
    phone: str
    email: str | None
    neighborhood: str | None
    unit_count: int
    status: str
    offers_luggage_valet: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class GuestRequestOut(BaseModel):
    id: int
    host_id: int | None
    guest_phone: str | None
    pickup_address: str
    service_type: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
