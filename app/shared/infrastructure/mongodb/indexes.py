"""MongoDB index management."""

from pymongo import ASCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.shared.infrastructure.mongodb.client import MongoDocument


async def create_indexes(
    database: AsyncDatabase[MongoDocument],
) -> None:
    """Create indexes required by implemented application queries."""
    await database.users.create_index(
        [("normalized_email", ASCENDING)],
        unique=True,
        name="uq_users_normalized_email",
    )
    await database.refresh_tokens.create_index(
        [("token_hash", ASCENDING)],
        unique=True,
        name="uq_refresh_tokens_token_hash",
    )
    await database.refresh_tokens.create_index(
        [("family_id", ASCENDING)],
        name="ix_refresh_tokens_family_id",
    )
    await database.refresh_tokens.create_index(
        [("user_id", ASCENDING)],
        name="ix_refresh_tokens_user_id",
    )
    await database.refresh_tokens.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        name="ix_refresh_tokens_expires_ttl",
    )
