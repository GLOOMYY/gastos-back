"""MongoDB persistence for financial accounts."""

from typing import cast

from bson import Decimal128
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.modules.accounts.domain.entities import Account
from app.modules.accounts.domain.exceptions import (
    AccountNameAlreadyExistsError,
    AccountNotFoundError,
)
from app.modules.accounts.infrastructure.documents import AccountDocument
from app.modules.accounts.infrastructure.mappers import (
    account_to_document,
    document_to_account,
)
from app.shared.infrastructure.mongodb.client import MongoDocument
from app.shared.infrastructure.mongodb.object_id import (
    InvalidObjectIdError,
    to_object_id,
)


class MongoAccountRepository:
    """Persist accounts in MongoDB."""

    def __init__(
        self,
        database: AsyncDatabase[MongoDocument],
        session: AsyncClientSession | None = None,
    ) -> None:
        """Initialize the repository with an optional transaction session."""
        self._collection: AsyncCollection[MongoDocument] = database["accounts"]
        self._session = session

    async def add(self, account: Account) -> Account:
        """Insert an account and translate duplicate active names."""
        document = account_to_document(account)
        document.pop("_id", None)
        try:
            result = await self._collection.insert_one(
                dict(document), session=self._session
            )
        except DuplicateKeyError as error:
            raise AccountNameAlreadyExistsError() from error
        document["_id"] = result.inserted_id
        return document_to_account(document)

    async def get_by_id(self, account_id: str) -> Account | None:
        """Retrieve an account by public identifier."""
        try:
            object_id = to_object_id(account_id)
        except InvalidObjectIdError:
            return None
        document = await self._collection.find_one(
            {"_id": object_id}, session=self._session
        )
        if document is None:
            return None
        return document_to_account(cast(AccountDocument, document))

    async def list_by_user(self, user_id: str) -> list[Account]:
        """List all accounts owned by a user."""
        try:
            owner_id = to_object_id(user_id)
        except InvalidObjectIdError:
            return []
        cursor = self._collection.find({"user_id": owner_id}).sort(
            [("is_active", -1), ("created_at", -1), ("_id", -1)]
        )
        return [
            document_to_account(cast(AccountDocument, document))
            async for document in cursor
        ]

    async def exists_name(
        self,
        user_id: str,
        normalized_name: str,
        excluding_id: str | None = None,
    ) -> bool:
        """Check active name uniqueness for an owner."""
        try:
            owner_id = to_object_id(user_id)
        except InvalidObjectIdError:
            return False
        query: MongoDocument = {
            "user_id": owner_id,
            "normalized_name": normalized_name,
            "is_active": True,
        }
        if excluding_id is not None:
            try:
                query["_id"] = {"$ne": to_object_id(excluding_id)}
            except InvalidObjectIdError:
                return False
        return await self._collection.find_one(query, {"_id": 1}) is not None

    async def update(self, account: Account) -> Account:
        """Persist mutable account state."""
        if account.id is None:
            raise ValueError("A persisted account must have an identifier.")
        try:
            object_id = to_object_id(account.id)
        except InvalidObjectIdError as error:
            raise AccountNotFoundError() from error
        try:
            result = await self._collection.update_one(
                {"_id": object_id, "user_id": to_object_id(account.user_id)},
                {
                    "$set": {
                        "name": account.name,
                        "normalized_name": account.normalized_name,
                        "description": account.description,
                        "balance": Decimal128(account.balance),
                        "is_favorite": account.is_favorite,
                        "is_active": account.is_active,
                        "updated_at": account.updated_at,
                        "schema_version": 2,
                    }
                },
                session=self._session,
            )
        except DuplicateKeyError as error:
            raise AccountNameAlreadyExistsError() from error
        if result.matched_count == 0:
            raise AccountNotFoundError()
        return account
