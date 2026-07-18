"""Retrieve an immutable financial transaction."""

from app.modules.transactions.application.dto import TransactionResult
from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.exceptions import TransactionNotFoundError
from app.modules.transactions.domain.repositories import TransactionRepository


def to_result(transaction: Transaction) -> TransactionResult:
    """Map a persisted transaction to an application result."""
    if transaction.id is None:
        raise ValueError("A persisted transaction must have an identifier.")
    return TransactionResult(
        id=transaction.id,
        user_id=transaction.user_id,
        account_id=transaction.account_id,
        category_id=transaction.category_id,
        transaction_type=transaction.transaction_type,
        amount=transaction.amount,
        currency=transaction.currency.code,
        occurred_at=transaction.occurred_at,
        description=transaction.description,
        note=transaction.note,
        reversal_of_id=transaction.reversal_of_id,
        status=transaction.status.value,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at,
    )


class GetTransaction:
    """Retrieve a transaction belonging to the authenticated user."""

    def __init__(self, repository: TransactionRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, user_id: str, transaction_id: str) -> TransactionResult:
        """Return an owned entry or hide foreign records."""
        transaction = await self._repository.get_by_id(transaction_id)
        if transaction is None or transaction.user_id != user_id:
            raise TransactionNotFoundError()
        return to_result(transaction)
