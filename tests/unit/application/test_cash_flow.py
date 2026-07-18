"""Unit tests for chart-ready cash-flow aggregation and history seeding."""

from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.modules.transactions.application.dto import (
    CashFlowInterval,
    GetCashFlowQuery,
)
from app.modules.transactions.application.use_cases.get_cash_flow import GetCashFlow
from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.enums import TransactionType
from app.modules.transactions.domain.exceptions import InvalidCashFlowRangeError
from app.modules.transactions.presentation.router import get_cash_flow
from scripts.seed_data import _ensure_transaction_history, _history_items

USER_ID = "507f1f77bcf86cd799439011"
ACCOUNT_ID = "507f1f77bcf86cd799439012"
INCOME_CATEGORY_ID = "507f1f77bcf86cd799439013"
EXPENSE_CATEGORY_ID = "507f1f77bcf86cd799439014"


class FakeCashFlowRepository:
    """In-memory transaction repository for chart queries."""

    def __init__(self, values: list[Transaction]) -> None:
        """Initialize repository values."""
        self.values = values

    async def list_in_range(
        self,
        user_id: str,
        currency: str,
        occurred_from: datetime,
        occurred_before: datetime,
    ) -> list[Transaction]:
        """Return owned entries within the requested range."""
        return [
            value
            for value in self.values
            if value.user_id == user_id
            and value.currency.code == currency
            and occurred_from <= value.occurred_at < occurred_before
        ]

    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        """Retrieve an entry by identifier."""
        return next(
            (value for value in self.values if value.id == transaction_id),
            None,
        )


def movement(
    transaction_id: str,
    transaction_type: TransactionType,
    amount: str,
    occurred_at: datetime,
    reversal_of_id: str | None = None,
) -> Transaction:
    """Build a persisted ledger fixture."""
    value = Transaction.create(
        user_id=USER_ID,
        account_id=ACCOUNT_ID,
        transaction_type=transaction_type,
        amount=Decimal(amount),
        currency="COP",
        occurred_at=occurred_at,
        reversal_of_id=reversal_of_id,
    )
    return replace(value, id=transaction_id)


@pytest.mark.asyncio
async def test_cash_flow_returns_zero_filled_daily_series_and_reversals() -> None:
    """Aggregate daily values and subtract a compensating expense reversal."""
    income_id = "507f1f77bcf86cd799439021"
    expense_id = "507f1f77bcf86cd799439022"
    values = [
        movement(
            income_id,
            TransactionType.INCOME,
            "100",
            datetime(2026, 7, 1, 12, tzinfo=UTC),
        ),
        movement(
            expense_id,
            TransactionType.EXPENSE,
            "40",
            datetime(2026, 7, 2, 12, tzinfo=UTC),
        ),
        movement(
            "507f1f77bcf86cd799439023",
            TransactionType.REVERSAL,
            "40",
            datetime(2026, 7, 3, 12, tzinfo=UTC),
            reversal_of_id=expense_id,
        ),
    ]
    result = await GetCashFlow(FakeCashFlowRepository(values)).execute(
        GetCashFlowQuery(
            user_id=USER_ID,
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 4),
        )
    )

    assert len(result.points) == 4
    assert result.points[-1].period == "2026-07-04"
    assert result.total_income == Decimal("100")
    assert result.total_expense == Decimal("0")
    assert result.net == Decimal("100")


@pytest.mark.asyncio
async def test_cash_flow_supports_monthly_buckets_and_http_mapping() -> None:
    """Return a chart response grouped into continuous monthly buckets."""
    values = [
        movement(
            "507f1f77bcf86cd799439024",
            TransactionType.INCOME,
            "300",
            datetime(2026, 6, 15, 12, tzinfo=UTC),
        ),
        movement(
            "507f1f77bcf86cd799439025",
            TransactionType.EXPENSE,
            "75",
            datetime(2026, 7, 5, 12, tzinfo=UTC),
        ),
    ]
    response = await get_cash_flow(
        current_user=SimpleNamespace(id=USER_ID),
        use_case=GetCashFlow(FakeCashFlowRepository(values)),
        date_from=date(2026, 6, 1),
        date_to=date(2026, 8, 31),
        currency="cop",
        interval=CashFlowInterval.MONTH,
    )

    assert [point.period for point in response.points] == [
        "2026-06",
        "2026-07",
        "2026-08",
    ]
    assert response.currency == "COP"
    assert response.net == Decimal("225")


@pytest.mark.asyncio
async def test_cash_flow_rejects_invalid_date_range() -> None:
    """Reject reversed chart date ranges before querying persistence."""
    with pytest.raises(InvalidCashFlowRangeError):
        await GetCashFlow(FakeCashFlowRepository([])).execute(
            GetCashFlowQuery(
                user_id=USER_ID,
                date_from=date(2026, 7, 2),
                date_to=date(2026, 7, 1),
            )
        )


class FakeSeedTransactionRepository:
    """Track seeded transaction notes in memory."""

    def __init__(self) -> None:
        """Initialize an empty note collection."""
        self.notes: set[str] = set()

    async def get_by_note(self, user_id: str, note: str) -> object | None:
        """Return a marker when the seed note already exists."""
        return object() if note in self.notes else None


class FakeRegisterMovement:
    """Capture seed commands as if they were persisted."""

    def __init__(self, repository: FakeSeedTransactionRepository) -> None:
        """Initialize the fake use case."""
        self.repository = repository

    async def execute(self, command: object) -> None:
        """Persist the command's deterministic seed note."""
        note = getattr(command, "note")
        self.repository.notes.add(note)


@pytest.mark.asyncio
async def test_transaction_history_seed_is_idempotent() -> None:
    """Create eighteen COP movements once and skip them on the next run."""
    repository = FakeSeedTransactionRepository()
    register = FakeRegisterMovement(repository)
    arguments = {
        "user_id": USER_ID,
        "account_id": ACCOUNT_ID,
        "income_category_id": INCOME_CATEGORY_ID,
        "expense_category_id": EXPENSE_CATEGORY_ID,
        "repository": repository,
        "register_income": register,
        "register_expense": register,
    }

    assert len(_history_items()) == 18
    assert await _ensure_transaction_history(**arguments) == 18
    assert await _ensure_transaction_history(**arguments) == 0
