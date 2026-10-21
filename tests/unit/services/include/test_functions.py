"""Unit tests for quantitative arithmetic, math, temporal, ranking, and pip blocks.

Description:
    Validates all 18 StrategyQuant X function building blocks implemented in
    app.services.include.functions: arithmetic operators (plus, minus,
    multiplication, division with zero-division safeguard), mathematical
    primitives (abs_val, round_to_decimals, exponential, logarithm,
    square_root, maximum, minimum), temporal numeric builders (get_date,
    get_time), rolling window rank extractors (indicator_highest,
    indicator_lowest), pip conversions (resolve_pip_size, convert_price_to_pips,
    convert_pips_to_price, async symbol properties, shift-indexed series),
    custom function registration/invocation, and the Functions facade class.

Purpose:
    FEAT-SERVICES-FUNCTIONS: Verification of quantitative function blocks.

Key Capabilities:
    - FR-TEST-FUNCTIONS-ARITHMETIC: Verify arithmetic and math function blocks.
    - FR-TEST-FUNCTIONS-RANK-TEMPORAL: Verify temporal and window ranking blocks.
    - FR-TEST-FUNCTIONS-PIPS-CUSTOM: Verify pip conversions, custom dispatch,
      and Functions facade methods.

Python API Usage:
    ```python
    from app.services.include.functions import Functions, plus

    assert plus(10.0, 5.0) == 15.0
    assert Functions(default_point=0.00001, default_digits=5).to_pips(0.0020) == 20.0
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/include/test_functions.py --no-cov
    ```
"""

from __future__ import annotations

import asyncio
import math

import numpy as np
import pytest
from app.services.include.functions import (
    DEFAULT_PIP_SIZE,
    FLOAT_MAX_VALUE,
    Functions,
    abs_val,
    convert_pips_to_price,
    convert_pips_to_price_symbol,
    convert_price_to_pips,
    convert_price_to_pips_symbol,
    custom_function,
    division,
    exponential,
    get_date,
    get_time,
    indicator_highest,
    indicator_lowest,
    logarithm,
    maximum,
    minimum,
    minus,
    multiplication,
    plus,
    register_custom_function,
    resolve_pip_size,
    round_to_decimals,
    square_root,
)
from app.services.indicators.base import IndicatorSeries


class _MockSymbolSync:
    """Mock broker symbol proxy with synchronous Point() and Digits()."""

    def __init__(self, point: float, digits: int | None) -> None:
        self._point = point
        self._digits = digits

    def Point(self) -> float:  # noqa: N802
        """Return symbol point size."""
        return self._point

    def Digits(self) -> int | None:  # noqa: N802
        """Return symbol digits precision."""
        return self._digits


class _MockSymbolAsync:
    """Mock broker symbol proxy with asynchronous Point() and Digits()."""

    def __init__(self, point: float, digits: int | None) -> None:
        self._point = point
        self._digits = digits

    async def Point(self) -> float:  # noqa: N802
        """Return symbol point size asynchronously."""
        return self._point

    async def Digits(self) -> int | None:  # noqa: N802
        """Return symbol digits precision asynchronously."""
        return self._digits


def test_arithmetic_blocks_and_nan_handling() -> None:
    """Verify plus, minus, multiplication, and division including zero divisor."""
    s1 = IndicatorSeries([10.0, 20.0, 30.0])
    s2 = IndicatorSeries([2.0, 4.0, 5.0])

    assert plus(s1, s2, shift=0) == pytest.approx(35.0)
    assert plus(s1, s2, shift=1) == pytest.approx(24.0)
    assert math.isnan(plus(float("nan"), 5.0))

    assert minus(s1, s2, shift=0) == pytest.approx(25.0)
    assert math.isnan(minus(5.0, float("nan")))

    assert multiplication(s1, s2, shift=0) == pytest.approx(150.0)
    assert math.isnan(multiplication(float("nan"), 2.0))

    assert division(s1, s2, shift=0) == pytest.approx(6.0)
    assert division(10.0, 0.0) == FLOAT_MAX_VALUE
    assert math.isnan(division(10.0, float("nan")))


def test_math_primitives_and_edge_cases() -> None:
    """Verify abs_val, round_to_decimals, exponential, logarithm, sqrt, max, min."""
    assert abs_val(-12.5) == pytest.approx(12.5)
    assert math.isnan(abs_val(float("nan")))

    assert round_to_decimals(1.2345678, decimals=4) == pytest.approx(1.2346)
    assert math.isnan(round_to_decimals(float("nan")))

    assert exponential(0.0) == pytest.approx(1.0)
    assert exponential(1000.0) == FLOAT_MAX_VALUE
    assert math.isnan(exponential(float("nan")))

    assert logarithm(math.e) == pytest.approx(1.0)
    assert math.isnan(logarithm(0.0))
    assert math.isnan(logarithm(-1.0))
    assert math.isnan(logarithm(float("nan")))

    assert square_root(9.0) == pytest.approx(3.0)
    assert math.isnan(square_root(-1.0))
    assert math.isnan(square_root(float("nan")))

    assert maximum(10.0, 25.0) == pytest.approx(25.0)
    assert math.isnan(maximum(10.0, float("nan")))

    assert minimum(10.0, 25.0) == pytest.approx(10.0)
    assert math.isnan(minimum(float("nan"), 25.0))


