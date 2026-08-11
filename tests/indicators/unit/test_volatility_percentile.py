"""Unit tests for the official volatility percentile/z-score calculator."""

import math

import pytest
from app.services.indicators import volatility_percentile

from tests.indicators.helpers import (
    assert_error,
    close_dataset,
    result_values,
    unwrap_response,
)

_CLOSES = [100.0, 101.0, 99.0, 103.0, 97.0, 105.0, 95.0, 108.0, 92.0, 110.0]


def _independent_percentile_zscore(
    vol_period: int, reference_period: int, annualization_factor: float
) -> tuple[list[float | None], list[float | None]]:
    """Independently hand-derive percentile/z-score over ``_CLOSES``.

    Args:
        vol_period: Inner realized-volatility window.
        reference_period: Trailing comparison window ``n``.
        annualization_factor: Declared annualization factor ``A``.

    Returns:
        A ``(percentile, z_score)`` pair of row-ordered expected values.
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
        series[index] = math.sqrt(annualization_factor * variance)

    percentile: list[float | None] = [None] * len(_CLOSES)
    z_score: list[float | None] = [None] * len(_CLOSES)
    for index in range(len(_CLOSES)):
        if series[index] is None:
            continue
        window_start = index - reference_period + 1
        if window_start < 0:
            continue
        window = series[window_start : index + 1]
        if any(value is None for value in window):
            continue
        current = series[index]
        less = sum(1 for value in window if value < current)
        equal = sum(1 for value in window if value == current)
        percentile[index] = 100.0 * (less + 0.5 * equal) / reference_period
        mean = sum(window) / reference_period
        variance = sum((value - mean) ** 2 for value in window) / (reference_period - 1)
        std = math.sqrt(variance)
        if std <= 0.0:
            continue
        z_score[index] = (current - mean) / std
    return percentile, z_score


def test_volatility_percentile_matches_independent_calculation() -> None:
    """Percentile/z-score match an independently hand-derived calculation."""
    data = close_dataset(_CLOSES)
    expected_pct, expected_z = _independent_percentile_zscore(2, 3, 252.0)
    result = unwrap_response(
        volatility_percentile(data, reference_period=3, vol_period=2)
    )
    values = result_values(result)
    actual_pct = values["volatility_percentile_3_2"].tolist()
    actual_z = values["volatility_zscore_3_2"].tolist()
    for actual_value, expected_value in zip(actual_pct, expected_pct, strict=True):
        if expected_value is None:
            assert math.isnan(actual_value)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)
    for actual_value, expected_value in zip(actual_z, expected_z, strict=True):
        if expected_value is None:
            assert math.isnan(actual_value)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_volatility_percentile_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the combined window stays entirely unavailable."""
    data = close_dataset(_CLOSES[:2])
    result = unwrap_response(
        volatility_percentile(data, reference_period=3, vol_period=2)
    )
    values = result_values(result)
    assert values["volatility_percentile_3_2"].isna().all()
    assert values["volatility_zscore_3_2"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_volatility_percentile_rejects_non_positive_close() -> None:
    """A non-positive close raises IND_INVALID_OHLC."""
    data = close_dataset([*_CLOSES[:-1], -1.0])
    assert_error(
        volatility_percentile(data, reference_period=3, vol_period=2),
        "IND_INVALID_OHLC",
    )


def test_volatility_percentile_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = close_dataset(_CLOSES)
    first = unwrap_response(
        volatility_percentile(data, reference_period=3, vol_period=2)
    )
    second = unwrap_response(
        volatility_percentile(data, reference_period=3, vol_period=2)
    )
    assert result_values(first)["volatility_percentile_3_2"].tolist() == pytest.approx(
        result_values(second)["volatility_percentile_3_2"].tolist(), nan_ok=True
    )
