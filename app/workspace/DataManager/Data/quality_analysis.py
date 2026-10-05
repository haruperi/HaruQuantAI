"""Classify stored-bar defects with explicit session hours and history.

Description:
    Classify stored-bar defects with explicit session hours and history.
    The caller supplies records and options explicitly; no provider, database,
    persistent preset, background worker or host-local timezone is assumed.
Purpose:
    FEAT-DATASET-MANAGEMENT: Historical Dataset Management.
Key Capabilities:
    - FR-DATASET-QUALITY-ANALYSIS: Owns this operation's validation and output.
      Associated: `analyze_quality()`.
      Logging: INFO completion with requirement, outcome and bounded count;
      WARNING rejection with a safe code and no record payloads.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data.contracts import (
        BarRecord,
        Catalog,
        Dataset,
    )
    from app.workspace.DataManager.Data.quality_analysis import (
        analyze_quality,
        SessionHours,
    )

    dataset = Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        records=(BarRecord(0, 1, 2, 0, 1),),
    )
    result = analyze_quality(
        dataset,
        interval_ms=60_000,
        session_hours=SessionHours(0, 23),
    )
    if result.is_success:
        data = result.unwrap()
    else:
        error_code = result.error_code
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_quality_analysis.py --no-cov
    ```
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from math import isfinite, trunc
from typing import cast
from zoneinfo import ZoneInfo

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse
from app.workspace.DataManager.Data.contracts import BarRecord, Dataset

WARMUP = 30
SPIKE_MULTIPLIER = 5
PERCENT_SCALE = 1000
MAX_HOUR = 23
SUNDAY = 7
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class ProblemKind(StrEnum):
    """First-matching defect precedence."""

    GAP = "gap"
    LOW = "low"
    HIGH = "high"
    SPIKE = "spike"


@dataclass(frozen=True, slots=True)
class SessionHours:
    """Explicit same-day operating hours in the dataset's named timezone."""

    open_hour: int
    close_hour: int


@dataclass(frozen=True, slots=True)
class QualityProblem:
    """One classified bar and optional inclusive missing-time bounds."""

    index: int
    time_ms: int
    kind: ProblemKind
    gap_from_ms: int | None = None
    gap_to_ms: int | None = None


@dataclass(frozen=True, slots=True)
class QualitySummary:
    """Classified-record counts; percentages use total stored bars as denominator."""

    total_count: int
    problems: tuple[QualityProblem, ...]
    gap_count: int
    ohlc_count: int
    spike_count: int
    gap_percent: float
    ohlc_percent: float
    spike_percent: float


def analyze_quality(
    dataset: Dataset, *, interval_ms: int, session_hours: SessionHours
) -> StandardResponse[QualitySummary]:
    """Evaluate finite stored bars; no inferred exchange calendar or resampling."""
    if dataset.timeframe == "TICK":
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "UNSUPPORTED_TIMEFRAME"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("UNSUPPORTED_TIMEFRAME", "Dataset operation rejected."),
        )
    error = _option_error(interval_ms, session_hours)
    if error is not None:
        logger.warning(
            "Dataset operation rejected", extra={"outcome": "error", "code": error}
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError(error, "Dataset operation rejected."),
        )
    bars = cast("tuple[BarRecord, ...]", dataset.records)
    ranges: deque[float] = deque(maxlen=WARMUP)
    problems: list[QualityProblem] = []
    previous: BarRecord | None = None
    zone = ZoneInfo(dataset.timezone)
    for index, bar in enumerate(bars):
        span = abs(bar.high - bar.low)
        if not isfinite(span) or not isfinite(sum(ranges)):
            logger.warning(
                "Dataset operation rejected",
                extra={"outcome": "error", "code": "INVALID_RANGE"},
            )
            return StandardResponse.failure(
                message="Dataset operation rejected.",
                error=StandardError("INVALID_RANGE", "Dataset operation rejected."),
            )
        try:
            gap = _gap(previous, bar, interval_ms, session_hours, zone)
        except OverflowError:
            logger.warning(
                "Dataset operation rejected",
                extra={"outcome": "error", "code": "INVALID_TIMESTAMP"},
            )
            return StandardResponse.failure(
                message="Dataset operation rejected.",
                error=StandardError("INVALID_TIMESTAMP", "Dataset operation rejected."),
            )
        kind = _kind(bar, ranges, gap is not None)
        if kind is not None:
            begin, end = gap if gap is not None else (None, None)
            problems.append(QualityProblem(index, bar.time_ms, kind, begin, end))
        ranges.append(span)
        previous = bar
    result = _summary(tuple(problems), len(bars))
    logger.info(
        "Dataset operation completed", extra={"outcome": "success", "count": len(bars)}
    )
    return StandardResponse.success(data=result)


