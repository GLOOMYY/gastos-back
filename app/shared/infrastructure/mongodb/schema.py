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
