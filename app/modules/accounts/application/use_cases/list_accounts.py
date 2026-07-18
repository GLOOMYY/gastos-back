"""List financial accounts owned by a user."""

from app.modules.accounts.application.dto import AccountResult
from app.modules.accounts.application.use_cases.get_account import to_result
from app.modules.accounts.domain.repositories import AccountRepository


class ListAccounts:
    """List the authenticated user's accounts."""

    def __init__(self, repository: AccountRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, user_id: str) -> list[AccountResult]:
        """Return accounts ordered by repository policy."""
        return [
            to_result(value) for value in await self._repository.list_by_user(user_id)
        ]
