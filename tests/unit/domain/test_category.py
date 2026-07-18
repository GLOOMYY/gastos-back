"""Unit tests for the financial category domain entity."""

import pytest

from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.enums import CategoryTransactionType
from app.modules.categories.domain.exceptions import (
    InvalidCategoryNameError,
    InvalidCategoryOwnerError,
)


def test_create_global_category() -> None:
    """A category without an owner is available globally."""
    category = Category.create(
        name=" Groceries ",
        transaction_type=CategoryTransactionType.EXPENSE,
        description=" Food and household supplies ",
    )

    assert category.id is None
    assert category.user_id is None
    assert category.name == "Groceries"
    assert category.normalized_name == "groceries"
    assert category.description == "Food and household supplies"
    assert category.is_global is True
    assert category.is_active is True


def test_create_user_owned_category() -> None:
    """A category may belong exclusively to one user."""
    category = Category.create(
        name="Freelance",
        transaction_type=CategoryTransactionType.INCOME,
        user_id=" user-1 ",
    )

    assert category.user_id == "user-1"
    assert category.is_global is False


def test_category_can_be_deactivated_and_activated() -> None:
    """Availability changes through explicit entity behavior."""
    category = Category.create(
        name="Groceries",
        transaction_type=CategoryTransactionType.EXPENSE,
    )

    category.deactivate()
    assert category.is_active is False

    category.activate()
    assert category.is_active is True


def test_category_rejects_blank_name() -> None:
    """Categories require a visible name."""
    with pytest.raises(InvalidCategoryNameError):
        Category.create(
            name=" ",
            transaction_type=CategoryTransactionType.EXPENSE,
        )


def test_category_rejects_blank_user_owner() -> None:
    """A present owner identifier cannot be blank."""
    with pytest.raises(InvalidCategoryOwnerError):
        Category.create(
            name="Groceries",
            transaction_type=CategoryTransactionType.EXPENSE,
            user_id=" ",
        )
