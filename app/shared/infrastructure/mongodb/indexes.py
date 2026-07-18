"""MongoDB index management."""

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.shared.infrastructure.mongodb.client import MongoDocument


async def create_indexes(
    database: AsyncDatabase[MongoDocument],
) -> None:
    """Create indexes required by implemented application queries."""
    await database.users.create_index(
        [("normalized_email", ASCENDING)],
        unique=True,
        name="uq_users_normalized_email",
    )
    await database.refresh_tokens.create_index(
        [("token_hash", ASCENDING)],
        unique=True,
        name="uq_refresh_tokens_token_hash",
    )
    await database.refresh_tokens.create_index(
        [("family_id", ASCENDING)],
        name="ix_refresh_tokens_family_id",
    )
    await database.refresh_tokens.create_index(
        [("user_id", ASCENDING)],
        name="ix_refresh_tokens_user_id",
    )
    await database.refresh_tokens.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        name="ix_refresh_tokens_expires_ttl",
    )
    await database.account_types.create_index(
        [("user_id", ASCENDING), ("normalized_name", ASCENDING)],
        unique=True,
        partialFilterExpression={"is_active": True},
        name="uq_account_types_owner_active_name",
    )
    await database.categories.create_index(
        [
            ("user_id", ASCENDING),
            ("normalized_name", ASCENDING),
            ("transaction_type", ASCENDING),
        ],
        unique=True,
        partialFilterExpression={"is_active": True},
        name="uq_categories_owner_active_name_type",
    )
    await database.accounts.create_index(
        [("user_id", ASCENDING), ("normalized_name", ASCENDING)],
        unique=True,
        partialFilterExpression={"is_active": True},
        name="uq_accounts_owner_active_name",
    )
    await database.accounts.create_index(
        [
            ("user_id", ASCENDING),
            ("is_active", DESCENDING),
            ("created_at", DESCENDING),
        ],
        name="ix_accounts_owner_active_created",
    )
    await database.accounts.create_index(
        [("user_id", ASCENDING), ("is_favorite", ASCENDING)],
        unique=True,
        partialFilterExpression={
            "is_favorite": True,
            "is_active": True,
        },
        name="uq_accounts_owner_favorite",
    )
    await database.transactions.create_index(
        [
            ("user_id", ASCENDING),
            ("occurred_at", DESCENDING),
            ("_id", DESCENDING),
        ],
        name="ix_transactions_owner_occurred",
    )
    await database.transactions.create_index(
        [
            ("user_id", ASCENDING),
            ("currency", ASCENDING),
            ("occurred_at", ASCENDING),
        ],
        name="ix_transactions_owner_currency_occurred",
    )
    await database.transactions.create_index(
        [("user_id", ASCENDING), ("note", ASCENDING)],
        name="ix_transactions_owner_note",
    )
    await database.transactions.create_index(
        [
            ("user_id", ASCENDING),
            ("account_id", ASCENDING),
            ("occurred_at", DESCENDING),
        ],
        name="ix_transactions_owner_account_occurred",
    )
    await database.transactions.create_index(
        [("reversal_of_id", ASCENDING)],
        unique=True,
        partialFilterExpression={"reversal_of_id": {"$type": "objectId"}},
        name="uq_transactions_reversal_of",
    )
    await database.transactions.create_index(
        [("transfer_id", ASCENDING)],
        partialFilterExpression={"transfer_id": {"$type": "string"}},
        name="ix_transactions_transfer_id",
    )
    await database.countries.create_index(
        [("code", ASCENDING)],
        unique=True,
        name="uq_countries_code",
    )
    await database.countries.create_index(
        [("alpha3_code", ASCENDING)],
        unique=True,
        name="uq_countries_alpha3_code",
    )
    await database.countries.create_index(
        [("is_active", DESCENDING), ("name", ASCENDING)],
        name="ix_countries_active_name",
    )
    await database.currencies.create_index(
        [("code", ASCENDING)],
        unique=True,
        name="uq_currencies_code",
    )
    await database.currencies.create_index(
        [("is_active", DESCENDING), ("kind", ASCENDING), ("code", ASCENDING)],
        name="ix_currencies_active_kind_code",
    )
    await database.currencies.create_index(
        [("country_codes", ASCENDING), ("kind", ASCENDING), ("code", ASCENDING)],
        name="ix_currencies_country_kind_code",
    )
