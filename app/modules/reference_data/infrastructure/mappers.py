"""Mappings for global country and currency documents."""

from app.modules.reference_data.domain.entities import (
    Country,
    CurrencyCatalogEntry,
)
from app.modules.reference_data.domain.enums import CurrencyKind
from app.modules.reference_data.infrastructure.documents import (
    CountryDocument,
    CurrencyDocument,
)
from app.shared.infrastructure.mongodb.object_id import to_object_id


def country_to_document(value: Country) -> CountryDocument:
    """Map a country entity to MongoDB."""
    document = CountryDocument(
        code=value.code,
        alpha3_code=value.alpha3_code,
        name=value.name,
        official_name=value.official_name,
        currency_codes=list(value.currency_codes),
        is_active=value.is_active,
        created_at=value.created_at,
        updated_at=value.updated_at,
        schema_version=1,
    )
    if value.id is not None:
        document["_id"] = to_object_id(value.id)
    return document


def document_to_country(document: CountryDocument) -> Country:
    """Map a MongoDB document to a country entity."""
    return Country(
        id=str(document["_id"]),
        code=document["code"],
        alpha3_code=document["alpha3_code"],
        name=document["name"],
        official_name=document["official_name"],
        currency_codes=tuple(document["currency_codes"]),
        is_active=document["is_active"],
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )


def currency_to_document(value: CurrencyCatalogEntry) -> CurrencyDocument:
    """Map a currency entity to MongoDB."""
    document = CurrencyDocument(
        code=value.code,
        name=value.name,
        symbol=value.symbol,
        kind=value.kind.value,
        country_codes=list(value.country_codes),
        is_active=value.is_active,
        created_at=value.created_at,
        updated_at=value.updated_at,
        schema_version=1,
    )
    if value.id is not None:
        document["_id"] = to_object_id(value.id)
    return document


def document_to_currency(document: CurrencyDocument) -> CurrencyCatalogEntry:
    """Map a MongoDB document to a currency entity."""
    return CurrencyCatalogEntry(
        id=str(document["_id"]),
        code=document["code"],
        name=document["name"],
        symbol=document.get("symbol"),
        kind=CurrencyKind(document["kind"]),
        country_codes=tuple(document["country_codes"]),
        is_active=document["is_active"],
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
