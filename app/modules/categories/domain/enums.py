"""Domain enumerations for financial categories."""

from enum import StrEnum


class CategoryTransactionType(StrEnum):
    """Movement directions supported by a category."""

    INCOME = "income"
    EXPENSE = "expense"
