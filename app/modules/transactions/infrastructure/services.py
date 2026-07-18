"""Infrastructure services for transaction use cases."""

from uuid import uuid4


class UuidTransferIdGenerator:
    """Generate unpredictable identifiers shared by transfer entries."""

    def generate(self) -> str:
        """Return a random UUID string."""
        return str(uuid4())
