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


class AccountTypeNotFoundError(AccountTypeDomainError):
    """Raised when an account type is unavailable to a user."""

    def __init__(self) -> None:
        """Initialize the missing account type error."""
        super().__init__("The account type was not found.")


class AccountTypeAccessDeniedError(AccountTypeDomainError):
    """Raised when a user attempts to mutate a global or foreign type."""

    def __init__(self) -> None:
        """Initialize the account type authorization error."""
        super().__init__("The account type cannot be modified by this user.")


class AccountTypeNameAlreadyExistsError(AccountTypeDomainError):
    """Raised when an owner already has an active type with the same name."""

    def __init__(self) -> None:
        """Initialize the duplicate account type name error."""
        super().__init__("An account type with this name already exists.")
