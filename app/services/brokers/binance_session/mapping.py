"""Binance Spot provider payload to canonical DTO mapping."""

# ruff: noqa: PLR2004 - native wire constants are normative provider evidence.

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.services.brokers.contracts import (
    BrokerBar,
    BrokerErrorCode,
    BrokerOrderBook,
    BrokerQuote,
    BrokerSymbolInfo,
    BrokerTick,
)
from app.services.brokers.contracts.protocols import _ProviderResponseError

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
