"""Binance provider payload to canonical DTO mapping."""

# ruff: noqa: PLR2004 - native wire constants are normative provider evidence.
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.contracts.broker.models import (
    BrokerHistoryPage,
    BrokerMarketState,
    ProviderRecord,
)
from app.contracts.catalogue.models import InstrumentRef
from app.services.brokers.canonical_contracts import (
    BrokerBar,
    BrokerErrorCode,
    BrokerOrderBook,
    BrokerQuote,
    BrokerSymbolInfo,
    BrokerTick,
)
from app.services.brokers.canonical_contracts.protocols import _ProviderResponseError

if TYPE_CHECKING:
    from app.contracts.common.models import JsonObject

_CANONICAL_INTERVALS = {
    "S1": "1s",
    "M1": "1m",
    "M3": "3m",
    "M5": "5m",
    "M15": "15m",
    "M30": "30m",
    "H1": "1h",
    "H2": "2h",
    "H4": "4h",
    "H6": "6h",
    "H8": "8h",
    "H12": "12h",
    "D1": "1d",
    "D3": "3d",
    "W1": "1w",
    "MN1": "1M",
}
_PROVIDER_INTERVALS = frozenset(_CANONICAL_INTERVALS.values())


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


def _provider_interval(timeframe: str) -> str:
    """Translate one canonical timeframe to an exact Binance interval.

    Args:
        timeframe: Canonical or exact provider timeframe.

    Returns:
        Binance's case-sensitive interval value.

    Raises:
        ValueError: If the timeframe has no declared Binance mapping.
    """
    if timeframe in _PROVIDER_INTERVALS:
        return timeframe
    try:
        return _CANONICAL_INTERVALS[timeframe.upper()]
    except KeyError as error:
        message = f"unsupported Binance timeframe: {timeframe}"
        raise ValueError(message) from error


def _map_symbol(value: dict[str, Any]) -> BrokerSymbolInfo:
    """Map exact Spot exchange metadata without canonical aliases.

    Args:
        value: Value supplied to the operation.

    Returns:
        Canonical symbol information.
    """
    symbol = str(value["symbol"])
    return BrokerSymbolInfo(
        provider_symbol=symbol,
        product_profile="binance_spot",
        price_unit=str(value["quoteAsset"]),
        quantity_unit=str(value["baseAsset"]),
        base_asset=str(value["baseAsset"]),
        quote_asset=str(value["quoteAsset"]),
        price_precision=int(value["quoteAssetPrecision"]),
        quantity_precision=int(value["baseAssetPrecision"]),
        trading_flags={"spot_trading_allowed": value.get("isSpotTradingAllowed")},
    )


def _map_quote(value: dict[str, Any], symbol: str) -> BrokerQuote:
    """Map genuine book-ticker values and quantities.

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.

    Returns:
        Canonical provider quote.
    """
    return BrokerQuote(
        symbol=symbol,
        price_unit="quote_asset",
        quantity_unit="base_asset",
        retrieved_at=datetime.now(UTC),
        bid=Decimal(str(value["bidPrice"])),
        ask=Decimal(str(value["askPrice"])),
        bid_quantity=Decimal(str(value["bidQty"])),
        ask_quantity=Decimal(str(value["askQty"])),
    )


def _map_trade(value: dict[str, Any], symbol: str) -> BrokerTick:
    """Map one genuine aggregate trade without inventing sequence evidence.

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.

    Returns:
        Canonical trade tick.
    """
    timestamp = datetime.fromtimestamp(int(value["T"]) / 1000, UTC)
    return BrokerTick(
        symbol=symbol,
        event_timestamp=timestamp,
        provider_receipt_timestamp=datetime.now(UTC),
        price_unit="quote_asset",
        quantity_unit="base_asset",
        tick_type="TRADE",
        provider_sequence_id=value.get("a"),
        last_price=Decimal(str(value["p"])),
        bid_quantity=Decimal(str(value["q"])),
    )


