"""cTrader protobuf fixture to canonical value mapping."""

# ruff: noqa: ANN401, FURB171 - protobuf fixtures expose heterogeneous fields.

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from app.services.brokers.contracts import (
    BrokerBar,
    BrokerDeal,
    BrokerErrorCode,
    BrokerOrder,
    BrokerOrderResult,
    BrokerPosition,
    BrokerQuote,
    BrokerSymbolInfo,
    BrokerTick,
)


def _field(value: object, name: str) -> Any:
    """Handle field.

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

    Returns:
        The operation result.
    """
    if isinstance(value, dict):
        return value[name]
    return getattr(value, name)


def _optional(value: object, name: str) -> Any:
    """Read one optional dictionary or protobuf field.

    Returns:
        Field value or ``None`` when absent.
    """
    if isinstance(value, dict):
        return value.get(name)
    has_field = getattr(value, "HasField", None)
    if callable(has_field):
        try:
            if not has_field(name):
                return None
        except ValueError:
            # Repeated/non-presence fields are read through their public value.
            pass
    return getattr(value, name, None)


def _map_quote(value: object, symbol: str, digits: int) -> BrokerQuote:
    """Map exact relative prices using provider symbol digits.

    Returns:
        Canonical provider quote.
    """
    divisor = Decimal(10) ** digits
    timestamp_raw = _optional(value, "timestamp")
    timestamp = (
        datetime.fromtimestamp(float(timestamp_raw) / 1000, UTC)
        if timestamp_raw is not None
        else None
    )
    bid_raw = _optional(value, "bid")
    ask_raw = _optional(value, "ask")
    return BrokerQuote(
        symbol=symbol,
        price_unit="quote_currency",
        quantity_unit="provider_volume",
        retrieved_at=datetime.now(UTC),
        bid=Decimal(bid_raw) / divisor if bid_raw is not None else None,
        ask=Decimal(ask_raw) / divisor if ask_raw is not None else None,
        provider_timestamp=timestamp,
    )


def _map_symbol(
    value: object,
    *,
    symbol_name: str,
    light: object | None = None,
) -> BrokerSymbolInfo:
    """Map exact cTrader symbol specification fields.

    Returns:
        Canonical provider-native symbol information.
    """
    digits = int(_field(value, "digits"))
    lot_size_raw = _optional(value, "lotSize")
    lot_size = Decimal(str(lot_size_raw)) if lot_size_raw else None
    volume_divisor = Decimal(100) * lot_size if lot_size is not None else None
    return BrokerSymbolInfo(
        provider_symbol=symbol_name,
        product_profile="ctrader",
        price_unit="quote_currency",
        quantity_unit="lots",
        price_precision=digits,
        min_quantity=(
            Decimal(str(_optional(value, "minVolume"))) / volume_divisor
            if _optional(value, "minVolume") is not None and volume_divisor is not None
            else None
        ),
        max_quantity=(
            Decimal(str(_optional(value, "maxVolume"))) / volume_divisor
            if _optional(value, "maxVolume") is not None and volume_divisor is not None
            else None
        ),
        quantity_step=(
            Decimal(str(_optional(value, "stepVolume"))) / volume_divisor
            if _optional(value, "stepVolume") is not None and volume_divisor is not None
            else None
        ),
        trading_flags={
            "enabled": (
                bool(_optional(light, "enabled")) if light is not None else None
            ),
            "short_selling": (
                bool(_optional(value, "enableShortSelling"))
                if _optional(value, "enableShortSelling") is not None
                else None
            ),
        },
        provider_metadata={
            "symbol_id": str(_field(value, "symbolId")),
            "lot_size": _optional(value, "lotSize"),
            "pip_position": _optional(value, "pipPosition"),
        },
    )


def _decode_tick_series(values: object) -> tuple[tuple[int, int], ...]:
    """Decode cTrader's first-absolute, subsequent-delta tick sequence.

    Returns:
        Absolute ``(timestamp_ms, relative_price)`` pairs.
    """
    timestamp = 0
    price = 0
    decoded: list[tuple[int, int]] = []
    for index, value in enumerate(cast("list[object]", values)):
        raw_timestamp = int(_field(value, "timestamp"))
        raw_price = int(_field(value, "tick"))
        if index == 0:
            timestamp = raw_timestamp
            price = raw_price
        else:
            timestamp += raw_timestamp
            price += raw_price
        decoded.append((timestamp, price))
    return tuple(decoded)


