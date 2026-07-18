"""MongoDB JSON Schema management for authentication collections."""

from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.shared.infrastructure.mongodb.client import MongoDocument

_USER_VALIDATOR: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "email",
            "normalized_email",
            "password_hash",
            "role",
            "favorite_currency",
            "country_code",
            "is_active",
            "created_at",
            "updated_at",
            "schema_version",
        ],
        "properties": {
            "email": {"bsonType": "string"},
            "normalized_email": {"bsonType": "string"},
            "password_hash": {"bsonType": "string"},
            "role": {"enum": ["user"]},
            "favorite_currency": {"bsonType": ["string", "null"]},
            "country_code": {"bsonType": ["string", "null"]},
            "is_active": {"bsonType": "bool"},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
            "schema_version": {"bsonType": "int"},
        },
    }
}

_REFRESH_TOKEN_VALIDATOR: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "_id",
            "user_id",
            "token_hash",
            "family_id",
            "expires_at",
            "revoked_at",
            "replaced_by_id",
            "created_at",
            "schema_version",
        ],
        "properties": {
            "_id": {"bsonType": "string"},
            "user_id": {"bsonType": "objectId"},
            "token_hash": {"bsonType": "string"},
            "family_id": {"bsonType": "string"},
            "expires_at": {"bsonType": "date"},
            "revoked_at": {"bsonType": ["date", "null"]},
            "replaced_by_id": {"bsonType": ["string", "null"]},
            "created_at": {"bsonType": "date"},
            "schema_version": {"bsonType": "int"},
        },
    }
}

_ACCOUNT_TYPE_VALIDATOR: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "user_id",
            "name",
            "normalized_name",
            "is_active",
            "created_at",
            "updated_at",
            "schema_version",
        ],
        "properties": {
            "user_id": {"bsonType": ["objectId", "null"]},
            "code": {"bsonType": ["string", "null"]},
            "name": {"bsonType": "string"},
            "normalized_name": {"bsonType": "string"},
            "description": {"bsonType": ["string", "null"]},
            "is_active": {"bsonType": "bool"},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
            "schema_version": {"bsonType": "int"},
        },
    }
}

_CATEGORY_VALIDATOR: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "user_id",
            "name",
            "normalized_name",
            "transaction_type",
            "is_active",
            "created_at",
            "updated_at",
            "schema_version",
        ],
        "properties": {
            "user_id": {"bsonType": ["objectId", "null"]},
            "name": {"bsonType": "string"},
            "normalized_name": {"bsonType": "string"},
            "transaction_type": {"enum": ["income", "expense"]},
            "description": {"bsonType": ["string", "null"]},
            "is_active": {"bsonType": "bool"},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
            "schema_version": {"bsonType": "int"},
        },
    }
}

_ACCOUNT_VALIDATOR: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "user_id",
            "account_type_id",
            "name",
            "normalized_name",
            "initial_balance",
            "balance",
            "currency",
            "is_favorite",
            "is_active",
            "created_at",
            "updated_at",
            "schema_version",
        ],
        "properties": {
            "user_id": {"bsonType": "objectId"},
            "account_type_id": {"bsonType": "objectId"},
            "name": {"bsonType": "string"},
            "normalized_name": {"bsonType": "string"},
            "description": {"bsonType": ["string", "null"]},
            "initial_balance": {"bsonType": "decimal"},
            "balance": {"bsonType": "decimal"},
            "currency": {"bsonType": "string"},
            "is_favorite": {"bsonType": "bool"},
            "is_active": {"bsonType": "bool"},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
            "schema_version": {"bsonType": "int"},
        },
    }
}

_COUNTRY_VALIDATOR: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "code",
            "alpha3_code",
            "name",
            "official_name",
            "currency_codes",
            "is_active",
            "created_at",
            "updated_at",
            "schema_version",
        ],
        "properties": {
            "code": {"bsonType": "string"},
            "alpha3_code": {"bsonType": "string"},
            "name": {"bsonType": "string"},
            "official_name": {"bsonType": "string"},
            "currency_codes": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
            },
            "is_active": {"bsonType": "bool"},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
            "schema_version": {"bsonType": "int"},
        },
    }
}

