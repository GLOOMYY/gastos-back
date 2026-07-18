"""Create an account and its immutable opening ledger entry."""

from datetime import UTC, datetime
from decimal import Decimal

from app.modules.account_types.domain.exceptions import AccountTypeNotFoundError
from app.modules.account_types.domain.repositories import AccountTypeRepository
from app.modules.accounts.application.dto import (
    AccountResult,
    CreateAccountCommand,
)
from app.modules.accounts.application.ports import AccountCreationStore
from app.modules.accounts.application.use_cases.get_account import to_result
from app.modules.accounts.domain.entities import Account
from app.modules.accounts.domain.exceptions import AccountNameAlreadyExistsError
from app.modules.accounts.domain.repositories import AccountRepository
from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.enums import TransactionType


class CreateAccount:
    """Create an owned account consistently with its opening balance."""

    def __init__(
        self,
        repository: AccountRepository,
        account_types: AccountTypeRepository,
        creation_store: AccountCreationStore,
    ) -> None:
        """Initialize the use case."""
        self._repository = repository
        self._account_types = account_types
        self._creation_store = creation_store

    async def execute(self, command: CreateAccountCommand) -> AccountResult:
        """Validate references and atomically persist opening state."""
        account_type = await self._account_types.get_by_id(command.account_type_id)
        if (
            account_type is None
            or not account_type.is_active
            or account_type.user_id not in (None, command.user_id)
        ):
            raise AccountTypeNotFoundError()
        account = Account.create(
            user_id=command.user_id,
            account_type_id=command.account_type_id,
            name=command.name,
            initial_balance=command.initial_balance,
            currency=command.currency,
            description=command.description,
        )
        if await self._repository.exists_name(
            command.user_id,
            account.normalized_name,
        ):
            raise AccountNameAlreadyExistsError()
        opening_entry = self._build_opening_entry(account)
        created = await self._creation_store.add(account, opening_entry)
        return to_result(created)

    @staticmethod
    def _build_opening_entry(account: Account) -> Transaction | None:
        """Build the immutable initial-balance entry when needed."""
        if account.initial_balance == Decimal("0"):
            return None
        return Transaction.create(
            user_id=account.user_id,
            account_id="pending",
            transaction_type=TransactionType.INITIAL_BALANCE,
            amount=account.initial_balance,
            currency=account.currency.code,
            occurred_at=datetime.now(UTC),
            description="Initial account balance",
        )
