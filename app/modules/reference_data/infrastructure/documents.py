"""MongoDB document shapes for reference catalogs."""

from datetime import datetime
from typing import NotRequired, TypedDict

from bson import ObjectId


class CountryDocument(TypedDict):
    """Persisted country reference document."""

    _id: NotRequired[ObjectId]
    code: str
    alpha3_code: str
    name: str
    official_name: str
    currency_codes: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    schema_version: int


class CurrencyDocument(TypedDict):
    """Persisted fiat or crypto reference document."""

    _id: NotRequired[ObjectId]
    code: str
    name: str
    symbol: str | None
    kind: str
    country_codes: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    schema_version: int
