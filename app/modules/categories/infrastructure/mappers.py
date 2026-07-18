"""Mappings between categories and MongoDB documents."""

from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.enums import CategoryTransactionType
from app.modules.categories.infrastructure.documents import CategoryDocument
from app.shared.infrastructure.mongodb.object_id import to_object_id


def category_to_document(value: Category) -> CategoryDocument:
    """Convert a category to a MongoDB document."""
    document = CategoryDocument(
        user_id=to_object_id(value.user_id) if value.user_id else None,
        name=value.name,
        normalized_name=value.normalized_name,
        transaction_type=value.transaction_type.value,
        description=value.description,
        is_active=value.is_active,
        created_at=value.created_at,
        updated_at=value.updated_at,
        schema_version=1,
    )
    if value.id is not None:
        document["_id"] = to_object_id(value.id)
    return document


def document_to_category(document: CategoryDocument) -> Category:
    """Convert a MongoDB document to a category entity."""
    owner = document["user_id"]
    return Category(
        id=str(document["_id"]),
        user_id=str(owner) if owner is not None else None,
        name=document["name"],
        transaction_type=CategoryTransactionType(document["transaction_type"]),
        description=document.get("description"),
        is_active=document["is_active"],
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
