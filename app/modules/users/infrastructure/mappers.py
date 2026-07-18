"""Mapping between user domain objects and MongoDB documents."""

from bson import ObjectId

from app.modules.users.application.dto import RefreshTokenRecord
from app.modules.users.domain.entities import User
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.value_objects import CountryCode, Email
from app.modules.users.infrastructure.documents import (
    RefreshTokenDocument,
    UserDocument,
)
from app.shared.domain.value_objects import Currency
from app.shared.infrastructure.mongodb.object_id import to_object_id

_USER_SCHEMA_VERSION = 2
_REFRESH_TOKEN_SCHEMA_VERSION = 1


def user_to_document(user: User) -> UserDocument:
    """Map a domain user to its MongoDB document."""
    document = UserDocument(
        email=user.email.value,
        normalized_email=user.email.normalized,
        password_hash=user.password_hash,
        role=user.role.value,
        favorite_currency=(
            user.favorite_currency.code if user.favorite_currency is not None else None
        ),
        country_code=(
            user.country_code.value if user.country_code is not None else None
        ),
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        schema_version=_USER_SCHEMA_VERSION,
    )
    if user.id is not None:
        document["_id"] = to_object_id(user.id)
    return document


def document_to_user(document: UserDocument) -> User:
    """Map a MongoDB user document to the domain entity."""
    object_id = document.get("_id")
    if not isinstance(object_id, ObjectId):
        raise ValueError("A persisted user document requires an ObjectId.")
    favorite_currency = document.get("favorite_currency")
    country_code = document.get("country_code")

    return User(
        id=str(object_id),
        email=Email.create(document["email"]),
        password_hash=document["password_hash"],
        role=UserRole(document["role"]),
        favorite_currency=(
            Currency.create(favorite_currency)
            if favorite_currency is not None
            else None
        ),
        country_code=(
            CountryCode.create(country_code) if country_code is not None else None
        ),
        is_active=document["is_active"],
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )


def refresh_token_to_document(
    record: RefreshTokenRecord,
) -> RefreshTokenDocument:
    """Map application refresh-token state to MongoDB."""
    return RefreshTokenDocument(
        _id=record.id,
        user_id=to_object_id(record.user_id),
        token_hash=record.token_hash,
        family_id=record.family_id,
        expires_at=record.expires_at,
        revoked_at=record.revoked_at,
        replaced_by_id=record.replaced_by_id,
        created_at=record.created_at,
        schema_version=_REFRESH_TOKEN_SCHEMA_VERSION,
    )


def document_to_refresh_token(
    document: RefreshTokenDocument,
) -> RefreshTokenRecord:
    """Map a MongoDB refresh-token document to application state."""
    return RefreshTokenRecord(
        id=document["_id"],
        user_id=str(document["user_id"]),
        token_hash=document["token_hash"],
        family_id=document["family_id"],
        expires_at=document["expires_at"],
        revoked_at=document["revoked_at"],
        replaced_by_id=document["replaced_by_id"],
        created_at=document["created_at"],
    )
