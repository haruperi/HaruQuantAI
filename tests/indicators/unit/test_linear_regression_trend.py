"""Unit tests for the official linear-regression-trend calculator."""

import math

import pytest
from app.services.indicators import linear_regression_trend

from tests.indicators.helpers import (
    assert_error,
    close_dataset,
    result_values,
    unwrap_response,
)

_CLOSES = [10.0, 11.0, 12.0, 13.0, 14.0]


def test_linear_regression_trend_matches_a_perfect_line() -> None:
    """A perfectly linear series has slope 1.0 and R2 of 1.0."""
    data = close_dataset(_CLOSES)
    result = unwrap_response(linear_regression_trend(data, period=5))
    values = result_values(result)
    assert values["linear_regression_slope_5_price"].iloc[-1] == pytest.approx(1.0)
    assert values["linear_regression_r_squared_5_price"].iloc[-1] == pytest.approx(1.0)
    assert values["linear_regression_direction_5_price"].iloc[-1] == 1.0


def test_linear_regression_trend_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the window stays entirely unavailable."""
    data = close_dataset(_CLOSES[:2])
    result = unwrap_response(linear_regression_trend(data, period=5))
    values = result_values(result)
    assert values["linear_regression_slope_5_price"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_linear_regression_trend_rejects_invalid_transform() -> None:
    """An unsupported transform is rejected before calculation."""
    data = close_dataset(_CLOSES)
    assert_error(
        linear_regression_trend(data, period=5, transform="bogus"),
        "IND_INVALID_PARAMETER",
    )


def test_linear_regression_trend_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = close_dataset(_CLOSES)
    first = unwrap_response(linear_regression_trend(data, period=5))
    second = unwrap_response(linear_regression_trend(data, period=5))
    first_values = result_values(first)["linear_regression_slope_5_price"].tolist()
    second_values = result_values(second)["linear_regression_slope_5_price"].tolist()
    for actual, expected in zip(first_values, second_values, strict=True):
        if math.isnan(expected):
            assert math.isnan(actual)
        else:
            assert actual == pytest.approx(expected)
