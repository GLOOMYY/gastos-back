"""Domain exceptions for account types."""


class AccountTypeDomainError(Exception):
    """Base exception for account type rule violations."""


class InvalidAccountTypeNameError(AccountTypeDomainError):
    """Raised when an account type name is blank."""

    def __init__(self) -> None:
        """Initialize the invalid account type name error."""
        super().__init__("The account type name cannot be empty.")


class InvalidAccountTypeOwnerError(AccountTypeDomainError):
    """Raised when a non-global account type has an empty owner."""

    def __init__(self) -> None:
        """Initialize the invalid account type owner error."""
        super().__init__("The account type owner cannot be empty.")
