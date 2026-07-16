"""Focused asynchronous broker capability protocols."""

from __future__ import annotations

# ruff: noqa: A002, ANN401, D102, D105, PYI034 - normative/dynamic boundary.
import asyncio
from collections.abc import AsyncIterator, Mapping
from datetime import datetime
from decimal import Decimal
from types import TracebackType
from typing import Any, Literal, Protocol, runtime_checkable

from app.services.brokers.contracts.enums import (
    BrokerCapabilityId,
    BrokerConnectionState,
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
from app.utils import logger


@runtime_checkable
class BrokerSubscription[TEvent](Protocol):
    """Typed bounded provider-event subscription."""

    @property
    def info(self) -> BrokerSubscriptionInfo: ...

    def events(self) -> AsyncIterator[TEvent | BrokerError]: ...

    async def unsubscribe(self) -> BrokerResult[None]: ...


@runtime_checkable
class MarketDataProvider(Protocol):
    """Provider-native market-data and subscription surface."""

    async def get_symbols(
        self,
        query: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerSymbolInfo]]: ...

    async def get_symbol_info(self, symbol: str) -> BrokerResult[BrokerSymbolInfo]: ...

    async def select_symbol(
        self, symbol: str, enabled: bool = True
    ) -> BrokerResult[None]: ...

    async def get_market_status(
        self, symbol: str
    ) -> BrokerResult[BrokerMarketStatus]: ...

    async def get_trading_sessions(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> BrokerResult[tuple[BrokerTradingSession, ...]]: ...

    async def get_quote(self, symbol: str) -> BrokerResult[BrokerQuote]: ...

    async def get_ticks(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerTick]]: ...

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerBar]]: ...

    async def get_order_book(
        self, symbol: str, depth: int | None = None
    ) -> BrokerResult[BrokerOrderBook]: ...

    async def get_spread(self, symbol: str) -> BrokerResult[Decimal]: ...

    async def subscribe_quotes(
        self, symbols: tuple[str, ...]
    ) -> BrokerResult[BrokerSubscription[BrokerQuote]]: ...

    async def subscribe_bars(
        self, symbols: tuple[str, ...], timeframe: str
    ) -> BrokerResult[BrokerSubscription[BrokerBar]]: ...

    async def subscribe_order_book(
        self, symbols: tuple[str, ...], depth: int | None = None
    ) -> BrokerResult[BrokerSubscription[BrokerOrderBook]]: ...

    async def unsubscribe(self, subscription_id: str) -> BrokerResult[None]: ...

    async def list_subscriptions(
        self,
    ) -> BrokerResult[tuple[BrokerSubscriptionInfo, ...]]: ...


@runtime_checkable
class AccountProvider(Protocol):
    """Provider-native platform, account, and execution-state reads."""

    async def get_feature_flags(self) -> BrokerResult[BrokerFeatureFlags]: ...

    async def supports(self, capability: BrokerCapabilityId) -> BrokerResult[bool]: ...

    async def get_platform_info(self) -> BrokerResult[BrokerPlatformInfo]: ...

    async def get_permissions(self) -> BrokerResult[BrokerPermissions]: ...

    async def list_accounts(
        self, cursor: str | None = None, limit: int | None = None
    ) -> BrokerResult[BrokerPage[BrokerAccountInfo]]: ...

    async def select_account(self, account_id: str) -> BrokerResult[None]: ...

    async def get_account_info(self) -> BrokerResult[BrokerAccountInfo]: ...

    async def get_balances(self) -> BrokerResult[tuple[BrokerBalance, ...]]: ...

    async def list_assets(
        self, cursor: str | None = None, limit: int | None = None
    ) -> BrokerResult[BrokerPage[BrokerAssetInfo]]: ...

    async def get_asset_info(self, asset: str) -> BrokerResult[BrokerAssetInfo]: ...

    async def get_positions(
        self,
        filter: BrokerPositionFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerPosition]]: ...

    async def get_position(self, position_id: str) -> BrokerResult[BrokerPosition]: ...

    async def get_orders(
        self,
        filter: BrokerOrderFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerOrder]]: ...

    async def get_order(self, order_id: str) -> BrokerResult[BrokerOrder]: ...

    async def list_order_history(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        symbol: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerOrder]]: ...

    async def list_deal_history(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        symbol: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerDeal]]: ...

    async def get_deal(self, deal_id: str) -> BrokerResult[BrokerDeal]: ...

    async def list_account_transactions(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerAccountTransaction]]: ...


@runtime_checkable
class TradeExecutionProvider(Protocol):
    """Single-target provider mutation primitives."""

    async def check_order(
        self, request: BrokerOrderRequest
    ) -> BrokerResult[BrokerOrderCheck]: ...

    async def place_order(
        self, request: BrokerOrderRequest
    ) -> BrokerResult[BrokerOrderResult]: ...

    async def modify_order(
        self, request: BrokerOrderModificationRequest
    ) -> BrokerResult[BrokerOrderResult]: ...

    async def cancel_order(
        self, order_id: str, client_request_id: str | None = None
    ) -> BrokerResult[BrokerOrderResult]: ...

    async def modify_position(
        self, request: BrokerPositionModificationRequest
    ) -> BrokerResult[BrokerPosition]: ...

    async def close_position(
        self, request: BrokerPositionCloseRequest
    ) -> BrokerResult[BrokerOrderResult]: ...

    async def replace_order(
        self, request: BrokerOrderModificationRequest
    ) -> BrokerResult[BrokerOrderResult]: ...


