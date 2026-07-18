"""Reference catalog enumerations."""

from enum import StrEnum


class CurrencyKind(StrEnum):
    """Supported kinds of monetary assets."""

    FIAT = "fiat"
    CRYPTO = "crypto"
