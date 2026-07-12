from datetime import datetime

from pydantic import BaseModel, Field


class LeadIn(BaseModel):
    name: str
    phone: str
    email: str | None = None
    address: str | None = None
    zip: str | None = None
    zip_code: str | None = None
    city: str
    crisis_type: str = "Unautomated-STR-Leak"


class LeadOut(BaseModel):
    id: int
    name: str
    phone: str
    email: str | None
    city: str
    crisis_type: str
    status: str
    servury_server_id: str | None
    servury_ip: str | None
    ghl_account_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpansionRunRequest(BaseModel):
    leads: list[LeadIn]
    dry_run: bool | None = None
    wallet_id: int | None = None


class CityLockRequest(BaseModel):
    lead: LeadIn
    dry_run: bool | None = None
    wallet_id: int | None = None


class ExpansionStatus(BaseModel):
    dry_run_default: bool
    max_cities: int
    live_batch_cap: int
    vps_cost_cents: int
    servury_configured: bool
    ghl_configured: bool
