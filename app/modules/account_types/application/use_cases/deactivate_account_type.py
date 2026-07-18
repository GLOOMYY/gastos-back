"""Deactivate a user-owned account type."""

from app.modules.account_types.application.dto import AccountTypeResult
from app.modules.account_types.application.use_cases.get_account_type import (
    to_result,
)
from app.modules.account_types.domain.exceptions import (
    AccountTypeAccessDeniedError,
    AccountTypeNotFoundError,
)
from app.modules.account_types.domain.repositories import AccountTypeRepository


class DeactivateAccountType:
    """Soft-delete an owned account type."""

    def __init__(self, repository: AccountTypeRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, user_id: str, account_type_id: str) -> AccountTypeResult:
        """Deactivate an owned account type without deleting history."""
        account_type = await self._repository.get_by_id(account_type_id)
        if account_type is None:
            raise AccountTypeNotFoundError()
        if account_type.user_id != user_id:
            raise AccountTypeAccessDeniedError()
        account_type.deactivate()
        return to_result(await self._repository.update(account_type))
