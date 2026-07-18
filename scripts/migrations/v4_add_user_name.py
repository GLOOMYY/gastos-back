"""Add the optional profile name to existing user documents."""

import asyncio
from datetime import UTC, datetime
import logging

from app.core.config import Settings, get_settings
from app.shared.infrastructure.mongodb.client import MongoDatabase
from app.shared.infrastructure.mongodb.schema import update_user_collection_schema

logger = logging.getLogger(__name__)


async def migrate(settings: Settings) -> None:
    """Idempotently backfill user names and apply the current validator."""
    mongodb_uri = settings.mongodb_uri
    database_name = settings.mongodb_database
    if mongodb_uri is None or not database_name:
        raise RuntimeError("MONGODB_URI and MONGODB_DATABASE are required.")
    mongo = MongoDatabase()
    try:
        await mongo.connect(
            mongodb_uri.get_secret_value(),
            database_name,
            settings.mongodb_server_selection_timeout_ms,
        )
        database = mongo.get_database()
        now = datetime.now(UTC)
        result = await database.users.update_many(
            {"name": {"$exists": False}},
            {
                "$set": {
                    "name": None,
                    "updated_at": now,
                    "schema_version": 3,
                }
            },
        )
        await update_user_collection_schema(database)
        logger.info(
            "User-name migration completed; matched=%s modified=%s.",
            result.matched_count,
            result.modified_count,
        )
    finally:
        await mongo.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(migrate(get_settings()))
