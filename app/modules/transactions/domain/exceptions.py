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


class TransactionNotFoundError(TransactionDomainError):
    """Raised when a transaction cannot be found."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__("The transaction was not found.")


class TransactionAlreadyReversedError(TransactionDomainError):
    """Raised when a confirmed transaction already has a reversal."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__("The transaction has already been reversed.")


class InvalidTransactionCategoryError(TransactionDomainError):
    """Raised when a category is unavailable or has the wrong type."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__("The category is invalid for this transaction.")


class TransactionCannotBeReversedError(TransactionDomainError):
    """Raised when a ledger entry is not eligible for reversal."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__("This transaction cannot be reversed.")


class InvalidTransactionCursorError(TransactionDomainError):
    """Raised when a transaction pagination cursor is malformed."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__("The transaction cursor is invalid.")


class InvalidCashFlowRangeError(TransactionDomainError):
    """Raised when a chart date range is reversed or too large."""

    def __init__(self) -> None:
        """Initialize the error."""
        super().__init__(
            "The cash-flow date range must contain between 1 and 366 days."
        )
