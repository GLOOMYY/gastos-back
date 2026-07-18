"""FastAPI composition for ledger use cases."""

from typing import Annotated

from fastapi import Depends

from app.modules.transactions.application.use_cases.get_transaction import (
    GetTransaction,
)
from app.modules.transactions.application.use_cases.get_cash_flow import GetCashFlow
from app.modules.transactions.application.use_cases.list_transactions import (
    ListTransactions,
)
from app.modules.transactions.infrastructure.repositories import (
    MongoTransactionRepository,
)
from app.modules.users.presentation.dependencies import DatabaseDep


def get_repository(database: DatabaseDep) -> MongoTransactionRepository:
    """Build the ledger repository."""
    return MongoTransactionRepository(database)


RepositoryDep = Annotated[MongoTransactionRepository, Depends(get_repository)]


def get_list(repository: RepositoryDep) -> ListTransactions:
    """Compose ledger listing."""
    return ListTransactions(repository)


def get_one(repository: RepositoryDep) -> GetTransaction:
    """Compose transaction retrieval."""
    return GetTransaction(repository)


def get_cash_flow(repository: RepositoryDep) -> GetCashFlow:
    """Compose the chart-ready cash-flow query."""
    return GetCashFlow(repository)


ListDep = Annotated[ListTransactions, Depends(get_list)]
GetDep = Annotated[GetTransaction, Depends(get_one)]
CashFlowDep = Annotated[GetCashFlow, Depends(get_cash_flow)]
