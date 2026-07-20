"""Dukascopy BI5 tick to canonical DTO mapping."""

import struct
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.brokers.contracts import BrokerBar, BrokerTick

_RECORD = struct.Struct(">3I2f")


def _map_ticks(
    payload: bytes,
    *,
    symbol: str,
    hour: datetime,
    price_divisor: int,
    limit: int,
) -> tuple[BrokerTick, ...]:
    """Decode validated BI5 records without inventing sequence evidence.

    Returns:
        Bounded chronological canonical ticks.

    Raises:
        ValueError: If payload shape or hour timestamp is invalid.
    """
    if len(payload) % _RECORD.size:
        raise ValueError("malformed Dukascopy BI5 record length")
    if hour.tzinfo is None or hour.utcoffset() is None:
        raise ValueError("Dukascopy hour must be timezone-aware")
    base = hour.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    ticks: list[BrokerTick] = []
    for offset in range(0, len(payload), _RECORD.size):
        milliseconds, ask, bid, ask_volume, bid_volume = _RECORD.unpack_from(
            payload, offset
        )
        timestamp = base + timedelta(milliseconds=milliseconds)
        ticks.append(
            BrokerTick(
                symbol=symbol,
                event_timestamp=timestamp,
                provider_receipt_timestamp=timestamp,
                price_unit="quote_currency",
                quantity_unit="provider_volume",
                tick_type="QUOTE",
                bid=Decimal(bid) / price_divisor,
                ask=Decimal(ask) / price_divisor,
                bid_quantity=Decimal(str(bid_volume)),
                ask_quantity=Decimal(str(ask_volume)),
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
        )
        for opening, prices in sorted(buckets.items())
    )