def _map_ticks(
    bids: object,
    asks: object,
    *,
    symbol: str,
    digits: int,
    limit: int,
) -> tuple[BrokerTick, ...]:
    """Merge cTrader BID and ASK historical sequences by timestamp.

    Returns:
        Bounded chronological canonical quote ticks.
    """
    divisor = Decimal(10) ** digits
    merged: dict[int, dict[str, Decimal]] = {}
    for timestamp, price in _decode_tick_series(bids):
        merged.setdefault(timestamp, {})["bid"] = Decimal(price) / divisor
    for timestamp, price in _decode_tick_series(asks):
        merged.setdefault(timestamp, {})["ask"] = Decimal(price) / divisor
    return tuple(
        BrokerTick(
            symbol=symbol,
            event_timestamp=datetime.fromtimestamp(timestamp / 1000, UTC),
            provider_receipt_timestamp=datetime.now(UTC),
            price_unit="quote_currency",
            quantity_unit="lots",
            tick_type="QUOTE",
            bid=prices.get("bid"),
            ask=prices.get("ask"),
        )
        for timestamp, prices in sorted(merged.items())[:limit]
    )


def _map_bar(
    value: object,
    *,
    symbol: str,
    digits: int,
    timeframe: str,
    duration_seconds: int,
) -> BrokerBar:
    """Map one delta-encoded cTrader trendbar.

    Returns:
        Canonical closed provider bar.
    """
    divisor = Decimal(10) ** digits
    low_raw = int(_field(value, "low"))
    opening = datetime.fromtimestamp(
        int(_field(value, "utcTimestampInMinutes")) * 60, UTC
    )
    return BrokerBar(
        symbol=symbol,
        opening_timestamp=opening,
        closing_timestamp=opening + timedelta(seconds=duration_seconds),
        is_closed=True,
        open=Decimal(low_raw + int(_field(value, "deltaOpen"))) / divisor,
        high=Decimal(low_raw + int(_field(value, "deltaHigh"))) / divisor,
        low=Decimal(low_raw) / divisor,
        close=Decimal(low_raw + int(_field(value, "deltaClose"))) / divisor,
        provider_timeframe=timeframe,
        requested_timeframe=timeframe,
        price_unit="quote_currency",
        quantity_unit="lots",
        tick_volume=Decimal(str(_field(value, "volume"))),
    )


def _side(value: object) -> str:
    """Map cTrader numeric trade side.

    Returns:
        Canonical trade side.
    """
    buy_code = 1
    sell_code = 2
    code = int(cast("Any", value))
    return "BUY" if code == buy_code else ("SELL" if code == sell_code else "UNKNOWN")


def _map_position(
    value: object, symbols: dict[int, str], lot_sizes: dict[int, Decimal]
) -> BrokerPosition:
    """Map one cTrader reconciled position.

    Returns:
        Canonical open position.
    """
    trade = _field(value, "tradeData")
    symbol_id = int(_field(trade, "symbolId"))
    money_digits = int(_optional(value, "moneyDigits") or 2)
    money_divisor = Decimal(10) ** money_digits
    status = int(_field(value, "positionStatus"))
    open_status = 1
    closed_status = 2
    trade_side = _side(_field(trade, "tradeSide"))
    return BrokerPosition(
        position_id=str(_field(value, "positionId")),
        symbol=symbols[symbol_id],
        side=cast(
            "Any",
            "LONG"
            if trade_side == "BUY"
            else ("SHORT" if trade_side == "SELL" else "UNKNOWN"),
        ),
        quantity=Decimal(str(_field(trade, "volume")))
        / (Decimal(100) * lot_sizes[symbol_id]),
        quantity_unit="lots",
        retrieved_at=datetime.now(UTC),
        state=(
            "OPEN"
            if status == open_status
            else ("CLOSED" if status == closed_status else "UNKNOWN")
        ),
        open_price=(
            Decimal(str(_optional(value, "price")))
            if _optional(value, "price") is not None
            else None
        ),
        swap=Decimal(str(_field(value, "swap"))) / money_divisor,
        stop_loss=(
            Decimal(str(_optional(value, "stopLoss")))
            if _optional(value, "stopLoss") is not None
            else None
        ),
        take_profit=(
            Decimal(str(_optional(value, "takeProfit")))
            if _optional(value, "takeProfit") is not None
            else None
        ),
        provider_timestamp=(
            datetime.fromtimestamp(
                int(_optional(value, "utcLastUpdateTimestamp")) / 1000, UTC
            )
            if _optional(value, "utcLastUpdateTimestamp")
            else None
        ),
    )


