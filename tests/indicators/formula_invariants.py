# ruff: noqa: S101
"""Reusable causal and deterministic assertions for indicator formula tests."""

from typing import Any

from app.services import indicators

from tests.indicators.helpers import build_dataset, unwrap_response


def assert_formula_invariants(
    operation: str,
    parameters: dict[str, Any],
    *,
    bars: list[tuple[float, float, float, float, float]] | None = None,
) -> None:
    """Assert bounded deterministic-series invariants for one formula.

    Args:
        operation: Package-root Indicators function name.
        parameters: Public formula keyword arguments.
        bars: Optional deterministic OHLCV fixture.

    Raises:
        AssertionError: If output shape or ordering violates the contract.
    """
    source = bars or [
        (
            100.0 + index * 0.2,
            101.0 + index * 0.2,
            99.0 + index * 0.2,
            100.1 + index * 0.2,
            1_000.0 + index * 10.0,
        )
        for index in range(24)
    ]
    function = getattr(indicators, operation)
    result = unwrap_response(function(build_dataset(source), **parameters))
    assert result.indicator_id == operation
    assert len(result.values) == len(source)
    assert result.values.index.is_monotonic_increasing


def oscillating_bars() -> list[tuple[float, float, float, float, float]]:
    """Return deterministic bars containing alternating pivots and breakouts.

    Returns:
        Forty OHLCV bars with broad alternating swing geometry.

    Raises:
        None.
    """
    closes = [100.0 + ((-1.0) ** index) * (2.0 + index * 0.08) for index in range(40)]
    return [
        (close - 0.4, close + 1.0, close - 1.0, close, 1_000.0 + index * 25.0)
        for index, close in enumerate(closes)
    ]
