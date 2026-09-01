"""cTrader provider payload to canonical value mapping."""

# ruff: noqa: ANN401, FURB171 - protobuf fixtures expose heterogeneous fields.
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from app.services.brokers.canonical_contracts import (
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

    Args:
        value: Value supplied to the operation.
        name: Value supplied to the operation.

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

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.
        digits: Value supplied to the operation.

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

    Args:
        value: Value supplied to the operation.
        symbol_name: Value supplied to the operation.
        light: Value supplied to the operation.

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

    Args:
        values: Value supplied to the operation.

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

    Args:
        bids: Value supplied to the operation.
        asks: Value supplied to the operation.
        symbol: Value supplied to the operation.
        digits: Value supplied to the operation.
        limit: Value supplied to the operation.

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

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.
        digits: Value supplied to the operation.
        timeframe: Value supplied to the operation.
        duration_seconds: Value supplied to the operation.

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

    Args:
        value: Value supplied to the operation.

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

    Args:
        value: Value supplied to the operation.
        symbols: Value supplied to the operation.
        lot_sizes: Value supplied to the operation.

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
    label = _optional(trade, "label")
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
        ownership_ref=f"ctrader-label:{label}" if label else None,
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

    Args:
        value: Value supplied to the operation.
        symbols: Value supplied to the operation.
        lot_sizes: Value supplied to the operation.

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

    Args:
        value: Value supplied to the operation.
        symbols: Value supplied to the operation.
        lot_sizes: Value supplied to the operation.

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

    Args:
        value: Value supplied to the operation.
        fallback_id: Value supplied to the operation.

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

    Args:
        code: Value supplied to the operation.
        operation: Value supplied to the operation.

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


def _normalize_decimal_str(val: Decimal | str | float | None) -> str | None:
    """Normalize decimal value to match DecimalValue regex pattern.

    Args:
        val: Input decimal or string.

    Returns:
        Normalized decimal string or None.
    """
    if val is None:
        return None
    d = Decimal(str(val))
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s == "-0":
        s = "0"
    return s


def _format_utc_timestamp(dt: datetime | None) -> str | None:
    """Format datetime to match UtcTimestamp regex pattern.

    Args:
        dt: Input datetime.

    Returns:
        Formatted UTC timestamp string or None.
    """
    if dt is None:
        return None
    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def map_market_state(
    session_id: str,
    generation: int,
    instrument: Any,
    provider_symbol: str,
    quote: BrokerQuote,
) -> Any:
    """Map canonical quote to BrokerMarketState wire record.

    Args:
        session_id: Active broker session ID.
        generation: Active session generation.
        instrument: Associated instrument reference.
        provider_symbol: Exact provider symbol.
        quote: Resolved canonical quote.

    Returns:
        BrokerMarketState model.
    """
    from app.contracts.broker.models import BrokerMarketState
    from app.contracts.catalogue.models import InstrumentRef

    inst = (
        instrument
        if isinstance(instrument, InstrumentRef)
        else InstrumentRef(instrument_id=str(uuid.uuid7()))
    )
    bid_str = _normalize_decimal_str(quote.bid)
    ask_str = _normalize_decimal_str(quote.ask)
    last_str = bid_str or ask_str
    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    event_time_str = (
        _format_utc_timestamp(quote.provider_timestamp)
        if quote.provider_timestamp
        else now_str
    )
    return BrokerMarketState(
        session_id=session_id,
        generation=generation,
        instrument=inst,
        provider_symbol=provider_symbol,
        market_status="OPEN",
        receipt_time=now_str,
        bid=bid_str,
        ask=ask_str,
        last=last_str,
        event_time=event_time_str,
    )


def map_event_market_state(
    session_id: str,
    generation: int,
    raw_event: dict[str, Any],
    instrument: Any | None = None,
) -> Any:
    """Normalize raw cTrader event payload to BrokerMarketState.

    Args:
        session_id: Active session ID.
        generation: Active session generation.
        raw_event: Raw provider event dictionary.
        instrument: Optional instrument reference.

    Returns:
        BrokerMarketState model.
    """
    from app.contracts.broker.models import BrokerMarketState
    from app.contracts.catalogue.models import InstrumentRef

    symbol = str(raw_event.get("symbol", raw_event.get("provider_symbol", "EURUSD")))
    inst = (
        instrument
        if isinstance(instrument, InstrumentRef)
        else InstrumentRef(instrument_id=str(uuid.uuid7()))
    )
    bid_str = _normalize_decimal_str(raw_event.get("bid"))
    ask_str = _normalize_decimal_str(raw_event.get("ask"))
    last_str = _normalize_decimal_str(raw_event.get("last")) or bid_str or ask_str
    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    return BrokerMarketState(
        session_id=session_id,
        generation=generation,
        instrument=inst,
        provider_symbol=symbol,
        market_status="OPEN",
        receipt_time=now_str,
        bid=bid_str,
        ask=ask_str,
        last=last_str,
        event_time=now_str,
    )


def map_account_snapshot(
    session_id: str,
    generation: int,
    account_ref: str,
    currency: str = "USD",
    equity: Decimal | str | float = "10000.00",
    balances: dict[str, Decimal | str | float] | None = None,
    margin: Decimal | str | float | None = None,
    free_margin: Decimal | str | float | None = None,
    permissions: tuple[str, ...] = ("READ",),
    provider_time: datetime | None = None,
) -> Any:
    """Map account fields to BrokerAccountSnapshot wire record.

    Args:
        session_id: Active broker session ID.
        generation: Active session generation.
        account_ref: Configured account reference.
        currency: Base account currency.
        equity: Account equity value.
        balances: Currency balance mapping.
        margin: Used margin value.
        free_margin: Available free margin value.
        permissions: Account permission tags.
        provider_time: Timestamp from provider.

    Returns:
        BrokerAccountSnapshot model.
    """
    from app.contracts.broker.models import BrokerAccountSnapshot
    from app.contracts.common.models import Money

    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    eq_norm = _normalize_decimal_str(equity) or "10000"
    b_dict = {
        k: _normalize_decimal_str(v) or "0"
        for k, v in (balances or {currency: eq_norm}).items()
    }
    m_money = (
        Money(amount=_normalize_decimal_str(margin) or "0", currency=currency)
        if margin is not None
        else None
    )
    fm_money = (
        Money(amount=_normalize_decimal_str(free_margin) or eq_norm, currency=currency)
        if free_margin is not None
        else None
    )
    return BrokerAccountSnapshot(
        session_id=session_id,
        generation=generation,
        account_ref=account_ref,
        currency=currency,
        equity=Money(amount=eq_norm, currency=currency),
        retrieved_at=now_str,
        balances=b_dict,
        margin=m_money,
        free_margin=fm_money,
        permissions=permissions,
        provider_time=_format_utc_timestamp(provider_time) if provider_time else None,
    )


def map_trading_state(
    session_id: str,
    generation: int,
    positions: tuple[BrokerPosition, ...] = (),
    orders: tuple[BrokerOrder, ...] = (),
    deals: tuple[BrokerDeal, ...] = (),
    duplicate_or_contradictory: tuple[str, ...] = (),
) -> Any:
    """Map trading entities to BrokerTradingState wire record.

    Args:
        session_id: Active session ID.
        generation: Active session generation.
        positions: Open positions.
        orders: Active or historical orders.
        deals: Execution deals.
        duplicate_or_contradictory: Anomaly tags.

    Returns:
        BrokerTradingState model.
    """
    from app.contracts.broker.models import BrokerTradingState, ProviderRecord

    now_str = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    pos_records = tuple(
        ProviderRecord(
            provider_id=p.position_id,
            record={
                "position_id": p.position_id,
                "symbol": p.symbol,
                "side": p.side,
                "quantity": _normalize_decimal_str(p.quantity) or "0",
                "state": p.state,
                "open_price": _normalize_decimal_str(p.open_price),
            },
        )
        for p in positions
    )
    ord_records = tuple(
        ProviderRecord(
            provider_id=o.order_id,
            record={
                "order_id": o.order_id,
                "symbol": o.symbol,
                "side": o.side,
                "order_type": o.order_type,
                "state": o.state,
                "quantity": _normalize_decimal_str(o.quantity) or "0",
                "filled": _normalize_decimal_str(o.filled) or "0",
            },
        )
        for o in orders
    )
    deal_records = tuple(
        ProviderRecord(
            provider_id=d.deal_id,
            record={
                "deal_id": d.deal_id,
                "order_id": d.order_id,
                "position_id": d.position_id,
                "symbol": d.symbol,
                "side": d.side,
                "quantity": _normalize_decimal_str(d.quantity) or "0",
                "price": _normalize_decimal_str(d.price) or "0",
            },
        )
        for d in deals
    )
    return BrokerTradingState(
        session_id=session_id,
        generation=generation,
        retrieved_at=now_str,
        positions=pos_records,
        orders=ord_records,
        deals=deal_records,
        duplicate_or_contradictory=duplicate_or_contradictory,
    )


def map_history_page(
    values: tuple[BrokerBar, ...] | tuple[BrokerTick, ...],
    symbol: str,
    timeframe: str,
    limit: int,
    page_id: str,
    retrieved_at: str | None = None,
    requested_timeframe: str | None = None,
    is_truncated: bool = False,
    cursor: str | None = None,
) -> Any:
    """Map bar/tick sequence to BrokerHistoryPage wire record.

    Args:
        values: Sequence of BrokerBar or BrokerTick.
        symbol: Provider symbol.
        timeframe: Provider timeframe interval.
        limit: Requested page size limit.
        page_id: Unique page ID.
        retrieved_at: Retrieval timestamp string.
        requested_timeframe: Canonical requested timeframe.
        is_truncated: Whether more records are available.
        cursor: Pagination cursor string.

    Returns:
        BrokerHistoryPage model.
    """
    from app.contracts.broker.models import BrokerHistoryPage, ProviderRecord

    del timeframe, requested_timeframe
    now_str = retrieved_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    records: list[ProviderRecord] = []
    for idx, item in enumerate(values):
        if isinstance(item, BrokerBar):
            rec_dict: dict[str, Any] = {
                "symbol": item.symbol,
                "open": _normalize_decimal_str(item.open) or "0",
                "high": _normalize_decimal_str(item.high) or "0",
                "low": _normalize_decimal_str(item.low) or "0",
                "close": _normalize_decimal_str(item.close) or "0",
                "volume": _normalize_decimal_str(item.tick_volume) or "0",
                "opening_timestamp": _format_utc_timestamp(item.opening_timestamp),
                "closing_timestamp": _format_utc_timestamp(item.closing_timestamp),
                "timeframe": item.provider_timeframe,
            }
        elif isinstance(item, BrokerTick):
            rec_dict = {
                "symbol": item.symbol,
                "bid": _normalize_decimal_str(item.bid),
                "ask": _normalize_decimal_str(item.ask),
                "event_timestamp": _format_utc_timestamp(item.event_timestamp),
            }
        else:
            rec_dict = {"symbol": symbol}
        records.append(ProviderRecord(provider_id=f"{symbol}:{idx}", record=rec_dict))
    selected = records[:limit]
    return BrokerHistoryPage(
        page_id=page_id,
        requested_count=limit,
        returned_count=len(selected),
        is_truncated=is_truncated or (len(records) > limit),
        retrieved_at=now_str,
        provider_cursor=cursor,
        records=tuple(selected),
    )
