"""Tests for walk-forward execution."""

# ruff: noqa: INP001

from app.services.optimization.validation import run_walk_forward_validation
from tests.optimization.unit.test_adapter import FakeAdapter
from tests.optimization.unit.test_validation_contracts import walk_forward_request


def test_walk_forward_runs_train_and_out_of_sample() -> None:
    """Every split produces paired training and OOS score evidence."""
    result = run_walk_forward_validation(walk_forward_request(), FakeAdapter())
    assert result.status == "completed"
    assert len(result.folds) == 3
    assert result.fold_pass_rate == 1.0
