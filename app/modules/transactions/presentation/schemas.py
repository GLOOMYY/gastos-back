"""HTTP schemas for immutable financial transactions."""

from datetime import datetime
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.transactions.domain.enums import TransactionType
from app.modules.transactions.application.dto import CashFlowInterval


class RegisterTransactionRequest(BaseModel):
    """Request to register an income or expense."""

    account_id: str = Field(min_length=24, max_length=24)
    category_id: str = Field(min_length=24, max_length=24)
    amount: Decimal = Field(gt=0)
    occurred_at: datetime
    description: str | None = Field(default=None, max_length=300)
    note: str | None = Field(default=None, max_length=500)


class ReverseTransactionRequest(BaseModel):
    """Request to append a compensating ledger entry."""

    reason: str = Field(min_length=1, max_length=300)


class TransactionResponse(BaseModel):
    """Public immutable ledger representation."""

    id: str
    user_id: str
    account_id: str
    category_id: str | None
    transaction_type: TransactionType
    amount: Decimal
    currency: str
    occurred_at: datetime
    description: str | None
    note: str | None
    reversal_of_id: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionPageResponse(BaseModel):
    """Cursor-paginated transaction response."""

    items: list[TransactionResponse]
    next_cursor: str | None
    has_more: bool

    model_config = ConfigDict(from_attributes=True)


class CashFlowPointResponse(BaseModel):
    """One chart-ready income and expense bucket."""

    period: str
    income: Decimal
    expense: Decimal
    net: Decimal

    model_config = ConfigDict(from_attributes=True)


class CashFlowResponse(BaseModel):
    """Cash-flow chart series with aggregate totals."""

    currency: str
    interval: CashFlowInterval
    date_from: date
    date_to: date
    points: list[CashFlowPointResponse]
    total_income: Decimal
    total_expense: Decimal
    net: Decimal

    model_config = ConfigDict(from_attributes=True)
