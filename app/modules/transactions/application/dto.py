"""Application DTOs for immutable ledger operations."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from app.modules.transactions.domain.enums import TransactionType


@dataclass(frozen=True, slots=True)
class RegisterTransactionCommand:
    """Input for registering an income or expense."""

    user_id: str
    account_id: str
    category_id: str
    amount: Decimal
    occurred_at: datetime
    description: str | None = None
    note: str | None = None


@dataclass(frozen=True, slots=True)
class ReverseTransactionCommand:
    """Input for reversing a confirmed ledger entry."""

    user_id: str
    transaction_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class TransactionResult:
    """Ledger entry returned to presentation."""

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


@dataclass(frozen=True, slots=True)
class TransactionPageResult:
    """Cursor page of immutable ledger entries."""

    items: list[TransactionResult]
    next_cursor: str | None
    has_more: bool


class CashFlowInterval(StrEnum):
    """Supported time buckets for cash-flow charts."""

    DAY = "day"
    MONTH = "month"


@dataclass(frozen=True, slots=True)
class GetCashFlowQuery:
    """Input for an authenticated cash-flow chart query."""

    user_id: str
    date_from: date
    date_to: date
    currency: str = "COP"
    interval: CashFlowInterval = CashFlowInterval.DAY


@dataclass(frozen=True, slots=True)
class CashFlowPoint:
    """Income, expense, and net values for one chart bucket."""

    period: str
    income: Decimal
    expense: Decimal
    net: Decimal


@dataclass(frozen=True, slots=True)
class CashFlowResult:
    """Chart-ready cash-flow series and totals."""

    currency: str
    interval: CashFlowInterval
    date_from: date
    date_to: date
    points: list[CashFlowPoint]
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
