"""Idempotently create the initial user configured through environment."""

import asyncio
from enum import StrEnum
import logging

from app.core.config import Settings, get_settings
from app.modules.users.application.dto import CreateUserCommand
from app.modules.users.application.use_cases.create_user import CreateUser
from app.modules.users.domain.exceptions import UserAlreadyExistsError
from app.modules.users.infrastructure.password_hasher import (
    PasslibPasswordHasher,
)
from app.modules.users.infrastructure.repositories import MongoUserRepository
from app.shared.infrastructure.mongodb.client import MongoDatabase
from app.shared.infrastructure.mongodb.indexes import create_indexes
from app.shared.infrastructure.mongodb.schema import (
    ensure_auth_collection_schemas,
)

logger = logging.getLogger(__name__)


class SeedOutcome(StrEnum):
    """Possible idempotent outcomes of the initial-user seed."""

    CREATED = "created"
    ALREADY_EXISTS = "already_exists"


async def create_initial_user(
    use_case: CreateUser,
    email: str,
    password: str,
) -> SeedOutcome:
    """Create the configured user unless its email is already registered.

    Args:
        use_case: Real or fake registration use case.
        email: Initial user email address.
        password: Initial raw password supplied through secret configuration.

    Returns:
        Whether the user was created or already existed.
    """
    try:
        await use_case.execute(
            CreateUserCommand(
                email=email,
                password=password,
            )
        )
    except UserAlreadyExistsError:
        return SeedOutcome.ALREADY_EXISTS
    return SeedOutcome.CREATED


async def seed_initial_user(settings: Settings) -> SeedOutcome:
    """Connect to MongoDB and run the initial-user seed.

    Args:
        settings: Environment-based application configuration.

    Returns:
        The idempotent seed outcome.

    Raises:
        RuntimeError: If a required seed or MongoDB setting is missing.
    """
    mongodb_uri = settings.mongodb_uri
    database_name = settings.mongodb_database
    email = settings.initial_user_email
    password = settings.initial_user_password

    missing_settings: list[str] = []
    if mongodb_uri is None or not mongodb_uri.get_secret_value().strip():
        missing_settings.append("MONGODB_URI")
    if database_name is None or not database_name.strip():
        missing_settings.append("MONGODB_DATABASE")
    if email is None or not email.strip():
        missing_settings.append("INITIAL_USER_EMAIL")
    if password is None or not password.get_secret_value():
        missing_settings.append("INITIAL_USER_PASSWORD")
    if missing_settings:
        names = ", ".join(missing_settings)
        raise RuntimeError(f"Missing required settings: {names}.")

    if (
        mongodb_uri is None
        or password is None
        or database_name is None
        or email is None
    ):
        raise RuntimeError("Initial user seed configuration is incomplete.")

    mongo_database = MongoDatabase()
    try:
        await mongo_database.connect(
            mongodb_uri.get_secret_value(),
            database_name,
        )
        database = mongo_database.get_database()
        await ensure_auth_collection_schemas(database)
        await create_indexes(database)
        use_case = CreateUser(
            user_repository=MongoUserRepository(database),
            password_hasher=PasslibPasswordHasher(),
        )
        return await create_initial_user(
            use_case=use_case,
            email=email,
            password=password.get_secret_value(),
        )
    finally:
        await mongo_database.disconnect()


def main() -> None:
    """Run the initial-user seed and report a secret-safe outcome."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    outcome = asyncio.run(seed_initial_user(get_settings()))
    logger.info("event=initial_user_seed_completed outcome=%s", outcome.value)


if __name__ == "__main__":
    main()
