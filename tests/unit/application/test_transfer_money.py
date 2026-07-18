"""Unit tests for same- and cross-currency account transfers."""

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.modules.accounts.domain.entities import Account
from app.modules.accounts.domain.exceptions import AccountNotFoundError
from app.modules.exchange_rates.application.dto import ExchangeRateQuote
from app.modules.exchange_rates.domain.exceptions import (
    ExchangeRateUnavailableError,
)
from app.modules.transactions.application.dto import TransferMoneyCommand
from app.modules.transactions.application.use_cases.transfer_money import (
    TransferMoney,
)
from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.enums import ExchangeRateMode, TransactionType
from app.modules.transactions.domain.exceptions import (
    InvalidTransferExchangeRateError,
    SameAccountTransferError,
)
from app.modules.transactions.presentation.router import (
    transfer_money as transfer_money_route,
)
from app.modules.transactions.presentation.schemas import TransferMoneyRequest

USER_ID = "507f1f77bcf86cd799439011"
OTHER_USER_ID = "507f1f77bcf86cd799439012"
TYPE_ID = "507f1f77bcf86cd799439013"
COP_ACCOUNT_ID = "507f1f77bcf86cd799439014"
USD_ACCOUNT_ID = "507f1f77bcf86cd799439015"
SECOND_COP_ACCOUNT_ID = "507f1f77bcf86cd799439016"


class FakeAccounts:
    """Retrieve account fixtures by identifier."""

    def __init__(self, *accounts: Account) -> None:
        """Index the supplied accounts."""
        self.accounts = {
            account.id: account for account in accounts if account.id is not None
        }

    async def get_by_id(self, account_id: str) -> Account | None:
        """Return one account fixture."""
        return self.accounts.get(account_id)

    async def add(self, account: Account) -> Account:
        """Satisfy the account repository protocol for this test double."""
        return account

    async def list_by_user(self, user_id: str) -> list[Account]:
        """Return accounts for one owner."""
        return [value for value in self.accounts.values() if value.user_id == user_id]

    async def exists_name(
        self,
        user_id: str,
        normalized_name: str,
        excluding_id: str | None = None,
    ) -> bool:
        """Return false because transfers do not query account names."""
        return False

    async def update(self, account: Account) -> Account:
        """Return unchanged because the transfer store owns balance writes."""
        return account


class FakeTransferStore:
    """Capture one atomic double-entry persistence request."""

    def __init__(self) -> None:
        """Initialize empty captured values."""
        self.source_amount: Decimal | None = None
        self.target_amount: Decimal | None = None
        self.outgoing: Transaction | None = None
        self.incoming: Transaction | None = None

    async def transfer(
        self,
        user_id: str,
        source_account_id: str,
        target_account_id: str,
        source_amount: Decimal,
        target_amount: Decimal,
        outgoing: Transaction,
        incoming: Transaction,
    ) -> tuple[Transaction, Transaction]:
        """Capture both entries as one indivisible store call."""
        self.source_amount = source_amount
        self.target_amount = target_amount
        self.outgoing = outgoing
        self.incoming = incoming
        return (
            replace(outgoing, id="507f1f77bcf86cd799439021"),
            replace(incoming, id="507f1f77bcf86cd799439022"),
        )


class FakeIdGenerator:
    """Return a deterministic transfer identifier."""

    def generate(self) -> str:
        """Return the test transfer identifier."""
        return "transfer-test-id"


class FakeExchangeRates:
    """Return a deterministic current market quote."""

    def __init__(self, rate: Decimal = Decimal("0.00025")) -> None:
        """Initialize the rate and call tracking."""
        self.rate = rate
        self.calls: list[tuple[str, str]] = []

    async def get_latest_rate(
        self,
        source_currency: str,
        target_currency: str,
    ) -> ExchangeRateQuote:
        """Return the configured quote."""
        self.calls.append((source_currency, target_currency))
        return ExchangeRateQuote(
            source_currency=source_currency,
            target_currency=target_currency,
            rate=self.rate,
            provider="fake-market",
            updated_at=datetime(2026, 7, 18, tzinfo=UTC),
        )


def _account(account_id: str, currency: str, user_id: str = USER_ID) -> Account:
    """Build a persisted active account fixture."""
    account = Account.create(
        user_id=user_id,
        account_type_id=TYPE_ID,
        name=f"{currency}-{account_id[-2:]}",
        initial_balance=Decimal("1000000"),
        currency=currency,
    )
    account.id = account_id
    return account


def _command(
    source_account_id: str = COP_ACCOUNT_ID,
    target_account_id: str = USD_ACCOUNT_ID,
    mode: ExchangeRateMode = ExchangeRateMode.MARKET,
    custom_rate: Decimal | None = None,
) -> TransferMoneyCommand:
    """Build a transfer command fixture."""
    return TransferMoneyCommand(
        user_id=USER_ID,
        source_account_id=source_account_id,
        target_account_id=target_account_id,
        amount=Decimal("400000"),
        occurred_at=datetime(2026, 7, 18, 12, tzinfo=UTC),
        exchange_rate_mode=mode,
        custom_exchange_rate=custom_rate,
        description="Savings transfer",
    )


