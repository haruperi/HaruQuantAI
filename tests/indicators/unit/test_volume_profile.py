"""Unit tests for the official rolling volume-profile calculator."""

import math

import pytest
from app.services.indicators import volume_profile
from app.services.indicators.structure.volume_profile import _window_profile

from tests.indicators.helpers import (
    assert_error,
    build_dataset,
    result_values,
    unwrap_response,
)

_BARS = [
    (10.0, 10.2, 9.8, 10.0, 100.0),
    (10.0, 10.2, 9.8, 10.0, 100.0),
    (10.0, 10.2, 9.8, 10.0, 500.0),
]


def test_volume_profile_poc_sits_within_the_window_range() -> None:
    """The POC falls within the trailing window's price range."""
    data = build_dataset(_BARS)
    result = unwrap_response(volume_profile(data, period=3, bins=4))
    values = result_values(result)
    poc = values["volume_profile_poc_3_4"].iloc[-1]
    assert 9.8 <= poc <= 10.2


def test_volume_profile_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the period stays entirely unavailable."""
    data = build_dataset(_BARS[:2])
    result = unwrap_response(volume_profile(data, period=3, bins=4))
    values = result_values(result)
    assert values["volume_profile_poc_3_4"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_volume_profile_rejects_zero_bins() -> None:
    """A non-positive bin count is rejected before calculation."""
    data = build_dataset(_BARS)
    assert_error(volume_profile(data, period=3, bins=0), "IND_INVALID_PARAMETER")


def test_volume_profile_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(volume_profile(data, period=3, bins=4))
    second = unwrap_response(volume_profile(data, period=3, bins=4))
    first_values = result_values(first)["volume_profile_poc_3_4"].tolist()
    second_values = result_values(second)["volume_profile_poc_3_4"].tolist()
    for actual, expected in zip(first_values, second_values, strict=True):
        if math.isnan(expected):
            assert math.isnan(actual)
        else:
            assert actual == pytest.approx(expected)


def test_window_profile_covers_zero_flat_and_bidirectional_value_area() -> None:
    """Exercise zero-volume, flat-price, and both value-area expansions."""
    import numpy as np

    assert _window_profile(np.array([1.0]), np.array([0.0]), 2, 0.7) is None
    assert _window_profile(np.array([1.0, 1.0]), np.array([1.0, 2.0]), 2, 0.7) == (
        1.0,
        1.0,
        1.0,
    )
    profile = _window_profile(
        np.array([1.0, 2.0, 3.0, 4.0]),
        np.array([4.0, 1.0, 2.0, 3.0]),
        4,
        1.0,
    )
    assert profile is not None
    assert profile[1] <= profile[0] < profile[2]
