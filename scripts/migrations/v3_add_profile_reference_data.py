"""Add favorite account, profile preferences, and reference catalogs."""

import asyncio
from datetime import UTC, datetime
import logging

from app.core.config import Settings, get_settings
from app.shared.infrastructure.mongodb.client import MongoDatabase
from app.shared.infrastructure.mongodb.indexes import create_indexes
from app.shared.infrastructure.mongodb.schema import (
    ensure_auth_collection_schemas,
    update_account_collection_schema,
    update_user_collection_schema,
)

logger = logging.getLogger(__name__)


async def migrate(settings: Settings) -> None:
    """Idempotently backfill new fields and apply catalog schemas."""
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
        await ensure_auth_collection_schemas(database)
        now = datetime.now(UTC)
        await database.users.update_many(
            {
                "$or": [
                    {"favorite_currency": {"$exists": False}},
                    {"country_code": {"$exists": False}},
                ]
            },
            {
                "$set": {
                    "favorite_currency": None,
                    "country_code": None,
                    "updated_at": now,
                    "schema_version": 2,
                }
            },
        )
        await database.accounts.update_many(
            {"is_favorite": {"$exists": False}},
            {
                "$set": {
                    "is_favorite": False,
                    "updated_at": now,
                    "schema_version": 2,
                }
            },
        )
        await update_user_collection_schema(database)
        await update_account_collection_schema(database)
        await create_indexes(database)
        logger.info("Profile and reference-data migration completed.")
    finally:
        await mongo.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(migrate(get_settings()))
