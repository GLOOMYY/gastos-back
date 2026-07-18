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
