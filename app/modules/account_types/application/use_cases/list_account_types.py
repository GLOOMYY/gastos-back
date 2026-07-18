"""List account types visible to a user."""

from app.modules.account_types.application.dto import AccountTypeResult
from app.modules.account_types.application.use_cases.get_account_type import (
    to_result,
)
from app.modules.account_types.domain.repositories import AccountTypeRepository


class ListAccountTypes:
    """List active global and private account types."""

    def __init__(self, repository: AccountTypeRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, user_id: str) -> list[AccountTypeResult]:
        """Return all account types available to the user."""
        records = await self._repository.list_available(user_id)
        return [to_result(record) for record in records]
