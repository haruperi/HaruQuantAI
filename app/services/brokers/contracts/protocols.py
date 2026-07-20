"""Focused asynchronous broker capability protocols."""

from __future__ import annotations

# ruff: noqa: A002, ANN401, BLE001, C901, PYI034 - normative boundary.
import asyncio
import functools
import inspect
from collections.abc import AsyncIterator, Mapping
from datetime import datetime
from decimal import Decimal
from types import TracebackType
from typing import Any, Literal, Protocol, cast, override, runtime_checkable

from app.services.brokers.contracts.enums import (
    BrokerCapabilityId,
    BrokerConnectionState,
    BrokerErrorCode,
)
from app.services.brokers.contracts.models import (
    BrokerAccountInfo,
    BrokerAccountTransaction,
    BrokerAssetInfo,
    BrokerBalance,
    BrokerBar,
    BrokerCapability,
    BrokerConnectionConfig,
    BrokerConnectionEvent,
    BrokerConnectionStatus,
    BrokerDeal,
    BrokerError,
    BrokerFeatureFlags,
    BrokerFeeEstimate,
    BrokerMarginRequest,
    BrokerMarketStatus,
    BrokerOrder,
    BrokerOrderBook,
    BrokerOrderCheck,
    BrokerOrderFilter,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerPage,
    BrokerPermissions,
    BrokerPlatformInfo,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionFilter,
    BrokerPositionModificationRequest,
    BrokerProfitRequest,
    BrokerQuote,
    BrokerResult,
    BrokerServerTime,
    BrokerSubscriptionInfo,
    BrokerSymbolInfo,
    BrokerTick,
    BrokerTradingSession,
)
from app.services.brokers.contracts.unsupported import _unsupported_result, _utc_now
from app.utils import generate_id, logger


@runtime_checkable
class BrokerSubscription[TEvent](Protocol):
    """Typed bounded provider-event subscription."""

    @property
    def info(self) -> BrokerSubscriptionInfo:
        """Handle info.

        Returns:
            The operation result.
        """
        ...

    def events(self) -> AsyncIterator[TEvent | BrokerError]:
        """Handle events.

        Returns:
            The operation result.
        """
        ...

    async def unsubscribe(self) -> BrokerResult[None]:
        """Handle unsubscribe.

        Returns:
            The operation result.
        """
        ...


@runtime_checkable
class MarketDataProvider(Protocol):
    """Provider-native market-data and subscription surface."""

    async def get_symbols(
        self,
        query: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerSymbolInfo]]:
        """Return get symbols.

        Args:
            query: Value supplied to the operation.
            cursor: Value supplied to the operation.
            limit: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_symbol_info(self, symbol: str) -> BrokerResult[BrokerSymbolInfo]:
        """Return get symbol info.

        Args:
            symbol: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def select_symbol(
        self, symbol: str, enabled: bool = True
    ) -> BrokerResult[None]:
        """Handle select symbol.

        Args:
            symbol: Value supplied to the operation.
            enabled: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_market_status(self, symbol: str) -> BrokerResult[BrokerMarketStatus]:
        """Return get market status.

        Args:
            symbol: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_trading_sessions(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> BrokerResult[tuple[BrokerTradingSession, ...]]:
        """Return get trading sessions.

        Args:
            symbol: Value supplied to the operation.
            start: Value supplied to the operation.
            end: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_quote(self, symbol: str) -> BrokerResult[BrokerQuote]:
        """Return get quote.

        Args:
            symbol: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_ticks(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerTick]]:
        """Return get ticks.

        Args:
            symbol: Value supplied to the operation.
            start: Value supplied to the operation.
            end: Value supplied to the operation.
            cursor: Value supplied to the operation.
            limit: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerBar]]:
        """Return get historical bars.

        Args:
            symbol: Value supplied to the operation.
            timeframe: Value supplied to the operation.
            start: Value supplied to the operation.
            end: Value supplied to the operation.
            cursor: Value supplied to the operation.
            limit: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_order_book(
        self, symbol: str, depth: int | None = None
    ) -> BrokerResult[BrokerOrderBook]:
        """Return get order book.

        Args:
            symbol: Value supplied to the operation.
            depth: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_spread(self, symbol: str) -> BrokerResult[Decimal]:
        """Return get spread.

        Args:
            symbol: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def subscribe_quotes(
        self, symbols: tuple[str, ...]
    ) -> BrokerResult[BrokerSubscription[BrokerQuote]]:
        """Handle subscribe quotes.

        Args:
            symbols: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def subscribe_bars(
        self, symbols: tuple[str, ...], timeframe: str
    ) -> BrokerResult[BrokerSubscription[BrokerBar]]:
        """Handle subscribe bars.

        Args:
            symbols: Value supplied to the operation.
            timeframe: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def subscribe_order_book(
        self, symbols: tuple[str, ...], depth: int | None = None
    ) -> BrokerResult[BrokerSubscription[BrokerOrderBook]]:
        """Handle subscribe order book.

        Args:
            symbols: Value supplied to the operation.
            depth: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def unsubscribe(self, subscription_id: str) -> BrokerResult[None]:
        """Handle unsubscribe.

        Args:
            subscription_id: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def list_subscriptions(
        self,
    ) -> BrokerResult[tuple[BrokerSubscriptionInfo, ...]]:
        """Return list subscriptions.

        Returns:
            The operation result.
        """
        ...


