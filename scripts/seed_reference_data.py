"""Seed countries and monetary assets as one reference-data operation."""

import asyncio
from dataclasses import dataclass
import logging

from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import Settings, get_settings
from app.shared.infrastructure.mongodb.client import MongoDatabase, MongoDocument
from app.shared.infrastructure.mongodb.indexes import create_indexes
from app.shared.infrastructure.mongodb.schema import ensure_auth_collection_schemas
from scripts.seed_countries import seed_countries
from scripts.seed_currencies import seed_currencies

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ReferenceSeedSummary:
    """Secret-safe counts reported by the reference-data seed."""

    changed_countries: int
    changed_currencies: int


async def seed_reference_data(
    database: AsyncDatabase[MongoDocument],
) -> ReferenceSeedSummary:
    """Upsert both global catalogs using one existing database connection."""
    return ReferenceSeedSummary(
        changed_countries=await seed_countries(database),
        changed_currencies=await seed_currencies(database),
    )


async def run(settings: Settings) -> ReferenceSeedSummary:
    """Connect to MongoDB and seed countries and monetary assets."""
    if settings.mongodb_uri is None or not settings.mongodb_database:
        raise RuntimeError("MONGODB_URI and MONGODB_DATABASE are required.")
    mongo = MongoDatabase()
    try:
        await mongo.connect(
            settings.mongodb_uri.get_secret_value(),
            settings.mongodb_database,
            settings.mongodb_server_selection_timeout_ms,
        )
        database = mongo.get_database()
        await ensure_auth_collection_schemas(database)
        await create_indexes(database)
        summary = await seed_reference_data(database)
        logger.info(
            "Reference-data seed completed; countries=%s currencies=%s.",
            summary.changed_countries,
            summary.changed_currencies,
        )
        return summary
    finally:
        await mongo.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run(get_settings()))
