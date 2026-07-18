"""Exceptions shared by multiple domain modules."""


class SharedDomainError(Exception):
    """Base exception for shared domain rule violations."""


class InvalidCurrencyError(SharedDomainError):
    """Raised when a currency code is malformed."""

    def __init__(self) -> None:
        """Initialize the invalid currency error."""
        super().__init__("The currency code must contain three letters.")
