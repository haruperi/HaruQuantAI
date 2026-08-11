"""Component tests for the official EMA-slope calculator."""

import math

import pytest
from app.services.indicators import ema_slope

from tests.indicators.helpers import (
    assert_error,
    build_dataset,
    result_values,
    unwrap_response,
)

_BARS = [
    (10.0, 10.5, 9.5, 10.0, 100.0),
    (10.0, 10.5, 9.5, 10.5, 100.0),
    (10.5, 11.0, 10.0, 11.0, 100.0),
    (11.0, 11.5, 10.5, 11.5, 100.0),
    (11.5, 12.0, 11.0, 12.0, 100.0),
    (12.0, 12.5, 11.5, 12.5, 100.0),
    (12.5, 13.0, 12.0, 13.0, 100.0),
]


def test_ema_slope_direction_is_positive_for_a_rising_series() -> None:
    """A strictly rising close series produces a positive direction sign."""
    data = build_dataset(_BARS)
    result = unwrap_response(ema_slope(data, period=3, lag=1, atr_period=3))
    values = result_values(result)
    direction = values["ema_slope_direction_3_1"]
    valid = direction.dropna()
    assert (valid == 1.0).all()


def test_ema_slope_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the warmup requirement stays entirely unavailable."""
    data = build_dataset(_BARS[:2])
    result = unwrap_response(ema_slope(data, period=3, lag=1, atr_period=3))
    values = result_values(result)
    assert values["ema_slope_ema_3"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_ema_slope_rejects_zero_period() -> None:
    """An invalid period is rejected before calculation."""
    data = build_dataset(_BARS)
    assert_error(
        ema_slope(data, period=1, lag=1, atr_period=3), "IND_INVALID_PARAMETER"
    )


def test_ema_slope_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(ema_slope(data, period=3, lag=1, atr_period=3))
    second = unwrap_response(ema_slope(data, period=3, lag=1, atr_period=3))
    first_values = result_values(first)["ema_slope_normalized_3_1_3"].tolist()
    second_values = result_values(second)["ema_slope_normalized_3_1_3"].tolist()
    for actual, expected in zip(first_values, second_values, strict=True):
        if math.isnan(expected):
            assert math.isnan(actual)
        else:
            assert actual == pytest.approx(expected)
