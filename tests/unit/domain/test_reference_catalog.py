"""Integrity tests for versioned country and monetary-asset data."""

from scripts.data.reference_catalog import (
    COUNTRY_DATA,
    CRYPTO_CURRENCY_DATA,
    FIAT_CURRENCY_DATA,
)


def test_reference_catalog_has_unique_and_complete_relations() -> None:
    """Every country currency points to one unique seeded fiat entry."""
    country_codes = [value[0] for value in COUNTRY_DATA]
    fiat_codes = [value[0] for value in FIAT_CURRENCY_DATA]
    crypto_codes = [value[0] for value in CRYPTO_CURRENCY_DATA]
    referenced_fiat = {
        currency_code for country in COUNTRY_DATA for currency_code in country[4]
    }

    assert len(COUNTRY_DATA) == 250
    assert len(country_codes) == len(set(country_codes))
    assert len(fiat_codes) == len(set(fiat_codes))
    assert len(crypto_codes) == len(set(crypto_codes))
    assert referenced_fiat <= set(fiat_codes)
    assert {"BTC", "ETH", "USDT", "BNB", "XRP", "USDC", "SOL"} <= set(crypto_codes)


def test_colombia_and_recent_iso_currency_changes_are_present() -> None:
    """The starter locale and current ISO 4217 changes stay protected."""
    countries = {value[0]: value[4] for value in COUNTRY_DATA}

    assert countries["CO"] == ("COP",)
    assert countries["BG"] == ("EUR",)
    assert countries["CW"] == ("XCG",)
    assert countries["SL"] == ("SLE",)
    assert countries["ZW"] == ("ZWG",)