@runtime_checkable
class AccountProvider(Protocol):
    """Provider-native platform, account, and execution-state reads."""

    async def get_feature_flags(self) -> BrokerResult[BrokerFeatureFlags]:
        """Return get feature flags.

        Returns:
            The operation result.
        """
        ...

    async def supports(self, capability: BrokerCapabilityId) -> BrokerResult[bool]:
        """Return supports.

        Args:
            capability: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_platform_info(self) -> BrokerResult[BrokerPlatformInfo]:
        """Return get platform info.

        Returns:
            The operation result.
        """
        ...

    async def get_permissions(self) -> BrokerResult[BrokerPermissions]:
        """Return get permissions.

        Returns:
            The operation result.
        """
        ...

    async def list_accounts(
        self, cursor: str | None = None, limit: int | None = None
    ) -> BrokerResult[BrokerPage[BrokerAccountInfo]]:
        """Return list accounts.

        Args:
            cursor: Value supplied to the operation.
            limit: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def select_account(self, account_id: str) -> BrokerResult[None]:
        """Handle select account.

        Args:
            account_id: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_account_info(self) -> BrokerResult[BrokerAccountInfo]:
        """Return get account info.

        Returns:
            The operation result.
        """
        ...

    async def get_balances(self) -> BrokerResult[tuple[BrokerBalance, ...]]:
        """Return get balances.

        Returns:
            The operation result.
        """
        ...

    async def list_assets(
        self, cursor: str | None = None, limit: int | None = None
    ) -> BrokerResult[BrokerPage[BrokerAssetInfo]]:
        """Return list assets.

        Args:
            cursor: Value supplied to the operation.
            limit: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_asset_info(self, asset: str) -> BrokerResult[BrokerAssetInfo]:
        """Return get asset info.

        Args:
            asset: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_positions(
        self,
        filter: BrokerPositionFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerPosition]]:
        """Return get positions.

        Args:
            filter: Value supplied to the operation.
            cursor: Value supplied to the operation.
            limit: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_position(self, position_id: str) -> BrokerResult[BrokerPosition]:
        """Return get position.

        Args:
            position_id: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_orders(
        self,
        filter: BrokerOrderFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerOrder]]:
        """Return get orders.

        Args:
            filter: Value supplied to the operation.
            cursor: Value supplied to the operation.
            limit: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_order(self, order_id: str) -> BrokerResult[BrokerOrder]:
        """Return get order.

        Args:
            order_id: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def list_order_history(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        symbol: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerOrder]]:
        """Return list order history.

        Args:
            start: Value supplied to the operation.
            end: Value supplied to the operation.
            symbol: Value supplied to the operation.
            cursor: Value supplied to the operation.
            limit: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def list_deal_history(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        symbol: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerDeal]]:
        """Return list deal history.

        Args:
            start: Value supplied to the operation.
            end: Value supplied to the operation.
            symbol: Value supplied to the operation.
            cursor: Value supplied to the operation.
            limit: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_deal(self, deal_id: str) -> BrokerResult[BrokerDeal]:
        """Return get deal.

        Args:
            deal_id: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def list_account_transactions(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerAccountTransaction]]:
        """Return list account transactions.

        Args:
            start: Value supplied to the operation.
            end: Value supplied to the operation.
            cursor: Value supplied to the operation.
            limit: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...


@runtime_checkable
class TradeExecutionProvider(Protocol):
    """Single-target provider mutation primitives."""

    async def check_order(
        self, request: BrokerOrderRequest
    ) -> BrokerResult[BrokerOrderCheck]:
        """Handle check order.

        Args:
            request: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def place_order(
        self, request: BrokerOrderRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Handle place order.

        Args:
            request: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def modify_order(
        self, request: BrokerOrderModificationRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Handle modify order.

        Args:
            request: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def cancel_order(
        self, order_id: str, client_request_id: str | None = None
    ) -> BrokerResult[BrokerOrderResult]:
        """Handle cancel order.

        Args:
            order_id: Value supplied to the operation.
            client_request_id: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def modify_position(
        self, request: BrokerPositionModificationRequest
    ) -> BrokerResult[BrokerPosition]:
        """Handle modify position.

        Args:
            request: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def close_position(
        self, request: BrokerPositionCloseRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Handle close position.

        Args:
            request: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def replace_order(
        self, request: BrokerOrderModificationRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Handle replace order.

        Args:
            request: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...


@runtime_checkable
class CalculationProvider(Protocol):
    """Provider-native calculation surface."""

    async def calculate_margin(
        self, request: BrokerMarginRequest
    ) -> BrokerResult[Decimal]:
        """Return calculate margin.

        Args:
            request: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def calculate_profit(
        self, request: BrokerProfitRequest
    ) -> BrokerResult[Decimal]:
        """Return calculate profit.

        Args:
            request: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...

    async def get_commission_estimate(
        self, request: BrokerOrderRequest
    ) -> BrokerResult[BrokerFeeEstimate]:
        """Return get commission estimate.

        Args:
            request: Value supplied to the operation.

        Returns:
            The operation result.
        """
        ...


@runtime_checkable
class BrokerAdapter(
    MarketDataProvider,
    AccountProvider,
    TradeExecutionProvider,
    CalculationProvider,
    Protocol,
):
    """Composite asynchronous broker adapter contract."""

    @property
    def contract_version(self) -> Literal["v1"]:
        """Handle contract version.

        Returns:
            The operation result.
        """
        ...

    @property
    def schema_id(self) -> Literal["brokers.adapter.v1"]:
        """Handle schema id.

        Returns:
            The operation result.
        """
        ...

    async def __aenter__(self) -> BrokerAdapter:
        """Handle aenter.

        Returns:
            The operation result.
        """
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Handle aexit.

        Args:
            exc_type: Value supplied to the operation.
            exc: Value supplied to the operation.
            traceback: Value supplied to the operation.
        """
        ...

    async def connect(self) -> BrokerResult[None]:
        """Handle connect.

        Returns:
            The operation result.
        """
        ...

    async def disconnect(self) -> BrokerResult[None]:
        """Handle disconnect.

        Returns:
            The operation result.
        """
        ...

    async def reconnect(self) -> BrokerResult[None]:
        """Handle reconnect.

        Returns:
            The operation result.
        """
        ...

    async def is_connected(self) -> BrokerResult[bool]:
        """Return is connected.

        Returns:
            The operation result.
        """
        ...

    async def get_connection_status(
        self,
    ) -> BrokerResult[BrokerConnectionStatus]:
        """Return get connection status.

        Returns:
            The operation result.
        """
        ...

    async def ping(self) -> BrokerResult[None]:
        """Handle ping.

        Returns:
            The operation result.
        """
        ...

    async def refresh_session(self) -> BrokerResult[None]:
        """Handle refresh session.

        Returns:
            The operation result.
        """
        ...

    async def get_server_time(self) -> BrokerResult[BrokerServerTime]:
        """Return get server time.

        Returns:
            The operation result.
        """
        ...

    async def get_last_error(self) -> BrokerResult[BrokerError | None]:
        """Return get last error.

        Returns:
            The operation result.
        """
        ...

    def connection_events(self) -> AsyncIterator[BrokerConnectionEvent]:
        """Handle connection events.

        Returns:
            The operation result.
        """
        ...


class _UnsupportedAdapterBase:
    """Lifecycle and fail-closed defaults shared by concrete adapters."""

    ADAPTER_VERSION = "1.0.0"
    _ENFORCE_DECLARED_AVAILABILITY = True
    _LOCAL_FAIL_SAFE_OPERATIONS = frozenset(
        {
            BrokerCapabilityId.DISCONNECT,
            BrokerCapabilityId.GET_CONNECTION_STATUS,
            BrokerCapabilityId.GET_LAST_ERROR,
            BrokerCapabilityId.CONNECTION_EVENTS,
            BrokerCapabilityId.GET_FEATURE_FLAGS,
            BrokerCapabilityId.SUPPORTS,
            BrokerCapabilityId.UNSUBSCRIBE,
            BrokerCapabilityId.LIST_SUBSCRIPTIONS,
        }
    )
    _MUTATION_OPERATIONS = frozenset(
        {
            BrokerCapabilityId.CHECK_ORDER,
            BrokerCapabilityId.PLACE_ORDER,
            BrokerCapabilityId.MODIFY_ORDER,
            BrokerCapabilityId.CANCEL_ORDER,
            BrokerCapabilityId.MODIFY_POSITION,
            BrokerCapabilityId.CLOSE_POSITION,
            BrokerCapabilityId.REPLACE_ORDER,
        }
    )

    def __init__(
        self,
        config: BrokerConnectionConfig,
        capabilities: Mapping[BrokerCapabilityId, BrokerCapability],
    ) -> None:
        """Handle init."""
        self._config = config
        self._capabilities = dict(capabilities)
        self._state = BrokerConnectionState.DISCONNECTED
        self._session_generation = 0
        self._last_error: BrokerError | None = None
        self._event_queue: asyncio.Queue[BrokerConnectionEvent] = asyncio.Queue(
            config.stream_buffer_size
        )

    @property
    def contract_version(self) -> Literal["v1"]:
        """Return the implemented broker boundary version."""
        return "v1"

    @property
    def schema_id(self) -> Literal["brokers.adapter.v1"]:
        """Return the composite adapter schema identifier."""
        return "brokers.adapter.v1"

    @override
    def __getattribute__(self, name: str) -> Any:
        """Enforce declared availability before provider implementation access.

        Args:
            name: Attribute name requested by the caller.

        Returns:
            The declared attribute or a fail-closed unsupported operation.
        """
        operation: BrokerCapabilityId | None = None
        if not name.startswith("_"):
            try:
                operation = BrokerCapabilityId(name)
            except ValueError:
                operation = None
            if operation is not None:
                enforce = object.__getattribute__(
                    self, "_ENFORCE_DECLARED_AVAILABILITY"
                )
                local = object.__getattribute__(self, "_LOCAL_FAIL_SAFE_OPERATIONS")
                capabilities = object.__getattribute__(self, "_capabilities")
                declared = capabilities.get(operation)
                if (
                    enforce
                    and operation not in local
                    and declared is not None
                    and declared.availability == "UNAVAILABLE"
                ):

                    async def _blocked(
                        *args: object, **kwargs: object
                    ) -> BrokerResult[Any]:
                        """Return the declared unavailable capability result.

                        Returns:
                            A deterministic unsupported result.
                        """
                        del args, kwargs
                        return self._unsupported(operation)

                    return _blocked
        attribute = object.__getattribute__(self, name)
        if operation is None or operation == BrokerCapabilityId.CONNECTION_EVENTS:
            return attribute
        if not callable(attribute):
            return attribute

        @functools.wraps(attribute)
        async def _guarded(*args: object, **kwargs: object) -> BrokerResult[Any]:
            """Normalize an adapter call into a canonical result.

            Returns:
                The canonical adapter result.

            Raises:
                asyncio.CancelledError: If the caller cancels the operation.
            """
            try:
                result = await attribute(*args, **kwargs)
                return cast("BrokerResult[Any]", result)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                return self._exception_result(operation, error)

        return _guarded

    async def __aenter__(self) -> _UnsupportedAdapterBase:
        """Connect and enter the adapter context.

        Returns:
            The connected adapter instance.

        Raises:
            RuntimeError: If the adapter cannot connect.
        """
        result = await self.connect()
        if not result.is_success:
            message = result.error.message if result.error else "connect failed"
            raise RuntimeError(message)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Handle aexit."""
        del exc_type, exc, traceback
        await self.disconnect()

    def _result[T](
        self,
        operation: BrokerCapabilityId,
        *,
        data: T | None = None,
        error: BrokerError | None = None,
        request_id: str | None = None,
        provider_metadata: Mapping[str, object] | None = None,
    ) -> BrokerResult[T]:
        """Build and log one canonical adapter result.

        Returns:
            The canonical result envelope.
        """
        result: BrokerResult[T] = BrokerResult(
            status="error" if error else "success",
            broker=self._config.broker_id,
            operation=operation,
            request_id=request_id or generate_id("req"),
            timestamp=_utc_now(),
            environment=self._config.environment,
            adapter_version=self.ADAPTER_VERSION,
            data=data,
            error=error,
            provider_metadata=provider_metadata or {},
        )
        bound = logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            operation=operation.value,
            request_id=result.request_id,
            result=result.status,
            provider_code=error.code.value if error is not None else None,
            latency_ms=result.latency_ms,
        )
        if error is not None:
            bound.warning("Broker operation returned canonical error")
        else:
            bound.info("Broker operation completed")
        return result

    async def _transition(
        self,
        state: BrokerConnectionState,
        *,
        reason: str | None = None,
        resynchronization_required: bool = False,
    ) -> None:
        """Handle transition."""
        if state == self._state:
            return
        event = BrokerConnectionEvent(
            previous_state=self._state,
            new_state=state,
            timestamp=_utc_now(),
            session_generation=self._session_generation,
            reason=reason,
            resynchronization_required=resynchronization_required,
        )
        self._state = state
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            previous_state=event.previous_state.value,
            new_state=state.value,
            session_generation=self._session_generation,
            reason=reason,
            resynchronization_required=resynchronization_required,
        ).info("Broker connection state transition")
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            self._state = BrokerConnectionState.DEGRADED
            logger.bind(
                broker=self._config.broker_id.value,
                environment=self._config.environment.value,
                new_state=BrokerConnectionState.DEGRADED.value,
            ).warning("Connection event buffer overflow; adapter degraded")

    async def connect(self) -> BrokerResult[None]:
        """Fail closed unless a provider verifies a real session.

        Returns:
            A canonical unsupported connection result.
        """
        return self._unsupported(BrokerCapabilityId.CONNECT)

    async def disconnect(self) -> BrokerResult[None]:
        """Idempotently close adapter-local state.

        Returns:
            A canonical successful disconnection result.
        """
        if self._state != BrokerConnectionState.DISCONNECTED:
            await self._transition(BrokerConnectionState.CLOSING)
            await self._transition(BrokerConnectionState.DISCONNECTED)
        return self._result(BrokerCapabilityId.DISCONNECT)

    async def reconnect(self) -> BrokerResult[None]:
        """Reconnect the same session without replaying an operation.

        Returns:
            The canonical result of the new connection attempt.
        """
        await self.disconnect()
        return await self.connect()

    async def is_connected(self) -> BrokerResult[bool]:
        """Return conservative locally retained session evidence.

        Provider adapters override this method when current connectivity can be
        verified. The shared default never upgrades non-provider evidence.

        Returns:
            A canonical result that is true only for a retained verified session.
        """
        return self._result(
            BrokerCapabilityId.IS_CONNECTED,
            data=self._state == BrokerConnectionState.READY,
        )

    async def get_connection_status(self) -> BrokerResult[BrokerConnectionStatus]:
        """Return detailed fail-closed session state."""
        return self._result(
            BrokerCapabilityId.GET_CONNECTION_STATUS,
            data=BrokerConnectionStatus(
                state=self._state,
                transport_connected=self._state == BrokerConnectionState.READY,
                environment=self._config.environment,
                session_generation=self._session_generation,
                observed_at=_utc_now(),
                application_authenticated=None,
                account_authenticated=None,
                trading_permitted=None,
                subscriptions_ready=None,
            ),
        )

    async def get_last_error(self) -> BrokerResult[BrokerError | None]:
        """Return the latest redacted non-authoritative error."""
        return self._result(BrokerCapabilityId.GET_LAST_ERROR, data=self._last_error)

    def connection_events(self) -> AsyncIterator[BrokerConnectionEvent]:
        """Return bounded lifecycle events for this adapter instance.

        Returns:
            An asynchronous iterator over connection lifecycle events.
        """

        async def _events() -> AsyncIterator[BrokerConnectionEvent]:
            """Yield adapter lifecycle events in publication order.

            Yields:
                The next connection lifecycle event.
            """
            while True:
                yield await self._event_queue.get()

        return _events()

    async def get_feature_flags(self) -> BrokerResult[BrokerFeatureFlags]:
        """Return the complete catalogue supplied by the registry."""
        flags = BrokerFeatureFlags(
            broker_id=self._config.broker_id,
            environment=self._config.environment,
            generated_at=_utc_now(),
            capabilities=self._capabilities,
            adapter_version=self.ADAPTER_VERSION,
            account_reference_redacted=(
                "***" if self._config.account_reference is not None else None
            ),
        )
        return self._result(BrokerCapabilityId.GET_FEATURE_FLAGS, data=flags)

    async def supports(self, capability: BrokerCapabilityId) -> BrokerResult[bool]:
        """Answer from the static declaration without probing a provider.

        Args:
            capability: Capability whose declared availability is requested.

        Returns:
            A canonical result containing declared support status.
        """
        declared = self._capabilities[capability]
        return self._result(
            BrokerCapabilityId.SUPPORTS,
            data=declared.availability in {"AVAILABLE", "DEGRADED"},
        )

    def _unsupported[T](self, operation: BrokerCapabilityId) -> BrokerResult[T]:
        """Return and record a deterministic unsupported result.

        Returns:
            The canonical unsupported result.
        """
        result: BrokerResult[T] = _unsupported_result(
            broker=self._config.broker_id,
            environment=self._config.environment,
            operation=operation,
            request_id=generate_id("req"),
            adapter_version=self.ADAPTER_VERSION,
        )
        self._last_error = result.error
        logger.bind(
            broker=self._config.broker_id.value,
            environment=self._config.environment.value,
            operation=operation.value,
            request_id=result.request_id,
            result="error",
            provider_code=(
                result.error.code.value if result.error is not None else None
            ),
        ).warning("Broker operation unavailable; failing closed without provider call")
        return result

    def _exception_result[T](
        self,
        operation: BrokerCapabilityId,
        error: BaseException,
    ) -> BrokerResult[T]:
        """Translate one public-boundary failure to a canonical result.

        Args:
            operation: Canonical operation that failed.
            error: Bounded exception raised by validation or provider access.

        Returns:
            A redacted canonical failure result.
        """
        if operation in self._MUTATION_OPERATIONS and isinstance(
            error, (OSError, TimeoutError, ConnectionError)
        ):
            code = BrokerErrorCode.BROKER_UNKNOWN_OUTCOME
        elif isinstance(error, TimeoutError):
            code = BrokerErrorCode.BROKER_TIMEOUT
        elif isinstance(error, (OSError, ConnectionError)):
            code = BrokerErrorCode.BROKER_CONNECTION_LOST
        elif isinstance(error, ImportError):
            code = BrokerErrorCode.BROKER_DEPENDENCY_MISSING
        elif isinstance(error, ValueError):
            code = BrokerErrorCode.BROKER_REQUEST_INVALID
        else:
            code = BrokerErrorCode.BROKER_RESPONSE_INVALID
        canonical = BrokerError(
            code=code,
            message=f"Broker {operation.value} failed",
            retryable=False,
            provider_message=type(error).__name__,
            capability=operation,
        )
        self._last_error = canonical
        return self._result(operation, error=canonical)

    def __getattr__(self, name: str) -> Any:
        """Return defaults only for canonical unsupported operations.

        Args:
            name: Missing attribute name requested by the caller.

        Returns:
            A fail-closed asynchronous unsupported operation.

        Raises:
            AttributeError: If the name is not a canonical broker capability.
        """
        try:
            operation = BrokerCapabilityId(name)
        except ValueError as error:
            raise AttributeError(name) from error

        async def _operation(*args: object, **kwargs: object) -> BrokerResult[Any]:
            """Return the dynamically selected unsupported result.

            Returns:
                The canonical unsupported result.
            """
            del args, kwargs
            return self._unsupported(operation)

        return _operation


def _make_unsupported_method(operation: BrokerCapabilityId) -> Any:
    """Create one structurally visible unsupported protocol method.

    Args:
        operation: Capability represented by the generated method.

    Returns:
        An asynchronous fail-closed unsupported method.
    """

    async def _method(
        self: _UnsupportedAdapterBase,
        *args: object,
        **kwargs: object,
    ) -> BrokerResult[Any]:
        """Return the generated unsupported operation result.

        Returns:
            The canonical unsupported result.
        """
        del args, kwargs
        return self._unsupported(operation)

    _method.__name__ = operation.value
    protocol_method = getattr(BrokerAdapter, operation.value)
    _method.__annotations__ = dict(protocol_method.__annotations__)
    _method.__signature__ = inspect.signature(protocol_method)  # type: ignore[attr-defined]
    return _method


for _operation_id in BrokerCapabilityId:
    if not hasattr(_UnsupportedAdapterBase, _operation_id.value):
        setattr(
            _UnsupportedAdapterBase,
            _operation_id.value,
            _make_unsupported_method(_operation_id),
        )
