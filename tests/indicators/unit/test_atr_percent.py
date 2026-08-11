"""Unit tests for the official ATR Percent volatility calculator."""

import math

import pytest
from app.services.indicators import atr_percent

from tests.indicators.helpers import (
    assert_error,
    build_dataset,
    result_values,
    unwrap_response,
)

_BARS = [
    (9.5, 10.0, 9.0, 9.5, 100.0),
    (10.5, 11.0, 10.0, 10.5, 100.0),
    (10.0, 10.5, 9.5, 10.0, 100.0),
    (11.5, 12.0, 11.0, 11.5, 100.0),
    (11.0, 11.5, 10.5, 11.0, 100.0),
    (12.5, 13.0, 12.0, 12.5, 100.0),
]


def _independent_atr_percent(period: int) -> list[float | None]:
    """Independently hand-derive ATR% from the ATR golden fixture.

    Args:
        period: The ATR smoothing period.

    Returns:
        Row-ordered expected ``atr_percent`` values, ``None`` for warmup.
    """
    highs = [bar[1] for bar in _BARS]
    lows = [bar[2] for bar in _BARS]
    closes = [bar[3] for bar in _BARS]
    true_range = []
    for index in range(len(_BARS)):
        prior_close = closes[index - 1] if index > 0 else closes[0]
        true_range.append(
            max(
                highs[index] - lows[index],
                abs(highs[index] - prior_close),
                abs(lows[index] - prior_close),
            )
        )
    atr_values: list[float | None] = [None] * len(_BARS)
    previous = sum(true_range[:period]) / period
    atr_values[period - 1] = previous
    for index in range(period, len(_BARS)):
        previous = (previous * (period - 1) + true_range[index]) / period
        atr_values[index] = previous
    return [
        None if value is None else 100.0 * value / closes[index]
        for index, value in enumerate(atr_values)
    ]


def test_atr_percent_matches_independent_calculation() -> None:
    """ATR% matches an independently hand-derived calculation."""
    data = build_dataset(_BARS)
    expected = _independent_atr_percent(2)
    result = unwrap_response(atr_percent(data, period=2))
    actual = result_values(result)["atr_percent_2"].tolist()
    for actual_value, expected_value in zip(actual, expected, strict=True):
        if expected_value is None:
            assert math.isnan(actual_value)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_atr_percent_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the period stays entirely unavailable."""
    data = build_dataset(_BARS[:1])
    result = unwrap_response(atr_percent(data, period=2))
    values = result_values(result)
    assert values["atr_percent_2"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_atr_percent_rejects_non_positive_close() -> None:
    """A non-positive close raises IND_INVALID_OHLC."""
    bars = [*_BARS[:-1], (0.0, 0.5, -0.5, 0.0, 100.0)]
    data = build_dataset(bars)
    assert_error(atr_percent(data, period=2), "IND_INVALID_OHLC")


def test_atr_percent_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(atr_percent(data, period=2))
    second = unwrap_response(atr_percent(data, period=2))
    assert result_values(first)["atr_percent_2"].tolist() == pytest.approx(
        result_values(second)["atr_percent_2"].tolist(), nan_ok=True
    )
