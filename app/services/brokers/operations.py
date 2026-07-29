"""Standalone public adapter operations and DTO builders for the Brokers domain."""

# ruff: noqa: TC001
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.services.brokers.contracts.enums import (
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerId,
)
from app.services.brokers.contracts.models import (
    BrokerAccountInfo,
    BrokerAccountTransaction,
    BrokerBalance,
    BrokerBar,
    BrokerConnectionConfig,
    BrokerConnectionStatus,
    BrokerDeal,
    BrokerError,
    BrokerFeatureFlags,
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
    BrokerSubscriptionInfo,
    BrokerSymbolInfo,
    BrokerTick,
    BrokerTradingSession,
)
from app.services.brokers.contracts.protocols import (
    BrokerAdapter,
    BrokerSubscription,
)
from app.utils.responses.models import StandardResponse

# --- DTO Builder Functions ---


def build_broker_connection_config(
    broker_id: BrokerId | str,
    environment: BrokerEnvironment | str,
    account_reference: str | None = None,
    credentials: Mapping[str, Any] | None = None,
    provider_enabled: bool = True,
    probe_symbol: str | None = None,
    connect_timeout_sec: float = 5.0,
    request_timeout_sec: float = 10.0,
    transport_reconnect_max_attempts: int = 3,
    stream_buffer_size: int = 1000,
    circuit_failure_threshold: int = 5,
    circuit_recovery_timeout_sec: float = 30.0,
    circuit_half_open_max_calls: int = 3,
    auto_connect: bool = False,
) -> BrokerConnectionConfig:
    """Build a BrokerConnectionConfig immutable instance.

    Args:
        broker_id: Broker or profile identifier.
        environment: Broker environment (e.g. demo, live).
        account_reference: Optional account reference.
        credentials: Optional resolved credentials mapping.
        provider_enabled: Whether the provider is enabled.
        probe_symbol: Optional verification probe symbol.
        connect_timeout_sec: Connect timeout in seconds.
        request_timeout_sec: Operation request timeout in seconds.
        transport_reconnect_max_attempts: Maximum reconnect attempts.
        stream_buffer_size: Maximum event queue size for streams.
        circuit_failure_threshold: Circuit breaker failure threshold.
        circuit_recovery_timeout_sec: Circuit recovery delay in seconds.
        circuit_half_open_max_calls: Circuit half-open max calls.
        auto_connect: Whether to auto-connect on operation.

    Returns:
        Configured BrokerConnectionConfig instance.
    """
    bid = BrokerId(broker_id) if isinstance(broker_id, str) else broker_id
    env = (
        BrokerEnvironment(environment) if isinstance(environment, str) else environment
    )
    return BrokerConnectionConfig(
        broker_id=bid,
        environment=env,
        account_reference=account_reference,
        credentials=credentials,
        provider_enabled=provider_enabled,
        probe_symbol=probe_symbol,
        connect_timeout_sec=connect_timeout_sec,
        request_timeout_sec=request_timeout_sec,
        transport_reconnect_max_attempts=transport_reconnect_max_attempts,
        stream_buffer_size=stream_buffer_size,
        circuit_failure_threshold=circuit_failure_threshold,
        circuit_recovery_timeout_sec=circuit_recovery_timeout_sec,
        circuit_half_open_max_calls=circuit_half_open_max_calls,
        auto_connect=auto_connect,
    )


