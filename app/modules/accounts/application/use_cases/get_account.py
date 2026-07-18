"""Retrieve an owned financial account."""

from app.modules.accounts.application.dto import AccountResult
from app.modules.accounts.domain.entities import Account
from app.modules.accounts.domain.exceptions import AccountNotFoundError
from app.modules.accounts.domain.repositories import AccountRepository


def to_result(account: Account) -> AccountResult:
    """Map a persisted account to an application result."""
    if account.id is None:
        raise ValueError("A persisted account must have an identifier.")
    return AccountResult(
        id=account.id,
        user_id=account.user_id,
        account_type_id=account.account_type_id,
        name=account.name,
        description=account.description,
        initial_balance=account.initial_balance,
        balance=account.balance,
        currency=account.currency.code,
        is_favorite=account.is_favorite,
        is_active=account.is_active,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


class GetAccount:
    """Retrieve an account belonging to the authenticated user."""

    def __init__(self, repository: AccountRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, user_id: str, account_id: str) -> AccountResult:
        """Return an owned account or hide foreign records."""
        account = await self._repository.get_by_id(account_id)
        if account is None or account.user_id != user_id:
            raise AccountNotFoundError()
        return to_result(account)
