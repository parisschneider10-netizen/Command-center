from datetime import datetime

from pydantic import BaseModel, Field


class DeployMission(BaseModel):
    mission_type: str = Field(description="host_visit | sticker_post | guerrilla_guest")
    neighborhood: str
    target_address: str | None = None
    host_id: int | None = None
    pay_cents: int | None = None
    dry_run: bool = True


class CompleteMission(BaseModel):
    proof_notes: str
    worker_ref: str
    ledger_id: int | None = None


class HostPayment(BaseModel):
    host_id: int
    amount_cents: int = Field(gt=0)
    description: str = "Host upfront package payment"


class MissionOut(BaseModel):
    id: int
    mission_type: str
    title: str
    neighborhood: str | None
    pay_on_completion_cents: int
    status: str
    rentahuman_bounty_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