def build_broker_order_request(
    broker_id: BrokerId | str,
    account_reference: str | None,
    symbol: str,
    order_type: str,
    side: str,
    quantity: Decimal | float | str,
    price: Decimal | float | str | None = None,
    stop_loss: Decimal | float | str | None = None,
    take_profit: Decimal | float | str | None = None,
    time_in_force: str = "gtc",
    client_order_id: str | None = None,
) -> BrokerOrderRequest:
    """Build a BrokerOrderRequest instance.

    Args:
        broker_id: Broker identifier.
        account_reference: Account reference string.
        symbol: Instrument symbol.
        order_type: Order type (market, limit, stop).
        side: Order side (buy, sell).
        quantity: Order quantity.
        price: Optional limit price.
        stop_loss: Optional stop loss price.
        take_profit: Optional take profit price.
        time_in_force: Time in force policy.
        client_order_id: Optional client-side order identifier.

    Returns:
        Configured BrokerOrderRequest instance.
    """
    bid = BrokerId(broker_id) if isinstance(broker_id, str) else broker_id
    return BrokerOrderRequest(
        broker_id=bid,
        account_reference=account_reference,
        symbol=symbol,
        order_type=order_type,
        side=side,
        quantity=Decimal(str(quantity)),
        price=Decimal(str(price)) if price is not None else None,
        stop_loss=Decimal(str(stop_loss)) if stop_loss is not None else None,
        take_profit=Decimal(str(take_profit)) if take_profit is not None else None,
        time_in_force=time_in_force,
        client_order_id=client_order_id,
    )


def build_broker_order_modification_request(
    broker_id: BrokerId | str,
    order_id: str,
    symbol: str,
    price: Decimal | float | str | None = None,
    stop_loss: Decimal | float | str | None = None,
    take_profit: Decimal | float | str | None = None,
    quantity: Decimal | float | str | None = None,
) -> BrokerOrderModificationRequest:
    """Build a BrokerOrderModificationRequest instance.

    Args:
        broker_id: Broker identifier.
        order_id: Order identifier.
        symbol: Instrument symbol.
        price: Optional new price.
        stop_loss: Optional new stop loss.
        take_profit: Optional new take profit.
        quantity: Optional new quantity.

    Returns:
        Configured BrokerOrderModificationRequest instance.
    """
    bid = BrokerId(broker_id) if isinstance(broker_id, str) else broker_id
    return BrokerOrderModificationRequest(
        broker_id=bid,
        order_id=order_id,
        symbol=symbol,
        price=Decimal(str(price)) if price is not None else None,
        stop_loss=Decimal(str(stop_loss)) if stop_loss is not None else None,
        take_profit=Decimal(str(take_profit)) if take_profit is not None else None,
        quantity=Decimal(str(quantity)) if quantity is not None else None,
    )


def build_broker_position_close_request(
    broker_id: BrokerId | str,
    position_id: str,
    symbol: str,
    quantity: Decimal | float | str | None = None,
) -> BrokerPositionCloseRequest:
    """Build a BrokerPositionCloseRequest instance.

    Args:
        broker_id: Broker identifier.
        position_id: Position identifier.
        symbol: Instrument symbol.
        quantity: Optional partial close quantity.

    Returns:
        Configured BrokerPositionCloseRequest instance.
    """
    bid = BrokerId(broker_id) if isinstance(broker_id, str) else broker_id
    return BrokerPositionCloseRequest(
        broker_id=bid,
        position_id=position_id,
        symbol=symbol,
        quantity=Decimal(str(quantity)) if quantity is not None else None,
    )


def build_broker_position_modification_request(
    broker_id: BrokerId | str,
    position_id: str,
    symbol: str,
    stop_loss: Decimal | float | str | None = None,
    take_profit: Decimal | float | str | None = None,
) -> BrokerPositionModificationRequest:
    """Build a BrokerPositionModificationRequest instance.

    Args:
        broker_id: Broker identifier.
        position_id: Position identifier.
        symbol: Instrument symbol.
        stop_loss: Optional stop loss price.
        take_profit: Optional take profit price.

    Returns:
        Configured BrokerPositionModificationRequest instance.
    """
    bid = BrokerId(broker_id) if isinstance(broker_id, str) else broker_id
    return BrokerPositionModificationRequest(
        broker_id=bid,
        position_id=position_id,
        symbol=symbol,
        stop_loss=Decimal(str(stop_loss)) if stop_loss is not None else None,
        take_profit=Decimal(str(take_profit)) if take_profit is not None else None,
    )


