"""Deactivate an owned financial account."""

from app.modules.accounts.domain.exceptions import AccountNotFoundError
from app.modules.accounts.domain.repositories import AccountRepository


class CloseAccount:
    """Soft-delete an account while retaining its financial history."""

    def __init__(self, repository: AccountRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, user_id: str, account_id: str) -> None:
        """Deactivate an account owned by the current user."""
        account = await self._repository.get_by_id(account_id)
        if account is None or account.user_id != user_id:
            raise AccountNotFoundError()
        account.deactivate()
        await self._repository.update(account)
