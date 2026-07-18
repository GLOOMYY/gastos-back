"""Update account metadata."""

from app.modules.accounts.application.dto import (
    AccountResult,
    UpdateAccountCommand,
)
from app.modules.accounts.application.use_cases.get_account import to_result
from app.modules.accounts.domain.exceptions import (
    AccountNameAlreadyExistsError,
    AccountNotFoundError,
)
from app.modules.accounts.domain.repositories import AccountRepository


class RenameAccount:
    """Update an owned account's name and description."""

    def __init__(self, repository: AccountRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, command: UpdateAccountCommand) -> AccountResult:
        """Update metadata after ownership and uniqueness checks."""
        account = await self._repository.get_by_id(command.account_id)
        if account is None or account.user_id != command.user_id:
            raise AccountNotFoundError()
        account.update_details(command.name, command.description)
        if await self._repository.exists_name(
            command.user_id,
            account.normalized_name,
            excluding_id=command.account_id,
        ):
            raise AccountNameAlreadyExistsError()
        return to_result(await self._repository.update(account))
