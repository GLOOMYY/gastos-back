"""Add transaction validator support for transfer and exchange metadata."""

import asyncio
import logging

from app.core.config import Settings, get_settings
from app.shared.infrastructure.mongodb.client import MongoDatabase
from app.shared.infrastructure.mongodb.indexes import create_indexes
from app.shared.infrastructure.mongodb.schema import (
    update_transaction_collection_schema,
)

logger = logging.getLogger(__name__)


async def migrate(settings: Settings) -> None:
    """Idempotently update the transaction validator and transfer index."""
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
        collections = set(await database.list_collection_names())
        if "transactions" in collections:
            await update_transaction_collection_schema(database)
        await create_indexes(database)
        logger.info("Transfer metadata migration completed.")
    finally:
        await mongo.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(migrate(get_settings()))
