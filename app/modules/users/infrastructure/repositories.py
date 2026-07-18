"""MongoDB repository implementations for user authentication."""

from datetime import datetime
from typing import cast

from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.modules.users.application.dto import RefreshTokenRecord
from app.modules.users.domain.entities import User
from app.modules.users.domain.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.modules.users.infrastructure.documents import (
    RefreshTokenDocument,
    UserDocument,
)
from app.modules.users.infrastructure.mappers import (
    document_to_refresh_token,
    document_to_user,
    refresh_token_to_document,
    user_to_document,
)
from app.shared.infrastructure.mongodb.client import MongoDocument
from app.shared.infrastructure.mongodb.object_id import (
    InvalidObjectIdError,
    to_object_id,
)


class MongoUserRepository:
    """Persist users in the MongoDB users collection."""

    def __init__(self, database: AsyncDatabase[MongoDocument]) -> None:
        """Initialize the user repository."""
        self._collection: AsyncCollection[MongoDocument] = database["users"]

    async def add(self, user: User) -> User:
        """Persist a new user and translate duplicate email violations."""
        document = user_to_document(user)
        document.pop("_id", None)
        try:
            result = await self._collection.insert_one(dict(document))
        except DuplicateKeyError as error:
            raise UserAlreadyExistsError() from error

        document["_id"] = result.inserted_id
        return document_to_user(document)

    async def get_by_id(self, user_id: str) -> User | None:
        """Return a user by ObjectId serialized as a string."""
        try:
            object_id = to_object_id(user_id)
        except InvalidObjectIdError:
            return None

        document = await self._collection.find_one({"_id": object_id})
        if document is None:
            return None
        return document_to_user(cast(UserDocument, document))

    async def get_by_normalized_email(
        self,
        normalized_email: str,
    ) -> User | None:
        """Return a user by its canonical email address."""
        document = await self._collection.find_one(
            {"normalized_email": normalized_email}
        )
        if document is None:
            return None
        return document_to_user(cast(UserDocument, document))

    async def update(self, user: User) -> None:
        """Persist mutable user fields and translate uniqueness conflicts."""
        if user.id is None:
            raise ValueError("A persisted user must have an identifier.")
        try:
            object_id = to_object_id(user.id)
        except InvalidObjectIdError as error:
            raise UserNotFoundError() from error

        try:
            result = await self._collection.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "email": user.email.value,
                        "normalized_email": user.email.normalized,
                        "password_hash": user.password_hash,
                        "role": user.role.value,
                        "name": user.name,
                        "favorite_currency": (
                            user.favorite_currency.code
                            if user.favorite_currency is not None
                            else None
                        ),
                        "country_code": (
                            user.country_code.value
                            if user.country_code is not None
                            else None
                        ),
                        "is_active": user.is_active,
                        "updated_at": user.updated_at,
                        "schema_version": 3,
                    }
                },
            )
        except DuplicateKeyError as error:
            raise UserAlreadyExistsError() from error
        if result.matched_count == 0:
            raise UserNotFoundError()


class MongoRefreshTokenRepository:
    """Persist refresh-token rotation state in MongoDB."""

    def __init__(self, database: AsyncDatabase[MongoDocument]) -> None:
        """Initialize the refresh-token repository."""
        self._collection: AsyncCollection[MongoDocument] = database["refresh_tokens"]

    async def add(self, record: RefreshTokenRecord) -> None:
        """Persist a newly issued refresh-token record."""
        document = refresh_token_to_document(record)
        await self._collection.insert_one(dict(document))

    async def get_by_hash(
        self,
        token_hash: str,
    ) -> RefreshTokenRecord | None:
        """Return refresh-token state by its SHA-256 fingerprint."""
        document = await self._collection.find_one({"token_hash": token_hash})
        if document is None:
            return None
        return document_to_refresh_token(cast(RefreshTokenDocument, document))

    async def consume(
        self,
        token_hash: str,
        replaced_by_id: str,
        revoked_at: datetime,
    ) -> bool:
        """Atomically consume a token that has not already been revoked."""
        result = await self._collection.update_one(
            {
                "token_hash": token_hash,
                "revoked_at": None,
                "expires_at": {"$gt": revoked_at},
            },
            {
                "$set": {
                    "revoked_at": revoked_at,
                    "replaced_by_id": replaced_by_id,
                }
            },
        )
        return result.modified_count == 1

    async def revoke_by_hash(
        self,
        token_hash: str,
        revoked_at: datetime,
    ) -> None:
        """Revoke an active refresh token when it exists."""
        await self._collection.update_one(
            {"token_hash": token_hash, "revoked_at": None},
            {"$set": {"revoked_at": revoked_at}},
        )

    async def revoke_family(
        self,
        family_id: str,
        revoked_at: datetime,
    ) -> None:
        """Revoke every active refresh token in a rotation family."""
        await self._collection.update_many(
            {"family_id": family_id, "revoked_at": None},
            {"$set": {"revoked_at": revoked_at}},
        )

    async def revoke_by_user(
        self,
        user_id: str,
        revoked_at: datetime,
    ) -> None:
        """Revoke every active refresh token belonging to a user."""
        try:
            object_id = to_object_id(user_id)
        except InvalidObjectIdError:
            return
        await self._collection.update_many(
            {"user_id": object_id, "revoked_at": None},
            {"$set": {"revoked_at": revoked_at}},
        )