def _map_kline(
    value: list[Any],
    symbol: str,
    timeframe: str,
    requested_timeframe: str | None = None,
) -> BrokerBar:
    """Map one documented Spot kline array.

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.
        timeframe: Value supplied to the operation.
        requested_timeframe: Value supplied to the operation.

    Returns:
        Canonical provider bar.

    Raises:
        _ProviderResponseError: If the provider kline array is incomplete.
    """
    if len(value) < 11:
        raise _ProviderResponseError("malformed Binance kline")
    return BrokerBar(
        symbol=symbol,
        opening_timestamp=datetime.fromtimestamp(int(value[0]) / 1000, UTC),
        closing_timestamp=datetime.fromtimestamp(int(value[6]) / 1000, UTC),
        is_closed=True,
        open=Decimal(str(value[1])),
        high=Decimal(str(value[2])),
        low=Decimal(str(value[3])),
        close=Decimal(str(value[4])),
        provider_timeframe=timeframe,
        requested_timeframe=requested_timeframe or timeframe,
        price_unit="quote_asset",
        quantity_unit="base_asset",
        trade_volume=Decimal(str(value[5])),
    )


def _map_stream_quote(value: dict[str, Any], symbol: str) -> BrokerQuote:
    """Map one genuine Binance book-ticker websocket event.

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.

    Returns:
        Canonical provider quote.
    """
    return BrokerQuote(
        symbol=symbol,
        price_unit="quote_asset",
        quantity_unit="base_asset",
        retrieved_at=datetime.now(UTC),
        bid=Decimal(str(value["b"])),
        ask=Decimal(str(value["a"])),
        bid_quantity=Decimal(str(value["B"])),
        ask_quantity=Decimal(str(value["A"])),
        provider_sequence_id=value.get("u"),
        provider_timestamp=(
            datetime.fromtimestamp(int(value["E"]) / 1000, UTC)
            if value.get("E") is not None
            else None
        ),
    )


def _map_stream_bar(value: dict[str, Any], symbol: str) -> BrokerBar:
    """Map one genuine Binance kline websocket event.

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.

    Returns:
        Canonical open or closed provider bar.
    """
    kline = value["k"]
    return BrokerBar(
        symbol=symbol,
        opening_timestamp=datetime.fromtimestamp(int(kline["t"]) / 1000, UTC),
        closing_timestamp=datetime.fromtimestamp(int(kline["T"]) / 1000, UTC),
        is_closed=bool(kline["x"]),
        open=Decimal(str(kline["o"])),
        high=Decimal(str(kline["h"])),
        low=Decimal(str(kline["l"])),
        close=Decimal(str(kline["c"])),
        provider_timeframe=str(kline["i"]),
        requested_timeframe=str(kline["i"]),
        price_unit="quote_asset",
        quantity_unit="base_asset",
        trade_volume=Decimal(str(kline["v"])),
    )


def _map_order_book(
    value: dict[str, Any], symbol: str, *, depth: int, is_snapshot: bool
) -> BrokerOrderBook:
    """Map one Binance REST snapshot or websocket depth event.

    Args:
        value: Value supplied to the operation.
        symbol: Value supplied to the operation.
        depth: Value supplied to the operation.
        is_snapshot: Value supplied to the operation.

    Returns:
        Canonical sequence-aware order book.
    """
    bids = value.get("bids", value.get("b", ()))
    asks = value.get("asks", value.get("a", ()))
    first_sequence = value.get("U")
    last_sequence = value.get("lastUpdateId", value.get("u"))
    return BrokerOrderBook(
        symbol=symbol,
        bids=tuple(
            (Decimal(str(price)), Decimal(str(quantity)))
            for price, quantity in bids[:depth]
        ),
        asks=tuple(
            (Decimal(str(price)), Decimal(str(quantity)))
            for price, quantity in asks[:depth]
        ),
        is_snapshot=is_snapshot,
        resnapshot_required=not is_snapshot and first_sequence is None,
        event_timestamp=(
            datetime.fromtimestamp(int(value["E"]) / 1000, UTC)
            if value.get("E") is not None
            else datetime.now(UTC)
        ),
        price_unit="quote_asset",
        quantity_unit="base_asset",
        first_sequence_id=int(first_sequence) if first_sequence is not None else None,
        last_sequence_id=int(last_sequence) if last_sequence is not None else None,
        depth_truncation=depth,
    )


