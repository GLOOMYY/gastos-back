"""Retrieve an account type visible to a user."""

from app.modules.account_types.application.dto import AccountTypeResult
from app.modules.account_types.domain.entities import AccountType
from app.modules.account_types.domain.exceptions import AccountTypeNotFoundError
from app.modules.account_types.domain.repositories import AccountTypeRepository


def to_result(account_type: AccountType) -> AccountTypeResult:
    """Map an account type entity to an application result."""
    if account_type.id is None:
        raise ValueError("A persisted account type must have an identifier.")
    return AccountTypeResult(
        id=account_type.id,
        user_id=account_type.user_id,
        code=account_type.code,
        name=account_type.name,
        description=account_type.description,
        is_active=account_type.is_active,
        created_at=account_type.created_at,
        updated_at=account_type.updated_at,
    )


class GetAccountType:
    """Retrieve a global or user-owned account type."""

    def __init__(self, repository: AccountTypeRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, user_id: str, account_type_id: str) -> AccountTypeResult:
        """Return an available account type or hide inaccessible records."""
        account_type = await self._repository.get_by_id(account_type_id)
        if account_type is None or account_type.user_id not in (None, user_id):
            raise AccountTypeNotFoundError()
        return to_result(account_type)
