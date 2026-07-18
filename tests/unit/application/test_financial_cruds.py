"""Unit tests for catalog, account, and ledger CRUD workflows."""

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.modules.account_types.application.dto import (
    CreateAccountTypeCommand,
    UpdateAccountTypeCommand,
)
from app.modules.account_types.application.use_cases.create_account_type import (
    CreateAccountType,
)
from app.modules.account_types.application.use_cases.deactivate_account_type import (
    DeactivateAccountType,
)
from app.modules.account_types.application.use_cases.get_account_type import (
    GetAccountType,
)
from app.modules.account_types.application.use_cases.list_account_types import (
    ListAccountTypes,
)
from app.modules.account_types.application.use_cases.update_account_type import (
    UpdateAccountType,
)
from app.modules.account_types.domain.entities import AccountType
from app.modules.account_types.domain.exceptions import (
    AccountTypeAccessDeniedError,
)
from app.modules.account_types.presentation.router import (
    create_account_type as create_account_type_route,
    deactivate_account_type as deactivate_account_type_route,
    get_account_type as get_account_type_route,
    list_account_types as list_account_types_route,
    update_account_type as update_account_type_route,
)
from app.modules.account_types.presentation.schemas import (
    CreateAccountTypeRequest,
    UpdateAccountTypeRequest,
)
from app.modules.accounts.application.dto import CreateAccountCommand
from app.modules.accounts.application.dto import UpdateAccountCommand
from app.modules.accounts.application.use_cases.close_account import CloseAccount
from app.modules.accounts.application.use_cases.create_account import CreateAccount
from app.modules.accounts.application.use_cases.get_account import GetAccount
from app.modules.accounts.application.use_cases.list_accounts import ListAccounts
from app.modules.accounts.application.use_cases.rename_account import RenameAccount
from app.modules.accounts.domain.entities import Account
from app.modules.accounts.presentation.router import (
    close_account as close_account_route,
    create_account as create_account_route,
    get_account as get_account_route,
    list_accounts as list_accounts_route,
    update_account as update_account_route,
)
from app.modules.accounts.presentation.schemas import (
    CreateAccountRequest,
    UpdateAccountRequest,
)
from app.modules.categories.application.dto import CreateCategoryCommand
from app.modules.categories.application.use_cases.create_category import (
    CreateCategory,
)
from app.modules.categories.application.use_cases.deactivate_category import (
    DeactivateCategory,
)
from app.modules.categories.application.use_cases.get_category import GetCategory
from app.modules.categories.application.use_cases.list_categories import (
    ListCategories,
)
from app.modules.categories.application.use_cases.update_category import (
    UpdateCategory,
)
from app.modules.categories.application.dto import UpdateCategoryCommand
from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.enums import CategoryTransactionType
from app.modules.categories.presentation.router import (
    create_category as create_category_route,
    deactivate_category as deactivate_category_route,
    get_category as get_category_route,
    list_categories as list_categories_route,
    update_category as update_category_route,
)
from app.modules.categories.presentation.schemas import (
    CreateCategoryRequest,
    UpdateCategoryRequest,
)
from app.modules.transactions.application.dto import (
    RegisterTransactionCommand,
    ReverseTransactionCommand,
)
from app.modules.transactions.application.use_cases.register_expense import (
    RegisterExpense,
)
from app.modules.transactions.application.use_cases.register_income import (
    RegisterIncome,
)
from app.modules.transactions.application.use_cases.list_transactions import (
    ListTransactions,
)
from app.modules.transactions.application.use_cases.get_transaction import (
    GetTransaction,
)
from app.modules.transactions.application.use_cases.reverse_transaction import (
    ReverseTransaction,
)
from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.enums import TransactionType
from app.core.config import Settings
from scripts.seed_data import seed_complete_data

USER_ID = "507f1f77bcf86cd799439011"
OTHER_USER_ID = "507f1f77bcf86cd799439012"
TYPE_ID = "507f1f77bcf86cd799439013"
ACCOUNT_ID = "507f1f77bcf86cd799439014"
CATEGORY_ID = "507f1f77bcf86cd799439015"
TRANSACTION_ID = "507f1f77bcf86cd799439016"


