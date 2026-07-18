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


class UserAlreadyExistsError(UserDomainError):
    """Raised when an email address is already registered."""

    def __init__(self) -> None:
        """Initialize the duplicate user error."""
        super().__init__("A user with this email already exists.")


class UserNotFoundError(UserDomainError):
    """Raised when a requested user does not exist."""

    def __init__(self) -> None:
        """Initialize the missing user error."""
        super().__init__("The user was not found.")


class InvalidCredentialsError(UserDomainError):
    """Raised when authentication credentials cannot be verified."""

    def __init__(self) -> None:
        """Initialize the invalid credentials error."""
        super().__init__("The email or password is incorrect.")


class InactiveUserError(UserDomainError):
    """Raised when an inactive user attempts an authenticated operation."""

    def __init__(self) -> None:
        """Initialize the inactive user error."""
        super().__init__("The user account is inactive.")


class InvalidPasswordError(UserDomainError):
    """Raised when a raw password does not meet registration requirements."""

    def __init__(self) -> None:
        """Initialize the invalid password error."""
        super().__init__("The password must contain between 8 and 128 characters.")


class InvalidAuthenticationTokenError(UserDomainError):
    """Raised when an access or refresh token cannot be trusted."""

    def __init__(self) -> None:
        """Initialize the invalid authentication token error."""
        super().__init__("The authentication token is invalid or expired.")


class NoUserChangesError(UserDomainError):
    """Raised when an update command contains no supported changes."""

    def __init__(self) -> None:
        """Initialize the empty user update error."""
        super().__init__("At least one user field must be updated.")
