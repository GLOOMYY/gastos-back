"""MongoDB adapters for atomic cross-module financial writes."""

from dataclasses import replace
from decimal import Decimal

from bson import Decimal128
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.modules.accounts.application.ports import AccountCreationStore
from app.modules.accounts.domain.entities import Account
from app.modules.accounts.domain.exceptions import (
    AccountNotFoundError,
    InactiveAccountError,
)
from app.modules.accounts.infrastructure.repositories import MongoAccountRepository
from app.modules.transactions.application.ports import LedgerStore
from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.exceptions import (
    TransactionAlreadyReversedError,
)
from app.modules.transactions.infrastructure.repositories import (
    MongoTransactionRepository,
)
from app.shared.infrastructure.mongodb.client import MongoDocument
from app.shared.infrastructure.mongodb.object_id import (
    InvalidObjectIdError,
    to_object_id,
)


class MongoAccountCreationStore(AccountCreationStore):
    """Atomically persist an account and its initial ledger entry."""

    def __init__(self, database: AsyncDatabase[MongoDocument]) -> None:
        """Initialize the store."""
        self._database = database

    async def add(
        self,
        account: Account,
        initial_transaction: Transaction | None,
    ) -> Account:
        """Store opening state using a MongoDB transaction when needed."""
        if initial_transaction is None:
            return await MongoAccountRepository(self._database).add(account)
        async with self._database.client.start_session() as session:
            async with await session.start_transaction():
                created = await MongoAccountRepository(
                    self._database,
                    session,
                ).add(account)
                if created.id is None:
                    raise ValueError("The created account has no identifier.")
                transaction = replace(initial_transaction, account_id=created.id)
                await MongoTransactionRepository(
                    self._database,
                    session,
                ).add(transaction)
                return created


class MongoLedgerStore(LedgerStore):
    """Persist a balance delta and ledger entry atomically."""

    def __init__(self, database: AsyncDatabase[MongoDocument]) -> None:
        """Initialize the store."""
        self._database = database

    async def apply(
        self,
        user_id: str,
        account_id: str,
        balance_delta: Decimal,
        transaction: Transaction,
    ) -> Transaction:
        """Apply the operation in an Atlas-compatible transaction."""
        try:
            owner_id = to_object_id(user_id)
            object_id = to_object_id(account_id)
        except InvalidObjectIdError as error:
            raise AccountNotFoundError() from error
        try:
            async with self._database.client.start_session() as session:
                async with await session.start_transaction():
                    updated = await self._database["accounts"].find_one_and_update(
                        {
                            "_id": object_id,
                            "user_id": owner_id,
                            "is_active": True,
                        },
                        {
                            "$inc": {"balance": Decimal128(balance_delta)},
                            "$set": {"updated_at": transaction.created_at},
                        },
                        return_document=ReturnDocument.AFTER,
                        session=session,
                    )
                    if updated is None:
                        existing = await self._database["accounts"].find_one(
                            {"_id": object_id, "user_id": owner_id},
                            {"is_active": 1},
                            session=session,
                        )
                        if existing is not None:
                            raise InactiveAccountError()
                        raise AccountNotFoundError()
                    return await MongoTransactionRepository(
                        self._database,
                        session,
                    ).add(transaction)
        except DuplicateKeyError as error:
            if transaction.reversal_of_id is not None:
                raise TransactionAlreadyReversedError() from error
            raise
