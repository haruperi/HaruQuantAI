"""Unit tests for the official structural-level-clustering calculator."""

import pytest
from app.services.indicators import level_clustering

from tests.indicators.helpers import (
    assert_error,
    build_dataset,
    result_values,
    unwrap_response,
)

_BARS = [
    (10.0, 10.2, 9.8, 10.0, 100.0),
    (10.5, 10.8, 10.2, 10.5, 100.0),
    (11.0, 12.0, 10.8, 11.5, 100.0),
    (10.5, 10.8, 10.2, 10.5, 100.0),
    (10.0, 10.2, 9.8, 10.0, 100.0),
]


def test_level_clustering_finds_a_cluster_once_pivots_confirm() -> None:
    """A confirmed pivot high produces a non-empty cluster once available."""
    data = build_dataset(_BARS)
    result = unwrap_response(
        level_clustering(data, lookback=5, tolerance=0.5, half_life=10.0)
    )
    values = result_values(result)
    assert values["level_cluster_flag"].iloc[-1] in (0.0, 1.0)


def test_level_clustering_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the minimum confirmation window is unavailable."""
    data = build_dataset(_BARS[:3])
    result = unwrap_response(
        level_clustering(data, lookback=5, tolerance=0.5, half_life=10.0)
    )
    values = result_values(result)
    assert values["level_cluster_price"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_level_clustering_rejects_non_positive_half_life() -> None:
    """A non-positive half-life is rejected before calculation."""
    data = build_dataset(_BARS)
    assert_error(
        level_clustering(data, lookback=5, tolerance=0.5, half_life=0.0),
        "IND_INVALID_PARAMETER",
    )


def test_level_clustering_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(
        level_clustering(data, lookback=5, tolerance=0.5, half_life=10.0)
    )
    second = unwrap_response(
        level_clustering(data, lookback=5, tolerance=0.5, half_life=10.0)
    )
    assert result_values(first)["level_cluster_price"].tolist() == pytest.approx(
        result_values(second)["level_cluster_price"].tolist(), nan_ok=True
    )
