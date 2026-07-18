"""HTTP schemas for countries and monetary assets."""

from pydantic import BaseModel, ConfigDict

from app.modules.reference_data.domain.enums import CurrencyKind


class CountryResponse(BaseModel):
    """Public country catalog entry."""

    id: str
    code: str
    alpha3_code: str
    name: str
    official_name: str
    currency_codes: tuple[str, ...]

    model_config = ConfigDict(from_attributes=True)


class CurrencyResponse(BaseModel):
    """Public fiat or crypto catalog entry."""

    id: str
    code: str
    name: str
    symbol: str | None
    kind: CurrencyKind
    country_codes: tuple[str, ...]

    model_config = ConfigDict(from_attributes=True)
