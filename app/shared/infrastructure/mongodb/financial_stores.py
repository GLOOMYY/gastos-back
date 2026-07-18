"""MongoDB adapters for atomic cross-module financial writes."""

from dataclasses import replace
from decimal import Decimal

from datetime import datetime

from bson import Decimal128, ObjectId
from pymongo import ReturnDocument
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.modules.accounts.application.ports import AccountCreationStore
from app.modules.accounts.domain.entities import Account
from app.modules.accounts.domain.exceptions import (
    AccountNotFoundError,
    InactiveAccountError,
)
from app.modules.accounts.infrastructure.repositories import MongoAccountRepository
from app.modules.transactions.application.ports import LedgerStore, TransferStore
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


class MongoTransferStore(TransferStore):
    """Atomically persist both balances and both immutable transfer entries."""

    def __init__(self, database: AsyncDatabase[MongoDocument]) -> None:
        """Initialize the Atlas-compatible transfer store."""
        self._database = database

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
        """Commit the complete double-entry transfer or roll it all back."""
        try:
            owner_id = to_object_id(user_id)
            source_id = to_object_id(source_account_id)
            target_id = to_object_id(target_account_id)
        except InvalidObjectIdError as error:
            raise AccountNotFoundError() from error

        async with self._database.client.start_session() as session:
            async with await session.start_transaction():
                await self._update_balance(
                    owner_id,
                    source_id,
                    -source_amount,
                    outgoing.created_at,
                    session,
                )
                await self._update_balance(
                    owner_id,
                    target_id,
                    target_amount,
                    incoming.created_at,
                    session,
                )
                repository = MongoTransactionRepository(self._database, session)
                created_outgoing = await repository.add(outgoing)
                created_incoming = await repository.add(incoming)
                return created_outgoing, created_incoming

    async def _update_balance(
        self,
        owner_id: ObjectId,
        account_id: ObjectId,
        delta: Decimal,
        updated_at: datetime,
        session: AsyncClientSession,
    ) -> None:
        """Update one active owned account inside the current transaction."""
        updated = await self._database["accounts"].find_one_and_update(
            {
                "_id": account_id,
                "user_id": owner_id,
                "is_active": True,
            },
            {
                "$inc": {"balance": Decimal128(delta)},
                "$set": {"updated_at": updated_at},
            },
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        if updated is not None:
            return
        existing = await self._database["accounts"].find_one(
            {"_id": account_id, "user_id": owner_id},
            {"is_active": 1},
            session=session,
        )
        if existing is not None:
            raise InactiveAccountError()
        raise AccountNotFoundError()
