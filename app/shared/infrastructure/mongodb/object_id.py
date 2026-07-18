"""Safe conversion helpers for MongoDB ObjectId values."""

from bson import ObjectId
from bson.errors import InvalidId


class InvalidObjectIdError(ValueError):
    """Raised when a public identifier is not a valid ObjectId string."""


def to_object_id(value: str) -> ObjectId:
    """Convert a public string identifier to ObjectId.

    Args:
        value: MongoDB ObjectId serialized as a string.

    Returns:
        The BSON ObjectId.

    Raises:
        InvalidObjectIdError: If the value is malformed.
    """
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as error:
        raise InvalidObjectIdError("The identifier is invalid.") from error
