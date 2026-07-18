"""Domain exceptions for the users module."""


class UserDomainError(Exception):
    """Base exception for user domain rule violations."""


class InvalidEmailError(UserDomainError):
    """Raised when an email address does not meet domain requirements."""

    def __init__(self) -> None:
        """Initialize the error without retaining personal information."""
        super().__init__("The email address is invalid.")


class EmptyPasswordHashError(UserDomainError):
    """Raised when a user is created without a password hash."""

    def __init__(self) -> None:
        """Initialize the empty password hash error."""
        super().__init__("The password hash cannot be empty.")
