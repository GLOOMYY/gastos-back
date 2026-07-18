"""MongoDB document typing for categories."""

from datetime import datetime
from typing import NotRequired, TypedDict

from bson import ObjectId


class CategoryDocument(TypedDict):
    """Stored category representation."""

    _id: NotRequired[ObjectId]
    user_id: ObjectId | None
    name: str
    normalized_name: str
    transaction_type: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    schema_version: int
