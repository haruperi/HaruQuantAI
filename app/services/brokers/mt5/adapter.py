"""Canonical MetaTrader 5 broker adapter."""

# ruff: noqa: A002 - public signatures and native failure sets are normative.

from collections.abc import Mapping
from datetime import UTC, datetime

from app.services.brokers.contracts import (
    BrokerAccountInfo,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerPage,
    BrokerPlatformInfo,
    BrokerPosition,
    BrokerQuote,
    BrokerResult,
    BrokerSymbolInfo,
    BrokerTick,
)
from app.services.brokers.contracts.protocols import _UnsupportedAdapterBase
from app.services.brokers.mt5.mapping import (
    _field,
    _map_account,
    _map_position,
    _map_quote,
    _map_symbol,
    _map_tick,
)
from app.services.brokers.mt5.transport import _MT5Transport


class MT5BrokerAdapter(_UnsupportedAdapterBase):
    """One isolated serialized MetaTrader 5 terminal/account adapter."""

    def __init__(
        self,
        config: BrokerConnectionConfig,
        capabilities: Mapping[BrokerCapabilityId, BrokerCapability],
        *,
        transport: _MT5Transport | None = None,
    ) -> None:
        if config.environment not in {BrokerEnvironment.LIVE, BrokerEnvironment.DEMO}:
            raise ValueError("MT5 requires LIVE or DEMO")
        if config.endpoint is not None:
            raise ValueError("MT5 does not accept endpoint override")
        required = {"login", "password", "server"}
        if config.credentials is None or not required <= set(config.credentials):
            raise ValueError("MT5 resolved login, password, and server are required")
        if config.account_reference != config.credentials["login"].get_secret_value():
            raise ValueError("MT5 account_reference must match login")
        super().__init__(config, capabilities)
        self._transport = transport or _MT5Transport(config)

    async def connect(self) -> BrokerResult[None]:
        """Connect and verify terminal, login, server, and trade evidence."""
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

    async def disconnect(self) -> BrokerResult[None]:
        """Idempotently release the owned terminal handle."""
        await self._transport.close()
        return await super().disconnect()

    async def ping(self) -> BrokerResult[None]:
        """Probe the verified terminal session."""
        terminal = await self._transport.call("terminal_info")
        if terminal is None:
            return self._unsupported(BrokerCapabilityId.PING)
        return self._result(BrokerCapabilityId.PING)

    async def get_symbols(
        self,
        query: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerSymbolInfo]]:
        """Return a caller-bounded page of exact MT5 symbols."""
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
        """Set only MT5 Market Watch selection state."""
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
        """Return caller-bounded genuine MT5 ticks."""
        del cursor
        if start is None or end is None or limit is None or limit <= 0:
            raise ValueError("tick start, end, and positive limit are required")
        values = await self._transport.call("copy_ticks_range", symbol, start, end, 7)
        items = tuple(_map_tick(value, symbol) for value in (values or ())[:limit])
        return self._result(
            BrokerCapabilityId.GET_TICKS,
            data=BrokerPage(
                items=items,
                limit=limit,
                truncated=bool(values) and len(values) > limit,
            ),
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
        filter: object | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerPosition]]:
        """Return caller-bounded direct MT5 position state."""
        del filter, cursor
        if limit is None or limit <= 0:
            raise ValueError("positive position limit is required")
        values = await self._transport.call("positions_get")
        items = tuple(_map_position(value) for value in (values or ())[:limit])
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

    def _error[T](
        self, operation: BrokerCapabilityId, code: BrokerErrorCode
    ) -> BrokerResult[T]:
        error = BrokerError(code=code, message=f"MT5 {operation.value} failed")
        self._last_error = error
        return self._result(operation, error=error)
