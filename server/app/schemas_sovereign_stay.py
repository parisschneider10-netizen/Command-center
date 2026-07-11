from pydantic import BaseModel, Field


class OnboardingPresale(BaseModel):
    host_name: str
    property_address: str
    city_grid: str
    worker_ref: str
    proof_notes: str
    dry_run_closer: bool = True


class CryptoPresale(BaseModel):
    host_name: str
    property_address: str
    city_grid: str
    treasury_tx_hash: str = Field(min_length=16)
    closer_wallet: str = Field(min_length=8)
    worker_ref: str
    closer_tx_hash: str | None = Field(
        default=None,
        description="Required after bootstrap play 1 — host pays closer direct",
    )
    proof_notes: str = ""
    dry_run_closer: bool = True
    mission_id: int | None = None


class OptimizationRun(BaseModel):
    current_vacancy_pct: float = Field(ge=0, le=1)


class CheckoutLogistics(BaseModel):
    guest_name: str
    dry_run: bool = True
