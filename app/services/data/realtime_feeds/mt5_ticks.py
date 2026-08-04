"""Genuine MT5 tick acquisition for Data-owned real-time streams."""

from __future__ import annotations

import asyncio
from collections import Counter
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol, cast

from app.services.brokers import get_broker_ticks
from app.services.data.contracts import DataError, TickRecord
from app.services.data.sources.composition import _resolve_realtime_session_raw
from app.utils import get_logger

logger = get_logger(__name__)

# MT5's Python integration is pull-based. A short bounded interval minimizes latency,
# while the overlapping cursor below prevents a scheduling pause from silently losing
# ticks. Saturating one batch is treated as a gap instead of presumed complete.
_MT5_TICK_POLL_INTERVAL_SECONDS = 0.05
_MT5_TICK_BATCH_LIMIT = 10_000


class _TickLike(Protocol):
    """Private structural view of the Brokers tick contract."""

    symbol: str
    event_timestamp: datetime
    provider_receipt_timestamp: datetime
    price_unit: str
    bid: Decimal | None
    ask: Decimal | None
    last_price: Decimal | None
    bid_quantity: Decimal | None
    ask_quantity: Decimal | None


class _PageLike(Protocol):
    """Private structural view of a Brokers page."""

    items: tuple[_TickLike, ...]


class _ResultLike(Protocol):
    """Private structural view of a Brokers result."""

    error: object | None
    data: _PageLike | None


def _signature(tick: _TickLike) -> tuple[object, ...]:
    """Return the provider fields used for overlap deduplication.

    Returns:
        Stable tick signature excluding local receipt time.
    """
    return (
        tick.event_timestamp,
        tick.bid,
        tick.ask,
        tick.last_price,
        tick.bid_quantity,
        tick.ask_quantity,
    )


def _canonical_tick(tick: _TickLike) -> TickRecord:
    """Map one Brokers-owned MT5 tick into Data's canonical record.

    Returns:
        Canonical provider-sourced tick.
    """
    return TickRecord(
        timestamp=tick.event_timestamp,
        source="mt5",
        source_symbol=str(tick.symbol),
        source_revision="mt5-live-v1",
        available_at=tick.provider_receipt_timestamp,
        bid=tick.bid,
        ask=tick.ask,
        last=tick.last_price,
        volume=None,
        price_unit=str(tick.price_unit),
        volume_unit=None,
    )


def _require_items(result: object, request_id: str) -> tuple[_TickLike, ...]:
    """Extract one successful Brokers page without crossing error contracts.

    Returns:
        Immutable page items.

    Raises:
        DataError: If Brokers did not return a successful tick page.
    """
    typed_result = cast("_ResultLike", result)
    if typed_result.error is not None or typed_result.data is None:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "mt5_tick_read"},
            request_id=request_id,
        )
    return tuple(typed_result.data.items)


def _unseen_ticks(
    items: tuple[_TickLike, ...],
    cursor: datetime,
    cursor_counts: Counter[tuple[object, ...]],
) -> tuple[tuple[_TickLike, ...], datetime, Counter[tuple[object, ...]]]:
    """Remove only overlap ticks already emitted at the cursor timestamp.

    Returns:
        New ticks, advanced cursor, and the multiplicities at that cursor.
    """
    starting_cursor = cursor
    prior_counts = cursor_counts.copy()
    encountered: Counter[tuple[object, ...]] = Counter()
    unseen: list[_TickLike] = []
    for item in items:
        timestamp = item.event_timestamp
        signature = _signature(item)
        if timestamp < cursor:
            continue
        if timestamp == starting_cursor:
            encountered[signature] += 1
            if encountered[signature] <= prior_counts[signature]:
                continue
        elif timestamp > cursor:
            cursor = timestamp
            cursor_counts = Counter()
        cursor_counts[signature] += 1
        unseen.append(item)
    return tuple(unseen), cursor, cursor_counts


async def iter_mt5_ticks(
    *,
    symbol: str,
    request_id: str,
    poll_interval_seconds: float = _MT5_TICK_POLL_INTERVAL_SECONDS,
    batch_limit: int = _MT5_TICK_BATCH_LIMIT,
) -> AsyncGenerator[TickRecord]:
    """Yield every available MT5 tick after subscription begins.

    Args:
        symbol: Provider symbol selected in MT5 Market Watch.
        request_id: Canonical request identifier.
        poll_interval_seconds: Positive delay between empty reads.
        batch_limit: Positive maximum ticks accepted per provider read.

    Yields:
        Ordered canonical ticks.

    Raises:
        DataError: If MT5 fails or a saturated batch makes completeness uncertain.
        ValueError: If polling bounds are invalid.
    """
    if poll_interval_seconds <= 0 or batch_limit <= 0:
        raise ValueError("MT5 tick stream bounds must be positive")
    logger.info("Opening Data-owned MT5 tick stream for %s", symbol)
    session = await asyncio.to_thread(
        _resolve_realtime_session_raw,
        "mt5",
        request_id,
    )
    adapter = await asyncio.to_thread(session.adapter, request_id)

    initial_result = await asyncio.to_thread(
        session.run,
        get_broker_ticks(adapter, symbol, limit=1),
        request_id,
    )
    initial_items = _require_items(initial_result, request_id)
    cursor = datetime.now(UTC)
    cursor_counts: Counter[tuple[object, ...]] = Counter()
    if initial_items:
        latest = initial_items[-1]
        cursor = latest.event_timestamp
        cursor_counts[_signature(latest)] += 1
        yield _canonical_tick(latest)

    while True:
        end = datetime.now(UTC)
        if end <= cursor:
            await asyncio.sleep(poll_interval_seconds)
            continue
        result = await asyncio.to_thread(
            session.run,
            get_broker_ticks(
                adapter,
                symbol,
                start_time=cursor,
                end_time=end,
                limit=batch_limit,
            ),
            request_id,
        )
        items = tuple(
            sorted(
                _require_items(result, request_id),
                key=lambda item: item.event_timestamp,
            )
        )
        unseen, cursor, cursor_counts = _unseen_ticks(items, cursor, cursor_counts)
        for item in unseen:
            yield _canonical_tick(item)
        if len(items) >= batch_limit:
            raise DataError(
                "DATA_DROPPED",
                safe_details={
                    "operation": "mt5_tick_stream",
                    "reason": "batch_saturated",
                },
                request_id=request_id,
            )
        if not unseen:
            await asyncio.sleep(poll_interval_seconds)


__all__: list[str] = []
