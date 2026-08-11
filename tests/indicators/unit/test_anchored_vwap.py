"""Unit tests for the official Anchored VWAP calculator."""

import pytest
from app.services.indicators import anchored_vwap

from tests.indicators.helpers import (
    assert_error,
    build_dataset,
    result_values,
    unwrap_response,
)

_BARS = [
    (10.0, 10.0, 10.0, 10.0, 100.0),
    (11.0, 11.0, 11.0, 11.0, 200.0),
    (12.0, 12.0, 12.0, 12.0, 300.0),
]


def test_anchored_vwap_matches_hand_calculation() -> None:
    """AVWAP matches a hand-derived volume-weighted average of typical price."""
    data = build_dataset(_BARS)
    result = unwrap_response(anchored_vwap(data, anchor_index=0))
    values = result_values(result)
    expected = (10.0 * 100.0 + 11.0 * 200.0 + 12.0 * 300.0) / (100.0 + 200.0 + 300.0)
    assert values["anchored_vwap_0"].iloc[-1] == pytest.approx(expected)


def test_anchored_vwap_rows_before_anchor_are_warmup() -> None:
    """Rows before the anchor index are unavailable, not zero-filled."""
    data = build_dataset(_BARS)
    result = unwrap_response(anchored_vwap(data, anchor_index=1))
    values = result_values(result)
    assert values["anchored_vwap_1"].iloc[0:1].isna().all()
    assert values["unavailable_reason"].iloc[0] == "warmup"


def test_anchored_vwap_rejects_out_of_range_anchor() -> None:
    """An anchor index outside the dataset is rejected before calculation."""
    data = build_dataset(_BARS)
    assert_error(anchored_vwap(data, anchor_index=99), "IND_INVALID_PARAMETER")


def test_anchored_vwap_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(anchored_vwap(data, anchor_index=0))
    second = unwrap_response(anchored_vwap(data, anchor_index=0))
    assert (
        result_values(first)["anchored_vwap_0"].tolist()
        == result_values(second)["anchored_vwap_0"].tolist()
    )
