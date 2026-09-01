"""Dukascopy web-chart tick to canonical DTO mapping."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.brokers.canonical_contracts import BrokerBar, BrokerTick
from app.services.brokers.dukascopy.transport import _ProviderResponseError

_TICK_FIELD_COUNT = 5


def _map_ticks(
    rows: tuple[tuple[object, ...], ...],
    *,
    symbol: str,
    start: datetime,
    end: datetime,
    limit: int,
) -> tuple[BrokerTick, ...]:
    """Map validated web-chart rows without inventing sequence evidence.

    Args:
        rows: Raw provider tick rows.
        symbol: Value supplied to the operation.
        start: Inclusive requested range boundary.
        end: Exclusive requested range boundary.
        limit: Value supplied to the operation.

    Returns:
        Bounded chronological canonical ticks.

    Raises:
        ValueError: If the requested range is invalid.
        _ProviderResponseError: If a provider row is malformed or unordered.
    """
    if (
        start.tzinfo is None
        or start.utcoffset() is None
        or end.tzinfo is None
        or end.utcoffset() is None
        or start >= end
    ):
        raise ValueError("ordered timezone-aware Dukascopy tick range is required")
    ticks: list[BrokerTick] = []
    previous: datetime | None = None
    for row in rows:
        if (
            len(row) < _TICK_FIELD_COUNT
            or isinstance(row[0], bool)
            or not isinstance(row[0], int)
        ):
            raise _ProviderResponseError("malformed Dukascopy tick row")
        try:
            timestamp = datetime.fromtimestamp(row[0] / 1000, start.tzinfo)
            bid = Decimal(str(row[1]))
            ask = Decimal(str(row[2]))
            bid_volume = Decimal(str(row[3])) / Decimal(1_000_000)
            ask_volume = Decimal(str(row[4])) / Decimal(1_000_000)
        except (TypeError, ValueError, ArithmeticError) as error:
            raise _ProviderResponseError("malformed Dukascopy tick values") from error
        if not start <= timestamp < end:
            continue
        if previous is not None and timestamp < previous:
            raise _ProviderResponseError("unordered Dukascopy tick rows")
        previous = timestamp
        ticks.append(
            BrokerTick(
                symbol=symbol,
                event_timestamp=timestamp,
                provider_receipt_timestamp=timestamp,
                price_unit="quote_currency",
                quantity_unit="provider_volume",
                tick_type="QUOTE",
                bid=bid,
                ask=ask,
                bid_quantity=bid_volume,
                ask_quantity=ask_volume,
            )
        )
        if len(ticks) == limit:
            break
    return tuple(ticks)


def _aggregate_bars(
    ticks: tuple[BrokerTick, ...],
    *,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
) -> tuple[BrokerBar, ...]:
    """Aggregate genuine Dukascopy quote ticks into local midpoint bars.

    Args:
        ticks: Genuine canonical quote ticks to aggregate.
        symbol: Exact provider-native symbol.
        timeframe: Explicit supported bar interval.
        start: Inclusive UTC range boundary.
        end: Exclusive UTC range boundary.

    Returns:
        Chronological closed midpoint OHLC bars with tick-volume evidence.

    Raises:
        ValueError: If the range or timeframe is unsupported.
    """
    durations = {
        "M1": timedelta(minutes=1),
        "M5": timedelta(minutes=5),
        "M15": timedelta(minutes=15),
        "M30": timedelta(minutes=30),
        "H1": timedelta(hours=1),
    }
    normalized = timeframe.upper()
    try:
        duration = durations[normalized]
    except KeyError as error:
        raise ValueError("unsupported Dukascopy aggregation timeframe") from error
    if (
        start.tzinfo is None
        or start.utcoffset() is None
        or end.tzinfo is None
        or end.utcoffset() is None
        or start >= end
    ):
        raise ValueError("ordered UTC-aware Dukascopy bar range is required")

    seconds = int(duration.total_seconds())
    buckets: dict[datetime, list[Decimal]] = {}
    for tick in ticks:
        if not start <= tick.event_timestamp < end:
            continue
        if tick.bid is not None and tick.ask is not None:
            price = (tick.bid + tick.ask) / Decimal(2)
        elif tick.last_price is not None:
            price = tick.last_price
        elif tick.bid is not None:
            price = tick.bid
        elif tick.ask is not None:
            price = tick.ask
        else:  # pragma: no cover - BrokerTick rejects price-free instances.
            continue
        epoch = int(tick.event_timestamp.timestamp())
        opening = datetime.fromtimestamp(epoch - (epoch % seconds), UTC)
        buckets.setdefault(opening, []).append(price)

    return tuple(
        BrokerBar(
            symbol=symbol,
            opening_timestamp=opening,
            closing_timestamp=opening + duration,
            is_closed=opening + duration <= end,
            open=prices[0],
            high=max(prices),
            low=min(prices),
            close=prices[-1],
            provider_timeframe="TICK",
            requested_timeframe=normalized,
            price_unit="quote_currency",
            quantity_unit="provider_volume",
            tick_volume=Decimal(len(prices)),
            spread=Decimal(0),
            spread_unit="price_unit",
        )
        for opening, prices in sorted(buckets.items())
    )


__all__: list[str] = [
    "_aggregate_bars",
    "_map_ticks",
]
