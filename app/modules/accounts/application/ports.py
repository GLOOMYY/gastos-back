"""Application ports for atomic account persistence."""

from typing import Protocol

from app.modules.accounts.domain.entities import Account
from app.modules.transactions.domain.entities import Transaction


class AccountCreationStore(Protocol):
    """Atomically store an account and its optional opening ledger entry."""

    async def add(
        self,
        account: Account,
        initial_transaction: Transaction | None,
    ) -> Account:
        """Persist both records in one supported database transaction."""
        ...
