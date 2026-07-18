"""Update a user-owned account type."""

from app.modules.account_types.application.dto import (
    AccountTypeResult,
    UpdateAccountTypeCommand,
)
from app.modules.account_types.application.use_cases.get_account_type import (
    to_result,
)
from app.modules.account_types.domain.exceptions import (
    AccountTypeAccessDeniedError,
    AccountTypeNameAlreadyExistsError,
    AccountTypeNotFoundError,
)
from app.modules.account_types.domain.repositories import AccountTypeRepository


class UpdateAccountType:
    """Update mutable fields of an owned account type."""

    def __init__(self, repository: AccountTypeRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(
        self,
        command: UpdateAccountTypeCommand,
    ) -> AccountTypeResult:
        """Update the record after ownership and uniqueness checks."""
        account_type = await self._repository.get_by_id(command.account_type_id)
        if account_type is None:
            raise AccountTypeNotFoundError()
        if account_type.user_id != command.user_id:
            raise AccountTypeAccessDeniedError()
        account_type.update_details(command.name, command.description)
        if await self._repository.exists_name(
            command.user_id,
            account_type.normalized_name,
            excluding_id=command.account_type_id,
        ):
            raise AccountTypeNameAlreadyExistsError()
        return to_result(await self._repository.update(account_type))
