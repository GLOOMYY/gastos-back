"""MongoDB document shapes for users and refresh tokens."""

from datetime import datetime
from typing import NotRequired, TypedDict

from bson import ObjectId


class UserDocument(TypedDict):
    """Persisted MongoDB representation of a user."""

    _id: NotRequired[ObjectId]
    email: str
    normalized_email: str
    password_hash: str
    role: str
    favorite_currency: NotRequired[str | None]
    country_code: NotRequired[str | None]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    schema_version: int


class RefreshTokenDocument(TypedDict):
    """Persisted MongoDB representation of a refresh-token session."""

    _id: str
    user_id: ObjectId
    token_hash: str
    family_id: str
    expires_at: datetime
    revoked_at: datetime | None
    replaced_by_id: str | None
    created_at: datetime
    schema_version: int