_CURRENCY_VALIDATOR: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "code",
            "name",
            "symbol",
            "kind",
            "country_codes",
            "is_active",
            "created_at",
            "updated_at",
            "schema_version",
        ],
        "properties": {
            "code": {"bsonType": "string"},
            "name": {"bsonType": "string"},
            "symbol": {"bsonType": ["string", "null"]},
            "kind": {"enum": ["fiat", "crypto"]},
            "country_codes": {
                "bsonType": "array",
                "items": {"bsonType": "string"},
            },
            "is_active": {"bsonType": "bool"},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
            "schema_version": {"bsonType": "int"},
        },
    }
}

_TRANSACTION_VALIDATOR: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "user_id",
            "account_id",
            "transaction_type",
            "amount",
            "currency",
            "occurred_at",
            "status",
            "created_at",
            "updated_at",
            "schema_version",
        ],
        "properties": {
            "user_id": {"bsonType": "objectId"},
            "account_id": {"bsonType": "objectId"},
            "category_id": {"bsonType": ["objectId", "null"]},
            "transaction_type": {"bsonType": "string"},
            "amount": {"bsonType": "decimal"},
            "currency": {"bsonType": "string"},
            "occurred_at": {"bsonType": "date"},
            "description": {"bsonType": ["string", "null"]},
            "note": {"bsonType": ["string", "null"]},
            "reversal_of_id": {"bsonType": ["objectId", "null"]},
            "transfer_id": {"bsonType": "string"},
            "exchange_rate": {"bsonType": "decimal"},
            "exchange_rate_mode": {"enum": ["market", "custom"]},
            "exchange_rate_provider": {"bsonType": "string"},
            "exchange_rate_timestamp": {"bsonType": "date"},
            "source_amount": {"bsonType": "decimal"},
            "target_amount": {"bsonType": "decimal"},
            "source_currency": {"bsonType": "string"},
            "target_currency": {"bsonType": "string"},
            "status": {"bsonType": "string"},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
            "schema_version": {"bsonType": "int"},
        },
    }
}


async def ensure_auth_collection_schemas(
    database: AsyncDatabase[MongoDocument],
) -> None:
    """Create or update JSON Schema validators for auth collections."""
    existing_collections = set(await database.list_collection_names())
    await _ensure_collection(
        database,
        existing_collections,
        "users",
        _USER_VALIDATOR,
    )
    await _ensure_collection(
        database,
        existing_collections,
        "refresh_tokens",
        _REFRESH_TOKEN_VALIDATOR,
    )
    for collection_name, validator in (
        ("account_types", _ACCOUNT_TYPE_VALIDATOR),
        ("categories", _CATEGORY_VALIDATOR),
        ("accounts", _ACCOUNT_VALIDATOR),
        ("transactions", _TRANSACTION_VALIDATOR),
        ("countries", _COUNTRY_VALIDATOR),
        ("currencies", _CURRENCY_VALIDATOR),
    ):
        await _ensure_collection(
            database,
            existing_collections,
            collection_name,
            validator,
        )


async def update_transaction_collection_schema(
    database: AsyncDatabase[MongoDocument],
) -> None:
    """Apply the current transaction validator to an existing collection."""
    await database.command(
        {
            "collMod": "transactions",
            "validator": _TRANSACTION_VALIDATOR,
            "validationLevel": "strict",
            "validationAction": "error",
        }
    )


async def update_user_collection_schema(
    database: AsyncDatabase[MongoDocument],
) -> None:
    """Apply the current user validator to an existing collection."""
    await _update_collection_schema(database, "users", _USER_VALIDATOR)


async def update_account_collection_schema(
    database: AsyncDatabase[MongoDocument],
) -> None:
    """Apply the current account validator to an existing collection."""
    await _update_collection_schema(database, "accounts", _ACCOUNT_VALIDATOR)


async def _update_collection_schema(
    database: AsyncDatabase[MongoDocument],
    collection_name: str,
    validator: dict[str, Any],
) -> None:
    """Apply one strict validator through MongoDB collMod."""
    await database.command(
        {
            "collMod": collection_name,
            "validator": validator,
            "validationLevel": "strict",
            "validationAction": "error",
        }
    )


async def _ensure_collection(
    database: AsyncDatabase[MongoDocument],
    existing_collections: set[str],
    collection_name: str,
    validator: dict[str, Any],
) -> None:
    """Create a validated collection when it does not exist.

    Existing validator changes are intentionally left to versioned migration
    scripts instead of being applied during application startup.
    """
    if collection_name in existing_collections:
        return

    await database.create_collection(
        collection_name,
        validator=validator,
        validationLevel="strict",
        validationAction="error",
    )
