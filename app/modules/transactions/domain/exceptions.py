"""Domain exceptions for financial transactions."""


class TransactionDomainError(Exception):
    """Base exception for transaction rule violations."""


class InvalidTransactionIdentifierError(TransactionDomainError):
    """Raised when a required transaction identifier is blank."""

    def __init__(self, field_name: str) -> None:
        """Initialize the invalid identifier error.

        Args:
            field_name: Name of the rejected identifier field.
        """
        super().__init__(f"The {field_name} cannot be empty.")


class InvalidTransactionAmountError(TransactionDomainError):
    """Raised when a transaction amount is not a positive Decimal."""

    def __init__(self) -> None:
        """Initialize the invalid transaction amount error."""
        super().__init__("The transaction amount must be a positive Decimal.")


class InvalidTransactionDateError(TransactionDomainError):
    """Raised when a movement date has no timezone."""

    def __init__(self) -> None:
        """Initialize the invalid transaction date error."""
        super().__init__("The transaction date must be timezone-aware.")
