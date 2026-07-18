"""Domain exceptions for exchange-rate operations."""


class ExchangeRateError(Exception):
    """Base exception for exchange-rate failures."""


class UnsupportedExchangeRateCurrencyError(ExchangeRateError):
    """Raised when the provider does not support a currency code."""

    def __init__(self) -> None:
        """Initialize a safe currency support error."""
        super().__init__("One or both currency codes are not supported.")


class InvalidConversionAmountError(ExchangeRateError):
    """Raised when a conversion amount is not positive."""

    def __init__(self) -> None:
        """Initialize the invalid monetary amount error."""
        super().__init__("The conversion amount must be greater than zero.")


class ExchangeRateUnavailableError(ExchangeRateError):
    """Raised when the external provider cannot supply a trustworthy rate."""

    def __init__(self) -> None:
        """Initialize an error that does not expose provider credentials."""
        super().__init__("Exchange-rate data is temporarily unavailable.")
