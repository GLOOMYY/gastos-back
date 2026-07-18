"""MongoDB persistence for immutable financial transactions."""

from datetime import datetime
from typing import cast

from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.infrastructure.documents import (
    TransactionDocument,
)
from app.modules.transactions.infrastructure.mappers import (
    document_to_transaction,
    transaction_to_document,
)
from app.shared.infrastructure.mongodb.client import MongoDocument
from app.shared.infrastructure.mongodb.object_id import (
    InvalidObjectIdError,
    to_object_id,
)


class MongoTransactionRepository:
    """Persist and query immutable ledger entries."""

    def __init__(
        self,
        database: AsyncDatabase[MongoDocument],
        session: AsyncClientSession | None = None,
    ) -> None:
        """Initialize with an optional MongoDB transaction session."""
        self._collection: AsyncCollection[MongoDocument] = database["transactions"]
        self._session = session

    async def add(self, transaction: Transaction) -> Transaction:
        """Append a transaction to the ledger."""
        document = transaction_to_document(transaction)
        document.pop("_id", None)
        result = await self._collection.insert_one(
            dict(document), session=self._session
        )
        document["_id"] = result.inserted_id
        return document_to_transaction(document)

    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        """Retrieve a transaction by public identifier."""
        try:
            object_id = to_object_id(transaction_id)
        except InvalidObjectIdError:
            return None
        document = await self._collection.find_one(
            {"_id": object_id}, session=self._session
        )
        if document is None:
            return None
        return document_to_transaction(cast(TransactionDocument, document))

    async def list_by_user(self, user_id: str) -> list[Transaction]:
        """List a user's ledger in deterministic newest-first order."""
        try:
            owner_id = to_object_id(user_id)
        except InvalidObjectIdError:
            return []
        cursor = self._collection.find({"user_id": owner_id}).sort(
            [("occurred_at", -1), ("_id", -1)]
        )
        return [
            document_to_transaction(cast(TransactionDocument, document))
            async for document in cursor
        ]

    async def list_page(
        self,
        user_id: str,
        limit: int,
        cursor: tuple[datetime, str] | None,
    ) -> list[Transaction]:
        """List a deterministic page supported by the ledger index."""
        try:
            owner_id = to_object_id(user_id)
        except InvalidObjectIdError:
            return []
        query: MongoDocument = {"user_id": owner_id}
        if cursor is not None:
            occurred_at, transaction_id = cursor
            try:
                cursor_id = to_object_id(transaction_id)
            except InvalidObjectIdError:
                return []
            query["$or"] = [
                {"occurred_at": {"$lt": occurred_at}},
                {"occurred_at": occurred_at, "_id": {"$lt": cursor_id}},
            ]
        cursor_result = (
            self._collection.find(query)
            .sort([("occurred_at", -1), ("_id", -1)])
            .limit(limit)
        )
        return [
            document_to_transaction(cast(TransactionDocument, document))
            async for document in cursor_result
        ]

    async def has_reversal(self, transaction_id: str) -> bool:
        """Check whether a ledger entry already has a reversal."""
        try:
            object_id = to_object_id(transaction_id)
        except InvalidObjectIdError:
            return False
        return (
            await self._collection.find_one(
                {"reversal_of_id": object_id}, {"_id": 1}, session=self._session
            )
            is not None
        )

    async def list_in_range(
        self,
        user_id: str,
        currency: str,
        occurred_from: datetime,
        occurred_before: datetime,
    ) -> list[Transaction]:
        """List confirmed entries for a chart range and currency."""
        try:
            owner_id = to_object_id(user_id)
        except InvalidObjectIdError:
            return []
        cursor = self._collection.find(
            {
                "user_id": owner_id,
                "currency": currency,
                "status": "confirmed",
                "occurred_at": {
                    "$gte": occurred_from,
                    "$lt": occurred_before,
                },
            }
        ).sort([("occurred_at", 1), ("_id", 1)])
        return [
            document_to_transaction(cast(TransactionDocument, document))
            async for document in cursor
        ]

    async def get_by_note(
        self,
        user_id: str,
        note: str,
    ) -> Transaction | None:
        """Retrieve an owned transaction by an exact seed-safe note."""
        try:
            owner_id = to_object_id(user_id)
        except InvalidObjectIdError:
            return None
        document = await self._collection.find_one({"user_id": owner_id, "note": note})
        if document is None:
            return None
        return document_to_transaction(cast(TransactionDocument, document))