class FakeAccountTypes:
    """In-memory account type repository."""

    def __init__(self, values: list[AccountType] | None = None) -> None:
        """Initialize repository values."""
        self.values = values or []

    async def add(self, value: AccountType) -> AccountType:
        """Add an account type."""
        value.id = TYPE_ID
        self.values.append(value)
        return value

    async def get_by_id(self, value_id: str) -> AccountType | None:
        """Find an account type."""
        return next((item for item in self.values if item.id == value_id), None)

    async def list_available(self, user_id: str) -> list[AccountType]:
        """List visible account types."""
        return [item for item in self.values if item.user_id in (None, user_id)]

    async def exists_name(
        self,
        user_id: str | None,
        normalized_name: str,
        excluding_id: str | None = None,
    ) -> bool:
        """Check scoped uniqueness."""
        return any(
            item.user_id == user_id
            and item.normalized_name == normalized_name
            and item.id != excluding_id
            and item.is_active
            for item in self.values
        )

    async def update(self, value: AccountType) -> AccountType:
        """Return a mutated account type."""
        return value


class FakeCategories:
    """In-memory category repository."""

    def __init__(self, values: list[Category] | None = None) -> None:
        """Initialize repository values."""
        self.values = values or []

    async def add(self, value: Category) -> Category:
        """Add a category."""
        value.id = CATEGORY_ID
        self.values.append(value)
        return value

    async def get_by_id(self, value_id: str) -> Category | None:
        """Find a category."""
        return next((item for item in self.values if item.id == value_id), None)

    async def list_available(
        self,
        user_id: str,
        transaction_type: CategoryTransactionType | None = None,
    ) -> list[Category]:
        """List visible categories."""
        return [
            item
            for item in self.values
            if item.user_id in (None, user_id)
            and (transaction_type is None or item.transaction_type is transaction_type)
        ]

    async def exists_name(
        self,
        user_id: str | None,
        normalized_name: str,
        transaction_type: CategoryTransactionType,
        excluding_id: str | None = None,
    ) -> bool:
        """Check category uniqueness."""
        return any(
            item.user_id == user_id
            and item.normalized_name == normalized_name
            and item.transaction_type is transaction_type
            and item.id != excluding_id
            for item in self.values
        )

    async def update(self, value: Category) -> Category:
        """Return a mutated category."""
        return value


class FakeAccounts:
    """In-memory account repository."""

    def __init__(self, account: Account | None = None) -> None:
        """Initialize with an optional account."""
        self.account = account

    async def add(self, account: Account) -> Account:
        """Add an account."""
        account.id = ACCOUNT_ID
        self.account = account
        return account

    async def get_by_id(self, account_id: str) -> Account | None:
        """Find the account."""
        if self.account is not None and self.account.id == account_id:
            return self.account
        return None

    async def list_by_user(self, user_id: str) -> list[Account]:
        """List owned accounts."""
        if self.account is not None and self.account.user_id == user_id:
            return [self.account]
        return []

    async def exists_name(
        self,
        user_id: str,
        normalized_name: str,
        excluding_id: str | None = None,
    ) -> bool:
        """Check account name uniqueness."""
        return False

    async def update(self, account: Account) -> Account:
        """Persist a mutated account."""
        self.account = account
        return account


class FakeAccountCreationStore:
    """Capture atomic account creation inputs."""

    def __init__(self) -> None:
        """Initialize captured state."""
        self.initial_transaction: Transaction | None = None

    async def add(
        self,
        account: Account,
        initial_transaction: Transaction | None,
    ) -> Account:
        """Assign IDs as an atomic database store would."""
        account.id = ACCOUNT_ID
        self.initial_transaction = initial_transaction
        return account


class FakeTransactions:
    """In-memory immutable transaction repository."""

    def __init__(self, transaction: Transaction | None = None) -> None:
        """Initialize with an optional transaction."""
        self.transaction = transaction
        self.reversed = False

    async def add(self, transaction: Transaction) -> Transaction:
        """Add a transaction."""
        self.transaction = replace(transaction, id=TRANSACTION_ID)
        return self.transaction

    async def get_by_id(self, transaction_id: str) -> Transaction | None:
        """Find a transaction."""
        if self.transaction is not None and self.transaction.id == transaction_id:
            return self.transaction
        return None

    async def list_by_user(self, user_id: str) -> list[Transaction]:
        """List owned transactions."""
        return [self.transaction] if self.transaction is not None else []

    async def list_page(
        self,
        user_id: str,
        limit: int,
        cursor: tuple[datetime, str] | None,
    ) -> list[Transaction]:
        """Return the configured transaction as one page."""
        return [self.transaction] if self.transaction is not None else []

    async def has_reversal(self, transaction_id: str) -> bool:
        """Return captured reversal state."""
        return self.reversed