@runtime_checkable
class CalculationProvider(Protocol):
    """Provider-native calculation surface."""

    async def calculate_margin(
        self, request: BrokerMarginRequest
    ) -> BrokerResult[Decimal]: ...

    async def calculate_profit(
        self, request: BrokerProfitRequest
    ) -> BrokerResult[Decimal]: ...

    async def get_commission_estimate(
        self, request: BrokerOrderRequest
    ) -> BrokerResult[BrokerFeeEstimate]: ...


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
    def contract_version(self) -> Literal["v1"]: ...

    @property
    def schema_id(self) -> Literal["brokers.adapter.v1"]: ...

    async def __aenter__(self) -> BrokerAdapter: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def connect(self) -> BrokerResult[None]: ...

    async def disconnect(self) -> BrokerResult[None]: ...

    async def reconnect(self) -> BrokerResult[None]: ...

    async def is_connected(self) -> BrokerResult[bool]: ...

    async def get_connection_status(
        self,
    ) -> BrokerResult[BrokerConnectionStatus]: ...

    async def ping(self) -> BrokerResult[None]: ...

    async def refresh_session(self) -> BrokerResult[None]: ...

    async def get_server_time(self) -> BrokerResult[BrokerServerTime]: ...

    async def get_last_error(self) -> BrokerResult[BrokerError | None]: ...

    def connection_events(self) -> AsyncIterator[BrokerConnectionEvent]: ...


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

    def __init__(
        self,
        config: BrokerConnectionConfig,
        capabilities: Mapping[BrokerCapabilityId, BrokerCapability],
    ) -> None:
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

    def __getattribute__(self, name: str) -> Any:
        """Enforce declared availability before provider implementation access."""
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
                        del args, kwargs
                        return self._unsupported(operation)

                    return _blocked
        return object.__getattribute__(self, name)

    async def __aenter__(self) -> _UnsupportedAdapterBase:
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
        result: BrokerResult[T] = BrokerResult(
            status="error" if error else "success",
            broker=self._config.broker_id,
            operation=operation,
            request_id=request_id or f"{operation.value}-{self._session_generation}",
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
        """Fail closed unless a provider verifies a real session."""
        return self._unsupported(BrokerCapabilityId.CONNECT)

    async def disconnect(self) -> BrokerResult[None]:
        """Idempotently close adapter-local state."""
        if self._state != BrokerConnectionState.DISCONNECTED:
            await self._transition(BrokerConnectionState.CLOSING)
            await self._transition(BrokerConnectionState.DISCONNECTED)
        return self._result(BrokerCapabilityId.DISCONNECT)

    async def reconnect(self) -> BrokerResult[None]:
        """Reconnect the same session without replaying an operation."""
        await self.disconnect()
        return await self.connect()

    async def is_connected(self) -> BrokerResult[bool]:
        """Return locally tracked verified-session state."""
        return self._result(
            BrokerCapabilityId.IS_CONNECTED,
            data=self._state == BrokerConnectionState.READY,
        )

    async def get_connection_status(self) -> BrokerResult[BrokerConnectionStatus]:
        """Return detailed fail-closed session state."""
        ready = self._state == BrokerConnectionState.READY
        return self._result(
            BrokerCapabilityId.GET_CONNECTION_STATUS,
            data=BrokerConnectionStatus(
                state=self._state,
                transport_connected=ready,
                environment=self._config.environment,
                session_generation=self._session_generation,
                observed_at=_utc_now(),
                application_authenticated=ready,
                account_authenticated=ready
                if self._config.account_reference is not None
                else None,
                trading_permitted=None,
                subscriptions_ready=ready,
            ),
        )

    async def get_last_error(self) -> BrokerResult[BrokerError | None]:
        """Return the latest redacted non-authoritative error."""
        return self._result(BrokerCapabilityId.GET_LAST_ERROR, data=self._last_error)

    def connection_events(self) -> AsyncIterator[BrokerConnectionEvent]:
        """Yield bounded lifecycle events for this adapter instance."""

        async def _events() -> AsyncIterator[BrokerConnectionEvent]:
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
        """Answer from the static declaration without probing a provider."""
        declared = self._capabilities[capability]
        return self._result(
            BrokerCapabilityId.SUPPORTS,
            data=declared.availability in {"AVAILABLE", "DEGRADED"},
        )

    def _unsupported[T](self, operation: BrokerCapabilityId) -> BrokerResult[T]:
        result: BrokerResult[T] = _unsupported_result(
            broker=self._config.broker_id,
            environment=self._config.environment,
            operation=operation,
            request_id=f"{operation.value}-{self._session_generation}",
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

    def __getattr__(self, name: str) -> Any:
        """Return defaults only for canonical unsupported operations."""
        try:
            operation = BrokerCapabilityId(name)
        except ValueError as error:
            raise AttributeError(name) from error

        async def _operation(*args: object, **kwargs: object) -> BrokerResult[Any]:
            del args, kwargs
            return self._unsupported(operation)

        return _operation


def _make_unsupported_method(operation: BrokerCapabilityId) -> Any:
    """Create one structurally visible unsupported protocol method."""

    async def _method(
        self: _UnsupportedAdapterBase,
        *args: object,
        **kwargs: object,
    ) -> BrokerResult[Any]:
        del args, kwargs
        return self._unsupported(operation)

    _method.__name__ = operation.value
    return _method


for _operation_id in BrokerCapabilityId:
    if not hasattr(_UnsupportedAdapterBase, _operation_id.value):
        setattr(
            _UnsupportedAdapterBase,
            _operation_id.value,
            _make_unsupported_method(_operation_id),
        )
