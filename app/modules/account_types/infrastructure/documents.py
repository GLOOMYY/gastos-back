"""MongoDB document typing for account types."""

from datetime import datetime
from typing import NotRequired, TypedDict

from bson import ObjectId


class AccountTypeDocument(TypedDict):
    """Stored representation of an account type."""

    _id: NotRequired[ObjectId]
    user_id: ObjectId | None
    code: str | None
    name: str
    normalized_name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    schema_version: int
