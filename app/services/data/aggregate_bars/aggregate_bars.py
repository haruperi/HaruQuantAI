"""Closed-bar aggregation for ``FEAT-DATA-AGGREGATE_BARS``.

The feature aggregates only committed bar-shaped versions whose source timeframe is
stored explicitly. Incomplete target buckets are omitted rather than padded, and
session-boundary aggregation fails closed until the Data/Catalogue contract carries
an unambiguous Catalogue session identity.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from app.contracts.common.models import ProblemDetails, Timeframe
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    AggregateBarsRequest,
    AggregateBarsSuccess,
    Bar,
)
from app.kernel.identity import generate_uuid7
from app.kernel.time import format_utc_timestamp, parse_utc_timestamp
from app.services.data.aggregate_bars.config import AggregateBarsConfig

if TYPE_CHECKING:
    from app.contracts.data.internal import DataSeriesStoreCapability

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_WEEK_EPOCH = datetime(1970, 1, 5, tzinfo=UTC)


def _failure(request_id: str, code: str, detail: str) -> DataFailure:
    """Build one stable aggregation failure.

    Args:
        request_id: Public request identity.
        code: Closed Data failure code.
        detail: Safe failure detail.

    Returns:
        Contract-native Data failure.
    """
    return DataFailure(
        request_id=request_id,
        code=code,  # type: ignore[arg-type]
        problem=ProblemDetails(
            status=422,
            code=code,
            detail=detail,
            request_id=request_id,
        ),
    )


def _duration(timeframe: Timeframe) -> timedelta:
    """Convert fixed-length timeframes into exact timedeltas.

    Args:
        timeframe: Public timeframe value.

    Returns:
        Exact fixed duration.

    Raises:
        ValueError: If the timeframe requires calendar-aware month semantics.
    """
    if timeframe.unit == "MINUTE":
        return timedelta(minutes=timeframe.multiple)
    if timeframe.unit == "DAY":
        return timedelta(days=timeframe.multiple)
    if timeframe.unit == "WEEK":
        return timedelta(weeks=timeframe.multiple)
    raise ValueError("MONTH aggregation requires calendar-aware boundaries")


def _bucket_start(value: datetime, timeframe: Timeframe) -> datetime:
    """Return the canonical UTC bucket start for one observation.

    Args:
        value: Aware UTC bar opening timestamp.
        timeframe: Target fixed-length timeframe.

    Returns:
        Canonical UTC bucket start.
    """
    duration = _duration(timeframe)
    anchor = _WEEK_EPOCH if timeframe.unit == "WEEK" else _EPOCH
    elapsed = value - anchor
    bucket = int(elapsed.total_seconds() // duration.total_seconds())
    return anchor + bucket * duration


def _aggregate_group(group: tuple[Bar, ...], timestamp: datetime, sequence: int) -> Bar:
    """Aggregate one complete source-bar group.

    Args:
        group: Chronologically ordered source bars.
        timestamp: Target bar opening timestamp.
        sequence: Target source sequence.

    Returns:
        One deterministic OHLCV bar.
    """
    spreads = tuple(bar.spread_ticks for bar in group)
    close_spread = spreads[-1] if spreads and all(item is not None for item in spreads) else None
    return Bar(
        timestamp=format_utc_timestamp(timestamp),
        open=group[0].open,
        high=str(max(Decimal(bar.high) for bar in group)),
        low=str(min(Decimal(bar.low) for bar in group)),
        close=group[-1].close,
        volume=str(sum((Decimal(bar.volume) for bar in group), Decimal(0))),
        spread_ticks=close_spread,
        source_sequence=sequence,
        flags=0,
    )


def aggregate_closed_bars(
    bars: tuple[Bar, ...],
    *,
    source_timeframe: Timeframe,
    target_timeframe: Timeframe,
    max_output_bars: int,
) -> tuple[Bar, ...]:
    """Aggregate complete UTC-aligned source buckets without lookahead.

    Args:
        bars: Committed source bars.
        source_timeframe: Exact cadence of the source version.
        target_timeframe: Requested coarser cadence.
        max_output_bars: Hard result bound.

    Returns:
        Complete target bars; incomplete buckets are omitted.

    Raises:
        ValueError: If timeframes are unsupported or not an exact multiple.
    """
    source_delta = _duration(source_timeframe)
    target_delta = _duration(target_timeframe)
    source_seconds = int(source_delta.total_seconds())
    target_seconds = int(target_delta.total_seconds())
    if target_seconds < source_seconds or target_seconds % source_seconds:
        raise ValueError("target timeframe must be an exact multiple of source timeframe")
    expected = target_seconds // source_seconds
    ordered = tuple(sorted(bars, key=lambda bar: (bar.timestamp, bar.source_sequence)))
    groups: dict[datetime, list[Bar]] = defaultdict(list)
    for bar in ordered:
        opened_at = parse_utc_timestamp(bar.timestamp)
        source_bucket = _bucket_start(opened_at, source_timeframe)
        if opened_at != source_bucket:
            raise ValueError("source bar timestamp is not aligned to its declared timeframe")
        groups[_bucket_start(opened_at, target_timeframe)].append(bar)
    output: list[Bar] = []
    for timestamp in sorted(groups):
        group = tuple(groups[timestamp])
        if len(group) != expected:
            continue
        expected_times = tuple(timestamp + source_delta * index for index in range(expected))
        actual_times = tuple(parse_utc_timestamp(bar.timestamp) for bar in group)
        if actual_times != expected_times:
            continue
        output.append(_aggregate_group(group, timestamp, len(output)))
        if len(output) > max_output_bars:
            raise ValueError("aggregation exceeds configured output bound")
    return tuple(output)


def _hash_bars(bars: tuple[Bar, ...]) -> str:
    payload = [bar.model_dump(mode="json") for bar in bars]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class AggregateBarsService:
    """Capability implementation for deterministic closed-bar aggregation."""

    def __init__(
        self,
        store: DataSeriesStoreCapability,
        config: AggregateBarsConfig,
    ) -> None:
        """Initialize with immutable storage and output bounds.

        Args:
            store: Declared Data series-store capability.
            config: Trusted aggregation configuration.
        """
        self._store = store
        self._config = config

    async def aggregate_bars(
        self,
        request: AggregateBarsRequest,
    ) -> AggregateBarsSuccess | DataFailure:
        """Validate a timeframe or aggregate one committed bar version.

        Args:
            request: Operation-discriminated aggregation request.

        Returns:
            Contract-native success or deterministic failure.
        """
        if request.operation == "VALIDATE_TIMEFRAME":
            assert request.target_timeframe is not None
            try:
                _duration(request.target_timeframe)
            except ValueError as error:
                return _failure(
                    request.request_id,
                    "DATA_TIMEFRAME_UNSUPPORTED",
                    str(error),
                )
            return AggregateBarsSuccess(request_id=request.request_id)

        assert request.spec is not None
        if request.spec.alignment_origin == "SESSION_BOUNDARY":
            return _failure(
                request.request_id,
                "DATA_ALIGNMENT_INCOMPATIBLE",
                (
                    "SESSION_BOUNDARY requires a Catalogue session identity, but "
                    "AggregationSpec v1 carries only session_version_id"
                ),
            )
        if request.spec.gap_policy == "SYNTHETIC_GAP":
            return _failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "Synthetic gap bars are not emitted without explicit provenance fields",
            )
        snapshot = await self._store.get_snapshot(request.spec.source_version_id)
        if snapshot is None:
            return _failure(request.request_id, "DATA_NOT_FOUND", "Source version is unavailable")
        if snapshot.timeframe is None:
            return _failure(
                request.request_id,
                "DATA_PRECISION_UNAVAILABLE",
                "Source version does not carry a declared bar timeframe",
            )
        bars = await self._store.read_bars(request.spec.source_version_id)
        if bars is None:
            return _failure(
                request.request_id,
                "DATA_ALIGNMENT_INCOMPATIBLE",
                "Aggregation requires bar-shaped source evidence",
            )
        try:
            derived = aggregate_closed_bars(
                bars,
                source_timeframe=snapshot.timeframe,
                target_timeframe=request.spec.target_timeframe,
                max_output_bars=self._config.max_output_bars,
            )
        except ValueError as error:
            code = (
                "DATA_TIMEFRAME_UNSUPPORTED"
                if "MONTH" in str(error) or "timeframe" in str(error)
                else "DATA_VALIDATION_FAILED"
            )
            return _failure(request.request_id, code, str(error))
        version_id = generate_uuid7()
        await self._store.put_bars(
            version_id,
            derived,
            content_hash=_hash_bars(derived),
            timeframe=request.spec.target_timeframe,
        )
        return AggregateBarsSuccess(
            request_id=request.request_id,
            spec=request.spec,
            derived_version_id=version_id,
        )


async def _demo() -> None:
    """Demonstrate pure M1-to-M2 closed-bar aggregation."""
    bars = (
        Bar(
            timestamp="2026-01-01T00:00:00.000000Z",
            open="1",
            high="2",
            low="1",
            close="1.5",
            volume="2",
            source_sequence=0,
            flags=0,
        ),
        Bar(
            timestamp="2026-01-01T00:01:00.000000Z",
            open="1.5",
            high="3",
            low="1.4",
            close="2",
            volume="3",
            source_sequence=1,
            flags=0,
        ),
    )
    print(
        [
            bar.model_dump(mode="json")
            for bar in aggregate_closed_bars(
                bars,
                source_timeframe=Timeframe(unit="MINUTE", multiple=1),
                target_timeframe=Timeframe(unit="MINUTE", multiple=2),
                max_output_bars=10,
            )
        ]
    )


if __name__ == "__main__":
    asyncio.run(_demo())
