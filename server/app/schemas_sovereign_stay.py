from pydantic import BaseModel, Field


class OnboardingPresale(BaseModel):
    host_name: str
    property_address: str
    city_grid: str
    worker_ref: str
    proof_notes: str
    dry_run_closer: bool = True


class OptimizationRun(BaseModel):
    current_vacancy_pct: float = Field(ge=0, le=1)


class CheckoutLogistics(BaseModel):
    guest_name: str
    dry_run: bool = True
