"""Unit tests for the official cumulative-volume-delta calculator."""

import pytest
from app.services.indicators import cumulative_volume_delta

from tests.indicators.helpers import (
    assert_error,
    build_dataset,
    result_values,
    unwrap_response,
)

_BARS = [
    (10.0, 10.5, 9.5, 10.5, 100.0),  # up bar: +100
    (10.5, 11.0, 10.0, 10.0, 200.0),  # down bar: -200
    (10.0, 10.8, 9.8, 10.6, 300.0),  # up bar: +300
]


def test_cumulative_volume_delta_matches_hand_calculation() -> None:
    """CVD matches a hand-derived close/open sign accumulation."""
    data = build_dataset(_BARS)
    result = unwrap_response(cumulative_volume_delta(data, window=1))
    values = result_values(result)
    assert values["cvd_1"].tolist() == pytest.approx([100.0, -100.0, 200.0])


def test_cumulative_volume_delta_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the window stays entirely unavailable."""
    data = build_dataset(_BARS)
    result = unwrap_response(cumulative_volume_delta(data, window=5))
    values = result_values(result)
    assert values["cvd_5"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_cumulative_volume_delta_rejects_zero_window() -> None:
    """A non-positive window is rejected before calculation."""
    data = build_dataset(_BARS)
    assert_error(cumulative_volume_delta(data, window=0), "IND_INVALID_PARAMETER")


def test_cumulative_volume_delta_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(cumulative_volume_delta(data, window=1))
    second = unwrap_response(cumulative_volume_delta(data, window=1))
    assert (
        result_values(first)["cvd_1"].tolist()
        == result_values(second)["cvd_1"].tolist()
    )
