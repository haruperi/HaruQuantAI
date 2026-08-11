"""Unit tests for the official Supertrend calculator."""

import math

import pytest
from app.services.indicators import supertrend

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
]


def test_supertrend_direction_is_positive_for_a_rising_series() -> None:
    """A steadily rising close series settles into the up-trend direction."""
    data = build_dataset(_BARS)
    result = unwrap_response(supertrend(data, atr_period=2, multiplier=3.0))
    values = result_values(result)
    direction = values["supertrend_direction_2"].dropna()
    assert direction.iloc[-1] == 1.0


def test_supertrend_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the ATR warmup stays entirely unavailable."""
    data = build_dataset(_BARS[:1])
    result = unwrap_response(supertrend(data, atr_period=2, multiplier=3.0))
    values = result_values(result)
    assert values["supertrend_line_2"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_supertrend_rejects_non_positive_multiplier() -> None:
    """A non-positive multiplier is rejected before calculation."""
    data = build_dataset(_BARS)
    assert_error(
        supertrend(data, atr_period=2, multiplier=0.0), "IND_INVALID_PARAMETER"
    )


def test_supertrend_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(supertrend(data, atr_period=2, multiplier=3.0))
    second = unwrap_response(supertrend(data, atr_period=2, multiplier=3.0))
    first_values = result_values(first)["supertrend_line_2"].tolist()
    second_values = result_values(second)["supertrend_line_2"].tolist()
    for actual, expected in zip(first_values, second_values, strict=True):
        if math.isnan(expected):
            assert math.isnan(actual)
        else:
            assert actual == pytest.approx(expected)
