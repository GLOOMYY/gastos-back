"""MongoDB repository for categories."""

from typing import cast

from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.enums import CategoryTransactionType
from app.modules.categories.domain.exceptions import (
    CategoryNameAlreadyExistsError,
    CategoryNotFoundError,
)
from app.modules.categories.infrastructure.documents import CategoryDocument
from app.modules.categories.infrastructure.mappers import (
    category_to_document,
    document_to_category,
)
from app.shared.infrastructure.mongodb.client import MongoDocument
from app.shared.infrastructure.mongodb.object_id import (
    InvalidObjectIdError,
    to_object_id,
)


class MongoCategoryRepository:
    """Persist categories in MongoDB."""

    def __init__(self, database: AsyncDatabase[MongoDocument]) -> None:
        """Initialize the repository."""
        self._collection: AsyncCollection[MongoDocument] = database["categories"]

    async def add(self, category: Category) -> Category:
        """Insert a category and translate duplicate names."""
        document = category_to_document(category)
        document.pop("_id", None)
        try:
            result = await self._collection.insert_one(dict(document))
        except DuplicateKeyError as error:
            raise CategoryNameAlreadyExistsError() from error
        document["_id"] = result.inserted_id
        return document_to_category(document)

    async def get_by_id(self, category_id: str) -> Category | None:
        """Return a category by public identifier."""
        try:
            object_id = to_object_id(category_id)
        except InvalidObjectIdError:
            return None
        document = await self._collection.find_one({"_id": object_id})
        if document is None:
            return None
        return document_to_category(cast(CategoryDocument, document))

    async def list_available(
        self,
        user_id: str,
        transaction_type: CategoryTransactionType | None = None,
    ) -> list[Category]:
        """List active global and private categories."""
        try:
            owner_id = to_object_id(user_id)
        except InvalidObjectIdError:
            return []
        query: MongoDocument = {
            "user_id": {"$in": [None, owner_id]},
            "is_active": True,
        }
        if transaction_type is not None:
            query["transaction_type"] = transaction_type.value
        cursor = self._collection.find(query).sort(
            [("transaction_type", 1), ("name", 1)]
        )
        return [
            document_to_category(cast(CategoryDocument, document))
            async for document in cursor
        ]

    async def exists_name(
        self,
        user_id: str | None,
        normalized_name: str,
        transaction_type: CategoryTransactionType,
        excluding_id: str | None = None,
    ) -> bool:
        """Check active uniqueness within category ownership and type."""
        query: MongoDocument = {
            "user_id": to_object_id(user_id) if user_id else None,
            "normalized_name": normalized_name,
            "transaction_type": transaction_type.value,
            "is_active": True,
        }
        if excluding_id is not None:
            try:
                query["_id"] = {"$ne": to_object_id(excluding_id)}
            except InvalidObjectIdError:
                return False
        return await self._collection.find_one(query, {"_id": 1}) is not None

    async def update(self, category: Category) -> Category:
        """Persist mutable category fields."""
        if category.id is None:
            raise ValueError("A persisted category must have an identifier.")
        try:
            object_id = to_object_id(category.id)
        except InvalidObjectIdError as error:
            raise CategoryNotFoundError() from error
        try:
            result = await self._collection.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "name": category.name,
                        "normalized_name": category.normalized_name,
                        "transaction_type": category.transaction_type.value,
                        "description": category.description,
                        "is_active": category.is_active,
                        "updated_at": category.updated_at,
                        "schema_version": 1,
                    }
                },
            )
        except DuplicateKeyError as error:
            raise CategoryNameAlreadyExistsError() from error
        if result.matched_count == 0:
            raise CategoryNotFoundError()
        return category
