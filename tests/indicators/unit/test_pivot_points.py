"""Unit tests for the official Traditional pivot-points calculator."""

import pytest
from app.services.indicators import pivot_points

from tests.indicators.helpers import build_dataset, result_values, unwrap_response

_BARS = [
    (10.0, 11.0, 9.0, 10.0, 100.0),
    (10.0, 10.5, 9.5, 10.0, 100.0),
]


def test_pivot_points_matches_hand_calculation() -> None:
    """P/R1/S1 match the Traditional formula over the prior bar's H/L/C."""
    data = build_dataset(_BARS)
    result = unwrap_response(pivot_points(data))
    values = result_values(result)
    expected_p = (11.0 + 9.0 + 10.0) / 3.0
    assert values["pivot_points_p"].iloc[1] == pytest.approx(expected_p)
    assert values["pivot_points_r1"].iloc[1] == pytest.approx(2 * expected_p - 9.0)
    assert values["pivot_points_s1"].iloc[1] == pytest.approx(2 * expected_p - 11.0)


def test_pivot_points_first_row_is_warmup() -> None:
    """The first row has no prior session and stays unavailable."""
    data = build_dataset(_BARS)
    result = unwrap_response(pivot_points(data))
    values = result_values(result)
    assert values["pivot_points_p"].iloc[:1].isna().all()
    assert values["unavailable_reason"].iloc[0] == "warmup"


def test_pivot_points_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(pivot_points(data))
    second = unwrap_response(pivot_points(data))
    assert (
        result_values(first)["pivot_points_p"].tolist()[1:]
        == result_values(second)["pivot_points_p"].tolist()[1:]
    )