def build_broker_margin_request(
    broker_id: BrokerId | str,
    symbol: str,
    side: str,
    quantity: Decimal | float | str,
    price: Decimal | float | str | None = None,
) -> BrokerMarginRequest:
    """Build a BrokerMarginRequest instance.

    Args:
        broker_id: Broker identifier.
        symbol: Instrument symbol.
        side: Trade side.
        quantity: Order quantity.
        price: Optional reference price.

    Returns:
        Configured BrokerMarginRequest instance.
    """
    bid = BrokerId(broker_id) if isinstance(broker_id, str) else broker_id
    return BrokerMarginRequest(
        broker_id=bid,
        symbol=symbol,
        side=side,
        quantity=Decimal(str(quantity)),
        price=Decimal(str(price)) if price is not None else None,
    )


def build_broker_profit_request(
    broker_id: BrokerId | str,
    symbol: str,
    side: str,
    quantity: Decimal | float | str,
    open_price: Decimal | float | str,
    close_price: Decimal | float | str,
) -> BrokerProfitRequest:
    """Build a BrokerProfitRequest instance.

    Args:
        broker_id: Broker identifier.
        symbol: Instrument symbol.
        side: Position side.
        quantity: Quantity.
        open_price: Opening price.
        close_price: Closing price.

    Returns:
        Configured BrokerProfitRequest instance.
    """
    bid = BrokerId(broker_id) if isinstance(broker_id, str) else broker_id
    return BrokerProfitRequest(
        broker_id=bid,
        symbol=symbol,
        side=side,
        quantity=Decimal(str(quantity)),
        open_price=Decimal(str(open_price)),
        close_price=Decimal(str(close_price)),
    )


