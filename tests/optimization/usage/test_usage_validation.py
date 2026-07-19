"""Runnable usage examples for walk-forward validation."""

from app.services.optimization.validation import (
    SplitMode,
    build_time_series_splits,
    run_walk_forward_validation,
)
from tests.optimization.unit.test_adapter import FakeAdapter
from tests.optimization.unit.test_validation_contracts import walk_forward_request


def test_usage_contracts_split_mode() -> None:
    """Select a chronological validation mode."""
    assert SplitMode.ROLLING.value == "rolling"


def test_usage_contracts_walk_forward_request() -> None:
    """Construct an observation-indexed request."""
    assert walk_forward_request().minimum_fold_count == 3


def test_usage_contracts_time_series_split() -> None:
    """Consume one explicit half-open UTC fold contract."""
    assert build_time_series_splits(walk_forward_request())[0].leakage_prevented


def test_usage_contracts_walk_forward_result() -> None:
    """Consume complete aggregate validation evidence."""
    result = run_walk_forward_validation(walk_forward_request(), FakeAdapter())
    assert result.status == "completed"


def test_usage_splits_build_time_series_splits() -> None:
    """Build leakage-safe folds."""
    assert len(build_time_series_splits(walk_forward_request())) == 3


def test_usage_walk_forward_run_validation() -> None:
    """Run a complete walk-forward validation."""
    assert (
        run_walk_forward_validation(
            walk_forward_request(), FakeAdapter()
        ).fold_pass_rate
        == 1.0
    )