class FakeLedger:
    """Capture an atomic balance delta and ledger append."""

    def __init__(self) -> None:
        """Initialize captured state."""
        self.delta = Decimal("0")

    async def apply(
        self,
        user_id: str,
        account_id: str,
        balance_delta: Decimal,
        transaction: Transaction,
    ) -> Transaction:
        """Capture and return a persisted transaction."""
        self.delta = balance_delta
        return replace(transaction, id=TRANSACTION_ID)


def account() -> Account:
    """Build a persisted active account fixture."""
    value = Account.create(
        USER_ID,
        TYPE_ID,
        "Wallet",
        Decimal("100"),
        "COP",
    )
    value.id = ACCOUNT_ID
    return value


def category(kind: CategoryTransactionType) -> Category:
    """Build a persisted global category fixture."""
    value = Category.create("Test", kind)
    value.id = CATEGORY_ID
    return value


@pytest.mark.asyncio
async def test_private_account_type_crud_and_global_write_protection() -> None:
    """Create private types and reject updates to global types."""
    repository = FakeAccountTypes()
    created = await CreateAccountType(repository).execute(
        CreateAccountTypeCommand(USER_ID, "Savings")
    )
    assert created.user_id == USER_ID

    global_type = AccountType.create("Cash")
    global_type.id = TYPE_ID
    repository.values = [global_type]
    with pytest.raises(AccountTypeAccessDeniedError):
        await UpdateAccountType(repository).execute(
            UpdateAccountTypeCommand(USER_ID, TYPE_ID, "Changed")
        )


@pytest.mark.asyncio
async def test_account_type_read_update_list_and_deactivate() -> None:
    """Exercise all owned account type operations."""
    value = AccountType.create("Savings", user_id=USER_ID)
    value.id = TYPE_ID
    repository = FakeAccountTypes([value])

    assert (await GetAccountType(repository).execute(USER_ID, TYPE_ID)).id == TYPE_ID
    assert len(await ListAccountTypes(repository).execute(USER_ID)) == 1
    updated = await UpdateAccountType(repository).execute(
        UpdateAccountTypeCommand(USER_ID, TYPE_ID, "Long-term savings", "Goals")
    )
    assert updated.name == "Long-term savings"
    deactivated = await DeactivateAccountType(repository).execute(USER_ID, TYPE_ID)
    assert deactivated.is_active is False


@pytest.mark.asyncio
async def test_create_private_category() -> None:
    """Create a category owned by the authenticated user."""
    result = await CreateCategory(FakeCategories()).execute(
        CreateCategoryCommand(
            USER_ID,
            "Freelance",
            CategoryTransactionType.INCOME,
        )
    )
    assert result.user_id == USER_ID
    assert result.transaction_type is CategoryTransactionType.INCOME


@pytest.mark.asyncio
async def test_category_read_update_list_and_deactivate() -> None:
    """Exercise all owned category operations."""
    value = Category.create(
        "Transport",
        CategoryTransactionType.EXPENSE,
        user_id=USER_ID,
    )
    value.id = CATEGORY_ID
    repository = FakeCategories([value])

    assert (
        await GetCategory(repository).execute(USER_ID, CATEGORY_ID)
    ).id == CATEGORY_ID
    listed = await ListCategories(repository).execute(
        USER_ID,
        CategoryTransactionType.EXPENSE,
    )
    assert len(listed) == 1
    updated = await UpdateCategory(repository).execute(
        UpdateCategoryCommand(
            USER_ID,
            CATEGORY_ID,
            "Public transport",
            CategoryTransactionType.EXPENSE,
            "Bus and train",
        )
    )
    assert updated.name == "Public transport"
    await DeactivateCategory(repository).execute(USER_ID, CATEGORY_ID)
    assert value.is_active is False