@pytest.mark.asyncio
async def test_same_currency_transfer_uses_identity_rate_without_provider() -> None:
    """Same-currency transfers move the exact amount without an API key."""
    store = FakeTransferStore()
    use_case = TransferMoney(
        FakeAccounts(
            _account(COP_ACCOUNT_ID, "COP"),
            _account(SECOND_COP_ACCOUNT_ID, "COP"),
        ),
        store,
        FakeIdGenerator(),
        None,
    )

    result = await use_case.execute(_command(target_account_id=SECOND_COP_ACCOUNT_ID))

    assert result.exchange_rate == Decimal("1")
    assert result.exchange_rate_mode is None
    assert store.source_amount == store.target_amount == Decimal("400000")
    assert store.outgoing is not None
    assert store.outgoing.transaction_type is TransactionType.TRANSFER_OUT
    assert store.outgoing.exchange_rate is None


@pytest.mark.asyncio
async def test_cross_currency_transfer_uses_market_quote() -> None:
    """Market mode obtains the current pair rate and records its metadata."""
    store = FakeTransferStore()
    rates = FakeExchangeRates()
    use_case = TransferMoney(
        FakeAccounts(
            _account(COP_ACCOUNT_ID, "COP"),
            _account(USD_ACCOUNT_ID, "USD"),
        ),
        store,
        FakeIdGenerator(),
        rates,
    )

    result = await use_case.execute(_command())

    assert rates.calls == [("COP", "USD")]
    assert result.target_amount == Decimal("100.00000")
    assert result.exchange_rate_mode is ExchangeRateMode.MARKET
    assert result.exchange_rate_provider == "fake-market"
    assert store.incoming is not None
    assert store.incoming.amount == Decimal("100.00000")
    assert store.incoming.transfer_id == result.transfer_id


@pytest.mark.asyncio
async def test_cross_currency_transfer_accepts_custom_rate_without_provider() -> None:
    """Custom mode uses the user's positive rate without calling the API."""
    use_case = TransferMoney(
        FakeAccounts(
            _account(COP_ACCOUNT_ID, "COP"),
            _account(USD_ACCOUNT_ID, "USD"),
        ),
        FakeTransferStore(),
        FakeIdGenerator(),
        None,
    )

    result = await use_case.execute(
        _command(
            mode=ExchangeRateMode.CUSTOM,
            custom_rate=Decimal("0.00030"),
        )
    )

    assert result.target_amount == Decimal("120.00000")
    assert result.exchange_rate_mode is ExchangeRateMode.CUSTOM
    assert result.exchange_rate_provider == "custom"


@pytest.mark.asyncio
async def test_transfer_rejects_foreign_account() -> None:
    """Authorization hides a destination account owned by another user."""
    use_case = TransferMoney(
        FakeAccounts(
            _account(COP_ACCOUNT_ID, "COP"),
            _account(USD_ACCOUNT_ID, "USD", OTHER_USER_ID),
        ),
        FakeTransferStore(),
        FakeIdGenerator(),
        FakeExchangeRates(),
    )

    with pytest.raises(AccountNotFoundError):
        await use_case.execute(_command())


@pytest.mark.asyncio
async def test_transfer_rejects_same_account_and_inconsistent_rates() -> None:
    """Transfer commands cannot reuse one account or mix rate modes."""
    account = _account(COP_ACCOUNT_ID, "COP")
    use_case = TransferMoney(
        FakeAccounts(account),
        FakeTransferStore(),
        FakeIdGenerator(),
        None,
    )
    with pytest.raises(SameAccountTransferError):
        await use_case.execute(_command(target_account_id=COP_ACCOUNT_ID))

    same_currency = TransferMoney(
        FakeAccounts(account, _account(SECOND_COP_ACCOUNT_ID, "COP")),
        FakeTransferStore(),
        FakeIdGenerator(),
        None,
    )
    with pytest.raises(InvalidTransferExchangeRateError):
        await same_currency.execute(
            _command(
                target_account_id=SECOND_COP_ACCOUNT_ID,
                mode=ExchangeRateMode.CUSTOM,
                custom_rate=Decimal("1"),
            )
        )


@pytest.mark.asyncio
async def test_cross_currency_transfer_requires_valid_selected_rate_mode() -> None:
    """Market needs a provider and custom mode needs an explicit rate."""
    use_case = TransferMoney(
        FakeAccounts(
            _account(COP_ACCOUNT_ID, "COP"),
            _account(USD_ACCOUNT_ID, "USD"),
        ),
        FakeTransferStore(),
        FakeIdGenerator(),
        None,
    )

    with pytest.raises(ExchangeRateUnavailableError):
        await use_case.execute(_command())
    with pytest.raises(InvalidTransferExchangeRateError):
        await use_case.execute(_command(mode=ExchangeRateMode.CUSTOM))


@pytest.mark.asyncio
async def test_transfer_http_route_maps_custom_rate_request() -> None:
    """The HTTP contract maps authenticated custom-rate transfers."""
    use_case = TransferMoney(
        FakeAccounts(
            _account(COP_ACCOUNT_ID, "COP"),
            _account(USD_ACCOUNT_ID, "USD"),
        ),
        FakeTransferStore(),
        FakeIdGenerator(),
        None,
    )

    response = await transfer_money_route(
        TransferMoneyRequest(
            source_account_id=COP_ACCOUNT_ID,
            target_account_id=USD_ACCOUNT_ID,
            amount=Decimal("400000"),
            occurred_at=datetime(2026, 7, 18, 12, tzinfo=UTC),
            exchange_rate_mode=ExchangeRateMode.CUSTOM,
            custom_exchange_rate=Decimal("0.00030"),
        ),
        SimpleNamespace(id=USER_ID),
        use_case,
    )

    assert response.transfer_id == "transfer-test-id"
    assert response.target_amount == Decimal("120.00000")
    assert response.outgoing_transaction.transaction_type is (
        TransactionType.TRANSFER_OUT
    )
