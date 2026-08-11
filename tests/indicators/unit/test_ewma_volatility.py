"""Unit tests for the official EWMA volatility calculator."""

import math

import pytest
from app.services.indicators import ewma_volatility

from tests.indicators.helpers import (
    assert_error,
    close_dataset,
    result_values,
    unwrap_response,
)

_CLOSES = [100.0, 101.0, 99.0, 102.0, 98.0, 103.0]


def _independent_ewma(decay: float, annualization_factor: float) -> list[float | None]:
    """Independently hand-derive seeded EWMA volatility over ``_CLOSES``.

    Args:
        decay: RiskMetrics decay ``lambda``.
        annualization_factor: Declared annualization factor ``A``.

    Returns:
        Row-ordered expected ``ewma_volatility`` values, ``None`` for warmup.
    """
    log_returns = [
        math.log(_CLOSES[index] / _CLOSES[index - 1])
        for index in range(1, len(_CLOSES))
    ]
    variance = [log_returns[0] ** 2]
    for value in log_returns[1:]:
        variance.append(decay * variance[-1] + (1.0 - decay) * value**2)
    expected: list[float | None] = [None]
    expected.extend(math.sqrt(annualization_factor * item) for item in variance)
    return expected


def test_ewma_volatility_matches_independent_calculation() -> None:
    """EWMA volatility matches an independently hand-derived calculation."""
    data = close_dataset(_CLOSES)
    expected = _independent_ewma(0.94, 252.0)
    result = unwrap_response(ewma_volatility(data, decay=0.94))
    actual = result_values(result)["ewma_volatility"].tolist()
    for actual_value, expected_value in zip(actual, expected, strict=True):
        if expected_value is None:
            assert math.isnan(actual_value)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_ewma_volatility_custom_annualization_factor() -> None:
    """A non-default annualization factor changes the output deterministically."""
    data = close_dataset(_CLOSES)
    expected = _independent_ewma(0.9, 365.0)
    result = unwrap_response(
        ewma_volatility(data, decay=0.9, annualization_factor=365.0)
    )
    actual = result_values(result)["ewma_volatility"].tolist()
    for actual_value, expected_value in zip(actual, expected, strict=True):
        if expected_value is None:
            assert math.isnan(actual_value)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_ewma_volatility_single_row_is_entirely_warmup() -> None:
    """A single-row dataset has no return and stays entirely unavailable."""
    data = close_dataset([100.0])
    result = unwrap_response(ewma_volatility(data, decay=0.94))
    values = result_values(result)
    assert values["ewma_volatility"].isna().all()
    assert (values["unavailable_reason"] == "warmup").all()


def test_ewma_volatility_rejects_non_positive_close() -> None:
    """A non-positive close raises IND_INVALID_OHLC."""
    data = close_dataset([100.0, -1.0, 99.0])
    assert_error(ewma_volatility(data, decay=0.94), "IND_INVALID_OHLC")


def test_ewma_volatility_is_deterministic() -> None:
    """Identical inputs and configuration produce identical output values."""
    data = close_dataset(_CLOSES)
    first = unwrap_response(ewma_volatility(data, decay=0.94))
    second = unwrap_response(ewma_volatility(data, decay=0.94))
    assert result_values(first)["ewma_volatility"].tolist() == pytest.approx(
        result_values(second)["ewma_volatility"].tolist(), nan_ok=True
    )