@pytest.mark.asyncio
async def test_create_account_builds_initial_balance_transaction() -> None:
    """Require an immutable opening entry for a non-zero balance."""
    type_value = AccountType.create("Cash")
    type_value.id = TYPE_ID
    store = FakeAccountCreationStore()
    result = await CreateAccount(
        FakeAccounts(),
        FakeAccountTypes([type_value]),
        store,
    ).execute(
        CreateAccountCommand(
            USER_ID,
            TYPE_ID,
            "Wallet",
            Decimal("250"),
            "COP",
        )
    )
    assert result.balance == Decimal("250")
    assert store.initial_transaction is not None
    assert store.initial_transaction.transaction_type is TransactionType.INITIAL_BALANCE


@pytest.mark.asyncio
async def test_account_read_update_list_and_close() -> None:
    """Exercise all non-financial account CRUD operations."""
    value = account()
    repository = FakeAccounts(value)

    assert (await GetAccount(repository).execute(USER_ID, ACCOUNT_ID)).id == ACCOUNT_ID
    assert len(await ListAccounts(repository).execute(USER_ID)) == 1
    updated = await RenameAccount(repository).execute(
        UpdateAccountCommand(USER_ID, ACCOUNT_ID, "Daily wallet", "Cash")
    )
    assert updated.name == "Daily wallet"
    await CloseAccount(repository).execute(USER_ID, ACCOUNT_ID)
    assert value.is_active is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("use_case_type", "category_type", "expected_delta"),
    [
        (RegisterIncome, CategoryTransactionType.INCOME, Decimal("25")),
        (RegisterExpense, CategoryTransactionType.EXPENSE, Decimal("-25")),
    ],
)
async def test_register_movement_applies_expected_atomic_delta(
    use_case_type: type[RegisterIncome] | type[RegisterExpense],
    category_type: CategoryTransactionType,
    expected_delta: Decimal,
) -> None:
    """Apply income and expense balance effects through the ledger port."""
    ledger = FakeLedger()
    use_case = use_case_type(
        FakeAccounts(account()),
        FakeCategories([category(category_type)]),
        ledger,
    )
    await use_case.execute(
        RegisterTransactionCommand(
            USER_ID,
            ACCOUNT_ID,
            CATEGORY_ID,
            Decimal("25"),
            datetime.now(UTC),
        )
    )
    assert ledger.delta == expected_delta


@pytest.mark.asyncio
async def test_reversal_appends_compensation_without_mutating_original() -> None:
    """Reverse an expense through a positive compensating balance delta."""
    original = Transaction.create(
        USER_ID,
        ACCOUNT_ID,
        TransactionType.EXPENSE,
        Decimal("30"),
        "COP",
        datetime.now(UTC),
        category_id=CATEGORY_ID,
    )
    original = replace(original, id=TRANSACTION_ID)
    transactions = FakeTransactions(original)
    ledger = FakeLedger()
    result = await ReverseTransaction(
        transactions,
        FakeAccounts(account()),
        ledger,
    ).execute(ReverseTransactionCommand(USER_ID, TRANSACTION_ID, "Correction"))
    assert ledger.delta == Decimal("30")
    assert result.reversal_of_id == TRANSACTION_ID
    assert transactions.transaction is original


@pytest.mark.asyncio
async def test_transaction_get_and_cursor_page() -> None:
    """Retrieve a transaction and generate a continuation cursor."""
    first = replace(
        Transaction.create(
            USER_ID,
            ACCOUNT_ID,
            TransactionType.INCOME,
            Decimal("10"),
            "COP",
            datetime.now(UTC),
        ),
        id=TRANSACTION_ID,
    )
    second = replace(first, id="507f1f77bcf86cd799439017")

    class PageTransactions(FakeTransactions):
        """Return enough records to produce a next cursor."""

        async def list_page(
            self,
            user_id: str,
            limit: int,
            cursor: tuple[datetime, str] | None,
        ) -> list[Transaction]:
            """Return two deterministic records."""
            return [first, second]

    repository = PageTransactions(first)
    assert (
        await GetTransaction(repository).execute(USER_ID, TRANSACTION_ID)
    ).id == TRANSACTION_ID
    page = await ListTransactions(repository).execute(USER_ID, 1)
    assert page.has_more is True
    assert page.next_cursor is not None
    continued = await ListTransactions(repository).execute(
        USER_ID,
        1,
        page.next_cursor,
    )
    assert continued.items[0].id == TRANSACTION_ID


