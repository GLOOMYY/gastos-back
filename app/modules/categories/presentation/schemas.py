"""HTTP schemas for categories."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.categories.domain.enums import CategoryTransactionType


class CreateCategoryRequest(BaseModel):
    """Request to create a private category."""

    name: str = Field(min_length=1, max_length=80)
    transaction_type: CategoryTransactionType
    description: str | None = Field(default=None, max_length=300)


class UpdateCategoryRequest(CreateCategoryRequest):
    """Request to replace editable category metadata."""


class CategoryResponse(BaseModel):
    """Public category representation."""

    id: str
    user_id: str | None
    name: str
    transaction_type: CategoryTransactionType
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
