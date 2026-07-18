"""Build chart-ready income and expense time series."""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from app.modules.transactions.application.dto import (
    CashFlowInterval,
    CashFlowPoint,
    CashFlowResult,
    GetCashFlowQuery,
)
from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.enums import TransactionType
from app.modules.transactions.domain.exceptions import InvalidCashFlowRangeError
from app.modules.transactions.domain.repositories import TransactionRepository
from app.shared.domain.value_objects import Currency

_ZERO = Decimal("0")


class GetCashFlow:
    """Aggregate owned ledger entries for a frontend cash-flow chart."""

    def __init__(self, repository: TransactionRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, query: GetCashFlowQuery) -> CashFlowResult:
        """Return continuous daily or monthly income and expense buckets."""
        day_count = (query.date_to - query.date_from).days + 1
        if day_count < 1 or day_count > 366:
            raise InvalidCashFlowRangeError()
        currency = Currency.create(query.currency).code
        occurred_from = datetime.combine(query.date_from, time.min, UTC)
        occurred_before = datetime.combine(
            query.date_to + timedelta(days=1),
            time.min,
            UTC,
        )
        transactions = await self._repository.list_in_range(
            query.user_id,
            currency,
            occurred_from,
            occurred_before,
        )
        buckets = self._empty_buckets(
            query.date_from,
            query.date_to,
            query.interval,
        )
        for transaction in transactions:
            await self._apply_transaction(buckets, transaction, query.interval)
        points = [
            CashFlowPoint(
                period=period,
                income=values[0],
                expense=values[1],
                net=values[0] - values[1],
            )
            for period, values in buckets.items()
        ]
        total_income = sum((point.income for point in points), _ZERO)
        total_expense = sum((point.expense for point in points), _ZERO)
        return CashFlowResult(
            currency=currency,
            interval=query.interval,
            date_from=query.date_from,
            date_to=query.date_to,
            points=points,
            total_income=total_income,
            total_expense=total_expense,
            net=total_income - total_expense,
        )

    async def _apply_transaction(
        self,
        buckets: dict[str, list[Decimal]],
        transaction: Transaction,
        interval: CashFlowInterval,
    ) -> None:
        """Apply a ledger entry, including compensating reversals."""
        period = self._period_key(transaction.occurred_at.date(), interval)
        if transaction.transaction_type is TransactionType.INCOME:
            buckets[period][0] += transaction.amount
        elif transaction.transaction_type is TransactionType.EXPENSE:
            buckets[period][1] += transaction.amount
        elif (
            transaction.transaction_type is TransactionType.REVERSAL
            and transaction.reversal_of_id is not None
        ):
            original = await self._repository.get_by_id(transaction.reversal_of_id)
            if original is None:
                return
            if original.transaction_type is TransactionType.INCOME:
                buckets[period][0] -= transaction.amount
            elif original.transaction_type is TransactionType.EXPENSE:
                buckets[period][1] -= transaction.amount

    @classmethod
    def _empty_buckets(
        cls,
        date_from: date,
        date_to: date,
        interval: CashFlowInterval,
    ) -> dict[str, list[Decimal]]:
        """Create ordered zero-filled periods for stable frontend charts."""
        buckets: dict[str, list[Decimal]] = {}
        current = date_from
        while current <= date_to:
            buckets.setdefault(cls._period_key(current, interval), [_ZERO, _ZERO])
            current += timedelta(days=1)
        return buckets

    @staticmethod
    def _period_key(value: date, interval: CashFlowInterval) -> str:
        """Return a stable ISO-style label for a chart bucket."""
        if interval is CashFlowInterval.MONTH:
            return value.strftime("%Y-%m")
        return value.isoformat()
