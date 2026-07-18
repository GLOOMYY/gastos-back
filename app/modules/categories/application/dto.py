"""Application DTOs for categories."""

from dataclasses import dataclass
from datetime import datetime

from app.modules.categories.domain.enums import CategoryTransactionType


@dataclass(frozen=True, slots=True)
class CreateCategoryCommand:
    """Input for private category creation."""

    user_id: str
    name: str
    transaction_type: CategoryTransactionType
    description: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateCategoryCommand:
    """Input for category updating."""

    user_id: str
    category_id: str
    name: str
    transaction_type: CategoryTransactionType
    description: str | None = None


@dataclass(frozen=True, slots=True)
class CategoryResult:
    """Category data returned to presentation."""

    id: str
    user_id: str | None
    name: str
    transaction_type: CategoryTransactionType
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
