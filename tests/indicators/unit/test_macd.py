"""Unit tests for the official MACD calculator."""

import math

import pytest
from app.services.indicators import macd

from tests.indicators.helpers import (
    assert_error,
    close_dataset,
    result_values,
    unwrap_response,
)

_CLOSES = [float(100 + i) for i in range(30)]


def _independent_ema(values: list[float], period: int) -> list[float | None]:
    """Independently hand-derive an SMA-seeded EMA."""
    result: list[float | None] = [None] * len(values)
    if len(values) < period:
        return result
    alpha = 2.0 / (period + 1)
    previous = sum(values[:period]) / period
    result[period - 1] = previous
    for index in range(period, len(values)):
        previous = values[index] * alpha + previous * (1.0 - alpha)
        result[index] = previous
    return result


def test_macd_matches_independent_calculation() -> None:
    """MACD line matches an independently hand-derived fast/slow EMA difference.

    Per spec ``IND-TR-05``, warmup is governed by the slow MA *plus* the
    signal seed policy, and every published output row (including the raw
    ``macd`` line) shares one uniform validity mask with ``signal`` and
    ``histogram`` — so the first ``signal_period - 1`` rows after the slow
    EMA becomes available are still warmup, even though the raw fast/slow
    difference is technically already computable there.
    """
    signal_period = 3
    data = close_dataset(_CLOSES)
    fast = _independent_ema(_CLOSES, 5)
    slow = _independent_ema(_CLOSES, 10)
    first_macd_valid = next(
        index
        for index, (f, s) in enumerate(zip(fast, slow, strict=True))
        if f is not None and s is not None
    )
    first_signal_valid = first_macd_valid + signal_period - 1
    expected = [
        None if f is None or s is None or index < first_signal_valid else f - s
        for index, (f, s) in enumerate(zip(fast, slow, strict=True))
    ]
    result = unwrap_response(
        macd(data, fast_period=5, slow_period=10, signal_period=signal_period)
    )
    actual = result_values(result)["macd_5_10"].tolist()
    for actual_value, expected_value in zip(actual, expected, strict=True):
        if expected_value is None:
            assert math.isnan(actual_value)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_macd_rejects_fast_period_not_less_than_slow() -> None:
    """A fast period that is not strictly less than the slow period is rejected."""
    data = close_dataset(_CLOSES)
    assert_error(
        macd(data, fast_period=10, slow_period=10, signal_period=3),
        "IND_INVALID_PARAMETER",
    )


def test_macd_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the warmup requirement stays entirely unavailable."""
    data = close_dataset(_CLOSES[:3])
    result = unwrap_response(macd(data, fast_period=5, slow_period=10, signal_period=3))
    values = result_values(result)
    assert values["macd_5_10"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_macd_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = close_dataset(_CLOSES)
    first = unwrap_response(macd(data, fast_period=5, slow_period=10, signal_period=3))
    second = unwrap_response(macd(data, fast_period=5, slow_period=10, signal_period=3))
    assert result_values(first)["macd_5_10"].tolist() == pytest.approx(
        result_values(second)["macd_5_10"].tolist(), nan_ok=True
    )