def _map_error_code(code: int) -> BrokerErrorCode:
    """Map the normative Binance native-error floor.

    Args:
        code: Value supplied to the operation.

    Returns:
        Stable canonical error code.
    """
    if code == -1003:
        return BrokerErrorCode.BROKER_RATE_LIMITED
    if code == -1121:
        return BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND
    if code == -2010:
        return BrokerErrorCode.BROKER_REQUEST_REJECTED
    if code == -2015:
        return BrokerErrorCode.BROKER_AUTHENTICATION_FAILED
    return BrokerErrorCode.BROKER_PROVIDER_ERROR


def map_history_page(
    values: list[Any],
    *,
    symbol: str,
    timeframe: str,
    limit: int,
    page_id: str,
    retrieved_at: str,
    requested_timeframe: str | None = None,
    is_trade: bool = False,
) -> BrokerHistoryPage:
    """Map provider klines or trades into a ratified BrokerHistoryPage wire model.

    Args:
        values: Raw kline or trade list from Binance transport.
        symbol: Exact provider symbol.
        timeframe: Timeframe interval.
        limit: Max requested items.
        page_id: UUID7 string.
        retrieved_at: UTC timestamp string.
        requested_timeframe: Optional caller requested timeframe.
        is_trade: Whether values are aggregate trades.

    Returns:
        Validated BrokerHistoryPage wire model.

    Raises:
        ValueError: If limit is not positive.
    """
    if limit <= 0:
        raise ValueError("positive Binance history limit is required")

    records: list[ProviderRecord] = []
    if is_trade:
        for val in values[:limit]:
            tick = _map_trade(val, symbol)
            trade_data: JsonObject = {
                "symbol": symbol,
                "event_timestamp": _format_utc_timestamp(tick.event_timestamp),
                "price": str(tick.last_price) if tick.last_price is not None else None,
                "quantity": (
                    str(tick.bid_quantity) if tick.bid_quantity is not None else None
                ),
                "sequence_id": str(tick.provider_sequence_id)
                if tick.provider_sequence_id
                else None,
                "provenance": {"provider": "binance_spot"},
            }
            records.append(
                ProviderRecord(provider_id="binance_spot", record=trade_data)
            )
    else:
        for val in values[:limit]:
            bar = _map_kline(
                val,
                symbol,
                timeframe,
                requested_timeframe=requested_timeframe,
            )
            vol_str = str(bar.trade_volume) if bar.trade_volume is not None else None
            bar_data: JsonObject = {
                "symbol": bar.symbol,
                "opening_timestamp": _format_utc_timestamp(bar.opening_timestamp),
                "closing_timestamp": _format_utc_timestamp(bar.closing_timestamp),
                "open": _normalize_decimal_str(bar.open),
                "high": _normalize_decimal_str(bar.high),
                "low": _normalize_decimal_str(bar.low),
                "close": _normalize_decimal_str(bar.close),
                "provider_timeframe": bar.provider_timeframe,
                "requested_timeframe": bar.requested_timeframe,
                "trade_volume": vol_str,
                "is_closed": bar.is_closed,
                "provenance": {"provider": "binance_spot"},
            }
            records.append(ProviderRecord(provider_id="binance_spot", record=bar_data))

    return BrokerHistoryPage(
        page_id=page_id,
        requested_count=limit,
        returned_count=len(records),
        is_truncated=len(values) > limit,
        retrieved_at=retrieved_at,
        provider_cursor=None,
        records=tuple(records),
    )


