"""Integration evidence for leakage-safe walk-forward optimization."""

# ruff: noqa: INP001

from app.services.optimization.validation import run_walk_forward_validation
from tests.optimization.unit.test_adapter import FakeAdapter
from tests.optimization.unit.test_validation_contracts import walk_forward_request


def test_walk_forward_enforces_purge_and_embargo() -> None:
    """Every end-to-end fold preserves configured leakage controls."""
    result = run_walk_forward_validation(walk_forward_request(), FakeAdapter())
    assert all(item.purge_bars == 1 for item in result.splits)
    assert all(item.embargo_bars >= 1 for item in result.splits)
    assert all(item.train_end <= item.test_start for item in result.splits)
