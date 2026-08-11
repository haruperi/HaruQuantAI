"""Unit tests for the official volatility-of-volatility calculator."""

import math

import pytest
from app.services.indicators import volatility_of_volatility

from tests.indicators.helpers import (
    assert_error,
    close_dataset,
    result_values,
    unwrap_response,
)

_CLOSES = [100.0, 101.0, 99.0, 103.0, 97.0, 105.0, 95.0, 108.0, 92.0, 110.0]


def _independent_vov(period: int, vol_period: int) -> list[float | None]:
    """Independently hand-derive volatility-of-volatility over ``_CLOSES``.

    Args:
        period: The outer log-change standard-deviation window ``n``.
        vol_period: The inner realized-volatility window.

    Returns:
        Row-ordered expected values, ``None`` for warmup.
    """
    log_returns = [
        math.log(_CLOSES[index] / _CLOSES[index - 1])
        for index in range(1, len(_CLOSES))
    ]
    series: list[float | None] = [None] * len(_CLOSES)
    for index in range(vol_period, len(_CLOSES)):
        window = log_returns[index - vol_period : index]
        mean = sum(window) / vol_period
        variance = sum((value - mean) ** 2 for value in window) / (vol_period - 1)
        series[index] = math.sqrt(variance)

    log_change: list[float | None] = [None] * len(_CLOSES)
    for index in range(1, len(_CLOSES)):
        previous = series[index - 1]
        current = series[index]
        if previous is None or current is None or previous <= 0.0 or current <= 0.0:
            continue
        log_change[index] = math.log(current / previous)

    expected: list[float | None] = [None] * len(_CLOSES)
    for index in range(len(_CLOSES)):
        window_start = index - period + 1
        if window_start < 1:
            continue
        window = log_change[window_start : index + 1]
        if any(value is None for value in window):
            continue
        mean = sum(window) / period
        variance = sum((value - mean) ** 2 for value in window) / (period - 1)
        expected[index] = math.sqrt(variance)
    return expected


def test_volatility_of_volatility_matches_independent_calculation() -> None:
    """VoV matches an independently hand-derived calculation."""
    data = close_dataset(_CLOSES)
    expected = _independent_vov(2, 2)
    result = unwrap_response(volatility_of_volatility(data, period=2, vol_period=2))
    actual = result_values(result)["volatility_of_volatility_2_2"].tolist()
    for actual_value, expected_value in zip(actual, expected, strict=True):
        if expected_value is None:
            assert math.isnan(actual_value)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_volatility_of_volatility_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the combined window stays entirely unavailable."""
    data = close_dataset(_CLOSES[:2])
    result = unwrap_response(volatility_of_volatility(data, period=2, vol_period=2))
    values = result_values(result)
    assert values["volatility_of_volatility_2_2"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_volatility_of_volatility_rejects_non_positive_close() -> None:
    """A non-positive close raises IND_INVALID_OHLC."""
    data = close_dataset([*_CLOSES[:-1], -1.0])
    assert_error(
        volatility_of_volatility(data, period=2, vol_period=2), "IND_INVALID_OHLC"
    )


def test_volatility_of_volatility_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = close_dataset(_CLOSES)
    first = unwrap_response(volatility_of_volatility(data, period=2, vol_period=2))
    second = unwrap_response(volatility_of_volatility(data, period=2, vol_period=2))
    assert result_values(first)[
        "volatility_of_volatility_2_2"
    ].tolist() == pytest.approx(
        result_values(second)["volatility_of_volatility_2_2"].tolist(), nan_ok=True
    )
