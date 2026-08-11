"""Unit tests for the official Donchian-channel calculator."""

import math

import pytest
from app.services.indicators import donchian_channels

from tests.indicators.helpers import (
    assert_error,
    build_dataset,
    result_values,
    unwrap_response,
)

_BARS = [
    (10.0, 10.5, 9.5, 10.0, 100.0),
    (10.0, 11.0, 9.0, 10.5, 100.0),
    (10.5, 10.8, 9.8, 10.2, 100.0),
]


def test_donchian_channels_matches_hand_calculation() -> None:
    """Upper/lower/middle match a hand-derived max/min over the window."""
    data = build_dataset(_BARS)
    result = unwrap_response(donchian_channels(data, period=3))
    values = result_values(result)
    assert values["donchian_upper_3"].iloc[-1] == pytest.approx(11.0)
    assert values["donchian_lower_3"].iloc[-1] == pytest.approx(9.0)
    assert values["donchian_middle_3"].iloc[-1] == pytest.approx(10.0)


def test_donchian_channels_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the period stays entirely unavailable."""
    data = build_dataset(_BARS[:2])
    result = unwrap_response(donchian_channels(data, period=3))
    values = result_values(result)
    assert values["donchian_upper_3"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_donchian_channels_rejects_short_period() -> None:
    """A period below the declared minimum is rejected before calculation."""
    data = build_dataset(_BARS)
    assert_error(donchian_channels(data, period=1), "IND_INVALID_PARAMETER")


def test_donchian_channels_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(donchian_channels(data, period=3))
    second = unwrap_response(donchian_channels(data, period=3))
    first_values = result_values(first)["donchian_upper_3"].tolist()
    second_values = result_values(second)["donchian_upper_3"].tolist()
    for actual, expected in zip(first_values, second_values, strict=True):
        if math.isnan(expected):
            assert math.isnan(actual)
        else:
            assert actual == pytest.approx(expected)
