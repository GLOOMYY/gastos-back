"""Unit tests for the financial account domain entity."""

from decimal import Decimal

import pytest

from app.modules.accounts.domain.entities import Account
from app.modules.accounts.domain.exceptions import InvalidAccountAmountError


def test_create_account_sets_opening_and_current_balance() -> None:
    """A new account starts with its supplied initial balance."""
    account = Account.create(
        user_id=" user-1 ",
        account_type_id=" type-1 ",
        name=" Main Account ",
        description=" Daily expenses ",
        initial_balance=Decimal("150.25"),
        currency=" cop ",
    )

    assert account.id is None
    assert account.user_id == "user-1"
    assert account.account_type_id == "type-1"
    assert account.name == "Main Account"
    assert account.normalized_name == "main account"
    assert account.description == "Daily expenses"
    assert account.initial_balance == Decimal("150.25")
    assert account.balance == Decimal("150.25")
    assert account.currency.code == "COP"
    assert account.is_active is True


def test_create_account_allows_negative_initial_balance() -> None:
    """Liability-like accounts may start with a negative balance."""
    account = Account.create(
        user_id="user-1",
        account_type_id="type-1",
        name="Debt",
        initial_balance=Decimal("-500.00"),
        currency="USD",
    )

    assert account.balance == Decimal("-500.00")


def test_debit_allows_balance_to_become_negative() -> None:
    """No global insufficient-balance rule is imposed on accounts."""
    account = Account.create(
        user_id="user-1",
        account_type_id="type-1",
        name="Cash",
        initial_balance=Decimal("10.00"),
        currency="USD",
    )

    account.debit(Decimal("25.00"))
    account.credit(Decimal("5.00"))

    assert account.balance == Decimal("-10.00")


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-1")])
def test_balance_changes_require_positive_amount(amount: Decimal) -> None:
    """Credits and debits use positive Decimal magnitudes."""
    account = Account.create(
        user_id="user-1",
        account_type_id="type-1",
        name="Cash",
        initial_balance=Decimal("0"),
        currency="USD",
    )

    with pytest.raises(InvalidAccountAmountError):
        account.credit(amount)


def test_create_account_rejects_float_balance() -> None:
    """Financial balances cannot enter the domain as floats."""
    with pytest.raises(InvalidAccountAmountError):
        Account.create(
            user_id="user-1",
            account_type_id="type-1",
            name="Cash",
            initial_balance=1.5,  # type: ignore[arg-type]
            currency="USD",
        )
