"""MongoDB document typing for accounts."""

from datetime import datetime
from typing import NotRequired, TypedDict

from bson import Decimal128, ObjectId


class AccountDocument(TypedDict):
    """Stored representation of a financial account."""

    _id: NotRequired[ObjectId]
    user_id: ObjectId
    account_type_id: ObjectId
    name: str
    normalized_name: str
    description: str | None
    initial_balance: Decimal128
    balance: Decimal128
    currency: str
    is_favorite: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    schema_version: int
