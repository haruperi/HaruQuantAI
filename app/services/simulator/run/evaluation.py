"""Point-in-time evidence assembly for canonical Simulation evaluation."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any, cast

from app.services.data import build_market_dataset


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
) -> object:
    """Invoke one shared Trading cycle with scheduler-bounded evidence.

    Args:
        dataset: Complete immutable source dataset.
        decision_at: Current scheduler instant.
        cycle: Injected owner composition invoking Trading's public cycle.

    Returns:
        The exact shared Trading-cycle result.
    """
    visible = build_point_in_time_dataset(dataset, decision_at)
    result = cycle(visible, decision_at)
    if inspect.isawaitable(result):
        return await cast("Awaitable[object]", result)
    return result


__all__ = [
    "build_evaluation_latency",
    "build_point_in_time_dataset",
    "run_point_in_time_evaluation",
]
