"""Application ports for atomic ledger operations."""

from decimal import Decimal
from typing import Protocol

from app.modules.transactions.domain.entities import Transaction


class LedgerStore(Protocol):
    """Atomically update a balance and append a ledger entry."""

    async def apply(
        self,
        user_id: str,
        account_id: str,
        balance_delta: Decimal,
        transaction: Transaction,
    ) -> Transaction:
        """Apply an atomic financial operation."""
        ...
