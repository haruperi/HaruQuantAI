"""Unit tests for the official Bollinger BandWidth calculator."""

import math
import statistics

import pytest
from app.services.indicators import bollinger_bandwidth

from tests.indicators.helpers import (
    assert_error,
    close_dataset,
    result_values,
    unwrap_response,
)

_CLOSES = [100.0, 101.0, 99.0, 102.0, 98.0, 103.0]


def _independent_bandwidth(period: int, std_dev: float) -> list[float | None]:
    """Independently hand-derive Bollinger BandWidth over ``_CLOSES``.

    Args:
        period: The rolling period.
        std_dev: The standard-deviation multiplier ``k``.

    Returns:
        Row-ordered expected ``bandwidth_percent`` values, ``None`` for warmup.
    """
    expected: list[float | None] = [None] * len(_CLOSES)
    for index in range(period - 1, len(_CLOSES)):
        window = _CLOSES[index - period + 1 : index + 1]
        middle = statistics.fmean(window)
        deviation = statistics.stdev(window)
        upper = middle + std_dev * deviation
        lower = middle - std_dev * deviation
        expected[index] = 100.0 * (upper - lower) / middle
    return expected


def test_bollinger_bandwidth_matches_independent_calculation() -> None:
    """Bandwidth percent matches an independently hand-derived calculation."""
    data = close_dataset(_CLOSES)
    expected = _independent_bandwidth(2, 2.0)
    result = unwrap_response(bollinger_bandwidth(data, period=2, std_dev=2.0))
    actual = result_values(result)["bollinger_bandwidth_percent_2"].tolist()
    for actual_value, expected_value in zip(actual, expected, strict=True):
        if expected_value is None:
            assert math.isnan(actual_value)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_bollinger_bandwidth_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the period stays entirely unavailable."""
    data = close_dataset(_CLOSES[:1])
    result = unwrap_response(bollinger_bandwidth(data, period=2, std_dev=2.0))
    values = result_values(result)
    assert values["bollinger_bandwidth_percent_2"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_bollinger_bandwidth_rejects_config_disagreement() -> None:
    """A supplied config disagreeing with wrapper args raises IND_INVALID_CONFIG."""
    from app.services.indicators import build_indicator_config

    data = close_dataset(_CLOSES)
    bad_config = build_indicator_config(
        indicator_id="bollinger_bandwidth",
        parameters=(("period", 5), ("std_dev", 2.0)),
        source=None,
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    assert_error(
        bollinger_bandwidth(data, period=2, std_dev=2.0, config=bad_config),
        "IND_INVALID_CONFIG",
    )


def test_bollinger_bandwidth_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = close_dataset(_CLOSES)
    first = unwrap_response(bollinger_bandwidth(data, period=2, std_dev=2.0))
    second = unwrap_response(bollinger_bandwidth(data, period=2, std_dev=2.0))
    assert result_values(first)[
        "bollinger_bandwidth_percent_2"
    ].tolist() == pytest.approx(
        result_values(second)["bollinger_bandwidth_percent_2"].tolist(), nan_ok=True
    )