@pytest.mark.asyncio
async def test_transaction_list_rejects_invalid_cursor() -> None:
    """Reject malformed opaque cursors before querying persistence."""
    from app.modules.transactions.domain.exceptions import (
        InvalidTransactionCursorError,
    )

    with pytest.raises(InvalidTransactionCursorError):
        await ListTransactions(FakeTransactions()).execute(
            USER_ID,
            20,
            "not-a-valid-cursor",
        )


@pytest.mark.asyncio
async def test_complete_seed_requires_explicit_database_settings() -> None:
    """Fail the complete seed before connecting when settings are absent."""
    with pytest.raises(RuntimeError, match="MONGODB_URI"):
        await seed_complete_data(Settings(_env_file=None))


@pytest.mark.asyncio
async def test_account_type_http_mapping_routes() -> None:
    """Map account type HTTP schemas through every CRUD route."""
    current_user = SimpleNamespace(id=USER_ID)
    repository = FakeAccountTypes()
    create_use_case = CreateAccountType(repository)
    response = await create_account_type_route(
        CreateAccountTypeRequest(name="Savings"),
        current_user,
        create_use_case,
    )
    assert response.name == "Savings"
    assert (
        len(
            await list_account_types_route(
                current_user,
                ListAccountTypes(repository),
            )
        )
        == 1
    )
    assert (
        await get_account_type_route(
            TYPE_ID,
            current_user,
            GetAccountType(repository),
        )
    ).id == TYPE_ID
    updated = await update_account_type_route(
        TYPE_ID,
        UpdateAccountTypeRequest(name="Emergency fund"),
        current_user,
        UpdateAccountType(repository),
    )
    assert updated.name == "Emergency fund"
    deleted = await deactivate_account_type_route(
        TYPE_ID,
        current_user,
        DeactivateAccountType(repository),
    )
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_category_http_mapping_routes() -> None:
    """Map category HTTP schemas through every CRUD route."""
    current_user = SimpleNamespace(id=USER_ID)
    repository = FakeCategories()
    response = await create_category_route(
        CreateCategoryRequest(
            name="Transport",
            transaction_type=CategoryTransactionType.EXPENSE,
        ),
        current_user,
        CreateCategory(repository),
    )
    assert response.name == "Transport"
    assert (
        len(
            await list_categories_route(
                current_user,
                ListCategories(repository),
                CategoryTransactionType.EXPENSE,
            )
        )
        == 1
    )
    assert (
        await get_category_route(
            CATEGORY_ID,
            current_user,
            GetCategory(repository),
        )
    ).id == CATEGORY_ID
    updated = await update_category_route(
        CATEGORY_ID,
        UpdateCategoryRequest(
            name="Bus",
            transaction_type=CategoryTransactionType.EXPENSE,
        ),
        current_user,
        UpdateCategory(repository),
    )
    assert updated.name == "Bus"
    deleted = await deactivate_category_route(
        CATEGORY_ID,
        current_user,
        DeactivateCategory(repository),
    )
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_account_http_mapping_routes() -> None:
    """Map account HTTP schemas through every CRUD route."""
    current_user = SimpleNamespace(id=USER_ID)
    account_type = AccountType.create("Cash")
    account_type.id = TYPE_ID
    created = await create_account_route(
        CreateAccountRequest(
            account_type_id=TYPE_ID,
            name="Wallet",
            initial_balance=Decimal("0"),
            currency="COP",
        ),
        current_user,
        CreateAccount(
            FakeAccounts(),
            FakeAccountTypes([account_type]),
            FakeAccountCreationStore(),
        ),
    )
    assert created.name == "Wallet"

    repository = FakeAccounts(account())
    assert len(await list_accounts_route(current_user, ListAccounts(repository))) == 1
    assert (
        await get_account_route(
            ACCOUNT_ID,
            current_user,
            GetAccount(repository),
        )
    ).id == ACCOUNT_ID
    updated = await update_account_route(
        ACCOUNT_ID,
        UpdateAccountRequest(name="Daily wallet"),
        current_user,
        RenameAccount(repository),
    )
    assert updated.name == "Daily wallet"
    deleted = await close_account_route(
        ACCOUNT_ID,
        current_user,
        CloseAccount(repository),
    )
    assert deleted.status_code == 204
