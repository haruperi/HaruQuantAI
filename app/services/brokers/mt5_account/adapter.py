"""Canonical MetaTrader 5 broker adapter."""

# ruff: noqa: A002 - public protocol signatures are normative.

from datetime import UTC, datetime
from decimal import Decimal
from typing import override

from app.services.brokers.contracts import (
    BrokerAccountInfo,
    BrokerBalance,
    BrokerBar,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerPage,
    BrokerPermissions,
    BrokerPlatformInfo,
    BrokerPosition,
    BrokerPositionFilter,
    BrokerQuote,
    BrokerResult,
    BrokerSymbolInfo,
    BrokerTick,
)
from app.services.brokers.contracts.protocols import (
    _RequestValidationError,
    _UnsupportedAdapterBase,
)
from app.services.brokers.mt5_account.mapping import (
    _field,
    _map_account,
    _map_balance,
    _map_bar,
    _map_permissions,
    _map_position,
    _map_quote,
    _map_symbol,
    _map_tick,
)
from app.services.brokers.mt5_account.transport import _MT5Transport


def _provider_ticket(value: str) -> int:
    """Parse one caller-supplied MT5 ticket before any provider transmission.

    Args:
        value: Caller-supplied provider order or position identifier.

    Returns:
        The exact integral MT5 ticket.

    Raises:
        _RequestValidationError: If the identifier is not a valid MT5 ticket.
            Raised before transmission so a malformed caller identifier is never
            reported as an uncertain mutation outcome.
    """
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise _RequestValidationError("MT5 ticket must be an integer") from error


from app.services.brokers.execution_history.mt5 import (  # noqa: E402
    _MT5ExecutionHistoryMixin,
)
from app.services.brokers.mt5_mutations.operations import (  # noqa: E402
    _MT5MutationsMixin,
)
from app.services.brokers.provider_calculations.mt5 import (  # noqa: E402
    _MT5CalculationsMixin,
)


