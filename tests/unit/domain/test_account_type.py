"""Unit tests for the account type domain entity."""

import pytest

from app.modules.account_types.domain.entities import AccountType
from app.modules.account_types.domain.exceptions import (
    InvalidAccountTypeNameError,
    InvalidAccountTypeOwnerError,
)


def test_create_global_account_type() -> None:
    """An account type without an owner is available globally."""
    account_type = AccountType.create(
        name=" Bank Account ",
        description=" Standard bank account ",
    )

    assert account_type.id is None
    assert account_type.user_id is None
    assert account_type.name == "Bank Account"
    assert account_type.normalized_name == "bank account"
    assert account_type.description == "Standard bank account"
    assert account_type.is_global is True
    assert account_type.is_active is True


def test_create_user_owned_account_type() -> None:
    """An account type may belong exclusively to one user."""
    account_type = AccountType.create(
        name="Family fund",
        user_id=" user-1 ",
    )

    assert account_type.user_id == "user-1"
    assert account_type.is_global is False


def test_account_type_can_be_deactivated_and_activated() -> None:
    """Availability changes through explicit entity behavior."""
    account_type = AccountType.create(name="Cash")

    account_type.deactivate()
    assert account_type.is_active is False

    account_type.activate()
    assert account_type.is_active is True


def test_account_type_rejects_blank_name() -> None:
    """Account types require a visible name."""
    with pytest.raises(InvalidAccountTypeNameError):
        AccountType.create(name=" ")


def test_account_type_rejects_blank_user_owner() -> None:
    """A present owner identifier cannot be blank."""
    with pytest.raises(InvalidAccountTypeOwnerError):
        AccountType.create(name="Cash", user_id=" ")
