"""Unit tests for the shared currency value object."""

import pytest

from app.shared.domain.exceptions import InvalidCurrencyError
from app.shared.domain.value_objects import Currency


def test_currency_is_normalized_to_uppercase() -> None:
    """A valid currency is trimmed and normalized."""
    currency = Currency.create(" cop ")

    assert currency.code == "COP"
    assert str(currency) == "COP"


def test_currency_accepts_longer_cryptocurrency_codes() -> None:
    """Well-known crypto symbols may contain more than three letters."""
    assert Currency.create("doge").code == "DOGE"


@pytest.mark.parametrize("value", ["", "CO", "COP1", "12A"])
def test_currency_rejects_invalid_codes(value: str) -> None:
    """A monetary asset code must contain 3-10 letters."""
    with pytest.raises(InvalidCurrencyError):
        Currency.create(value)
