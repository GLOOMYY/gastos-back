"""Select or clear the authenticated user's favorite account."""

from app.modules.accounts.application.dto import (
    AccountResult,
    SetFavoriteAccountCommand,
)
from app.modules.accounts.application.ports import FavoriteAccountStore
from app.modules.accounts.application.use_cases.get_account import to_result
from app.modules.accounts.domain.exceptions import (
    AccountNotFoundError,
    InactiveAccountError,
)
from app.modules.accounts.domain.repositories import AccountRepository


class SetFavoriteAccount:
    """Maintain at most one active favorite account for a user."""

    def __init__(
        self,
        accounts: AccountRepository,
        store: FavoriteAccountStore,
    ) -> None:
        """Initialize account reads and atomic favorite persistence."""
        self._accounts = accounts
        self._store = store

    async def execute(
        self,
        command: SetFavoriteAccountCommand,
    ) -> AccountResult:
        """Validate ownership and update favorite state atomically."""
        account = await self._accounts.get_by_id(command.account_id)
        if account is None or account.user_id != command.user_id:
            raise AccountNotFoundError()
        if not account.is_active:
            raise InactiveAccountError()
        updated = await self._store.set_favorite(
            command.user_id,
            command.account_id,
            command.is_favorite,
        )
        return to_result(updated)
