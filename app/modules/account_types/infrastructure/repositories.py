"""MongoDB repository for account types."""

from typing import cast

from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.modules.account_types.domain.entities import AccountType
from app.modules.account_types.domain.exceptions import (
    AccountTypeNameAlreadyExistsError,
    AccountTypeNotFoundError,
)
from app.modules.account_types.infrastructure.documents import (
    AccountTypeDocument,
)
from app.modules.account_types.infrastructure.mappers import (
    account_type_to_document,
    document_to_account_type,
)
from app.shared.infrastructure.mongodb.client import MongoDocument
from app.shared.infrastructure.mongodb.object_id import (
    InvalidObjectIdError,
    to_object_id,
)


class MongoAccountTypeRepository:
    """Persist account types in MongoDB."""

    def __init__(self, database: AsyncDatabase[MongoDocument]) -> None:
        """Initialize the repository."""
        self._collection: AsyncCollection[MongoDocument] = database["account_types"]

    async def add(self, account_type: AccountType) -> AccountType:
        """Insert an account type and translate duplicate names."""
        document = account_type_to_document(account_type)
        document.pop("_id", None)
        try:
            result = await self._collection.insert_one(dict(document))
        except DuplicateKeyError as error:
            raise AccountTypeNameAlreadyExistsError() from error
        document["_id"] = result.inserted_id
        return document_to_account_type(document)

    async def get_by_id(self, account_type_id: str) -> AccountType | None:
        """Return an account type by public identifier."""
        try:
            object_id = to_object_id(account_type_id)
        except InvalidObjectIdError:
            return None
        document = await self._collection.find_one({"_id": object_id})
        if document is None:
            return None
        return document_to_account_type(cast(AccountTypeDocument, document))

    async def list_available(self, user_id: str) -> list[AccountType]:
        """List active global and user-owned types."""
        try:
            owner_id = to_object_id(user_id)
        except InvalidObjectIdError:
            return []
        cursor = self._collection.find(
            {"user_id": {"$in": [None, owner_id]}, "is_active": True}
        ).sort([("user_id", 1), ("name", 1)])
        return [
            document_to_account_type(cast(AccountTypeDocument, document))
            async for document in cursor
        ]

    async def exists_name(
        self,
        user_id: str | None,
        normalized_name: str,
        excluding_id: str | None = None,
    ) -> bool:
        """Check active name uniqueness within an ownership scope."""
        query: MongoDocument = {
            "user_id": to_object_id(user_id) if user_id else None,
            "normalized_name": normalized_name,
            "is_active": True,
        }
        if excluding_id is not None:
            try:
                query["_id"] = {"$ne": to_object_id(excluding_id)}
            except InvalidObjectIdError:
                return False
        return await self._collection.find_one(query, {"_id": 1}) is not None

    async def update(self, account_type: AccountType) -> AccountType:
        """Persist mutable account type fields."""
        if account_type.id is None:
            raise ValueError("A persisted account type must have an identifier.")
        try:
            object_id = to_object_id(account_type.id)
        except InvalidObjectIdError as error:
            raise AccountTypeNotFoundError() from error
        try:
            result = await self._collection.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "name": account_type.name,
                        "normalized_name": account_type.normalized_name,
                        "description": account_type.description,
                        "is_active": account_type.is_active,
                        "updated_at": account_type.updated_at,
                        "schema_version": 1,
                    }
                },
            )
        except DuplicateKeyError as error:
            raise AccountTypeNameAlreadyExistsError() from error
        if result.matched_count == 0:
            raise AccountTypeNotFoundError()
        return account_type
