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
    tx_hash: str = Field(min_length=16)
    closer_wallet: str = Field(min_length=8, description="Closer USDC wallet for $30 payout")
    worker_ref: str
    amount_cents: int | None = Field(default=None, ge=1)
    proof_notes: str = ""
    dry_run_closer: bool = True
    mission_id: int | None = None


class OptimizationRun(BaseModel):
    current_vacancy_pct: float = Field(ge=0, le=1)


class CheckoutLogistics(BaseModel):
    guest_name: str
    dry_run: bool = True
