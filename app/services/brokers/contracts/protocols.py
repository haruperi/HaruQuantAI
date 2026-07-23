"""Focused asynchronous broker capability protocols."""

from __future__ import annotations

# ruff: noqa: A002, ANN401, TC001 - normative boundary.
import inspect
from collections.abc import AsyncIterator
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Protocol, runtime_checkable

from app.services.brokers.adapter_runtime.base import (
    _UnsupportedAdapterBase as _UnsupportedAdapterBase,  # noqa: PLC0414
)
from app.services.brokers.adapter_runtime.errors import (
    _CircuitOpenError as _CircuitOpenError,  # noqa: PLC0414
)
from app.services.brokers.adapter_runtime.errors import (
    _ProviderResponseError as _ProviderResponseError,  # noqa: PLC0414
)
from app.services.brokers.adapter_runtime.errors import (
    _RateLimitedError as _RateLimitedError,  # noqa: PLC0414
)
from app.services.brokers.adapter_runtime.errors import (
    _RequestValidationError as _RequestValidationError,  # noqa: PLC0414
)
from app.services.brokers.contracts.enums import (
    BrokerCapabilityId,
)
from app.services.brokers.contracts.models import (
    BrokerAccountInfo,
    BrokerAccountTransaction,
    BrokerAssetInfo,
    BrokerBalance,
    BrokerBar,
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
