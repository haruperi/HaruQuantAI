"""Tests for leakage-safe time-series splitting."""

# ruff: noqa: INP001

from app.services.optimization.validation import build_time_series_splits
from tests.optimization.unit.test_validation_contracts import walk_forward_request


def test_time_series_split_rejects_overlap() -> None:
    """Constructed folds preserve a positive purge and embargo gap."""
    splits = build_time_series_splits(walk_forward_request())
    assert len(splits) == 3
    assert all(item.train_end_index <= item.test_start_index for item in splits)
    assert all(item.leakage_prevented for item in splits)


def test_anchored_and_expanding_have_growing_train_semantics() -> None:
    """Both growing-window labels retain index zero as training start."""
    anchored = build_time_series_splits(walk_forward_request(mode="anchored"))
    expanding = build_time_series_splits(walk_forward_request(mode="expanding"))
    assert tuple(item.train_start_index for item in anchored) == (0, 0, 0)
    assert anchored == expanding


def test_build_time_series_splits_enforces_trade_duration_embargo() -> None:
    """Average trade duration raises the effective embargo deterministically."""
    splits = build_time_series_splits(
        walk_forward_request(embargo_bars=0, average_trade_duration_bars=2)
    )
    assert all(item.embargo_bars == 2 for item in splits)
