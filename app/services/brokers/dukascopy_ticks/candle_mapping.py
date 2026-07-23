"""Map Dukascopy web-chart candle rows to canonical broker bars."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation

from app.services.brokers.contracts import BrokerBar
from app.services.brokers.contracts.protocols import _ProviderResponseError

_TIMEFRAMES = {
    "M1": ("1MIN", timedelta(minutes=1)),
    "M5": ("5MIN", timedelta(minutes=5)),
    "M15": ("15MIN", timedelta(minutes=15)),
    "M30": ("30MIN", timedelta(minutes=30)),
    "H1": ("1HOUR", timedelta(hours=1)),
}
_CANDLE_FIELD_COUNT = 6


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
        return _TIMEFRAMES[timeframe.upper()][0]
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
    normalized = timeframe.upper()
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


__all__: list[str] = []
