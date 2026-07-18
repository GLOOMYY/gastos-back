"""Idempotently seed global fiat and cryptocurrency catalogs."""

import asyncio
import logging

from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import Settings, get_settings
from app.modules.reference_data.domain.entities import CurrencyCatalogEntry
from app.modules.reference_data.domain.enums import CurrencyKind
from app.modules.reference_data.infrastructure.repositories import (
    MongoReferenceDataRepository,
)
from app.shared.infrastructure.mongodb.client import MongoDatabase, MongoDocument
from app.shared.infrastructure.mongodb.indexes import create_indexes
from app.shared.infrastructure.mongodb.schema import ensure_auth_collection_schemas
from scripts.data.reference_catalog import (
    CRYPTO_CURRENCY_DATA,
    FIAT_CURRENCY_DATA,
)

logger = logging.getLogger(__name__)


async def seed_currencies(database: AsyncDatabase[MongoDocument]) -> int:
    """Upsert every versioned fiat and principal crypto monetary asset."""
    fiat = [
        CurrencyCatalogEntry.create(
            code=code,
            name=name,
            symbol=symbol,
            kind=CurrencyKind.FIAT,
            country_codes=country_codes,
        )
        for code, name, symbol, country_codes in FIAT_CURRENCY_DATA
    ]
    crypto = [
        CurrencyCatalogEntry.create(
            code=code,
            name=name,
            symbol=symbol,
            kind=CurrencyKind.CRYPTO,
            country_codes=country_codes,
        )
        for code, name, symbol, country_codes in CRYPTO_CURRENCY_DATA
    ]
    return await MongoReferenceDataRepository(database).upsert_currencies(
        [*fiat, *crypto]
    )


async def run(settings: Settings) -> int:
    """Connect to MongoDB and seed the global monetary-asset catalog."""
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
        changed = await seed_currencies(database)
        logger.info("Currency catalog seed completed; changed=%s.", changed)
        return changed
    finally:
        await mongo.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run(get_settings()))
