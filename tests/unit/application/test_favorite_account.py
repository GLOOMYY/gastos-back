"""Unit tests for selecting a unique favorite account."""

from decimal import Decimal

import pytest

from app.modules.accounts.application.dto import SetFavoriteAccountCommand
from app.modules.accounts.application.use_cases.set_favorite_account import (
    SetFavoriteAccount,
)
from app.modules.accounts.domain.entities import Account
from app.modules.accounts.domain.exceptions import AccountNotFoundError

USER_ID = "user-1"
OTHER_USER_ID = "user-2"


def _account(account_id: str, user_id: str = USER_ID) -> Account:
    """Build one persisted active account."""
    value = Account.create(
        user_id=user_id,
        account_type_id="type-1",
        name=f"Account {account_id}",
        initial_balance=Decimal("100"),
        currency="COP",
    )
    value.id = account_id
    return value


class FakeAccounts:
    """Provide account reads for favorite selection."""

    def __init__(self, values: list[Account]) -> None:
        """Index configured accounts by identifier."""
        self.values = {value.id: value for value in values}

    async def get_by_id(self, account_id: str) -> Account | None:
        """Return one configured account."""
        return self.values.get(account_id)


class FakeFavoriteStore:
    """Simulate the atomic unique-favorite persistence boundary."""

    def __init__(self, values: list[Account]) -> None:
        """Keep the accounts whose state is changed."""
        self.values = values
        self.calls = 0

    async def set_favorite(
        self,
        user_id: str,
        account_id: str,
        is_favorite: bool,
    ) -> Account:
        """Clear the prior favorite and update the selected account."""
        self.calls += 1
        selected = next(value for value in self.values if value.id == account_id)
        if is_favorite:
            for value in self.values:
                if value.user_id == user_id:
                    value.is_favorite = False
        selected.is_favorite = is_favorite
        return selected


@pytest.mark.asyncio
async def test_selecting_favorite_clears_previous_account() -> None:
    """A user retains at most one favorite account."""
    previous = _account("account-1")
    previous.is_favorite = True
    selected = _account("account-2")
    accounts = FakeAccounts([previous, selected])
    store = FakeFavoriteStore([previous, selected])

    result = await SetFavoriteAccount(accounts, store).execute(
        SetFavoriteAccountCommand(USER_ID, "account-2", True)
    )

    assert result.is_favorite is True
    assert previous.is_favorite is False
    assert selected.is_favorite is True


@pytest.mark.asyncio
async def test_favorite_selection_enforces_account_ownership() -> None:
    """A user cannot infer or select another user's account."""
    foreign_account = _account("account-1", OTHER_USER_ID)
    accounts = FakeAccounts([foreign_account])
    store = FakeFavoriteStore([foreign_account])

    with pytest.raises(AccountNotFoundError):
        await SetFavoriteAccount(accounts, store).execute(
            SetFavoriteAccountCommand(USER_ID, "account-1", True)
        )

    assert store.calls == 0
