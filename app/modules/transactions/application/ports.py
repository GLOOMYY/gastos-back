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


class TransferStore(Protocol):
    """Atomically update two balances and append both transfer entries."""

    async def transfer(
        self,
        user_id: str,
        source_account_id: str,
        target_account_id: str,
        source_amount: Decimal,
        target_amount: Decimal,
        outgoing: Transaction,
        incoming: Transaction,
    ) -> tuple[Transaction, Transaction]:
        """Persist an indivisible double-entry account transfer."""
        ...


class TransferIdGenerator(Protocol):
    """Generate unpredictable identifiers shared by transfer entries."""

    def generate(self) -> str:
        """Return a new transfer identifier."""
        ...