def _option_error(interval_ms: int, session_hours: SessionHours) -> str | None:
    if type(interval_ms) is not int or interval_ms <= 0:
        return "INVALID_INTERVAL"
    if not all(
        type(hour) is int and 0 <= hour <= MAX_HOUR
        for hour in (session_hours.open_hour, session_hours.close_hour)
    ):
        return "INVALID_SESSION"
    if session_hours.open_hour > session_hours.close_hour:
        return "UNSUPPORTED_OVERNIGHT_SESSION"
    return None


def _kind(bar: BarRecord, ranges: deque[float], has_gap: bool) -> ProblemKind | None:
    if has_gap:
        return ProblemKind.GAP
    if bar.low > min(bar.high, bar.open, bar.close):
        return ProblemKind.LOW
    if bar.high < max(bar.low, bar.open, bar.close):
        return ProblemKind.HIGH
    if len(ranges) == WARMUP and abs(bar.high - bar.low) >= SPIKE_MULTIPLIER * (
        sum(ranges) / WARMUP
    ):
        return ProblemKind.SPIKE
    return None


def _gap(
    previous: BarRecord | None,
    bar: BarRecord,
    interval: int,
    hours: SessionHours,
    zone: ZoneInfo,
) -> tuple[int, int] | None:
    if previous is None:
        return None
    current_local = (EPOCH + timedelta(milliseconds=bar.time_ms)).astimezone(zone)
    last_local = (EPOCH + timedelta(milliseconds=previous.time_ms)).astimezone(zone)
    if current_local.isoweekday() == SUNDAY:
        return None
    gap: tuple[int, int] | None = None
    if current_local.date() == last_local.date():
        if bar.time_ms - previous.time_ms > interval:
            gap = (
                previous.time_ms + interval,
                max(previous.time_ms + interval, bar.time_ms - interval),
            )
    elif last_local.isoweekday() != SUNDAY and last_local.hour < hours.close_hour:
        closing = last_local.replace(
            hour=hours.close_hour, minute=0, second=0, microsecond=0
        )
        gap = (previous.time_ms + interval, _millis(closing))
    elif current_local.hour > hours.open_hour:
        opening = current_local.replace(
            hour=hours.open_hour, minute=0, second=0, microsecond=0
        )
        gap = (_millis(opening), bar.time_ms - interval)
    return gap if gap is not None and gap[0] <= gap[1] else None


def _millis(value: datetime) -> int:
    return (value.astimezone(UTC) - EPOCH) // timedelta(milliseconds=1)


def _summary(problems: tuple[QualityProblem, ...], count: int) -> QualitySummary:
    gap = sum(problem.kind == ProblemKind.GAP for problem in problems)
    ohlc = sum(
        problem.kind in (ProblemKind.LOW, ProblemKind.HIGH) for problem in problems
    )
    spike = sum(problem.kind == ProblemKind.SPIKE for problem in problems)

    def percent(value: int) -> float:
        return (
            trunc(value * 100 / count * PERCENT_SCALE) / PERCENT_SCALE if count else 0.0
        )

    return QualitySummary(
        count, problems, gap, ohlc, spike, percent(gap), percent(ohlc), percent(spike)
    )


logger = get_logger(__name__).bind(requirement="FR-DATASET-QUALITY-ANALYSIS")