def build_broker_order_filter(
    symbol: str | None = None,
    status: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> BrokerOrderFilter:
    """Build a BrokerOrderFilter instance.

    Args:
        symbol: Optional symbol filter.
        status: Optional status filter.
        start_time: Optional start timestamp.
        end_time: Optional end timestamp.

    Returns:
        Configured BrokerOrderFilter instance.
    """
    return BrokerOrderFilter(
        symbol=symbol,
        status=status,
        start_time=start_time,
        end_time=end_time,
    )


def build_broker_position_filter(
    symbol: str | None = None,
) -> BrokerPositionFilter:
    """Build a BrokerPositionFilter instance.

    Args:
        symbol: Optional symbol filter.

    Returns:
        Configured BrokerPositionFilter instance.
    """
    return BrokerPositionFilter(symbol=symbol)


# --- Standalone Adapter Operation Delegate Functions ---


async def connect_broker(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerConnectionStatus]:
    """Connect the broker adapter session.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing connection status.
    """
    return await adapter.connect()


async def disconnect_broker(
    adapter: BrokerAdapter,
) -> StandardResponse[None]:
    """Disconnect the broker adapter session.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response confirming disconnection.
    """
    return await adapter.disconnect()


async def reconnect_broker(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerConnectionStatus]:
    """Reconnect the broker adapter session.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing connection status.
    """
    return await adapter.reconnect()


def is_broker_connected(adapter: BrokerAdapter) -> bool:
    """Check if the broker adapter session is currently connected.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        True if connected, False otherwise.
    """
    return adapter.is_connected()


def get_broker_connection_status(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerConnectionStatus]:
    """Get connection status of the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response with detailed connection status.
    """
    return adapter.get_connection_status()


async def ping_broker(adapter: BrokerAdapter) -> StandardResponse[None]:
    """Ping the broker provider transport.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response confirming ping success.
    """
    return await adapter.ping()


def get_broker_last_error(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerError | None]:
    """Get last error reported by the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing last BrokerError or None.
    """
    return adapter.get_last_error()


def get_broker_feature_flags(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerFeatureFlags]:
    """Get runtime feature flags for the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing feature flags.
    """
    return adapter.get_feature_flags()


def supports_broker_capability(
    adapter: BrokerAdapter,
    capability_id: BrokerCapabilityId,
) -> bool:
    """Check if the broker adapter supports a given capability.

    Args:
        adapter: Targeted broker adapter.
        capability_id: Capability identifier to check.

    Returns:
        True if supported and available, False otherwise.
    """
    return adapter.supports(capability_id)


async def get_broker_platform_info(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerPlatformInfo]:
    """Get platform info from the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing platform info.
    """
    return await adapter.get_platform_info()


async def get_broker_balances(
    adapter: BrokerAdapter,
) -> StandardResponse[tuple[BrokerBalance, ...]]:
    """Get account balances from the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing tuple of balances.
    """
    return await adapter.get_balances()


async def get_broker_permissions(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerPermissions]:
    """Get account permissions from the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing permissions.
    """
    return await adapter.get_permissions()


async def get_broker_account_info(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerAccountInfo]:
    """Get account details from the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing account info.
    """
    return await adapter.get_account_info()


async def get_broker_symbols(
    adapter: BrokerAdapter,
    query: str | None = None,
    cursor: str | None = None,
    limit: int | None = None,
) -> StandardResponse[BrokerPage[BrokerSymbolInfo]]:
    """Get page of symbols from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        query: Optional symbol query.
        cursor: Optional pagination cursor.
        limit: Optional page limit.

    Returns:
        Standard response containing page of symbol info.
    """
    return await adapter.get_symbols(query=query, cursor=cursor, limit=limit)


async def get_broker_symbol_info(
    adapter: BrokerAdapter,
    symbol: str,
) -> StandardResponse[BrokerSymbolInfo]:
    """Get symbol info from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing symbol info.
    """
    return await adapter.get_symbol_info(symbol)


async def select_broker_symbol(
    adapter: BrokerAdapter,
    symbol: str,
    enabled: bool = True,
) -> StandardResponse[None]:
    """Select or subscribe symbol on the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        enabled: Enable or disable selection.

    Returns:
        Standard response confirming selection outcome.
    """
    return await adapter.select_symbol(symbol, enabled=enabled)


async def get_broker_market_status(
    adapter: BrokerAdapter,
    symbol: str,
) -> StandardResponse[BrokerMarketStatus]:
    """Get market status for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing market status.
    """
    return await adapter.get_market_status(symbol)


async def get_broker_trading_sessions(
    adapter: BrokerAdapter,
    symbol: str,
) -> StandardResponse[tuple[BrokerTradingSession, ...]]:
    """Get trading sessions for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing trading sessions tuple.
    """
    return await adapter.get_trading_sessions(symbol)


async def get_broker_quote(
    adapter: BrokerAdapter,
    symbol: str,
) -> StandardResponse[BrokerQuote]:
    """Get current quote for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing latest quote.
    """
    return await adapter.get_quote(symbol)


async def get_broker_spread(
    adapter: BrokerAdapter,
    symbol: str,
) -> StandardResponse[Decimal]:
    """Get current spread for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing spread value.
    """
    return await adapter.get_spread(symbol)


async def get_broker_ticks(
    adapter: BrokerAdapter,
    symbol: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int | None = None,
) -> StandardResponse[tuple[BrokerTick, ...]]:
    """Get historical ticks for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        start_time: Optional start timestamp.
        end_time: Optional end timestamp.
        limit: Optional record count limit.

    Returns:
        Standard response containing ticks tuple.
    """
    return await adapter.get_ticks(
        symbol, start_time=start_time, end_time=end_time, limit=limit
    )


async def get_broker_historical_bars(
    adapter: BrokerAdapter,
    symbol: str,
    timeframe: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int | None = None,
) -> StandardResponse[tuple[BrokerBar, ...]]:
    """Get historical bars for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        timeframe: Bar timeframe.
        start_time: Optional start timestamp.
        end_time: Optional end timestamp.
        limit: Optional bar count limit.

    Returns:
        Standard response containing bars tuple.
    """
    return await adapter.get_historical_bars(
        symbol,
        timeframe,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


async def get_broker_order_book(
    adapter: BrokerAdapter,
    symbol: str,
    depth: int | None = None,
) -> StandardResponse[BrokerOrderBook]:
    """Get order book for a symbol from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        depth: Optional order book depth limit.

    Returns:
        Standard response containing order book.
    """
    return await adapter.get_order_book(symbol, depth=depth)


async def subscribe_broker_quotes(
    adapter: BrokerAdapter,
    symbol: str,
) -> StandardResponse[BrokerSubscription[BrokerQuote]]:
    """Subscribe to quote updates for a symbol.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing subscription handle.
    """
    return await adapter.subscribe_quotes(symbol)


async def subscribe_broker_bars(
    adapter: BrokerAdapter,
    symbol: str,
    timeframe: str,
) -> StandardResponse[BrokerSubscription[BrokerBar]]:
    """Subscribe to bar updates for a symbol.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        timeframe: Bar timeframe string.

    Returns:
        Standard response containing subscription handle.
    """
    return await adapter.subscribe_bars(symbol, timeframe)


async def subscribe_broker_order_book(
    adapter: BrokerAdapter,
    symbol: str,
    depth: int | None = None,
) -> StandardResponse[BrokerSubscription[BrokerOrderBook]]:
    """Subscribe to order book updates for a symbol.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        depth: Optional order book depth limit.

    Returns:
        Standard response containing subscription handle.
    """
    return await adapter.subscribe_order_book(symbol, depth=depth)


async def unsubscribe_broker(
    subscription: BrokerSubscription[Any],
) -> StandardResponse[None]:
    """Unsubscribe an active subscription handle.

    Args:
        subscription: Active broker subscription handle.

    Returns:
        Standard response confirming unsubscribe outcome.
    """
    return await subscription.unsubscribe()


async def list_broker_subscriptions(
    adapter: BrokerAdapter,
) -> StandardResponse[tuple[BrokerSubscriptionInfo, ...]]:
    """List active subscriptions on the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing tuple of subscription info.
    """
    return await adapter.list_subscriptions()


async def get_broker_positions(
    adapter: BrokerAdapter,
    filter_spec: BrokerPositionFilter | None = None,
) -> StandardResponse[tuple[BrokerPosition, ...]]:
    """Get active positions from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        filter_spec: Optional position filter.

    Returns:
        Standard response containing positions tuple.
    """
    return await adapter.get_positions(filter=filter_spec)


async def get_broker_position(
    adapter: BrokerAdapter,
    position_id: str,
) -> StandardResponse[BrokerPosition]:
    """Get position details by position ID.

    Args:
        adapter: Targeted broker adapter.
        position_id: Position identifier.

    Returns:
        Standard response containing position details.
    """
    return await adapter.get_position(position_id)


async def get_broker_orders(
    adapter: BrokerAdapter,
    filter_spec: BrokerOrderFilter | None = None,
) -> StandardResponse[tuple[BrokerOrder, ...]]:
    """Get active orders from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        filter_spec: Optional order filter.

    Returns:
        Standard response containing orders tuple.
    """
    return await adapter.get_orders(filter=filter_spec)


async def get_broker_order(
    adapter: BrokerAdapter,
    order_id: str,
) -> StandardResponse[BrokerOrder]:
    """Get order details by order ID.

    Args:
        adapter: Targeted broker adapter.
        order_id: Order identifier.

    Returns:
        Standard response containing order details.
    """
    return await adapter.get_order(order_id)


async def list_broker_order_history(
    adapter: BrokerAdapter,
    filter_spec: BrokerOrderFilter | None = None,
    cursor: str | None = None,
    limit: int | None = None,
) -> StandardResponse[BrokerPage[BrokerOrder]]:
    """List historical orders from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        filter_spec: Optional order filter.
        cursor: Optional pagination cursor.
        limit: Optional page limit.

    Returns:
        Standard response containing page of orders.
    """
    return await adapter.list_order_history(
        filter=filter_spec, cursor=cursor, limit=limit
    )


async def list_broker_deal_history(
    adapter: BrokerAdapter,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    cursor: str | None = None,
    limit: int | None = None,
) -> StandardResponse[BrokerPage[BrokerDeal]]:
    """List historical deals/fills from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        start_time: Optional start timestamp.
        end_time: Optional end timestamp.
        cursor: Optional pagination cursor.
        limit: Optional page limit.

    Returns:
        Standard response containing page of deals.
    """
    return await adapter.list_deal_history(
        start_time=start_time, end_time=end_time, cursor=cursor, limit=limit
    )


async def get_broker_deal(
    adapter: BrokerAdapter,
    deal_id: str,
) -> StandardResponse[BrokerDeal]:
    """Get deal/fill details by deal ID.

    Args:
        adapter: Targeted broker adapter.
        deal_id: Deal identifier.

    Returns:
        Standard response containing deal details.
    """
    return await adapter.get_deal(deal_id)


async def list_broker_account_transactions(
    adapter: BrokerAdapter,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    cursor: str | None = None,
    limit: int | None = None,
) -> StandardResponse[BrokerPage[BrokerAccountTransaction]]:
    """List account transactions (deposits, withdrawals, fees).

    Args:
        adapter: Targeted broker adapter.
        start_time: Optional start timestamp.
        end_time: Optional end timestamp.
        cursor: Optional pagination cursor.
        limit: Optional page limit.

    Returns:
        Standard response containing page of transactions.
    """
    return await adapter.list_account_transactions(
        start_time=start_time, end_time=end_time, cursor=cursor, limit=limit
    )


async def check_broker_order(
    adapter: BrokerAdapter,
    request: BrokerOrderRequest,
) -> StandardResponse[BrokerOrderCheck]:
    """Pre-validate order request on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        request: Order request.

    Returns:
        Standard response containing check result.
    """
    return await adapter.check_order(request)


async def place_broker_order(
    adapter: BrokerAdapter,
    request: BrokerOrderRequest,
) -> StandardResponse[BrokerOrderResult]:
    """Place new order on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        request: Order request.

    Returns:
        Standard response containing order execution result.
    """
    return await adapter.place_order(request)


async def modify_broker_order(
    adapter: BrokerAdapter,
    request: BrokerOrderModificationRequest,
) -> StandardResponse[BrokerOrderResult]:
    """Modify open order on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        request: Order modification request.

    Returns:
        Standard response containing modification result.
    """
    return await adapter.modify_order(request)


async def cancel_broker_order(
    adapter: BrokerAdapter,
    order_id: str,
    symbol: str | None = None,
) -> StandardResponse[BrokerOrderResult]:
    """Cancel open order on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        order_id: Target order ID.
        symbol: Optional instrument symbol.

    Returns:
        Standard response containing cancellation result.
    """
    return await adapter.cancel_order(order_id, symbol=symbol)


async def modify_broker_position(
    adapter: BrokerAdapter,
    request: BrokerPositionModificationRequest,
) -> StandardResponse[BrokerOrderResult]:
    """Modify position stop loss / take profit on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        request: Position modification request.

    Returns:
        Standard response containing modification result.
    """
    return await adapter.modify_position(request)


async def close_broker_position(
    adapter: BrokerAdapter,
    request: BrokerPositionCloseRequest,
) -> StandardResponse[BrokerOrderResult]:
    """Close position on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        request: Position close request.

    Returns:
        Standard response containing close result.
    """
    return await adapter.close_position(request)


async def calculate_broker_margin(
    adapter: BrokerAdapter,
    request: BrokerMarginRequest,
) -> StandardResponse[Decimal]:
    """Calculate required margin for potential trade.

    Args:
        adapter: Targeted broker adapter.
        request: Margin calculation request.

    Returns:
        Standard response containing required margin amount.
    """
    return await adapter.calculate_margin(request)


async def calculate_broker_profit(
    adapter: BrokerAdapter,
    request: BrokerProfitRequest,
) -> StandardResponse[Decimal]:
    """Calculate projected profit/loss for trade parameters.

    Args:
        adapter: Targeted broker adapter.
        request: Profit calculation request.

    Returns:
        Standard response containing calculated profit amount.
    """
    return await adapter.calculate_profit(request)
