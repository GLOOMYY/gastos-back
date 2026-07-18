"""Unit tests for the financial transaction domain entity."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.enums import (
    TransactionStatus,
    TransactionType,
)
from app.modules.transactions.domain.exceptions import (
    InvalidTransactionAmountError,
    InvalidTransactionDateError,
    InvalidTransactionIdentifierError,
)


def test_create_confirmed_transaction() -> None:
    """A valid movement becomes a normalized immutable ledger entry."""
    occurred_at = datetime(2026, 7, 17, 12, 30, tzinfo=UTC)

    transaction = Transaction.create(
        user_id=" user-1 ",
        account_id=" account-1 ",
        category_id=" category-1 ",
        transaction_type=TransactionType.EXPENSE,
        amount=Decimal("25.50"),
        currency=" cop ",
        occurred_at=occurred_at,
        description=" Lunch ",
        note=" With the team ",
    )

    assert transaction.id is None
    assert transaction.user_id == "user-1"
    assert transaction.account_id == "account-1"
    assert transaction.category_id == "category-1"
    assert transaction.amount == Decimal("25.50")
    assert transaction.currency.code == "COP"
    assert transaction.occurred_at == occurred_at
    assert transaction.description == "Lunch"
    assert transaction.note == "With the team"
    assert transaction.status is TransactionStatus.CONFIRMED


def test_confirmed_transaction_is_immutable() -> None:
    """Confirmed ledger entries cannot be edited in place."""
    transaction = Transaction.create(
        user_id="user-1",
        account_id="account-1",
        transaction_type=TransactionType.INCOME,
        amount=Decimal("100"),
        currency="USD",
        occurred_at=datetime.now(UTC),
    )

    with pytest.raises(FrozenInstanceError):
        transaction.amount = Decimal("200")  # type: ignore[misc]


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-1")])
def test_transaction_requires_positive_amount(amount: Decimal) -> None:
    """Ledger amounts use a positive magnitude."""
    with pytest.raises(InvalidTransactionAmountError):
        Transaction.create(
            user_id="user-1",
            account_id="account-1",
            transaction_type=TransactionType.EXPENSE,
            amount=amount,
            currency="USD",
            occurred_at=datetime.now(UTC),
        )


def test_transaction_rejects_float_amount() -> None:
    """Financial movements cannot enter the domain as floats."""
    with pytest.raises(InvalidTransactionAmountError):
        Transaction.create(
            user_id="user-1",
            account_id="account-1",
            transaction_type=TransactionType.EXPENSE,
            amount=10.5,  # type: ignore[arg-type]
            currency="USD",
            occurred_at=datetime.now(UTC),
        )


def test_transaction_rejects_naive_occurrence_date() -> None:
    """Movement dates must identify an absolute point in time."""
    with pytest.raises(InvalidTransactionDateError):
        Transaction.create(
            user_id="user-1",
            account_id="account-1",
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("10"),
            currency="USD",
            occurred_at=datetime(2026, 7, 17, 12, 30),
        )


def test_transaction_rejects_blank_required_identifier() -> None:
    """A transaction must reference an owner and account."""
    with pytest.raises(InvalidTransactionIdentifierError):
        Transaction.create(
            user_id=" ",
            account_id="account-1",
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("10"),
            currency="USD",
            occurred_at=datetime.now(UTC),
        )
