"""Reverse an immutable confirmed financial transaction."""

from datetime import UTC, datetime
from decimal import Decimal

from app.modules.accounts.domain.exceptions import AccountNotFoundError
from app.modules.accounts.domain.repositories import AccountRepository
from app.modules.transactions.application.dto import (
    ReverseTransactionCommand,
    TransactionResult,
)
from app.modules.transactions.application.ports import LedgerStore
from app.modules.transactions.application.use_cases.get_transaction import (
    to_result,
)
from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.enums import TransactionType
from app.modules.transactions.domain.exceptions import (
    TransactionAlreadyReversedError,
    TransactionCannotBeReversedError,
    TransactionNotFoundError,
)
from app.modules.transactions.domain.repositories import TransactionRepository


class ReverseTransaction:
    """Append a compensating entry instead of editing financial history."""

    def __init__(
        self,
        transactions: TransactionRepository,
        accounts: AccountRepository,
        ledger: LedgerStore,
    ) -> None:
        """Initialize the use case."""
        self._transactions = transactions
        self._accounts = accounts
        self._ledger = ledger

    async def execute(
        self,
        command: ReverseTransactionCommand,
    ) -> TransactionResult:
        """Validate eligibility and atomically append compensation."""
        original = await self._transactions.get_by_id(command.transaction_id)
        if original is None or original.user_id != command.user_id:
            raise TransactionNotFoundError()
        if original.transaction_type not in {
            TransactionType.INCOME,
            TransactionType.EXPENSE,
            TransactionType.INITIAL_BALANCE,
        }:
            raise TransactionCannotBeReversedError()
        if await self._transactions.has_reversal(command.transaction_id):
            raise TransactionAlreadyReversedError()
        account = await self._accounts.get_by_id(original.account_id)
        if account is None or account.user_id != command.user_id:
            raise AccountNotFoundError()
        delta = self._reversal_delta(original)
        reversal = Transaction.create(
            user_id=command.user_id,
            account_id=original.account_id,
            transaction_type=TransactionType.REVERSAL,
            amount=abs(original.amount),
            currency=original.currency.code,
            occurred_at=datetime.now(UTC),
            description=command.reason,
            reversal_of_id=command.transaction_id,
        )
        created = await self._ledger.apply(
            command.user_id,
            original.account_id,
            delta,
            reversal,
        )
        return to_result(created)

    @staticmethod
    def _reversal_delta(original: Transaction) -> Decimal:
        """Return the inverse balance effect of the original entry."""
        if original.transaction_type is TransactionType.EXPENSE:
            return original.amount
        return -original.amount
