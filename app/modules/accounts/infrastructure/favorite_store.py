"""MongoDB adapter for unique favorite account selection."""

from datetime import UTC, datetime
from typing import cast

from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from app.modules.accounts.application.ports import FavoriteAccountStore
from app.modules.accounts.domain.entities import Account
from app.modules.accounts.domain.exceptions import AccountNotFoundError
from app.modules.accounts.infrastructure.documents import AccountDocument
from app.modules.accounts.infrastructure.mappers import document_to_account
from app.shared.infrastructure.mongodb.client import MongoDocument
from app.shared.infrastructure.mongodb.object_id import (
    InvalidObjectIdError,
    to_object_id,
)


class MongoFavoriteAccountStore(FavoriteAccountStore):
    """Use a MongoDB transaction to keep favorite selection unique."""

    def __init__(self, database: AsyncDatabase[MongoDocument]) -> None:
        """Initialize the account collection."""
        self._database = database
        self._collection = database["accounts"]

    async def set_favorite(
        self,
        user_id: str,
        account_id: str,
        is_favorite: bool,
    ) -> Account:
        """Set or clear favorite state without exposing intermediate state."""
        try:
            owner_id = to_object_id(user_id)
            object_id = to_object_id(account_id)
        except InvalidObjectIdError as error:
            raise AccountNotFoundError() from error
        now = datetime.now(UTC)
        async with self._database.client.start_session() as session:
            async with await session.start_transaction():
                if is_favorite:
                    await self._collection.update_many(
                        {
                            "user_id": owner_id,
                            "is_favorite": True,
                            "_id": {"$ne": object_id},
                        },
                        {
                            "$set": {
                                "is_favorite": False,
                                "updated_at": now,
                                "schema_version": 2,
                            }
                        },
                        session=session,
                    )
                document = await self._collection.find_one_and_update(
                    {
                        "_id": object_id,
                        "user_id": owner_id,
                        "is_active": True,
                    },
                    {
                        "$set": {
                            "is_favorite": is_favorite,
                            "updated_at": now,
                            "schema_version": 2,
                        }
                    },
                    return_document=ReturnDocument.AFTER,
                    session=session,
                )
                if document is None:
                    raise AccountNotFoundError()
                return document_to_account(cast(AccountDocument, document))
