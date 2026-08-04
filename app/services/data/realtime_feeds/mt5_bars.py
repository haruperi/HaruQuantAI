"""Closed-bar MT5 acquisition for Data-owned real-time streams."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol, cast

from app.services.brokers import get_broker_historical_bars
from app.services.data.contracts import DataError, OHLCVRecord
from app.services.data.sources.composition import _resolve_realtime_session_raw
from app.services.data.time_sessions.timeframes import _get_timeframe_spec_raw
from app.utils import get_logger

logger = get_logger(__name__)

# A newly closed MT5 bar can become visible shortly after its UTC boundary. These
# bounded confirmation reads avoid emitting a partial bar or busy-polling all period.
_BAR_CONFIRMATION_POLL_SECONDS = 0.25
_BAR_CONFIRMATION_ATTEMPTS = 20


class _BarLike(Protocol):
    """Private structural view of the Brokers bar contract."""

    symbol: str
    opening_timestamp: datetime
    closing_timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    price_unit: str
    quantity_unit: str
    trade_volume: Decimal | None
    tick_volume: Decimal | None
    spread: Decimal | None
    spread_unit: str | None


class _PageLike(Protocol):
    """Private structural view of a Brokers page."""

    items: tuple[_BarLike, ...]


class _ResultLike(Protocol):
    """Private structural view of a Brokers result."""

    error: object | None
    data: _PageLike | None


def _require_latest_bar(result: object, request_id: str) -> _BarLike | None:
    """Extract the newest successful Brokers bar.

    Returns:
        Latest bar or ``None`` when MT5 has no closed bar.

    Raises:
        DataError: If Brokers reports a failed read.
    """
    typed_result = cast("_ResultLike", result)
    if typed_result.error is not None or typed_result.data is None:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "mt5_closed_bar_read"},
            request_id=request_id,
        )
    items = tuple(typed_result.data.items)
    return items[-1] if items else None


def _canonical_bar(bar: _BarLike) -> OHLCVRecord:
    """Map one genuine closed Brokers bar to Data's canonical record.

    Returns:
        Canonical closed OHLCV record.

    Raises:
        DataError: If genuine provider volume evidence is absent.
    """
    trade_volume = bar.trade_volume
    tick_volume = bar.tick_volume
    if trade_volume is not None:
        volume = trade_volume
        volume_unit = str(bar.quantity_unit)
    elif tick_volume is not None:
        volume = tick_volume
        volume_unit = "ticks"
    else:
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={"field": "volume"},
        )
    spread = bar.spread
    return OHLCVRecord(
        timestamp=bar.opening_timestamp,
        source="mt5",
        source_symbol=str(bar.symbol),
        source_revision="mt5-live-v1",
        available_at=bar.closing_timestamp,
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=Decimal(volume),
        price_unit=str(bar.price_unit),
        volume_unit=volume_unit,
        spread=spread,
        spread_unit=(str(bar.spread_unit) if spread is not None else None),
    )


def _seconds_until_boundary(now: datetime, timeframe: str) -> float:
    """Return seconds until the next canonical UTC timeframe boundary.

    Returns:
        Positive delay in seconds.
    """
    duration = _get_timeframe_spec_raw(timeframe).duration
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    elapsed = now - epoch
    next_boundary = epoch + (elapsed // duration + 1) * duration
    return max((next_boundary - now).total_seconds(), 0.001)


async def iter_mt5_closed_bars(
    *,
    symbol: str,
    timeframe: str,
    request_id: str,
) -> AsyncGenerator[OHLCVRecord]:
    """Yield the latest closed MT5 bar and every later close exactly once.

    Args:
        symbol: Provider symbol selected in MT5 Market Watch.
        timeframe: Canonical bar timeframe.
        request_id: Canonical request identifier.

    Yields:
        Canonical closed bars in opening-time order.

    Raises:
        DataError: If MT5 fails or returns invalid bar evidence.
    """
    _get_timeframe_spec_raw(timeframe)
    logger.info(
        "Opening Data-owned MT5 closed-bar stream for %s %s",
        symbol,
        timeframe,
    )
    session = await asyncio.to_thread(
        _resolve_realtime_session_raw,
        "mt5",
        request_id,
    )
    adapter = await asyncio.to_thread(session.adapter, request_id)

    async def read_latest() -> _BarLike | None:
        """Read the latest genuine closed provider bar."""
        result = await asyncio.to_thread(
            session.run,
            get_broker_historical_bars(
                adapter,
                symbol,
                timeframe,
                limit=1,
            ),
            request_id,
        )
        return _require_latest_bar(result, request_id)

    latest = await read_latest()
    last_open = None
    if latest is not None:
        last_open = latest.opening_timestamp
        yield _canonical_bar(latest)

    while True:
        await asyncio.sleep(_seconds_until_boundary(datetime.now(UTC), timeframe))
        for _ in range(_BAR_CONFIRMATION_ATTEMPTS):
            candidate = await read_latest()
            if candidate is not None:
                opening = candidate.opening_timestamp
                if last_open is None or opening > last_open:
                    last_open = opening
                    yield _canonical_bar(candidate)
                    break
            await asyncio.sleep(_BAR_CONFIRMATION_POLL_SECONDS)


__all__: list[str] = []
