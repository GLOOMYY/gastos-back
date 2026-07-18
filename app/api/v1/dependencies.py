"""Cross-module composition for financial application use cases."""

from typing import Annotated

from fastapi import Depends

from app.modules.account_types.infrastructure.repositories import (
    MongoAccountTypeRepository,
)
from app.modules.accounts.application.use_cases.create_account import CreateAccount
from app.modules.accounts.infrastructure.repositories import (
    MongoAccountRepository,
)
from app.modules.categories.infrastructure.repositories import (
    MongoCategoryRepository,
)
from app.modules.exchange_rates.presentation.dependencies import (
    OptionalProviderDep,
)
from app.modules.transactions.application.use_cases.register_expense import (
    RegisterExpense,
)
from app.modules.transactions.application.use_cases.register_income import (
    RegisterIncome,
)
from app.modules.transactions.application.use_cases.reverse_transaction import (
    ReverseTransaction,
)
from app.modules.transactions.application.use_cases.transfer_money import (
    TransferMoney,
)
from app.modules.transactions.infrastructure.repositories import (
    MongoTransactionRepository,
)
from app.modules.transactions.infrastructure.services import (
    UuidTransferIdGenerator,
)
from app.modules.users.presentation.dependencies import DatabaseDep
from app.shared.infrastructure.mongodb.financial_stores import (
    MongoAccountCreationStore,
    MongoLedgerStore,
    MongoTransferStore,
)


def get_create_account(database: DatabaseDep) -> CreateAccount:
    """Compose account creation across catalog and ledger ports."""
    return CreateAccount(
        MongoAccountRepository(database),
        MongoAccountTypeRepository(database),
        MongoAccountCreationStore(database),
    )


def get_register_income(database: DatabaseDep) -> RegisterIncome:
    """Compose income registration across financial modules."""
    return RegisterIncome(
        MongoAccountRepository(database),
        MongoCategoryRepository(database),
        MongoLedgerStore(database),
    )


def get_register_expense(database: DatabaseDep) -> RegisterExpense:
    """Compose expense registration across financial modules."""
    return RegisterExpense(
        MongoAccountRepository(database),
        MongoCategoryRepository(database),
        MongoLedgerStore(database),
    )


def get_reverse_transaction(database: DatabaseDep) -> ReverseTransaction:
    """Compose immutable transaction reversal."""
    return ReverseTransaction(
        MongoTransactionRepository(database),
        MongoAccountRepository(database),
        MongoLedgerStore(database),
    )


def get_transfer_money(
    database: DatabaseDep,
    exchange_rates: OptionalProviderDep,
) -> TransferMoney:
    """Compose atomic transfers with optional market-rate infrastructure."""
    return TransferMoney(
        MongoAccountRepository(database),
        MongoTransferStore(database),
        UuidTransferIdGenerator(),
        exchange_rates,
    )


CreateAccountDep = Annotated[CreateAccount, Depends(get_create_account)]
IncomeDep = Annotated[RegisterIncome, Depends(get_register_income)]
ExpenseDep = Annotated[RegisterExpense, Depends(get_register_expense)]
ReverseDep = Annotated[ReverseTransaction, Depends(get_reverse_transaction)]
TransferDep = Annotated[TransferMoney, Depends(get_transfer_money)]