class MT5BrokerAdapter(
    _MT5CalculationsMixin,
    _MT5ExecutionHistoryMixin,
    _MT5MutationsMixin,
    _UnsupportedAdapterBase,
):
    """One isolated serialized MetaTrader 5 terminal/account adapter."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        *,
        transport: _MT5Transport | None = None,
    ) -> None:
        """Initialize the MT5BrokerAdapter instance.

        Args:
            config: Value supplied to the operation.
            transport: Value supplied to the operation.

        Raises:
            ValueError: If the documented operation cannot complete.
        """
        if config.environment not in {BrokerEnvironment.LIVE, BrokerEnvironment.DEMO}:
            raise ValueError("MT5 requires LIVE or DEMO")
        if config.endpoint is not None:
            raise ValueError("MT5 does not accept endpoint override")
        required = {"login", "password", "server"}
        if config.credentials is None or not required <= set(config.credentials):
            raise ValueError("MT5 resolved login, password, and server are required")
        if config.account_reference != config.credentials["login"].get_secret_value():
            raise ValueError("MT5 account_reference must match login")
        super().__init__(config)
        self._transport = transport or _MT5Transport(
            config, self._record_provider_latency
        )

    @override
    async def connect(self) -> BrokerResult[None]:
        """Connect and verify terminal, login, server, and trade evidence.

        Returns:
            Canonical connection result.
        """
        await self._transition(BrokerConnectionState.CONNECTING)
        try:
            initialized = await self._transport.connect()
            account = await self._transport.call("account_info")
            terminal = await self._transport.call("terminal_info")
            credentials = self._config.credentials or {}
            expected_login = credentials["login"].get_secret_value()
            expected_server = credentials["server"].get_secret_value()
            verified = (
                initialized
                and account is not None
                and terminal is not None
                and str(_field(account, "login")) == expected_login
                and str(_field(account, "server")) == expected_server
            )
        except (
            ImportError,
            OSError,
            TimeoutError,
            ValueError,
            ConnectionError,
        ) as error:
            verified = False
            self._last_error = BrokerError(
                code=BrokerErrorCode.BROKER_CONNECTION_FAILED,
                message="MT5 connection verification failed",
                provider_message=type(error).__name__,
            )
        if not verified:
            if self._last_error is None:
                self._last_error = BrokerError(
                    code=BrokerErrorCode.BROKER_CONNECTION_FAILED,
                    message="MT5 connection verification failed",
                )
            await self._transition(
                BrokerConnectionState.FAILED, reason="verification_failed"
            )
            return self._result(BrokerCapabilityId.CONNECT, error=self._last_error)
        self._session_generation += 1
        await self._transition(BrokerConnectionState.READY)
        return self._result(BrokerCapabilityId.CONNECT)

    @override
    async def disconnect(self) -> BrokerResult[None]:
        """Idempotently release the owned terminal handle.

        Returns:
            Canonical disconnection result.
        """
        await self._transport.close()
        return await super().disconnect()

    async def ping(self) -> BrokerResult[None]:
        """Probe the verified terminal session.

        Returns:
            Canonical provider-health result.
        """
        terminal = await self._transport.call("terminal_info")
        if terminal is None:
            return self._unsupported(BrokerCapabilityId.PING)
        return self._result(BrokerCapabilityId.PING)

    @override
    async def is_connected(self) -> BrokerResult[bool]:
        """Verify the retained MT5 terminal and configured account identity.

        Returns:
            Canonical current connectivity evidence.
        """
        account = await self._transport.call("account_info")
        terminal = await self._transport.call("terminal_info")
        credentials = self._config.credentials or {}
        expected_login = credentials["login"].get_secret_value()
        expected_server = credentials["server"].get_secret_value()
        connected = (
            account is not None
            and terminal is not None
            and str(_field(account, "login")) == expected_login
            and str(_field(account, "server")) == expected_server
        )
        return self._result(BrokerCapabilityId.IS_CONNECTED, data=connected)

    async def get_symbols(
        self,
        query: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerSymbolInfo]]:
        """Return a caller-bounded page of exact MT5 symbols.

        Raises:
            ValueError: If the requested limit is not positive.
        """
        del cursor
        if limit is None or limit <= 0:
            raise ValueError("positive symbol limit is required")
        values = (
            await self._transport.call("symbols_get", query)
            if query
            else await self._transport.call("symbols_get")
        )
        items = tuple(_map_symbol(value) for value in (values or ())[:limit])
        return self._result(
            BrokerCapabilityId.GET_SYMBOLS,
            data=BrokerPage(
                items=items,
                limit=limit,
                truncated=bool(values) and len(values) > limit,
            ),
        )

    async def get_symbol_info(self, symbol: str) -> BrokerResult[BrokerSymbolInfo]:
        """Return direct MT5 symbol specifications."""
        value = await self._transport.call("symbol_info", symbol)
        if value is None:
            return self._error(
                BrokerCapabilityId.GET_SYMBOL_INFO,
                BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND,
            )
        return self._result(BrokerCapabilityId.GET_SYMBOL_INFO, data=_map_symbol(value))

    async def select_symbol(
        self, symbol: str, enabled: bool = True
    ) -> BrokerResult[None]:
        """Set only MT5 Market Watch selection state.

        Returns:
            Canonical symbol-selection result.
        """
        if not await self._transport.call("symbol_select", symbol, enabled):
            return self._error(
                BrokerCapabilityId.SELECT_SYMBOL,
                BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND,
            )
        return self._result(BrokerCapabilityId.SELECT_SYMBOL)

    async def get_quote(self, symbol: str) -> BrokerResult[BrokerQuote]:
        """Return the latest genuine MT5 quote."""
        value = await self._transport.call("symbol_info_tick", symbol)
        if value is None:
            return self._error(
                BrokerCapabilityId.GET_QUOTE, BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND
            )
        return self._result(
            BrokerCapabilityId.GET_QUOTE, data=_map_quote(value, symbol)
        )

    async def get_ticks(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerTick]]:
        """Return caller-bounded genuine MT5 ticks.

        Raises:
            ValueError: If the limit or optional range is invalid.
        """
        del cursor
        if limit is None or limit <= 0:
            raise ValueError("positive tick limit is required")
        if (start is None) != (end is None):
            raise ValueError("tick start and end must be supplied together")
        if start is None or end is None:
            latest = await self._transport.call("symbol_info_tick", symbol)
            available = () if latest is None else (latest,)
            items = tuple(_map_tick(value, symbol) for value in available)
        else:
            if start >= end:
                raise ValueError("tick start must precede end")
            values = await self._transport.call(
                "copy_ticks_from",
                symbol,
                start,
                limit,
                7,
            )
            available = values if values is not None else ()
            items = tuple(
                tick
                for tick in (_map_tick(value, symbol) for value in available[:limit])
                if tick.event_timestamp <= end
            )
        return self._result(
            BrokerCapabilityId.GET_TICKS,
            data=BrokerPage(
                items=items,
                limit=limit,
                truncated=len(available) > limit,
            ),
        )

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerBar]]:
        """Return caller-bounded genuine MT5 historical bars.

        Raises:
            ValueError: If the limit, timeframe, or optional range is invalid.
        """
        del cursor
        if limit is None or limit <= 0:
            raise ValueError("positive bar limit is required")
        if (start is None) != (end is None):
            raise ValueError("bar start and end must be supplied together")
        normalized_timeframe = timeframe.upper()
        constant_names = {
            "M1": "TIMEFRAME_M1",
            "M2": "TIMEFRAME_M2",
            "M3": "TIMEFRAME_M3",
            "M4": "TIMEFRAME_M4",
            "M5": "TIMEFRAME_M5",
            "M6": "TIMEFRAME_M6",
            "M10": "TIMEFRAME_M10",
            "M12": "TIMEFRAME_M12",
            "M15": "TIMEFRAME_M15",
            "M20": "TIMEFRAME_M20",
            "M30": "TIMEFRAME_M30",
            "H1": "TIMEFRAME_H1",
            "H2": "TIMEFRAME_H2",
            "H3": "TIMEFRAME_H3",
            "H4": "TIMEFRAME_H4",
            "H6": "TIMEFRAME_H6",
            "H8": "TIMEFRAME_H8",
            "H12": "TIMEFRAME_H12",
            "D1": "TIMEFRAME_D1",
            "W1": "TIMEFRAME_W1",
            "MN1": "TIMEFRAME_MN1",
        }
        try:
            provider_timeframe = await self._transport.constant(
                constant_names[normalized_timeframe]
            )
        except KeyError as error:
            raise ValueError("unsupported MT5 timeframe") from error
        if start is None or end is None:
            values = await self._transport.call(
                "copy_rates_from_pos",
                symbol,
                provider_timeframe,
                1,
                limit,
            )
        else:
            if start >= end:
                raise ValueError("bar start must precede end")
            values = await self._transport.call(
                "copy_rates_range",
                symbol,
                provider_timeframe,
                start,
                end,
            )
        available = values if values is not None else ()
        items = tuple(
            _map_bar(value, symbol, normalized_timeframe) for value in available[:limit]
        )
        return self._result(
            BrokerCapabilityId.GET_HISTORICAL_BARS,
            data=BrokerPage(
                items=items,
                limit=limit,
                truncated=len(available) > limit,
            ),
        )

    async def get_spread(self, symbol: str) -> BrokerResult[Decimal]:
        """Return the current genuine MT5 bid/ask spread."""
        value = await self._transport.call("symbol_info_tick", symbol)
        if value is None:
            return self._error(
                BrokerCapabilityId.GET_SPREAD,
                BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND,
            )
        quote = _map_quote(value, symbol)
        if quote.bid is None or quote.ask is None:
            return self._error(
                BrokerCapabilityId.GET_SPREAD,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
            )
        return self._result(
            BrokerCapabilityId.GET_SPREAD,
            data=quote.ask - quote.bid,
        )

    async def get_account_info(self) -> BrokerResult[BrokerAccountInfo]:
        """Return direct MT5 account state."""
        value = await self._transport.call("account_info")
        if value is None:
            return self._error(
                BrokerCapabilityId.GET_ACCOUNT_INFO,
                BrokerErrorCode.BROKER_ACCOUNT_NOT_FOUND,
            )
        return self._result(
            BrokerCapabilityId.GET_ACCOUNT_INFO, data=_map_account(value)
        )

    async def get_positions(
        self,
        filter: BrokerPositionFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerPosition]]:
        """Return caller-bounded direct MT5 position state.

        Raises:
            ValueError: If the requested limit is not positive.
        """
        del cursor
        if limit is None or limit <= 0:
            raise ValueError("positive position limit is required")
        kwargs = {"symbol": filter.symbol} if filter and filter.symbol else {}
        values = await self._transport.call("positions_get", **kwargs)
        mapped = tuple(_map_position(value) for value in (values or ()))
        if filter is not None and filter.side is not None:
            mapped = tuple(item for item in mapped if item.side == filter.side)
        items = mapped[:limit]
        return self._result(
            BrokerCapabilityId.GET_POSITIONS,
            data=BrokerPage(
                items=items,
                limit=limit,
                truncated=bool(values) and len(values) > limit,
            ),
        )

    async def get_platform_info(self) -> BrokerResult[BrokerPlatformInfo]:
        """Return redacted terminal version and environment evidence."""
        version = await self._transport.call("version")
        return self._result(
            BrokerCapabilityId.GET_PLATFORM_INFO,
            data=BrokerPlatformInfo(
                broker_id=self._config.broker_id,
                provider_name="MetaTrader 5",
                product_profile="mt5_terminal",
                environment=self._config.environment,
                observed_at=datetime.now(UTC),
                api_or_terminal_version=str(version) if version is not None else None,
            ),
        )

    async def get_permissions(self) -> BrokerResult[BrokerPermissions]:
        """Return permissions directly reported by MT5 account and terminal.

        Returns:
            Canonical permission evidence.
        """
        account = await self._transport.call("account_info")
        terminal = await self._transport.call("terminal_info")
        if account is None or terminal is None:
            return self._error(
                BrokerCapabilityId.GET_PERMISSIONS,
                BrokerErrorCode.BROKER_NOT_CONNECTED,
            )
        return self._result(
            BrokerCapabilityId.GET_PERMISSIONS,
            data=_map_permissions(account, terminal),
        )

    async def get_balances(self) -> BrokerResult[tuple[BrokerBalance, ...]]:
        """Return the provider account-currency balance.

        Returns:
            Canonical balance tuple.
        """
        account = await self._transport.call("account_info")
        if account is None:
            return self._error(
                BrokerCapabilityId.GET_BALANCES,
                BrokerErrorCode.BROKER_ACCOUNT_NOT_FOUND,
            )
        return self._result(
            BrokerCapabilityId.GET_BALANCES,
            data=(_map_balance(account),),
        )

    @override
    async def get_last_error(self) -> BrokerResult[BrokerError | None]:
        """Return the latest canonical or provider-reported MT5 diagnostic.

        Returns:
            Redacted non-authoritative error evidence, when present.
        """
        if self._last_error is not None:
            return self._result(
                BrokerCapabilityId.GET_LAST_ERROR, data=self._last_error
            )
        native = await self._transport.call("last_error")
        if not native or native[0] == 1:
            return self._result(BrokerCapabilityId.GET_LAST_ERROR, data=None)
        error = BrokerError(
            code=BrokerErrorCode.BROKER_PROVIDER_ERROR,
            message="MT5 provider reported an error",
            provider_code=str(native[0]),
            provider_message=str(native[1]),
        )
        return self._result(BrokerCapabilityId.GET_LAST_ERROR, data=error)

    @staticmethod
    def _validate_history(
        start: datetime | None,
        end: datetime | None,
        cursor: str | None,
        limit: int | None,
    ) -> None:
        """Validate bounded MT5 history arguments before provider access.

        Raises:
            ValueError: If the range, cursor, or limit is invalid.
        """
        if start is None or end is None or start >= end:
            raise ValueError("explicit ordered history range is required")
        if cursor is not None:
            raise ValueError("MT5 history cursors are unsupported")
        if limit is None or limit <= 0:
            raise ValueError("positive history limit is required")

    def _error[T](
        self, operation: BrokerCapabilityId, code: BrokerErrorCode
    ) -> BrokerResult[T]:
        """Handle error.

        Args:
            operation: Value supplied to the operation.
            code: Value supplied to the operation.

        Returns:
            The operation result.
        """
        error = BrokerError(code=code, message=f"MT5 {operation.value} failed")
        self._last_error = error
        return self._result(operation, error=error)
