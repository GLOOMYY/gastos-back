"""Repository abstractions for immutable ledger entries."""

from datetime import datetime
from typing import Protocol

from app.modules.transactions.domain.entities import Transaction


class TransactionRepository(Protocol):
    """Persistence operations for financial transactions."""

    async def add(self, transaction: Transaction) -> Transaction:
        """Persist and return an immutable ledger entry."""
        ...

    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        """Retrieve a ledger entry by public identifier."""
        ...

    async def list_by_user(self, user_id: str) -> list[Transaction]:
        """List entries belonging to a user."""
        ...

    async def list_page(
        self,
        user_id: str,
        limit: int,
        cursor: tuple[datetime, str] | None,
    ) -> list[Transaction]:
        """List at most limit entries after an optional ordering cursor."""
        ...

    async def has_reversal(self, transaction_id: str) -> bool:
        """Return whether a transaction already has a reversal."""
        ...

    async def list_in_range(
        self,
        user_id: str,
        currency: str,
        occurred_from: datetime,
        occurred_before: datetime,
    ) -> list[Transaction]:
        """List confirmed entries in an owner, currency, and date range."""
        ...

    async def get_by_note(
        self,
        user_id: str,
        note: str,
    ) -> Transaction | None:
        """Retrieve an owned entry by its exact note."""
        ...
