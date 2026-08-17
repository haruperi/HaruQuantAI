"""Point-in-time evidence assembly for canonical Simulation evaluation."""

from __future__ import annotations

import inspect
from bisect import bisect_right
from collections.abc import Awaitable, Callable
from datetime import datetime
from itertools import pairwise
from typing import Any, cast

from app.services.data import build_market_dataset


class _PointInTimeDatasetCursor:
    """Materialize scheduler-visible prefixes without repeated validation."""

    def __init__(self, dataset: object) -> None:
        """Index one already validated immutable source dataset.

        Args:
            dataset: Complete Data-owned ``MarketDataset`` admitted for the run.
        """
        self._dataset = dataset
        self._records = tuple(cast("Any", dataset).records)
        self._timestamps = tuple(record.timestamp for record in self._records)
        self._available_at = tuple(record.available_at for record in self._records)
        self._prefix_ordered = all(
            left <= right
            for values in (self._timestamps, self._available_at)
            for left, right in pairwise(values)
        )
        self._visible_count = -1
        self._visible_dataset: object | None = None

    def build(self, decision_at: datetime) -> object:
        """Return the exact evidence visible at one scheduler instant.

        Args:
            decision_at: Current scheduler decision instant.

        Returns:
            A Data-owned dataset containing no future evidence.

        Raises:
            ValueError: If no source evidence is visible.
        """
        if not self._prefix_ordered:
            return build_point_in_time_dataset(self._dataset, decision_at)
        visible_count = min(
            bisect_right(self._timestamps, decision_at),
            bisect_right(self._available_at, decision_at),
        )
        if visible_count == 0:
            raise ValueError("no market evidence is available at decision_at")
        if visible_count == self._visible_count and self._visible_dataset is not None:
            return self._visible_dataset
        records = self._records[:visible_count]
        quality_report = cast("Any", self._dataset).quality_report.model_copy(
            update={"record_count": visible_count, "checked_count": visible_count}
        )
        self._visible_dataset = cast("Any", self._dataset).model_copy(
            update={
                "records": records,
                "start": records[0].timestamp,
                "end": records[-1].timestamp,
                "available_at": records[-1].available_at,
                "record_count": visible_count,
                "quality_report": quality_report,
            }
        )
        self._visible_count = visible_count
        return self._visible_dataset


def build_point_in_time_dataset(dataset: object, decision_at: datetime) -> object:
    """Return only records safely available at one scheduler instant.

    Args:
        dataset: Immutable Data-owned ``MarketDataset`` value.
        decision_at: Current scheduler decision instant.

    Returns:
        A Data-owned dataset containing no future timestamp or availability.

    Raises:
        ValueError: If no source evidence is available at the decision instant.
    """
    records = tuple(
        record
        for record in cast("Any", dataset).records
        if record.timestamp <= decision_at and record.available_at <= decision_at
    )
    if not records:
        raise ValueError("no market evidence is available at decision_at")
    material = cast("Any", dataset).model_dump(mode="python", warnings=False)
    quality_report = cast("Any", dataset).quality_report.model_copy(
        update={"record_count": len(records), "checked_count": len(records)}
    )
    material.update(
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=max(record.available_at for record in records),
        record_count=len(records),
        quality_report=quality_report,
    )
    return build_market_dataset(**material)


def build_evaluation_latency(
    started_at: datetime | None, completed_at: datetime | None
) -> float | None:
    """Return scheduler latency only when both clock edges are captured.

    Args:
        started_at: Scheduler instant before evaluation, when captured.
        completed_at: Scheduler instant after evaluation, when captured.

    Returns:
        Non-negative elapsed seconds, or ``None`` for missing evidence.

    Raises:
        ValueError: If the captured edges move scheduler time backwards.
    """
    if started_at is None or completed_at is None:
        return None
    elapsed = (completed_at - started_at).total_seconds()
    if elapsed < 0:
        raise ValueError("evaluation clock edges are reversed")
    return elapsed


async def run_point_in_time_evaluation(
    dataset: object,
    decision_at: datetime,
    cycle: Callable[[object, datetime], object | Awaitable[object]],
    *,
    point_in_time_cursor: _PointInTimeDatasetCursor | None = None,
) -> object:
    """Invoke one shared Trading cycle with scheduler-bounded evidence.

    Args:
        dataset: Complete immutable source dataset.
        decision_at: Current scheduler instant.
        cycle: Injected owner composition invoking Trading's public cycle.
        point_in_time_cursor: Optional run-scoped validated-prefix cache.

    Returns:
        The exact shared Trading-cycle result.
    """
    visible = (
        point_in_time_cursor.build(decision_at)
        if point_in_time_cursor is not None
        else build_point_in_time_dataset(dataset, decision_at)
    )
    result = cycle(visible, decision_at)
    if inspect.isawaitable(result):
        return await cast("Awaitable[object]", result)
    return result


__all__ = [
    "build_evaluation_latency",
    "build_point_in_time_dataset",
    "run_point_in_time_evaluation",
]
