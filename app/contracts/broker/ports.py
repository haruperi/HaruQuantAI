"""Typing protocols for Broker Port boundaries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from app.contracts.broker.errors import BrokerFailure
    from app.contracts.broker.models import (
        BrokerAccountInfo,
        BrokerAccountSnapshot,
        BrokerBalance,
        BrokerBar,
        BrokerCalculationResult,
        BrokerDeal,
        BrokerMarginCalculationRequest,
        BrokerOrder,
        BrokerOrderCheck,
        BrokerOrderModificationRequest,
        BrokerOrderRequest,
        BrokerOrderResult,
        BrokerPlatformInfo,
        BrokerPosition,
        BrokerPositionModificationRequest,
        BrokerProfitCalculationRequest,
        BrokerQuote,
        BrokerSubscription,
        BrokerSubscriptionInfo,
        BrokerSymbolInfo,
        BrokerTerminalInfo,
        BrokerTick,
        BrokerTransaction,
        ManageSessionsRequest,
        ManageSessionsSuccess,
        ReadProviderStateRequest,
        ReadProviderStateSuccess,
        StandardResponse,
        TransportOrdersRequest,
        TransportOrdersSuccess,
    )


# FR 1: Terminal Environment Access (CTerminalInfo equivalent)
@runtime_checkable
class TerminalInfoPort(Protocol):
    """Port for accessing broker environment and terminal properties."""

    async def connect(self) -> StandardResponse[bool]:
        """Establish provider connection."""
        ...

    async def disconnect(self) -> StandardResponse[bool]:
        """Release provider connection."""
        ...

    async def ping(self) -> StandardResponse[float]:
        """Measure round-trip latency to the provider."""
        ...

    def is_connected(self) -> StandardResponse[bool]:
        """Return provider connection state."""
        ...

    def get_connection_status(self) -> StandardResponse[dict[str, Any]]:
        """Return full connection status dictionary."""
        ...

    async def get_platform_info(self) -> StandardResponse[BrokerPlatformInfo]:
        """Return platform environment details."""
        ...

    async def get_terminal_info(self) -> StandardResponse[BrokerTerminalInfo]:
        """Return full terminal properties."""
        ...


# FR 2: Account Properties & State (CAccountInfo equivalent)
@runtime_checkable
class AccountInfoPort(Protocol):
    """Port for accessing current account properties and balances."""

    async def get_account_info(self) -> StandardResponse[BrokerAccountInfo]:
        """Return current account properties."""
        ...

    async def get_balances(self) -> StandardResponse[tuple[BrokerBalance, ...]]:
        """Return asset and currency balances."""
        ...

    async def get_account_snapshot(self) -> StandardResponse[BrokerAccountSnapshot]:
        """Return standard account snapshot."""
        ...


# FR 3: Symbol Properties & Market Data (CSymbolInfo equivalent)
@runtime_checkable
class SymbolInfoPort(Protocol):
    """Port for querying symbol specifications, market data, and streaming."""

    async def get_symbols(self) -> StandardResponse[tuple[str, ...]]:
        """Return discoverable symbol names."""
        ...

    async def get_symbol_info(self, symbol: str) -> StandardResponse[BrokerSymbolInfo]:
        """Return symbol specification."""
        ...

    async def get_quote(self, symbol: str) -> StandardResponse[BrokerQuote]:
        """Return current bid/ask quote."""
        ...

    async def get_spread(self, symbol: str) -> StandardResponse[float]:
        """Return current spread in points/pips."""
        ...

    async def get_ticks(
        self, symbol: str, count: int = 100
    ) -> StandardResponse[tuple[BrokerTick, ...]]:
        """Return historical ticks."""
        ...

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
        count: int | None = None,
    ) -> StandardResponse[tuple[BrokerBar, ...]]:
        """Return historical OHLCV bars."""
        ...

    async def subscribe_quotes(
        self, symbols: Sequence[str]
    ) -> StandardResponse[BrokerSubscription[BrokerQuote]]:
        """Open real-time quote subscription."""
        ...

    async def subscribe_ticks(
        self, symbols: Sequence[str]
    ) -> StandardResponse[BrokerSubscription[BrokerTick]]:
        """Open real-time tick stream."""
        ...

    async def subscribe_bars(
        self, symbols: Sequence[str], timeframe: str
    ) -> StandardResponse[BrokerSubscription[BrokerBar]]:
        """Open real-time bar stream."""
        ...

    async def unsubscribe(self, subscription_id: str) -> StandardResponse[bool]:
        """Unsubscribe from an active stream."""
        ...

    def list_subscriptions(
        self,
    ) -> StandardResponse[tuple[BrokerSubscriptionInfo, ...]]:
        """List active subscription handles."""
        ...


# FR 4: Pending Orders State (COrderInfo equivalent)
@runtime_checkable
class OrderInfoPort(Protocol):
    """Port for querying pending and working orders."""

    async def get_orders(
        self, symbol: str | None = None
    ) -> StandardResponse[tuple[BrokerOrder, ...]]:
        """Return active pending and working orders."""
        ...

    async def get_order(self, order_id: str) -> StandardResponse[BrokerOrder]:
        """Return single order by ID or ticket."""
        ...

    async def check_order(
        self, request: BrokerOrderRequest
    ) -> StandardResponse[BrokerOrderCheck]:
        """Pre-validate order without submission."""
        ...


# FR 5: Historical Orders State (CHistoryOrderInfo equivalent)
@runtime_checkable
class HistoryOrderInfoPort(Protocol):
    """Port for querying historical completed and cancelled orders."""

    async def list_order_history(
        self,
        symbol: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> StandardResponse[tuple[BrokerOrder, ...]]:
        """Return completed and cancelled order history."""
        ...

    async def get_history_order(self, order_id: str) -> StandardResponse[BrokerOrder]:
        """Return single historical order."""
        ...


# FR 6: Deal & Transaction State (CDealInfo equivalent)
@runtime_checkable
class DealsInfoPort(Protocol):
    """Port for querying executions, deals, and balance transactions."""

    async def get_deals(
        self, deal_id: str | None = None
    ) -> StandardResponse[tuple[BrokerDeal, ...]]:
        """Return deal records."""
        ...

    async def list_deal_history(
        self,
        symbol: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> StandardResponse[tuple[BrokerDeal, ...]]:
        """Return deal history."""
        ...

    async def list_account_transactions(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> StandardResponse[tuple[BrokerTransaction, ...]]:
        """Return balance/credit transactions."""
        ...


# FR 7: Open Positions State (CPositionInfo equivalent)
@runtime_checkable
class PositionsInfoPort(Protocol):
    """Port for querying open positions."""

    async def get_positions(
        self, symbol: str | None = None
    ) -> StandardResponse[tuple[BrokerPosition, ...]]:
        """Return open positions."""
        ...

    async def get_position(self, position_id: str) -> StandardResponse[BrokerPosition]:
        """Return single open position by ID or ticket."""
        ...


# FR 8: Trade & Mutation Functions (CTrade equivalent)
@runtime_checkable
class TradePort(Protocol):
    """Port for placing orders, modifying positions, and calculating margins."""

    async def place_order(
        self, request: BrokerOrderRequest
    ) -> StandardResponse[BrokerOrderResult]:
        """Submit a new order."""
        ...

    async def modify_order(
        self, request: BrokerOrderModificationRequest
    ) -> StandardResponse[BrokerOrderResult]:
        """Modify a pending order."""
        ...

    async def cancel_order(
        self, order_id: str, client_request_id: str | None = None
    ) -> StandardResponse[BrokerOrderResult]:
        """Cancel a pending order."""
        ...

    async def modify_position(
        self, request: BrokerPositionModificationRequest
    ) -> StandardResponse[BrokerPosition]:
        """Modify stop-loss/take-profit of an open position."""
        ...

    async def close_position(
        self, position_id: str, volume: float | None = None
    ) -> StandardResponse[BrokerOrderResult]:
        """Close an open position."""
        ...

    async def calculate_margin(
        self, request: BrokerMarginCalculationRequest
    ) -> StandardResponse[BrokerCalculationResult]:
        """Calculate required margin."""
        ...

    async def calculate_profit(
        self, request: BrokerProfitCalculationRequest
    ) -> StandardResponse[BrokerCalculationResult]:
        """Calculate expected profit."""
        ...


# Composite & Gateway Ports
@runtime_checkable
class ManageSessionsCapability(Protocol):
    """Capability protocol for provider session lifecycle operations."""

    async def manage_sessions(
        self,
        request: ManageSessionsRequest,
    ) -> ManageSessionsSuccess | BrokerFailure:
        """Open, transition, reconnect, assess, and close fenced sessions."""
        ...


@runtime_checkable
class ReadProviderStateCapability(Protocol):
    """Capability protocol for provider-truth read operations."""

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        """Read and normalize genuine provider account and market state."""
        ...


@runtime_checkable
class TransportOrdersCapability(Protocol):
    """Capability protocol for authorized execution transport operations."""

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Validate, submit, cancel, modify, and journal transport requests."""
        ...


@runtime_checkable
class ProviderBackend(Protocol):
    """Typed provider-backend port implemented by each provider feature."""

    async def manage_sessions(
        self,
        request: ManageSessionsRequest,
    ) -> ManageSessionsSuccess | BrokerFailure:
        """Handle one explicitly addressed provider session operation."""
        ...

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        """Read genuine provider truth for one explicitly addressed read."""
        ...

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Transport one upstream-authorized provider order operation."""
        ...


@runtime_checkable
class BrokerResolverCapability(Protocol):
    """Capability protocol for resolving active broker module."""

    def get_broker_module(self) -> dict[str, Any]:
        """Resolve and return active broker module configuration."""
        ...
