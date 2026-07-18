"""Lifecycle management for the asynchronous MongoDB client."""

from typing import Any

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

MongoDocument = dict[str, Any]


class MongoDatabase:
    """Own a reusable asynchronous MongoDB client and database handle."""

    def __init__(self) -> None:
        """Initialize a disconnected MongoDB holder."""
        self.client: AsyncMongoClient[MongoDocument] | None = None
        self.database: AsyncDatabase[MongoDocument] | None = None

    async def connect(self, uri: str, database_name: str) -> None:
        """Connect to MongoDB and verify server availability.

        Args:
            uri: MongoDB connection string.
            database_name: Database selected for the application.
        """
        self.client = AsyncMongoClient[MongoDocument](uri)
        self.database = self.client[database_name]
        await self.client.admin.command("ping")

    async def disconnect(self) -> None:
        """Close the MongoDB client when it is connected."""
        if self.client is not None:
            await self.client.close()
        self.client = None
        self.database = None

    def get_database(self) -> AsyncDatabase[MongoDocument]:
        """Return the initialized database handle.

        Raises:
            RuntimeError: If MongoDB is not connected.
        """
        if self.database is None:
            raise RuntimeError("MongoDB is not configured or connected.")
        return self.database
