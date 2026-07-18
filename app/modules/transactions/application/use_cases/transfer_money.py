"""Transfer money atomically between two accounts owned by one user."""

from datetime import datetime
from decimal import Decimal

from app.modules.accounts.domain.exceptions import (
    AccountNotFoundError,
    InactiveAccountError,
)
from app.modules.accounts.domain.repositories import AccountRepository
from app.modules.exchange_rates.application.ports import ExchangeRateProvider
from app.modules.exchange_rates.domain.exceptions import (
    ExchangeRateUnavailableError,
)
from app.modules.transactions.application.dto import (
    TransferMoneyCommand,
    TransferResult,
)
from app.modules.transactions.application.ports import (
    TransferIdGenerator,
    TransferStore,
)
from app.modules.transactions.application.use_cases.get_transaction import (
    to_result,
)
from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.enums import (
    ExchangeRateMode,
    TransactionType,
)
from app.modules.transactions.domain.exceptions import (
    InvalidTransactionAmountError,
    InvalidTransferExchangeRateError,
    SameAccountTransferError,
)


class TransferMoney:
    """Create an indivisible double-entry transfer between owned accounts."""

    def __init__(
        self,
        accounts: AccountRepository,
        store: TransferStore,
        id_generator: TransferIdGenerator,
        exchange_rates: ExchangeRateProvider | None,
    ) -> None:
        """Initialize account, persistence, identifier, and rate ports."""
        self._accounts = accounts
        self._store = store
        self._id_generator = id_generator
        self._exchange_rates = exchange_rates

    async def execute(self, command: TransferMoneyCommand) -> TransferResult:
        """Validate, price, and persist both sides of the transfer."""
        if command.source_account_id == command.target_account_id:
            raise SameAccountTransferError()
        if not isinstance(command.amount, Decimal) or command.amount <= 0:
            raise InvalidTransactionAmountError()

        source = await self._accounts.get_by_id(command.source_account_id)
        target = await self._accounts.get_by_id(command.target_account_id)
        if source is None or source.user_id != command.user_id:
            raise AccountNotFoundError()
        if target is None or target.user_id != command.user_id:
            raise AccountNotFoundError()
        if not source.is_active or not target.is_active:
            raise InactiveAccountError()

        source_currency = source.currency.code
        target_currency = target.currency.code
        is_cross_currency = source_currency != target_currency
        rate, mode, provider, rate_timestamp = await self._resolve_rate(
            command,
            source_currency,
            target_currency,
            is_cross_currency,
        )
        target_amount = command.amount * rate
        transfer_id = self._id_generator.generate()

        outgoing = Transaction.create(
            user_id=command.user_id,
            account_id=command.source_account_id,
            transaction_type=TransactionType.TRANSFER_OUT,
            amount=command.amount,
            currency=source_currency,
            occurred_at=command.occurred_at,
            description=command.description,
            note=command.note,
            transfer_id=transfer_id,
            source_amount=command.amount,
            target_amount=target_amount,
            source_currency=source_currency,
            target_currency=target_currency,
            exchange_rate=rate if is_cross_currency else None,
            exchange_rate_mode=mode,
            exchange_rate_provider=provider,
            exchange_rate_timestamp=rate_timestamp,
        )
        incoming = Transaction.create(
            user_id=command.user_id,
            account_id=command.target_account_id,
            transaction_type=TransactionType.TRANSFER_IN,
            amount=target_amount,
            currency=target_currency,
            occurred_at=command.occurred_at,
            description=command.description,
            note=command.note,
            transfer_id=transfer_id,
            source_amount=command.amount,
            target_amount=target_amount,
            source_currency=source_currency,
            target_currency=target_currency,
            exchange_rate=rate if is_cross_currency else None,
            exchange_rate_mode=mode,
            exchange_rate_provider=provider,
            exchange_rate_timestamp=rate_timestamp,
        )
        created_outgoing, created_incoming = await self._store.transfer(
            user_id=command.user_id,
            source_account_id=command.source_account_id,
            target_account_id=command.target_account_id,
            source_amount=command.amount,
            target_amount=target_amount,
            outgoing=outgoing,
            incoming=incoming,
        )
        return TransferResult(
            transfer_id=transfer_id,
            source_amount=command.amount,
            target_amount=target_amount,
            source_currency=source_currency,
            target_currency=target_currency,
            exchange_rate=rate,
            exchange_rate_mode=mode,
            exchange_rate_provider=provider,
            exchange_rate_timestamp=rate_timestamp,
            outgoing_transaction=to_result(created_outgoing),
            incoming_transaction=to_result(created_incoming),
        )

    async def _resolve_rate(
        self,
        command: TransferMoneyCommand,
        source_currency: str,
        target_currency: str,
        is_cross_currency: bool,
    ) -> tuple[
        Decimal,
        ExchangeRateMode | None,
        str | None,
        datetime | None,
    ]:
        """Resolve same-currency, custom, or current market pricing."""
        if not is_cross_currency:
            if (
                command.exchange_rate_mode is ExchangeRateMode.CUSTOM
                or command.custom_exchange_rate is not None
            ):
                raise InvalidTransferExchangeRateError()
            return Decimal("1"), None, None, None

        if command.exchange_rate_mode is ExchangeRateMode.CUSTOM:
            rate = command.custom_exchange_rate
            if not isinstance(rate, Decimal) or rate <= 0:
                raise InvalidTransferExchangeRateError()
            return rate, ExchangeRateMode.CUSTOM, "custom", command.occurred_at

        if command.custom_exchange_rate is not None:
            raise InvalidTransferExchangeRateError()
        if self._exchange_rates is None:
            raise ExchangeRateUnavailableError()
        quote = await self._exchange_rates.get_latest_rate(
            source_currency,
            target_currency,
        )
        if (
            quote.source_currency != source_currency
            or quote.target_currency != target_currency
            or quote.rate <= 0
        ):
            raise ExchangeRateUnavailableError()
        return (
            quote.rate,
            ExchangeRateMode.MARKET,
            quote.provider,
            quote.updated_at,
        )
