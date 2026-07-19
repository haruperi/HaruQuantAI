"""Leakage-safe chronological split construction."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.services.optimization.validation.contracts import (
    SplitMode,
    TimeSeriesSplit,
    WalkForwardRequest,
)
from app.utils import logger


def _boundary(observations: tuple[datetime, ...], index: int) -> datetime:
    """Resolve one half-open observation boundary.

    Args:
        observations: Equally spaced UTC observation times.
        index: Half-open boundary index.

    Returns:
        Existing observation time or one cadence beyond the last observation.
    """
    logger.debug("Resolving Optimization observation boundary")
    if index < len(observations):
        return observations[index]
    cadence = observations[1] - observations[0]
    return observations[-1] + timedelta(seconds=cadence.total_seconds())


def build_time_series_splits(
    request: WalkForwardRequest,
) -> tuple[TimeSeriesSplit, ...]:
    """Build rolling or growing-train half-open walk-forward folds.

    Args:
        request: Validated walk-forward request.

    Returns:
        Ordered leakage-safe folds.

    Raises:
        ValueError: If the observations cannot produce the minimum fold count.
    """
    logger.info("Building leakage-safe Optimization time-series splits")
    effective_embargo = max(
        request.embargo_bars,
        request.average_trade_duration_bars or 0,
    )
    observations = request.observation_times
    raw_train_end = request.train_bars
    splits: list[TimeSeriesSplit] = []
    while True:
        test_start = raw_train_end + effective_embargo
        test_end = test_start + request.test_bars
        if test_end > len(observations):
            break
        effective_train_end = raw_train_end - request.purge_bars
        train_start = (
            raw_train_end - request.train_bars
            if request.mode is SplitMode.ROLLING
            else 0
        )
        fold_index = len(splits)
        splits.append(
            TimeSeriesSplit(
                fold_id=f"fold-{fold_index:04d}",
                train_start_index=train_start,
                train_end_index=effective_train_end,
                test_start_index=test_start,
                test_end_index=test_end,
                train_start=_boundary(observations, train_start),
                train_end=_boundary(observations, effective_train_end),
                test_start=_boundary(observations, test_start),
                test_end=_boundary(observations, test_end),
                purge_bars=request.purge_bars,
                embargo_bars=effective_embargo,
                leakage_prevented=True,
            )
        )
        raw_train_end += request.step_bars
    if len(splits) < request.minimum_fold_count:
        raise ValueError("observations cannot satisfy minimum_fold_count")
    return tuple(splits)


__all__ = ["build_time_series_splits"]
