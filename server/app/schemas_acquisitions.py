from datetime import datetime

from pydantic import BaseModel, Field


class AcquisitionCreate(BaseModel):
    category: str
    name: str
    description: str | None = None
    equipment_spec: str | None = None
    target_cost_cents: int = Field(default=0, ge=0)
    priority: int = Field(default=5, ge=1, le=10)
    empire_tier: int = Field(default=1, ge=1, le=5)
    sovereign_required: bool = True
    vendor_candidates: str | None = None
    source_node: str = "manual"


class AcquisitionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    equipment_spec: str | None = None
    target_cost_cents: int | None = Field(default=None, ge=0)
    priority: int | None = Field(default=None, ge=1, le=10)
    empire_tier: int | None = Field(default=None, ge=1, le=5)
    status: str | None = None
    vendor_candidates: str | None = None


class AcquisitionOut(BaseModel):
    id: int
    category: str
    name: str
    description: str | None
    equipment_spec: str | None
    target_cost_cents: int
    funded_cents: int
    status: str
    priority: int
    empire_tier: int
    sovereign_required: bool
    vendor_candidates: str | None
    source_node: str
    created_at: datetime
    updated_at: datetime
    acquired_at: datetime | None

    model_config = {"from_attributes": True}
