"""HTTP schemas for exchange rates and currency conversion."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ConvertCurrencyRequest(BaseModel):
    """Request to convert a positive amount between two currencies."""

    source_currency: str = Field(min_length=3, max_length=3)
    target_currency: str = Field(min_length=3, max_length=3)
    amount: Decimal = Field(gt=0)


class ExchangeRateResponse(BaseModel):
    """Public latest exchange-rate quote."""

    source_currency: str
    target_currency: str
    rate: Decimal
    provider: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CurrencyConversionResponse(BaseModel):
    """Public conversion result including quote traceability."""

    source_currency: str
    target_currency: str
    source_amount: Decimal
    converted_amount: Decimal
    rate: Decimal
    provider: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
