from pydantic import BaseModel, Field


class KcLeadIn(BaseModel):
    name: str
    phone: str
    email: str | None = None
    address: str | None = None
    neighborhood: str | None = None
    listing_url: str | None = None
    unit_count: int = Field(default=1, ge=1)
    source: str = "ai_scrape"
    package_sku: str = "launch_5pack"
    notes: str | None = None


class KcLeadBatch(BaseModel):
    leads: list[KcLeadIn]


class DispatchCloser(BaseModel):
    dry_run: bool = True
    pay_cents: int = 4500


class CloseSaleAtDoor(BaseModel):
    lead_id: int
    mission_id: int
    host_prepay_cents: int = Field(gt=0)
    package_sku: str = "launch_5pack"
    proof_notes: str
    worker_ref: str
