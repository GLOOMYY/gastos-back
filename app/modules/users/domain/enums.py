"""Domain enumerations for the users module."""

from enum import StrEnum


class UserRole(StrEnum):
    """Roles currently supported by the application."""

    USER = "user"
