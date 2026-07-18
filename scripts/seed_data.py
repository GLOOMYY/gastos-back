"""Idempotently seed a complete starter dataset for local testing."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import logging

from app.core.config import Settings, get_settings
from app.modules.account_types.domain.entities import AccountType
from app.modules.account_types.infrastructure.repositories import (
    MongoAccountTypeRepository,
)
from app.modules.accounts.application.dto import (
    CreateAccountCommand,
    SetFavoriteAccountCommand,
)
from app.modules.accounts.application.use_cases.create_account import CreateAccount
from app.modules.accounts.application.use_cases.set_favorite_account import (
    SetFavoriteAccount,
)
from app.modules.accounts.infrastructure.favorite_store import (
    MongoFavoriteAccountStore,
)
from app.modules.accounts.infrastructure.repositories import (
    MongoAccountRepository,
)
from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.enums import CategoryTransactionType
from app.modules.categories.infrastructure.repositories import (
    MongoCategoryRepository,
)
from app.modules.transactions.application.dto import RegisterTransactionCommand
from app.modules.transactions.application.use_cases.register_expense import (
    RegisterExpense,
)
from app.modules.transactions.application.use_cases.register_income import (
    RegisterIncome,
)
from app.modules.transactions.infrastructure.repositories import (
    MongoTransactionRepository,
)
from app.modules.users.application.dto import CreateUserCommand
from app.modules.users.application.use_cases.create_user import CreateUser
from app.modules.users.domain.exceptions import UserAlreadyExistsError
from app.modules.users.domain.value_objects import Email
from app.modules.users.infrastructure.password_hasher import PasslibPasswordHasher
from app.modules.users.infrastructure.repositories import MongoUserRepository
from app.shared.infrastructure.mongodb.client import MongoDatabase
from app.shared.infrastructure.mongodb.financial_stores import (
    MongoAccountCreationStore,
    MongoLedgerStore,
)
from app.shared.infrastructure.mongodb.indexes import create_indexes
from app.shared.infrastructure.mongodb.schema import ensure_auth_collection_schemas
from scripts.seed_reference_data import seed_reference_data

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SeedSummary:
    """Secret-safe result of the complete seed."""

    user_id: str
    account_type_id: str
    account_id: str
    created_user: bool
    created_account: bool
    created_transactions: int


@dataclass(frozen=True, slots=True)
class HistoryItem:
    """One deterministic transaction in the starter history."""

    days_ago: int
    transaction_type: CategoryTransactionType
    amount: Decimal
    description: str


async def seed_complete_data(settings: Settings) -> SeedSummary:
    """Create a user, catalogs, account, and opening transaction."""
    uri, database_name, email, password = _required_settings(settings)
    mongo = MongoDatabase()
    try:
        await mongo.connect(uri, database_name)
        database = mongo.get_database()
        await ensure_auth_collection_schemas(database)
        await create_indexes(database)
        await seed_reference_data(database)

        users = MongoUserRepository(database)
        create_user = CreateUser(users, PasslibPasswordHasher())
        created_user = True
        try:
            user_result = await create_user.execute(
                CreateUserCommand(email=email, password=password)
            )
            user_id = user_result.id
        except UserAlreadyExistsError:
            created_user = False
            user = await users.get_by_normalized_email(Email.create(email).normalized)
            if user is None or user.id is None:
                raise RuntimeError("The initial user could not be retrieved.")
            user_id = user.id

        user = await users.get_by_id(user_id)
        if user is None:
            raise RuntimeError("The initial user could not be retrieved.")
        user.update_preferences(favorite_currency="COP", country_code="CO")
        await users.update(user)

        account_types = MongoAccountTypeRepository(database)
        account_type = await _ensure_account_type(account_types, user_id)
        categories = MongoCategoryRepository(database)
        income_category, expense_category = await _ensure_categories(
            categories,
            user_id,
        )

        accounts = MongoAccountRepository(database)
        existing_account = next(
            (
                value
                for value in await accounts.list_by_user(user_id)
                if value.is_active
                and value.normalized_name
                == settings.initial_account_name.strip().casefold()
            ),
            None,
        )
        created_account = existing_account is None
        if existing_account is None:
            account_result = await CreateAccount(
                accounts,
                account_types,
                MongoAccountCreationStore(database),
            ).execute(
                CreateAccountCommand(
                    user_id=user_id,
                    account_type_id=_required_id(account_type.id),
                    name=settings.initial_account_name,
                    initial_balance=settings.initial_account_balance,
                    currency=settings.initial_account_currency,
                    description="Starter account created by the complete seed.",
                )
            )
            account_id = account_result.id
            account_currency = account_result.currency
        else:
            account_id = _required_id(existing_account.id)
            account_currency = existing_account.currency.code

        await SetFavoriteAccount(
            accounts,
            MongoFavoriteAccountStore(database),
        ).execute(
            SetFavoriteAccountCommand(
                user_id=user_id,
                account_id=account_id,
                is_favorite=True,
            )
        )

        if account_currency != "COP":
            raise RuntimeError(
                "The complete history seed requires a COP initial account."
            )
        transactions = MongoTransactionRepository(database)
        ledger = MongoLedgerStore(database)
        created_transactions = await _ensure_transaction_history(
            user_id=user_id,
            account_id=account_id,
            income_category_id=_required_id(income_category.id),
            expense_category_id=_required_id(expense_category.id),
            repository=transactions,
            register_income=RegisterIncome(accounts, categories, ledger),
            register_expense=RegisterExpense(accounts, categories, ledger),
        )

        return SeedSummary(
            user_id=user_id,
            account_type_id=_required_id(account_type.id),
            account_id=account_id,
            created_user=created_user,
            created_account=created_account,
            created_transactions=created_transactions,
        )
    finally:
        await mongo.disconnect()


async def _ensure_account_type(
    repository: MongoAccountTypeRepository,
    user_id: str,
) -> AccountType:
    """Ensure the global starter account type exists."""
    values = await repository.list_available(user_id)
    existing = next(
        (value for value in values if value.code == "CASH" and value.is_global),
        None,
    )
    if existing is not None:
        return existing
    return await repository.add(
        AccountType.create(
            user_id=None,
            code="CASH",
            name="Cash",
            description="Cash and general-purpose accounts.",
        )
    )


async def _ensure_categories(
    repository: MongoCategoryRepository,
    user_id: str,
) -> tuple[Category, Category]:
    """Ensure global and private starter categories exist."""
    specifications = (
        (None, "Salary", CategoryTransactionType.INCOME),
        (None, "Food", CategoryTransactionType.EXPENSE),
        (user_id, "Personal income", CategoryTransactionType.INCOME),
        (user_id, "Personal expenses", CategoryTransactionType.EXPENSE),
    )
    for owner_id, name, transaction_type in specifications:
        if await repository.exists_name(
            owner_id,
            name.casefold(),
            transaction_type,
        ):
            continue
        await repository.add(
            Category.create(
                user_id=owner_id,
                name=name,
                transaction_type=transaction_type,
                description="Starter category created by the complete seed.",
            )
        )
    available = await repository.list_available(user_id)
    income = next(
        (
            value
            for value in available
            if value.user_id is None
            and value.normalized_name == "salary"
            and value.transaction_type is CategoryTransactionType.INCOME
        ),
        None,
    )
    expense = next(
        (
            value
            for value in available
            if value.user_id is None
            and value.normalized_name == "food"
            and value.transaction_type is CategoryTransactionType.EXPENSE
        ),
        None,
    )
    if income is None or expense is None:
        raise RuntimeError("The starter categories could not be retrieved.")
    return income, expense


async def _ensure_transaction_history(
    *,
    user_id: str,
    account_id: str,
    income_category_id: str,
    expense_category_id: str,
    repository: MongoTransactionRepository,
    register_income: RegisterIncome,
    register_expense: RegisterExpense,
) -> int:
    """Create a deterministic 90-day COP history without duplicates."""
    anchor = datetime.now(UTC).replace(
        hour=12,
        minute=0,
        second=0,
        microsecond=0,
    )
    created = 0
    for index, item in enumerate(_history_items(), start=1):
        note = f"seed:history:v1:{index:02d}"
        if await repository.get_by_note(user_id, note) is not None:
            continue
        command = RegisterTransactionCommand(
            user_id=user_id,
            account_id=account_id,
            category_id=(
                income_category_id
                if item.transaction_type is CategoryTransactionType.INCOME
                else expense_category_id
            ),
            amount=item.amount,
            occurred_at=anchor - timedelta(days=item.days_ago),
            description=item.description,
            note=note,
        )
        if item.transaction_type is CategoryTransactionType.INCOME:
            await register_income.execute(command)
        else:
            await register_expense.execute(command)
        created += 1
    return created


def _history_items() -> tuple[HistoryItem, ...]:
    """Return realistic income and expense samples spanning three months."""
    return (
        HistoryItem(88, CategoryTransactionType.INCOME, Decimal("3200000"), "Salary"),
        HistoryItem(
            84, CategoryTransactionType.EXPENSE, Decimal("420000"), "Groceries"
        ),
        HistoryItem(78, CategoryTransactionType.EXPENSE, Decimal("95000"), "Dining"),
        HistoryItem(73, CategoryTransactionType.INCOME, Decimal("450000"), "Freelance"),
        HistoryItem(
            67, CategoryTransactionType.EXPENSE, Decimal("180000"), "Utilities"
        ),
        HistoryItem(
            61, CategoryTransactionType.EXPENSE, Decimal("120000"), "Transport"
        ),
        HistoryItem(58, CategoryTransactionType.INCOME, Decimal("3200000"), "Salary"),
        HistoryItem(
            53, CategoryTransactionType.EXPENSE, Decimal("460000"), "Groceries"
        ),
        HistoryItem(47, CategoryTransactionType.EXPENSE, Decimal("135000"), "Dining"),
        HistoryItem(42, CategoryTransactionType.INCOME, Decimal("380000"), "Freelance"),
        HistoryItem(
            36, CategoryTransactionType.EXPENSE, Decimal("195000"), "Utilities"
        ),
        HistoryItem(
            31, CategoryTransactionType.EXPENSE, Decimal("110000"), "Transport"
        ),
        HistoryItem(28, CategoryTransactionType.INCOME, Decimal("3200000"), "Salary"),
        HistoryItem(
            23, CategoryTransactionType.EXPENSE, Decimal("440000"), "Groceries"
        ),
        HistoryItem(17, CategoryTransactionType.EXPENSE, Decimal("125000"), "Dining"),
        HistoryItem(12, CategoryTransactionType.INCOME, Decimal("520000"), "Freelance"),
        HistoryItem(6, CategoryTransactionType.EXPENSE, Decimal("205000"), "Utilities"),
        HistoryItem(2, CategoryTransactionType.EXPENSE, Decimal("90000"), "Transport"),
    )


def _required_settings(settings: Settings) -> tuple[str, str, str, str]:
    """Validate and return seed settings without exposing secret values."""
    if settings.initial_account_currency.strip().upper() != "COP":
        raise RuntimeError("INITIAL_ACCOUNT_CURRENCY must be COP for this seed.")
    uri = settings.mongodb_uri.get_secret_value() if settings.mongodb_uri else ""
    database = settings.mongodb_database or ""
    email = settings.initial_user_email or ""
    password = (
        settings.initial_user_password.get_secret_value()
        if settings.initial_user_password
        else ""
    )
    missing = [
        name
        for name, value in (
            ("MONGODB_URI", uri),
            ("MONGODB_DATABASE", database),
            ("INITIAL_USER_EMAIL", email),
            ("INITIAL_USER_PASSWORD", password),
        )
        if not value.strip()
    ]
    if missing:
        raise RuntimeError(f"Missing required settings: {', '.join(missing)}.")
    return uri, database, email, password


def _required_id(value: str | None) -> str:
    """Return a persistence identifier or fail on an invalid seed state."""
    if value is None:
        raise RuntimeError("A seeded resource has no identifier.")
    return value


def main() -> None:
    """Run the complete starter seed and log only public identifiers."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    summary = asyncio.run(seed_complete_data(get_settings()))
    logger.info(
        "event=complete_seed_finished user_id=%s account_id=%s "
        "created_user=%s created_account=%s created_transactions=%s",
        summary.user_id,
        summary.account_id,
        summary.created_user,
        summary.created_account,
        summary.created_transactions,
    )


if __name__ == "__main__":
    main()
