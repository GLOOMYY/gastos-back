"""Small infrastructure services used by authentication use cases."""

from datetime import UTC, datetime
from uuid import uuid4


class SystemClock:
    """Provide timezone-aware current UTC time."""

    def now(self) -> datetime:
        """Return the current UTC time."""
        return datetime.now(UTC)


class UuidGenerator:
    """Generate unpredictable UUID identifiers."""

    def generate(self) -> str:
        """Return a random UUID string."""
        return str(uuid4())
