"""Map Dukascopy channel candle rows to canonical broker bars."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

from app.contracts.broker.models import BrokerHistoryPage, ProviderRecord
from app.services.brokers.canonical_contracts import BrokerBar
from app.services.brokers.dukascopy.transport import _ProviderResponseError

if TYPE_CHECKING:
    from app.contracts.common.models import JsonObject

_TIMEFRAMES = {
    "M1": ("1MIN", timedelta(minutes=1)),
    "M5": ("5MIN", timedelta(minutes=5)),
    "M15": ("15MIN", timedelta(minutes=15)),
    "M30": ("30MIN", timedelta(minutes=30)),
    "H1": ("1HOUR", timedelta(hours=1)),
}
_CANDLE_FIELD_COUNT = 6


def _normalize_timeframe(timeframe: str) -> str:
    """Normalize documented duration notation to provider candle notation.

    Args:
        timeframe: Caller-supplied canonical duration or provider notation.

    Returns:
        Dukascopy mapping key.
    """
    return {
        "1M": "M1",
        "5M": "M5",
        "15M": "M15",
        "30M": "M30",
        "1H": "H1",
    }.get(timeframe.upper(), timeframe.upper())


def _provider_interval(timeframe: str) -> str:
    """Return the exact Dukascopy web-chart interval for one timeframe.

    Args:
        timeframe: Canonical requested timeframe.

    Returns:
        Provider interval string.

    Raises:
        ValueError: If the timeframe is unsupported.
    """
    try:
        return _TIMEFRAMES[_normalize_timeframe(timeframe)][0]
    except KeyError as error:
        raise ValueError("unsupported Dukascopy candle timeframe") from error


def _map_candles(
    rows: tuple[tuple[object, ...], ...],
    *,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
) -> tuple[BrokerBar, ...]:
    """Validate and map genuine provider BID candle rows.

    Args:
        rows: Provider rows shaped as timestamp, OHLC, and volume.
        symbol: Canonical exact provider symbol.
        timeframe: Canonical requested timeframe.
        start: Inclusive UTC request boundary.
        end: Exclusive UTC request boundary.

    Returns:
        Chronological canonical BID bars within the requested range.

    Raises:
        ValueError: If the request timeframe or range is invalid.
        _ProviderResponseError: If a provider row is malformed or unordered.
    """
    normalized = _normalize_timeframe(timeframe)
    try:
        _, duration = _TIMEFRAMES[normalized]
    except KeyError as error:
        raise ValueError("unsupported Dukascopy candle timeframe") from error
    if (
        start.tzinfo is None
        or start.utcoffset() is None
        or end.tzinfo is None
        or end.utcoffset() is None
        or start >= end
    ):
        raise ValueError("ordered timezone-aware Dukascopy candle range is required")

    normalized_start = start.astimezone(UTC)
    normalized_end = end.astimezone(UTC)
    bars: list[BrokerBar] = []
    previous: datetime | None = None
    for row in rows:
        if (
            len(row) != _CANDLE_FIELD_COUNT
            or isinstance(row[0], bool)
            or not isinstance(row[0], int)
        ):
            raise _ProviderResponseError("malformed Dukascopy candle row")
        opening = datetime.fromtimestamp(row[0] / 1000, UTC)
        if previous is not None and opening <= previous:
            raise _ProviderResponseError("unordered Dukascopy candle rows")
        previous = opening
        if not normalized_start <= opening < normalized_end:
            continue
        try:
            open_price, high, low, close, volume = (
                Decimal(str(value)) for value in row[1:]
            )
            bar = BrokerBar(
                symbol=symbol,
                opening_timestamp=opening,
                closing_timestamp=opening + duration,
                is_closed=opening + duration <= normalized_end,
                open=open_price,
                high=high,
                low=low,
                close=close,
                provider_timeframe=_provider_interval(normalized),
                requested_timeframe=normalized,
                price_unit="quote_currency",
                quantity_unit="provider_volume",
                trade_volume=volume,
            )
        except (InvalidOperation, TypeError, ValueError) as error:
            raise _ProviderResponseError("invalid Dukascopy candle values") from error
        bars.append(bar)
    return tuple(bars)


def map_history_page(
    rows: tuple[tuple[object, ...], ...],
    *,
    symbol: str,
    timeframe: str,
    limit: int,
    page_id: str,
    retrieved_at: str,
    start: datetime,
    end: datetime,
    truncated: bool = False,
    requested_timeframe: str | None = None,
) -> BrokerHistoryPage:
    """Map Dukascopy candle rows into a ratified BrokerHistoryPage wire model.

    Args:
        rows: Raw provider candle rows.
        symbol: Exact provider symbol.
        timeframe: Canonical requested timeframe.
        limit: Max requested items.
        page_id: UUID7 string for the history page.
        retrieved_at: UTC timestamp string.
        start: Range start boundary.
        end: Range end boundary.
        truncated: Whether the underlying batch was truncated.
        requested_timeframe: Optional caller requested timeframe.

    Returns:
        Validated BrokerHistoryPage.
    """
    bars = _map_candles(
        rows,
        symbol=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
    )
    records: list[ProviderRecord] = []
    for bar in bars[:limit]:
        vol_str = str(bar.trade_volume) if bar.trade_volume is not None else None
        record_data: JsonObject = {
            "symbol": bar.symbol,
            "opening_timestamp": bar.opening_timestamp.isoformat(),
            "closing_timestamp": bar.closing_timestamp.isoformat(),
            "open": str(bar.open),
            "high": str(bar.high),
            "low": str(bar.low),
            "close": str(bar.close),
            "provider_timeframe": bar.provider_timeframe,
            "requested_timeframe": requested_timeframe or bar.requested_timeframe,
            "trade_volume": vol_str,
            "is_closed": bar.is_closed,
            "provenance": {
                "provider": "dukascopy",
                "offer_side": "BID",
                "research_only": True,
            },
        }
        records.append(
            ProviderRecord(
                provider_id="dukascopy",
                record=record_data,
            )
        )

    return BrokerHistoryPage(
        page_id=page_id,
        requested_count=limit,
        returned_count=len(records),
        is_truncated=truncated or len(bars) > limit,
        retrieved_at=retrieved_at,
        provider_cursor=None,
        records=tuple(records),
    )


__all__: list[str] = [
    "_map_candles",
    "_normalize_timeframe",
    "_provider_interval",
    "map_history_page",
]
