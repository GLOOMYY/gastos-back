"""Domain exceptions for financial accounts."""


class AccountDomainError(Exception):
    """Base exception for account rule violations."""


class InvalidAccountNameError(AccountDomainError):
    """Raised when an account name is blank."""

    def __init__(self) -> None:
        """Initialize the invalid account name error."""
        super().__init__("The account name cannot be empty.")


class InvalidAccountOwnerError(AccountDomainError):
    """Raised when an account has no valid owner."""

    def __init__(self) -> None:
        """Initialize the invalid account owner error."""
        super().__init__("The account owner cannot be empty.")


class InvalidAccountTypeIdError(AccountDomainError):
    """Raised when an account has no valid account type identifier."""

    def __init__(self) -> None:
        """Initialize the invalid account type identifier error."""
        super().__init__("The account type identifier cannot be empty.")


class InvalidAccountAmountError(AccountDomainError):
    """Raised when an account receives an invalid monetary amount."""

    def __init__(self, *, positive_required: bool = False) -> None:
        """Initialize the invalid monetary amount error.

        Args:
            positive_required: Whether the rejected amount had to be positive.
        """
        message = "The amount must use Decimal."
        if positive_required:
            message = "The amount must be a positive Decimal."
        super().__init__(message)