def map_market_state(
    session_id: str,
    generation: int,
    instrument: InstrumentRef,
    provider_symbol: str,
    *,
    quote: BrokerQuote | None = None,
    order_book: BrokerOrderBook | None = None,
    market_status: str = "OPEN",
    receipt_time: str | None = None,
) -> BrokerMarketState:
    """Map quote/order-book state to BrokerMarketState wire record.

    Args:
        session_id: Session identifier.
        generation: Session generation.
        instrument: Catalogue instrument reference.
        provider_symbol: Provider symbol string.
        quote: Optional provider quote.
        order_book: Optional order book snapshot.
        market_status: Market status string.
        receipt_time: Optional receipt timestamp.

    Returns:
        Validated BrokerMarketState wire record.
    """
    now_utc = receipt_time or _format_utc_timestamp(datetime.now(UTC)) or ""
    bid_val: str | None = None
    ask_val: str | None = None
    seq: int | None = None
    event_time: str | None = None

    if quote is not None:
        bid_val = _normalize_decimal_str(quote.bid)
        ask_val = _normalize_decimal_str(quote.ask)
        seq = (
            int(quote.provider_sequence_id)
            if quote.provider_sequence_id is not None
            else None
        )
        event_time = _format_utc_timestamp(quote.retrieved_at)
    elif order_book is not None:
        if order_book.bids:
            bid_val = _normalize_decimal_str(order_book.bids[0][0])
        if order_book.asks:
            ask_val = _normalize_decimal_str(order_book.asks[0][0])
        seq = order_book.last_sequence_id
        event_time = _format_utc_timestamp(order_book.event_timestamp)

    status_val = "OPEN" if market_status.upper() == "OPEN" else "CLOSED"

    return BrokerMarketState(
        session_id=session_id,
        generation=generation,
        instrument=instrument,
        provider_symbol=provider_symbol,
        market_status=status_val,  # type: ignore[arg-type]
        receipt_time=now_utc,
        bid=bid_val,
        ask=ask_val,
        last=None,
        provider_sequence=seq,
        event_time=event_time,
    )


def map_event_market_state(
    session_id: str,
    generation: int,
    raw_event: dict[str, Any],
    instrument: InstrumentRef | None = None,
) -> BrokerMarketState:
    """Normalize raw Binance websocket event into BrokerMarketState.

    Args:
        session_id: Session identifier.
        generation: Session generation.
        raw_event: Raw dictionary event from websocket.
        instrument: Optional instrument reference.

    Returns:
        Normalized BrokerMarketState.
    """
    now_utc = _format_utc_timestamp(datetime.now(UTC)) or ""
    inst = instrument or InstrumentRef(instrument_id=str(uuid.uuid7()))
    symbol = str(raw_event.get("s", raw_event.get("symbol", "UNKNOWN")))

    # Check if event is bookTicker ("b", "a", "u")
    if "b" in raw_event and "a" in raw_event:
        bid = _normalize_decimal_str(raw_event["b"])
        ask = _normalize_decimal_str(raw_event["a"])
        seq = int(raw_event["u"]) if "u" in raw_event else None
        event_time = (
            _format_utc_timestamp(
                datetime.fromtimestamp(int(raw_event["E"]) / 1000, UTC)
            )
            if "E" in raw_event
            else now_utc
        )
        return BrokerMarketState(
            session_id=session_id,
            generation=generation,
            instrument=inst,
            provider_symbol=symbol,
            market_status="OPEN",
            receipt_time=now_utc,
            bid=bid,
            ask=ask,
            last=None,
            provider_sequence=seq,
            event_time=event_time,
        )

    # Check if event is kline ("k")
    if "k" in raw_event:
        kline = raw_event["k"]
        close_price = _normalize_decimal_str(kline.get("c", "0"))
        seq = int(raw_event["E"]) if "E" in raw_event else None
        event_time = (
            _format_utc_timestamp(
                datetime.fromtimestamp(int(raw_event["E"]) / 1000, UTC)
            )
            if "E" in raw_event
            else now_utc
        )
        return BrokerMarketState(
            session_id=session_id,
            generation=generation,
            instrument=inst,
            provider_symbol=symbol,
            market_status="OPEN",
            receipt_time=now_utc,
            bid=close_price,
            ask=close_price,
            last=close_price,
            provider_sequence=seq,
            event_time=event_time,
        )

    # Generic fallback
    return BrokerMarketState(
        session_id=session_id,
        generation=generation,
        instrument=inst,
        provider_symbol=symbol,
        market_status="OPEN",
        receipt_time=now_utc,
        bid=None,
        ask=None,
        last=None,
        provider_sequence=None,
        event_time=now_utc,
    )
