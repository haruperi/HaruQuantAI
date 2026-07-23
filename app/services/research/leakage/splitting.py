"""Deterministic chronological splitting for Research evidence."""

from __future__ import annotations

import hashlib
from datetime import UTC

import pandas as pd

from app.services.research.contracts import TimeSplitResult
from app.utils import ValidationError, canonical_json, logger

_MIN_PARTITION_ROWS = 1


def enforce_time_split(
    data: pd.DataFrame,
    *,
    train_fraction: float,
    validation_fraction: float,
    gap_rows: int = 0,
) -> TimeSplitResult:
    """Split a UTC frame into chronological non-overlapping partitions.

    Rows in each requested gap are intentionally excluded. Inputs are not mutated.

    Args:
        data: Monotonic UTC-indexed feature frame.
        train_fraction: Fraction assigned to training before the first gap.
        validation_fraction: Fraction assigned to validation before the second gap.
        gap_rows: Non-negative embargo rows between partitions.

    Returns:
        Detached partitions, UTC boundaries, and deterministic split hash.

    Raises:
        ValidationError: If fractions, index, gap, or sample size is invalid.
    """
    logger.info("Enforcing chronological Research split")
    if not isinstance(data.index, pd.DatetimeIndex) or data.index.tz is None:
        raise ValidationError("RES_INPUT_INVALID", "UTC_TIME_INDEX_REQUIRED")
    if not data.index.is_monotonic_increasing or data.index.has_duplicates:
        raise ValidationError("RES_INPUT_INVALID", "ORDERED_UNIQUE_TIME_REQUIRED")
    if (
        train_fraction <= 0
        or validation_fraction <= 0
        or train_fraction + validation_fraction >= 1
    ):
        raise ValidationError("RES_INPUT_INVALID", "INVALID_SPLIT_FRACTIONS")
    if gap_rows < 0:
        raise ValidationError("RES_INPUT_INVALID", "INVALID_SPLIT_GAP")
    train_end = int(len(data) * train_fraction)
    validation_start = train_end + gap_rows
    validation_end = validation_start + int(len(data) * validation_fraction)
    test_start = validation_end + gap_rows
    train = data.iloc[:train_end].copy(deep=True)
    validation = data.iloc[validation_start:validation_end].copy(deep=True)
    test = data.iloc[test_start:].copy(deep=True)
    if any(len(part) < _MIN_PARTITION_ROWS for part in (train, validation, test)):
        raise ValidationError("RES_INSUFFICIENT_DATA", "EMPTY_TIME_PARTITION")
    boundaries = {
        "train_start": train.index[0].to_pydatetime().astimezone(UTC),
        "train_end": train.index[-1].to_pydatetime().astimezone(UTC),
        "validation_start": validation.index[0].to_pydatetime().astimezone(UTC),
        "validation_end": validation.index[-1].to_pydatetime().astimezone(UTC),
        "test_start": test.index[0].to_pydatetime().astimezone(UTC),
        "test_end": test.index[-1].to_pydatetime().astimezone(UTC),
    }
    payload = {
        "rows": len(data),
        "train_fraction": train_fraction,
        "validation_fraction": validation_fraction,
        "gap_rows": gap_rows,
        "boundaries": {key: value.isoformat() for key, value in boundaries.items()},
    }
    split_hash = hashlib.sha256(canonical_json(payload).encode()).hexdigest()
    return TimeSplitResult(train, validation, test, boundaries, split_hash)


__all__ = ("enforce_time_split",)
