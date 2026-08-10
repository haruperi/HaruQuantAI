"""Shared adapter lifecycle and capability delegation operations."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.services.brokers.canonical_contracts.enums import BrokerCapabilityId
from app.services.brokers.canonical_contracts.models import (
    BrokerAccountInfo,
    BrokerAccountTransaction,
    BrokerAssetInfo,
    BrokerBalance,
    BrokerBar,
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
    BrokerOrderProtectionRequest,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerPage,
    BrokerPermissions,
    BrokerPlatformInfo,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionFilter,
    BrokerPositionModificationRequest,
    BrokerPositionReductionRequest,
    BrokerProfitRequest,
    BrokerQuote,
    BrokerServerTime,
    BrokerSubscriptionInfo,
    BrokerSymbolInfo,
    BrokerTick,
    BrokerTradingSession,
)

if TYPE_CHECKING:
    from app.services.brokers.canonical_contracts.protocols import (
        BrokerAdapter,
        BrokerSubscription,
    )
    from app.services.brokers.canonical_contracts.responses import StandardResponse


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


async def disconnect_broker(adapter: BrokerAdapter) -> StandardResponse[None]:
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


async def is_broker_connected(adapter: BrokerAdapter) -> StandardResponse[bool]:
    """Check if the broker adapter session is currently connected.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing the verified connectivity state.
    """
    return await adapter.is_connected()


async def get_broker_connection_status(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerConnectionStatus]:
    """Get connection status of the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response with detailed connection status.
    """
    return await adapter.get_connection_status()


async def ping_broker(adapter: BrokerAdapter) -> StandardResponse[None]:
    """Ping the broker provider transport.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response confirming ping success.
    """
    return await adapter.ping()


async def get_broker_last_error(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerError | None]:
    """Get last error reported by the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing last BrokerError or None.
    """
    return await adapter.get_last_error()


async def get_broker_feature_flags(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerFeatureFlags]:
    """Get runtime feature flags for the broker adapter.

    Args:
        adapter: Targeted broker adapter.

    Returns:
        Standard response containing feature flags.
    """
    return await adapter.get_feature_flags()


async def supports_broker_capability(
    adapter: BrokerAdapter, capability_id: BrokerCapabilityId | str
) -> StandardResponse[bool]:
    """Check if the broker adapter supports a given capability.

    Args:
        adapter: Targeted broker adapter.
        capability_id: Capability identifier to check.

    Returns:
        True if supported and available, False otherwise.
    """
    capability = (
        BrokerCapabilityId(capability_id)
        if isinstance(capability_id, str)
        else capability_id
    )
    return await adapter.supports(capability)


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
    adapter: BrokerAdapter, symbol: str
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
    adapter: BrokerAdapter, symbol: str, enabled: bool = True
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
    adapter: BrokerAdapter, symbol: str
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
    adapter: BrokerAdapter, symbol: str
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
    adapter: BrokerAdapter, symbol: str
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
    adapter: BrokerAdapter, symbol: str
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
) -> StandardResponse[BrokerPage[BrokerTick]]:
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
    return await adapter.get_ticks(symbol, start=start_time, end=end_time, limit=limit)


async def get_broker_historical_bars(
    adapter: BrokerAdapter,
    symbol: str,
    timeframe: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int | None = None,
) -> StandardResponse[BrokerPage[BrokerBar]]:
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
        symbol, timeframe, start=start_time, end=end_time, limit=limit
    )


async def get_broker_order_book(
    adapter: BrokerAdapter, symbol: str, depth: int | None = None
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
    adapter: BrokerAdapter, symbol: str | tuple[str, ...]
) -> StandardResponse[BrokerSubscription[BrokerQuote]]:
    """Subscribe to quote updates for a symbol.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.

    Returns:
        Standard response containing subscription handle.
    """
    symbols = (symbol,) if isinstance(symbol, str) else symbol
    return await adapter.subscribe_quotes(symbols)


async def subscribe_broker_bars(
    adapter: BrokerAdapter, symbol: str | tuple[str, ...], timeframe: str
) -> StandardResponse[BrokerSubscription[BrokerBar]]:
    """Subscribe to bar updates for a symbol.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        timeframe: Bar timeframe string.

    Returns:
        Standard response containing subscription handle.
    """
    symbols = (symbol,) if isinstance(symbol, str) else symbol
    return await adapter.subscribe_bars(symbols, timeframe)


async def subscribe_broker_order_book(
    adapter: BrokerAdapter, symbol: str | tuple[str, ...], depth: int | None = None
) -> StandardResponse[BrokerSubscription[BrokerOrderBook]]:
    """Subscribe to order book updates for a symbol.

    Args:
        adapter: Targeted broker adapter.
        symbol: Instrument symbol.
        depth: Optional order book depth limit.

    Returns:
        Standard response containing subscription handle.
    """
    symbols = (symbol,) if isinstance(symbol, str) else symbol
    return await adapter.subscribe_order_book(symbols, depth=depth)


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
    limit: int = 1000,
) -> StandardResponse[BrokerPage[BrokerPosition]]:
    """Get open positions from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        filter_spec: Optional position filter.
        limit: Maximum items to return.

    Returns:
        Standard response containing positions tuple.
    """
    return await adapter.get_positions(filter=filter_spec, limit=limit)


async def get_broker_position(
    adapter: BrokerAdapter, position_id: str
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
    limit: int = 1000,
) -> StandardResponse[BrokerPage[BrokerOrder]]:
    """Get active orders from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        filter_spec: Optional order filter.
        limit: Maximum items to return.

    Returns:
        Standard response containing orders tuple.
    """
    return await adapter.get_orders(filter=filter_spec, limit=limit)


async def get_broker_order(
    adapter: BrokerAdapter, order_id: str
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
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    symbol: str | None = None,
    cursor: str | None = None,
    limit: int | None = None,
) -> StandardResponse[BrokerPage[BrokerOrder]]:
    """List historical orders from the broker adapter.

    Args:
        adapter: Targeted broker adapter.
        start_time: Inclusive history start timestamp.
        end_time: Exclusive history end timestamp.
        symbol: Optional exact provider symbol.
        cursor: Optional pagination cursor.
        limit: Optional page limit.

    Returns:
        Standard response containing page of orders.
    """
    return await adapter.list_order_history(
        start=start_time, end=end_time, symbol=symbol, cursor=cursor, limit=limit
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
        start=start_time, end=end_time, cursor=cursor, limit=limit
    )


async def get_broker_deal(
    adapter: BrokerAdapter, deal_id: str
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
        start=start_time, end=end_time, cursor=cursor, limit=limit
    )


async def check_broker_order(
    adapter: BrokerAdapter, request: BrokerOrderRequest
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
    adapter: BrokerAdapter, request: BrokerOrderRequest
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
    adapter: BrokerAdapter, request: BrokerOrderModificationRequest
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
    adapter: BrokerAdapter, order_id: str, client_request_id: str | None = None
) -> StandardResponse[BrokerOrderResult]:
    """Cancel open order on broker adapter.

    Args:
        adapter: Targeted broker adapter.
        order_id: Target order ID.
        client_request_id: Optional caller idempotency identifier.

    Returns:
        Standard response containing cancellation result.
    """
    return await adapter.cancel_order(order_id, client_request_id=client_request_id)


async def modify_broker_position(
    adapter: BrokerAdapter, request: BrokerPositionModificationRequest
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
    adapter: BrokerAdapter, request: BrokerPositionCloseRequest
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
    adapter: BrokerAdapter, request: BrokerMarginRequest
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
    adapter: BrokerAdapter, request: BrokerProfitRequest
) -> StandardResponse[Decimal]:
    """Calculate projected profit/loss for trade parameters.

    Args:
        adapter: Targeted broker adapter.
        request: Profit calculation request.

    Returns:
        Standard response containing calculated profit amount.
    """
    return await adapter.calculate_profit(request)


async def refresh_broker_session(adapter: BrokerAdapter) -> StandardResponse[None]:
    """Refresh one Broker session through its opaque adapter.

    Args:
        adapter: Value supplied to the operation.

    Returns:
        The canonical refresh result.
    """
    return await adapter.refresh_session()


async def get_broker_server_time(
    adapter: BrokerAdapter,
) -> StandardResponse[BrokerServerTime]:
    """Get provider-reported server time through the root boundary.

    Args:
        adapter: Value supplied to the operation.

    Returns:
        The canonical server-time result.
    """
    return await adapter.get_server_time()


def get_broker_connection_events(adapter: BrokerAdapter) -> object:
    """Return the opaque asynchronous connection-event stream.

    Args:
        adapter: Value supplied to the operation.

    Returns:
        object: The operation result.
    """
    return adapter.connection_events()


async def list_broker_accounts(
    adapter: BrokerAdapter, cursor: str | None = None, limit: int | None = None
) -> StandardResponse[BrokerPage[BrokerAccountInfo]]:
    """List provider-visible accounts through the root boundary.

    Args:
        adapter: Value supplied to the operation.
        cursor: Value supplied to the operation.
        limit: Value supplied to the operation.

    Returns:
        The canonical bounded account page.
    """
    return await adapter.list_accounts(cursor=cursor, limit=limit)


async def select_broker_account(
    adapter: BrokerAdapter, account_id: str
) -> StandardResponse[None]:
    """Select one provider account through the root boundary.

    Args:
        adapter: Value supplied to the operation.
        account_id: Value supplied to the operation.

    Returns:
        The canonical selection result.
    """
    return await adapter.select_account(account_id)


async def list_broker_assets(
    adapter: BrokerAdapter, cursor: str | None = None, limit: int | None = None
) -> StandardResponse[BrokerPage[BrokerAssetInfo]]:
    """List provider-visible assets through the root boundary.

    Args:
        adapter: Value supplied to the operation.
        cursor: Value supplied to the operation.
        limit: Value supplied to the operation.

    Returns:
        The canonical bounded asset page.
    """
    return await adapter.list_assets(cursor=cursor, limit=limit)


async def get_broker_asset_info(
    adapter: BrokerAdapter, asset: str
) -> StandardResponse[BrokerAssetInfo]:
    """Get one provider asset through the root boundary.

    Args:
        adapter: Value supplied to the operation.
        asset: Value supplied to the operation.

    Returns:
        The canonical asset result.
    """
    return await adapter.get_asset_info(asset)


async def get_broker_commission_estimate(
    adapter: BrokerAdapter, request: BrokerOrderRequest
) -> StandardResponse[BrokerFeeEstimate]:
    """Get one provider commission estimate through the root boundary.

    Args:
        adapter: Value supplied to the operation.
        request: Value supplied to the operation.

    Returns:
        The canonical commission-estimate result.
    """
    return await adapter.get_commission_estimate(request)


async def replace_broker_order(
    adapter: BrokerAdapter, request: BrokerOrderModificationRequest
) -> StandardResponse[BrokerOrderResult]:
    """Replace one provider order through the root boundary.

    Args:
        adapter: Value supplied to the operation.
        request: Value supplied to the operation.

    Returns:
        The canonical replacement result.
    """
    return await adapter.replace_order(request)


def build_broker_order_protection_request(
    order_id: str,
    idempotency_key: str,
    stop_loss: Decimal | float | str | None = None,
    take_profit: Decimal | float | str | None = None,
    trailing_distance: Decimal | float | str | None = None,
    client_request_id: str | None = None,
) -> BrokerOrderProtectionRequest:
    """Build a BrokerOrderProtectionRequest instance (``feature``).

    Args:
        order_id: Target order identifier.
        idempotency_key: Explicit adapter-boundary idempotency key.
        stop_loss: Optional stop-loss price.
        take_profit: Optional take-profit price.
        trailing_distance: Optional trailing-stop distance.
        client_request_id: Optional caller request identifier.

    Returns:
        Configured BrokerOrderProtectionRequest instance.
    """
    return BrokerOrderProtectionRequest(
        order_id=order_id,
        idempotency_key=idempotency_key,
        stop_loss=Decimal(str(stop_loss)) if stop_loss is not None else None,
        take_profit=Decimal(str(take_profit)) if take_profit is not None else None,
        trailing_distance=Decimal(str(trailing_distance))
        if trailing_distance is not None
        else None,
        client_request_id=client_request_id,
    )


def build_broker_position_reduce_request(
    position_id: str,
    quantity: Decimal | float | str,
    quantity_unit: str,
    idempotency_key: str,
    client_request_id: str | None = None,
) -> BrokerPositionReductionRequest:
    """Build a BrokerPositionReductionRequest instance (``feature``).

    Args:
        position_id: Target position identifier.
        quantity: Quantity to reduce.
        quantity_unit: Provider quantity unit.
        idempotency_key: Explicit adapter-boundary idempotency key.
        client_request_id: Optional caller request identifier.

    Returns:
        Configured BrokerPositionReductionRequest instance.
    """
    return BrokerPositionReductionRequest(
        position_id=position_id,
        quantity=Decimal(str(quantity)),
        quantity_unit=quantity_unit,
        idempotency_key=idempotency_key,
        client_request_id=client_request_id,
    )


async def attach_broker_protection(
    adapter: BrokerAdapter, request: BrokerOrderProtectionRequest
) -> StandardResponse[BrokerOrderResult]:
    """Attach bracketing protection to one order through the root boundary.

    Args:
        adapter: Targeted broker adapter.
        request: Order protection request.

    Returns:
        Standard response containing the protection attachment result.
    """
    return await adapter.attach_protection(request)


async def reduce_broker_position(
    adapter: BrokerAdapter, request: BrokerPositionReductionRequest
) -> StandardResponse[BrokerOrderResult]:
    """Reduce one open position by an explicit quantity through the root boundary.

    Args:
        adapter: Targeted broker adapter.
        request: Position reduction request.

    Returns:
        Standard response containing the reduction result.
    """
    return await adapter.reduce_position(request)
