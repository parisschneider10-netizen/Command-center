from datetime import datetime

from pydantic import BaseModel, Field


class BasketHostSignup(BaseModel):
    name: str
    phone: str
    email: str | None = None
    address: str | None = None
    neighborhood: str | None = None
    unit_count: int = Field(default=1, ge=1)


class BasketPrepay(BaseModel):
    host_id: int
    package_sku: str = Field(description="launch_5pack | single_basket | bundle_laundry_intro")
    amount_cents: int | None = None


class BasketLockSpec(BaseModel):
    spec: str | None = None


class BasketHostOut(BaseModel):
    id: int
    name: str
    phone: str
    neighborhood: str | None
    program: str
    status: str
    welcome_basket_credits: int
    prepaid_balance_cents: int
    locked_basket_spec: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
