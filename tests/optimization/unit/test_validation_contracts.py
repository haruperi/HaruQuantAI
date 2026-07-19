"""Tests for walk-forward validation contracts."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta

import pytest
from app.services.optimization.validation import (
    SplitMode,
    WalkForwardRequest,
    WalkForwardResult,
    build_time_series_splits,
)
from pydantic import ValidationError
from tests.optimization.unit.test_search_contracts import search_request


def walk_forward_request(**overrides) -> WalkForwardRequest:
    """Build a valid three-fold walk-forward request."""
    start = datetime(2025, 1, 1, tzinfo=UTC)
    payload = {
        "search": search_request(),
        "mode": "rolling",
        "observation_times": tuple(
            start + timedelta(hours=index) for index in range(11)
        ),
        "train_bars": 3,
        "test_bars": 2,
        "step_bars": 2,
        "purge_bars": 1,
        "embargo_bars": 1,
        "average_trade_duration_bars": 1,
        "minimum_fold_count": 3,
    }
    payload.update(overrides)
    return WalkForwardRequest.model_validate(payload)


def test_split_mode_excludes_custom_and_cpcv() -> None:
    """Only the three approved chronological modes exist."""
    assert {item.value for item in SplitMode} == {"rolling", "anchored", "expanding"}


def test_walk_forward_request_validates_windows() -> None:
    """Unequally spaced timestamps fail before split construction."""
    times = list(walk_forward_request().observation_times)
    times[-1] += timedelta(minutes=1)
    with pytest.raises(ValidationError, match="equally spaced"):
        walk_forward_request(observation_times=tuple(times))


def test_walk_forward_result_rejects_invalid_rate() -> None:
    """Aggregate pass rate must remain a probability."""
    with pytest.raises(ValidationError, match="pass rate"):
        WalkForwardResult(
            splits=(),
            folds=(),
            fold_pass_rate=2.0,
            parameter_drift_score=None,
            oos_retention_score=None,
            walk_forward_efficiency=None,
            status="completed",
        )


def test_time_series_split_rejects_overlap() -> None:
    """The split contract rejects overlapping half-open indices."""
    split = build_time_series_splits(walk_forward_request())[0]
    payload = split.model_dump(mode="python")
    payload["test_start_index"] = split.train_end_index - 1
    with pytest.raises(ValidationError, match="ordered"):
        type(split).model_validate(payload)
