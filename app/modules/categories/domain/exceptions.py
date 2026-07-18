"""Domain exceptions for financial categories."""


class CategoryDomainError(Exception):
    """Base exception for category rule violations."""


class InvalidCategoryNameError(CategoryDomainError):
    """Raised when a category name is blank."""

    def __init__(self) -> None:
        """Initialize the invalid category name error."""
        super().__init__("The category name cannot be empty.")


class InvalidCategoryOwnerError(CategoryDomainError):
    """Raised when a non-global category has an empty owner."""

    def __init__(self) -> None:
        """Initialize the invalid category owner error."""
        super().__init__("The category owner cannot be empty.")


class CategoryNotFoundError(CategoryDomainError):
    """Raised when a category is unavailable to a user."""

    def __init__(self) -> None:
        """Initialize the missing category error."""
        super().__init__("The category was not found.")


class CategoryAccessDeniedError(CategoryDomainError):
    """Raised when a user attempts to mutate a global or foreign category."""

    def __init__(self) -> None:
        """Initialize the category authorization error."""
        super().__init__("The category cannot be modified by this user.")


class CategoryNameAlreadyExistsError(CategoryDomainError):
    """Raised when a category name already exists in an ownership scope."""

    def __init__(self) -> None:
        """Initialize the duplicate category name error."""
        super().__init__("A category with this name already exists.")
