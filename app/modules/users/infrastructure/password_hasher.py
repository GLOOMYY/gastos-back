"""Passlib password hashing adapter."""

from passlib.context import CryptContext  # type: ignore[import-untyped]
from passlib.exc import InvalidHashError  # type: ignore[import-untyped]


class PasslibPasswordHasher:
    """Hash and verify passwords using Argon2 through Passlib."""

    def __init__(self) -> None:
        """Configure the approved password hashing scheme."""
        self._context = CryptContext(
            schemes=["argon2"],
            deprecated="auto",
        )

    def hash(self, password: str) -> str:
        """Return an Argon2 hash for a raw password."""
        return self._context.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        """Safely verify a raw password against its stored hash."""
        try:
            return self._context.verify(password, password_hash)
        except (InvalidHashError, ValueError, TypeError):
            return False