def _map_order(
    value: object, symbols: dict[int, str], lot_sizes: dict[int, Decimal]
) -> BrokerOrder:
    """Map one cTrader active or historical order.

    Returns:
        Canonical provider order.
    """
    trade = _field(value, "tradeData")
    symbol_id = int(_field(trade, "symbolId"))
    volume_divisor = Decimal(100) * lot_sizes[symbol_id]
    quantity = Decimal(str(_field(trade, "volume"))) / volume_divisor
    filled = Decimal(str(_optional(value, "executedVolume") or 0)) / volume_divisor
    type_code = int(_field(value, "orderType"))
    status_code = int(_field(value, "orderStatus"))
    return BrokerOrder(
        order_id=str(_field(value, "orderId")),
        symbol=symbols[int(_field(trade, "symbolId"))],
        side=cast("Any", _side(_field(trade, "tradeSide"))),
        order_type={1: "MARKET", 2: "LIMIT", 3: "STOP", 6: "STOP_LIMIT"}.get(
            type_code, "UNKNOWN"
        ),
        state={
            1: "ACCEPTED",
            2: "FILLED",
            3: "REJECTED",
            4: "EXPIRED",
            5: "CANCELLED",
        }.get(status_code, "UNKNOWN"),
        quantity=quantity,
        filled=filled,
        remaining=max(Decimal(0), quantity - filled),
        quantity_unit="lots",
        retrieved_at=datetime.now(UTC),
        client_order_id=(
            str(_optional(value, "clientOrderId"))
            if _optional(value, "clientOrderId")
            else None
        ),
        price=(
            Decimal(str(_optional(value, "limitPrice")))
            if _optional(value, "limitPrice") is not None
            else None
        ),
        stop_price=(
            Decimal(str(_optional(value, "stopPrice")))
            if _optional(value, "stopPrice") is not None
            else None
        ),
        product_profile="ctrader",
        provider_timestamp=(
            datetime.fromtimestamp(
                int(_optional(value, "utcLastUpdateTimestamp")) / 1000, UTC
            )
            if _optional(value, "utcLastUpdateTimestamp")
            else None
        ),
        provider_metadata={
            "native_order_type": type_code,
            "native_order_state": status_code,
        },
    )


def _map_deal(
    value: object, symbols: dict[int, str], lot_sizes: dict[int, Decimal]
) -> BrokerDeal:
    """Map one cTrader execution deal.

    Returns:
        Canonical provider deal.
    """
    money_digits = int(_optional(value, "moneyDigits") or 2)
    return BrokerDeal(
        deal_id=str(_field(value, "dealId")),
        order_id=str(_field(value, "orderId")),
        position_id=str(_field(value, "positionId")),
        symbol=symbols[int(_field(value, "symbolId"))],
        side=cast("Any", _side(_field(value, "tradeSide"))),
        quantity=Decimal(str(_field(value, "filledVolume")))
        / (Decimal(100) * lot_sizes[int(_field(value, "symbolId"))]),
        quantity_unit="lots",
        price=Decimal(str(_field(value, "executionPrice"))),
        partial=int(_field(value, "filledVolume")) < int(_field(value, "volume")),
        retrieved_at=datetime.now(UTC),
        fee=(
            Decimal(str(_optional(value, "commission"))) / (Decimal(10) ** money_digits)
            if _optional(value, "commission") is not None
            else None
        ),
        provider_timestamp=datetime.fromtimestamp(
            int(_field(value, "executionTimestamp")) / 1000, UTC
        ),
    )


def _map_order_result(
    value: object, fallback_id: str | None = None
) -> BrokerOrderResult:
    """Map one cTrader execution event acknowledgement.

    Returns:
        Canonical explicit mutation outcome.
    """
    error_code = _optional(value, "errorCode")
    order = _optional(value, "order")
    deal = _optional(value, "deal")
    order_id = (
        str(_optional(order, "orderId"))
        if order is not None and _optional(order, "orderId")
        else fallback_id
    )
    rejected = bool(error_code)
    return BrokerOrderResult(
        acknowledged=True,
        outcome="REJECTED" if rejected else "ACCEPTED",
        retrieved_at=datetime.now(UTC),
        order_id=None if rejected else order_id,
        deal_ids=(str(_optional(deal, "dealId")),)
        if deal is not None and _optional(deal, "dealId")
        else (),
        provider_code=str(error_code) if error_code else None,
    )


def _map_error_code(code: str, operation: str) -> BrokerErrorCode:
    """Map the normative cTrader native-error floor.

    Returns:
        Stable canonical error code.
    """
    if code in {"MARKET_CLOSED"}:
        return BrokerErrorCode.BROKER_MARKET_CLOSED
    if code == "NOT_ENOUGH_MONEY":
        return BrokerErrorCode.BROKER_INSUFFICIENT_MARGIN
    if code in {
        "INVALID_REQUEST",
        "INVALID_VOLUME",
        "INVALID_STOPS",
        "BAD_VOLUME",
        "INVALID_EXPIRATION",
    }:
        return BrokerErrorCode.BROKER_REQUEST_INVALID
    if code == "ORDER_NOT_FOUND" and "order" in operation:
        return BrokerErrorCode.BROKER_ORDER_NOT_FOUND
    if code == "POSITION_NOT_FOUND" and "position" in operation:
        return BrokerErrorCode.BROKER_POSITION_NOT_FOUND
    return BrokerErrorCode.BROKER_PROVIDER_ERROR
