"""HTTP schemas for financial accounts."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CreateAccountRequest(BaseModel):
    """Request to create a financial account."""

    account_type_id: str = Field(min_length=24, max_length=24)
    name: str = Field(min_length=1, max_length=80)
    initial_balance: Decimal = Decimal("0")
    currency: str = Field(min_length=3, max_length=3)
    description: str | None = Field(default=None, max_length=300)


class UpdateAccountRequest(BaseModel):
    """Request to update non-financial account metadata."""

    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=300)


class AccountResponse(BaseModel):
    """Public account representation."""

    id: str
    user_id: str
    account_type_id: str
    name: str
    description: str | None
    initial_balance: Decimal
    balance: Decimal
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
