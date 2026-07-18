"""Idempotently seed the global country and territory catalog."""

import asyncio
import logging

from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import Settings, get_settings
from app.modules.reference_data.domain.entities import Country
from app.modules.reference_data.infrastructure.repositories import (
    MongoReferenceDataRepository,
)
from app.shared.infrastructure.mongodb.client import MongoDatabase, MongoDocument
from app.shared.infrastructure.mongodb.indexes import create_indexes
from app.shared.infrastructure.mongodb.schema import ensure_auth_collection_schemas
from scripts.data.reference_catalog import COUNTRY_DATA

logger = logging.getLogger(__name__)


async def seed_countries(database: AsyncDatabase[MongoDocument]) -> int:
    """Upsert every versioned country and territory by alpha-2 code."""
    countries = [
        Country.create(
            code=code,
            alpha3_code=alpha3_code,
            name=name,
            official_name=official_name,
            currency_codes=currency_codes,
        )
        for code, alpha3_code, name, official_name, currency_codes in COUNTRY_DATA
    ]
    return await MongoReferenceDataRepository(database).upsert_countries(countries)


async def run(settings: Settings) -> int:
    """Connect to MongoDB and seed the global country catalog."""
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
        changed = await seed_countries(database)
        logger.info("Country catalog seed completed; changed=%s.", changed)
        return changed
    finally:
        await mongo.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run(get_settings()))