def test_temporal_and_window_rank_blocks() -> None:
    """Verify get_date, get_time, indicator_highest, and indicator_lowest."""
    assert get_date() == 20160101
    assert get_date(2026, 10, 21) == 20261021

    assert get_time() == 0
    assert get_time(14, 30, 45) == 143045

    arr = np.array([10.0, 50.0, 20.0, 40.0, 30.0])
    assert indicator_highest(arr, period=5, nth_value=0, shift=0) == pytest.approx(50.0)
    assert indicator_highest(arr, period=5, nth_value=1, shift=0) == pytest.approx(40.0)
    assert indicator_highest(arr, period=1, nth_value=0) == pytest.approx(-1.0)
    assert indicator_highest(arr, period=5, nth_value=5) == pytest.approx(-1.0)
    assert indicator_highest(arr, period=5, nth_value=-1) == pytest.approx(-1.0)
    assert indicator_highest(arr, period=10, nth_value=0) == pytest.approx(-1.0)

    assert indicator_lowest(arr, period=5, nth_value=0, shift=0) == pytest.approx(10.0)
    assert indicator_lowest(arr, period=5, nth_value=1, shift=0) == pytest.approx(20.0)
    assert indicator_lowest(arr, period=1, nth_value=0) == pytest.approx(-1.0)
    assert indicator_lowest(arr, period=5, nth_value=5) == pytest.approx(-1.0)
    assert indicator_lowest(arr, period=10, nth_value=0) == pytest.approx(-1.0)


def test_pip_conversions_and_custom_functions() -> None:
    """Verify resolve_pip_size, pip/price conversions at shift, and custom registry."""
    assert resolve_pip_size(pip_size=0.01) == pytest.approx(0.01)
    assert resolve_pip_size(point=0.00001, digits=5) == pytest.approx(0.0001)
    assert resolve_pip_size(point=0.001, digits=3) == pytest.approx(0.01)
    assert resolve_pip_size(point=0.00001, digits=None) == pytest.approx(0.0001)
    assert resolve_pip_size(point=0.01, digits=2) == pytest.approx(0.01)
    assert resolve_pip_size() == pytest.approx(DEFAULT_PIP_SIZE)

    diff_series = IndicatorSeries([0.0010, 0.0020, 0.0035])
    assert convert_price_to_pips(
        diff_series, shift=1, point=0.00001, digits=5
    ) == pytest.approx(20.0)
    assert math.isnan(convert_price_to_pips(float("nan"), point=0.00001, digits=5))

    pips_series = IndicatorSeries([10.0, 20.0, 35.0])
    assert convert_pips_to_price(
        pips_series, shift=1, point=0.00001, digits=5
    ) == pytest.approx(0.0020)
    assert math.isnan(convert_pips_to_price(float("nan"), point=0.00001, digits=5))

    sym_sync = _MockSymbolSync(0.00001, 5)
    sym_async = _MockSymbolAsync(0.001, 3)

    assert asyncio.run(
        convert_price_to_pips_symbol(diff_series, sym_sync, shift=1)
    ) == pytest.approx(20.0)
    assert asyncio.run(
        convert_pips_to_price_symbol(pips_series, sym_async, shift=1)
    ) == pytest.approx(0.20)

    register_custom_function("double_plus", lambda x, y=1: x * 2 + y)
    assert custom_function("double_plus", 5, y=3) == 13
    assert custom_function("adhoc", 4, handler=lambda v: v + 10) == 14
    with pytest.raises(NotImplementedError, match="not registered"):
        custom_function("unregistered_fn")


def test_functions_facade_complete() -> None:
    """Verify all methods on the consolidated Functions facade class."""
    fn = Functions(default_point=0.00001, default_digits=5)
    assert fn.plus(3.0, 4.0) == pytest.approx(7.0)
    assert fn.minus(10.0, 4.0) == pytest.approx(6.0)
    assert fn.multiplication(3.0, 5.0) == pytest.approx(15.0)
    assert fn.division(15.0, 3.0) == pytest.approx(5.0)
    assert fn.abs_val(-7.5) == pytest.approx(7.5)
    assert fn.round_to_decimals(1.234567, decimals=3) == pytest.approx(1.235)
    assert fn.exponential(0.0) == pytest.approx(1.0)
    assert fn.logarithm(1.0) == pytest.approx(0.0)
    assert fn.square_root(16.0) == pytest.approx(4.0)
    assert fn.maximum(2.0, 8.0) == pytest.approx(8.0)
    assert fn.minimum(2.0, 8.0) == pytest.approx(2.0)
    assert fn.get_date(2025, 6, 15) == 20250615
    assert fn.get_time(9, 45, 0) == 94500

    s = IndicatorSeries([1.0, 5.0, 3.0, 4.0, 2.0])
    assert fn.indicator_highest(s, period=5, nth_value=0) == pytest.approx(5.0)
    assert fn.indicator_lowest(s, period=5, nth_value=0) == pytest.approx(1.0)

    assert fn.resolve_pip_size() == pytest.approx(0.0001)
    assert fn.resolve_pip_size(point=0.01, digits=2) == pytest.approx(0.01)
    assert fn.to_pips(0.0025) == pytest.approx(25.0)
    assert fn.to_pips(0.25, point=0.01, digits=2) == pytest.approx(25.0)
    assert fn.to_price(25.0) == pytest.approx(0.0025)
    assert fn.to_price(25.0, point=0.01, digits=2) == pytest.approx(0.25)

    sym_async = _MockSymbolAsync(0.00001, 5)
    assert asyncio.run(fn.to_pips_symbol(0.0030, sym_async)) == pytest.approx(30.0)
    assert asyncio.run(fn.to_price_symbol(30.0, sym_async)) == pytest.approx(0.0030)

    fn.register_custom_function("cube_fn", lambda v: v**3)
    assert fn.custom_function("cube_fn", 3) == 27
