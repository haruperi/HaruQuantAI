"""Unit tests for the official Rogers-Satchell volatility calculator."""

import math

import pytest
from app.services.indicators import rogers_satchell_volatility

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
]


def _independent_rs(period: int, annualization_factor: float) -> list[float | None]:
    """Independently hand-derive Rogers-Satchell volatility over ``_BARS``.

    Args:
        period: The rolling window length ``n``.
        annualization_factor: Declared annualization factor ``A``.

    Returns:
        Row-ordered expected values, ``None`` for warmup.
    """
    per_bar = []
    for open_, high, low, close, _volume in _BARS:
        per_bar.append(
            math.log(high / open_) * math.log(high / close)
            + math.log(low / open_) * math.log(low / close)
        )
    expected: list[float | None] = [None] * len(_BARS)
    for index in range(period - 1, len(_BARS)):
        window = per_bar[index - period + 1 : index + 1]
        mean_variance = sum(window) / period
        expected[index] = math.sqrt(
            annualization_factor / period * max(mean_variance, 0.0)
        )
    return expected


def test_rogers_satchell_volatility_matches_independent_calculation() -> None:
    """Rogers-Satchell volatility matches an independently hand-derived calculation."""
    data = build_dataset(_BARS)
    expected = _independent_rs(2, 252.0)
    result = unwrap_response(rogers_satchell_volatility(data, period=2))
    actual = result_values(result)["rogers_satchell_volatility_2"].tolist()
    for actual_value, expected_value in zip(actual, expected, strict=True):
        if expected_value is None:
            assert math.isnan(actual_value)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_rogers_satchell_volatility_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the period stays entirely unavailable."""
    data = build_dataset(_BARS[:1])
    result = unwrap_response(rogers_satchell_volatility(data, period=2))
    values = result_values(result)
    assert values["rogers_satchell_volatility_2"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_rogers_satchell_volatility_rejects_non_positive_ohlc() -> None:
    """A non-positive OHLC value raises IND_INVALID_OHLC."""
    bars = [*_BARS[:-1], (0.0, 0.5, -0.5, 0.0, 100.0)]
    data = build_dataset(bars)
    assert_error(rogers_satchell_volatility(data, period=2), "IND_INVALID_OHLC")


def test_rogers_satchell_volatility_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = build_dataset(_BARS)
    first = unwrap_response(rogers_satchell_volatility(data, period=2))
    second = unwrap_response(rogers_satchell_volatility(data, period=2))
    assert result_values(first)[
        "rogers_satchell_volatility_2"
    ].tolist() == pytest.approx(
        result_values(second)["rogers_satchell_volatility_2"].tolist(), nan_ok=True
    )
