"""Unit tests for the official Aroon calculator."""

import math

import pytest
from app.services.indicators import aroon

from tests.indicators.helpers import (
    assert_error,
    build_dataset,
    result_values,
    unwrap_response,
)

# Highest high on the last bar, lowest low on the first bar -> AroonUp=100, AroonDown=0.
_BARS = [
    (10.0, 10.0, 9.0, 9.5, 100.0),
    (10.0, 10.5, 9.5, 10.0, 100.0),
    (10.5, 11.0, 10.0, 10.5, 100.0),
    (11.0, 12.0, 10.5, 11.5, 100.0),
]


def test_aroon_matches_hand_calculation_at_the_extremes() -> None:
    """AroonUp is 100 and AroonDown is 0 when the extremes sit at each edge."""
    data = build_dataset(_BARS)
    result = unwrap_response(aroon(data, lookback=3))
    values = result_values(result)
    assert values["aroon_up_3"].iloc[-1] == pytest.approx(100.0)
    assert values["aroon_down_3"].iloc[-1] == pytest.approx(0.0)
    assert values["aroon_oscillator_3"].iloc[-1] == pytest.approx(100.0)


def test_aroon_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than N+1 bars stays entirely unavailable."""
    data = build_dataset(_BARS[:2])
    result = unwrap_response(aroon(data, lookback=3))
    values = result_values(result)
    assert values["aroon_up_3"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_aroon_rejects_zero_lookback() -> None:
    """A non-positive lookback is rejected before calculation."""
    data = build_dataset(_BARS)
    assert_error(aroon(data, lookback=0), "IND_INVALID_PARAMETER")


def test_aroon_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(aroon(data, lookback=3))
    second = unwrap_response(aroon(data, lookback=3))
    first_values = result_values(first)["aroon_oscillator_3"].tolist()
    second_values = result_values(second)["aroon_oscillator_3"].tolist()
    for actual, expected in zip(first_values, second_values, strict=True):
        if math.isnan(expected):
            assert math.isnan(actual)
        else:
            assert actual == pytest.approx(expected)
