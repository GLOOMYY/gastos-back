"""Register an income and update its account atomically."""

from app.modules.accounts.domain.exceptions import (
    AccountNotFoundError,
    InactiveAccountError,
)
from app.modules.accounts.domain.repositories import AccountRepository
from app.modules.categories.domain.enums import CategoryTransactionType
from app.modules.categories.domain.exceptions import CategoryNotFoundError
from app.modules.categories.domain.repositories import CategoryRepository
from app.modules.transactions.application.dto import (
    RegisterTransactionCommand,
    TransactionResult,
)
from app.modules.transactions.application.ports import LedgerStore
from app.modules.transactions.application.use_cases.get_transaction import (
    to_result,
)
from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.exceptions import (
    InvalidTransactionCategoryError,
)
from app.modules.transactions.domain.enums import TransactionType


class RegisterIncome:
    """Register an income against an active owned account."""

    def __init__(
        self,
        accounts: AccountRepository,
        categories: CategoryRepository,
        ledger: LedgerStore,
    ) -> None:
        """Initialize the use case."""
        self._accounts = accounts
        self._categories = categories
        self._ledger = ledger

    async def execute(
        self,
        command: RegisterTransactionCommand,
    ) -> TransactionResult:
        """Validate ownership and append the income atomically."""
        account = await self._accounts.get_by_id(command.account_id)
        if account is None or account.user_id != command.user_id:
            raise AccountNotFoundError()
        if not account.is_active:
            raise InactiveAccountError()
        category = await self._categories.get_by_id(command.category_id)
        if category is None:
            raise CategoryNotFoundError()
        if (
            not category.is_active
            or category.user_id not in (None, command.user_id)
            or category.transaction_type is not CategoryTransactionType.INCOME
        ):
            raise InvalidTransactionCategoryError()
        transaction = Transaction.create(
            user_id=command.user_id,
            account_id=command.account_id,
            category_id=command.category_id,
            transaction_type=TransactionType.INCOME,
            amount=command.amount,
            currency=account.currency.code,
            occurred_at=command.occurred_at,
            description=command.description,
            note=command.note,
        )
        created = await self._ledger.apply(
            command.user_id,
            command.account_id,
            command.amount,
            transaction,
        )
        return to_result(created)
