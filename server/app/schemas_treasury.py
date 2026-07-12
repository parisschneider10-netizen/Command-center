from datetime import datetime

from pydantic import BaseModel, Field


class WalletCreate(BaseModel):
    name: str
    agent_id: int | None = None
    daily_limit_cents: int = Field(default=5000, ge=0)


class WalletOut(BaseModel):
    id: int
    agent_id: int | None
    name: str
    balance_cents: int
    daily_limit_cents: int
    daily_spent_cents: int
    currency: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SpendRequest(BaseModel):
    wallet_id: int
    amount_cents: int = Field(gt=0)
    description: str
    counterparty: str | None = None
    a2a_ref: str | None = None


class LedgerOut(BaseModel):
    id: int
    wallet_id: int | None
    amount_cents: int
    direction: str
    description: str
    status: str
    counterparty: str | None
    a2a_ref: str | None
    nuclear_required: bool
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}
