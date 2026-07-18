"""Create a user-owned account type."""

from app.modules.account_types.application.dto import (
    AccountTypeResult,
    CreateAccountTypeCommand,
)
from app.modules.account_types.application.use_cases.get_account_type import (
    to_result,
)
from app.modules.account_types.domain.entities import AccountType
from app.modules.account_types.domain.exceptions import (
    AccountTypeNameAlreadyExistsError,
)
from app.modules.account_types.domain.repositories import AccountTypeRepository


class CreateAccountType:
    """Create a private account type for the authenticated user."""

    def __init__(self, repository: AccountTypeRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(
        self,
        command: CreateAccountTypeCommand,
    ) -> AccountTypeResult:
        """Create an account type when its private name is available."""
        account_type = AccountType.create(
            user_id=command.user_id,
            name=command.name,
            description=command.description,
            code=command.code,
        )
        if await self._repository.exists_name(
            command.user_id,
            account_type.normalized_name,
        ):
            raise AccountTypeNameAlreadyExistsError()
        return to_result(await self._repository.add(account_type))
