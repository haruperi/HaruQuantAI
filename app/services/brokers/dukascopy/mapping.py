"""Dukascopy BI5 tick to canonical DTO mapping."""

import struct
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.brokers.contracts import BrokerTick

_RECORD = struct.Struct(">3I2f")


def _map_ticks(
    payload: bytes,
    *,
    symbol: str,
    hour: datetime,
    price_divisor: int,
    limit: int,
) -> tuple[BrokerTick, ...]:
    """Decode validated BI5 records without inventing sequence evidence."""
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
