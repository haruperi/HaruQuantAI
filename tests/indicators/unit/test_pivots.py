"""Unit tests for the official confirmed swing pivot calculator."""

import pytest
from app.services.indicators import pivots

from tests.indicators.helpers import (
    assert_error,
    build_dataset,
    result_values,
    unwrap_response,
)

# Bar index 2 is a clean pivot high (13.0) and pivot low (11.0) with one bar on
# each side; confirmed at index 3 with left=right=1.
_BARS = [
    (11.5, 12.0, 11.0, 11.5, 100.0),
    (12.0, 12.5, 11.5, 12.0, 100.0),
    (12.5, 13.0, 11.0, 12.5, 100.0),
    (12.0, 12.5, 11.5, 12.0, 100.0),
]


def test_pivots_confirms_at_the_right_bar_offset() -> None:
    """A clean pivot high/low is confirmed exactly `right` bars later."""
    data = build_dataset(_BARS)
    result = unwrap_response(pivots(data, left=1, right=1))
    values = result_values(result)
    assert values["pivot_high_flag_1_1"].iloc[3] == 1.0
    assert values["pivot_high_price_1_1"].iloc[3] == pytest.approx(13.0)
    assert values["pivot_low_flag_1_1"].iloc[3] == 1.0
    assert values["pivot_low_price_1_1"].iloc[3] == pytest.approx(11.0)
    assert values["pivot_high_flag_1_1"].iloc[2] == 0.0


def test_pivots_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the left+right window stays entirely unavailable."""
    data = build_dataset(_BARS[:2])
    result = unwrap_response(pivots(data, left=1, right=1))
    values = result_values(result)
    assert values["pivot_high_flag_1_1"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_pivots_rejects_zero_left() -> None:
    """A non-positive left-bar count is rejected before calculation."""
    data = build_dataset(_BARS)
    assert_error(pivots(data, left=0, right=1), "IND_INVALID_PARAMETER")


def test_pivots_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(pivots(data, left=1, right=1))
    second = unwrap_response(pivots(data, left=1, right=1))
    assert result_values(first)["pivot_high_price_1_1"].tolist() == pytest.approx(
        result_values(second)["pivot_high_price_1_1"].tolist(), nan_ok=True
    )
