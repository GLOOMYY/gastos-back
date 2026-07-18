"""Domain enumerations for financial transactions."""

from enum import StrEnum


class TransactionType(StrEnum):
    """Supported financial transaction types."""

    INCOME = "income"
    EXPENSE = "expense"
    INITIAL_BALANCE = "initial_balance"
    TRANSFER_OUT = "transfer_out"
    TRANSFER_IN = "transfer_in"
    REVERSAL = "reversal"


class TransactionStatus(StrEnum):
    """Lifecycle states supported by financial transactions."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REVERSED = "reversed"
