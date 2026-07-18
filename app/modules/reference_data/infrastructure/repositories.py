"""MongoDB repository for countries and monetary assets."""

from typing import cast

from pymongo import UpdateOne
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from app.modules.reference_data.domain.entities import (
    Country,
    CurrencyCatalogEntry,
)
from app.modules.reference_data.domain.enums import CurrencyKind
from app.modules.reference_data.infrastructure.documents import (
    CountryDocument,
    CurrencyDocument,
)
from app.modules.reference_data.infrastructure.mappers import (
    country_to_document,
    currency_to_document,
    document_to_country,
    document_to_currency,
)
from app.shared.infrastructure.mongodb.client import MongoDocument


class MongoReferenceDataRepository:
    """Persist and query global reference catalogs."""

    def __init__(self, database: AsyncDatabase[MongoDocument]) -> None:
        """Initialize country and currency collections."""
        self._countries: AsyncCollection[MongoDocument] = database["countries"]
        self._currencies: AsyncCollection[MongoDocument] = database["currencies"]

    async def list_countries(self) -> list[Country]:
        """List active countries by display name."""
        cursor = self._countries.find({"is_active": True}).sort("name", 1)
        return [
            document_to_country(cast(CountryDocument, document))
            async for document in cursor
        ]

    async def list_currencies(
        self,
        kind: CurrencyKind | None = None,
        country_code: str | None = None,
    ) -> list[CurrencyCatalogEntry]:
        """List active monetary assets with supported filters."""
        query: MongoDocument = {"is_active": True}
        if kind is not None:
            query["kind"] = kind.value
        if country_code is not None:
            query["country_codes"] = country_code
        cursor = self._currencies.find(query).sort("code", 1)
        return [
            document_to_currency(cast(CurrencyDocument, document))
            async for document in cursor
        ]

    async def country_exists(self, code: str) -> bool:
        """Check one active country code."""
        return (
            await self._countries.find_one(
                {"code": code, "is_active": True},
                {"_id": 1},
            )
            is not None
        )

    async def currency_exists(self, code: str) -> bool:
        """Check one active monetary asset code."""
        return (
            await self._currencies.find_one(
                {"code": code, "is_active": True},
                {"_id": 1},
            )
            is not None
        )

    async def upsert_countries(self, values: list[Country]) -> int:
        """Bulk upsert country documents by stable code."""
        if not values:
            return 0
        operations = []
        for value in values:
            document = dict(country_to_document(value))
            document.pop("_id", None)
            created_at = document.pop("created_at")
            operations.append(
                UpdateOne(
                    {"code": value.code},
                    {
                        "$set": document,
                        "$setOnInsert": {"created_at": created_at},
                    },
                    upsert=True,
                )
            )
        result = await self._countries.bulk_write(operations, ordered=False)
        return result.upserted_count + result.modified_count

    async def upsert_currencies(
        self,
        values: list[CurrencyCatalogEntry],
    ) -> int:
        """Bulk upsert fiat and crypto documents by stable code."""
        if not values:
            return 0
        operations = []
        for value in values:
            document = dict(currency_to_document(value))
            document.pop("_id", None)
            created_at = document.pop("created_at")
            operations.append(
                UpdateOne(
                    {"code": value.code},
                    {
                        "$set": document,
                        "$setOnInsert": {"created_at": created_at},
                    },
                    upsert=True,
                )
            )
        result = await self._currencies.bulk_write(operations, ordered=False)
        return result.upserted_count + result.modified_count
