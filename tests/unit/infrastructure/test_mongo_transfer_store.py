"""Atomic boundary tests for the MongoDB transfer store."""

from datetime import UTC, datetime
from decimal import Decimal
from types import TracebackType
from typing import cast

import pytest
from pymongo.asynchronous.database import AsyncDatabase

from app.modules.accounts.domain.exceptions import AccountNotFoundError
from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.enums import TransactionType
from app.shared.infrastructure.mongodb.client import MongoDocument
from app.shared.infrastructure.mongodb.financial_stores import MongoTransferStore

USER_ID = "507f1f77bcf86cd799439011"
SOURCE_ID = "507f1f77bcf86cd799439014"
TARGET_ID = "507f1f77bcf86cd799439015"


class FakeTransactionContext:
    """Capture whether the transaction scope receives a failure."""

    def __init__(self) -> None:
        """Initialize without a captured exception."""
        self.exception_type: type[BaseException] | None = None

    async def __aenter__(self) -> None:
        """Enter the fake transaction."""

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Capture the failure that triggers driver rollback."""
        self.exception_type = exception_type
        return False


class FakeSession:
    """Provide one fake MongoDB transaction context."""

    def __init__(self) -> None:
        """Initialize the transaction context."""
        self.transaction = FakeTransactionContext()

    async def start_transaction(self) -> FakeTransactionContext:
        """Return the fake transaction context."""
        return self.transaction


class FakeSessionContext:
    """Provide an asynchronous session context manager."""

    def __init__(self, session: FakeSession) -> None:
        """Initialize with the session returned on entry."""
        self.session = session

    async def __aenter__(self) -> FakeSession:
        """Return the fake session."""
        return self.session

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Propagate any persistence error."""
        return False


class FakeClient:
    """Start the configured session context."""

    def __init__(self, session: FakeSession) -> None:
        """Initialize with one session."""
        self.session = session

    def start_session(self) -> FakeSessionContext:
        """Return an asynchronous session context manager."""
        return FakeSessionContext(self.session)


class FakeAccountsCollection:
    """Succeed for the source update and fail for the destination."""

    def __init__(self) -> None:
        """Initialize balance update call tracking."""
        self.update_calls = 0

    async def find_one_and_update(self, *args: object, **kwargs: object) -> object:
        """Return an account only for the first balance update."""
        self.update_calls += 1
        return {} if self.update_calls == 1 else None

    async def find_one(self, *args: object, **kwargs: object) -> None:
        """Report that the failed destination account does not exist."""


class FakeDatabase:
    """Expose only the database behavior reached by the failure scenario."""

    def __init__(self) -> None:
        """Initialize fake client and accounts collection."""
        self.session = FakeSession()
        self.client = FakeClient(self.session)
        self.accounts = FakeAccountsCollection()

    def __getitem__(self, name: str) -> FakeAccountsCollection:
        """Return the accounts collection used before ledger inserts."""
        return self.accounts


def _entry(account_id: str, transaction_type: TransactionType) -> Transaction:
    """Build one side of a same-currency transfer."""
    return Transaction.create(
        user_id=USER_ID,
        account_id=account_id,
        transaction_type=transaction_type,
        amount=Decimal("10"),
        currency="COP",
        occurred_at=datetime(2026, 7, 18, tzinfo=UTC),
        transfer_id="transfer-test-id",
        source_amount=Decimal("10"),
        target_amount=Decimal("10"),
        source_currency="COP",
        target_currency="COP",
    )


@pytest.mark.asyncio
async def test_destination_failure_reaches_transaction_scope_for_rollback() -> None:
    """A partial balance failure exits the MongoDB transaction with error."""
    database = FakeDatabase()
    store = MongoTransferStore(cast(AsyncDatabase[MongoDocument], database))

    with pytest.raises(AccountNotFoundError):
        await store.transfer(
            user_id=USER_ID,
            source_account_id=SOURCE_ID,
            target_account_id=TARGET_ID,
            source_amount=Decimal("10"),
            target_amount=Decimal("10"),
            outgoing=_entry(SOURCE_ID, TransactionType.TRANSFER_OUT),
            incoming=_entry(TARGET_ID, TransactionType.TRANSFER_IN),
        )

    assert database.accounts.update_calls == 2
    assert database.session.transaction.exception_type is AccountNotFoundError
