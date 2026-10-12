"""Unit test suite for StrategyQuant X functions building blocks.

Description:
    Tests verification of arithmetic operators with zero-division safeguards,
    mathematical primitives, temporal numeric builders, rolling window rank
    extractors, pip conversions with broker symbol point integration, custom
    functions, and the Functions facade class.

Purpose:
    FEAT-SERVICES-FUNCTION-TESTS: Comprehensive test coverage for function blocks.

Key Capabilities:
    - FR-SERVICES-TEST-FUNCTIONS: Assert exact calculations, edge-case bounds,
      and broker Point() async conversions.
      Associated: `test_arithmetic_operators()`, `test_math_primitives()`,
        `test_temporal_builders()`, `test_rank_extractors()`,
        `test_pip_conversions()`, `test_async_broker_pip_conversions()`,
        `test_custom_functions()`, `test_functions_facade()`.
      Logging: DEBUG on test execution.

Python API Usage:
    ```python
    uv run pytest tests/unit/services/test_functions.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_functions.py --no-cov
    ```
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from app.services.utils.functions import (
    SQX_MAX_VALUE,
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


def test_arithmetic_operators() -> None:
    """Verify basic arithmetic operators, NaN handling, and division ceiling."""
    # Addition
    assert plus(10.0, 5.0) == 15.0
    assert math.isnan(plus(float("nan"), 5.0))
    assert math.isnan(plus(10.0, float("nan")))

    # Subtraction
    assert minus(10.0, 4.0) == 6.0
    assert math.isnan(minus(float("nan"), 4.0))

    # Multiplication
    assert multiplication(6.0, 7.0) == 42.0
    assert math.isnan(multiplication(6.0, float("nan")))

    # Division
    assert division(10.0, 2.0) == 5.0
    assert math.isnan(division(float("nan"), 2.0))
    assert math.isnan(division(10.0, float("nan")))

    # Zero-division safeguard: returns SQX_MAX_VALUE
    assert division(10.0, 0.0) == SQX_MAX_VALUE
    assert division(0.0, 0.0) == SQX_MAX_VALUE

    # Evaluation with array and historical shifts
    arr1 = np.array([2.0, 4.0, 6.0])
    arr2 = np.array([1.0, 2.0, 3.0])
    assert plus(arr1, arr2, shift=0) == 9.0  # 6 + 3
    assert minus(arr1, arr2, shift=1) == 2.0  # 4 - 2
    assert multiplication(arr1, arr2, shift=2) == 2.0  # 2 * 1
    assert division(arr1, arr2, shift=0) == 2.0  # 6 / 3


def test_math_primitives() -> None:
    """Verify math functions (abs, round, exp, log, sqrt, min, max)."""
    # Abs
    assert abs_val(-5.5) == 5.5
    assert abs_val(3.2) == 3.2
    assert math.isnan(abs_val(float("nan")))

    # Round
    assert round_to_decimals(1.234567, decimals=4) == 1.2346
    assert round_to_decimals(1.234567, decimals=2) == 1.23
    assert math.isnan(round_to_decimals(float("nan"), decimals=2))

    # Exponential
    assert exponential(0.0) == pytest.approx(1.0)
    assert exponential(1.0) == pytest.approx(math.e)
    assert exponential(1000.0) == SQX_MAX_VALUE  # Overflow safeguard
    assert math.isnan(exponential(float("nan")))

    # Logarithm
    assert logarithm(math.e) == pytest.approx(1.0)
    assert math.isnan(logarithm(0.0))
    assert math.isnan(logarithm(-1.0))
    assert math.isnan(logarithm(float("nan")))

    # SquareRoot
    assert square_root(9.0) == 3.0
    assert math.isnan(square_root(-4.0))
    assert math.isnan(square_root(float("nan")))

    # Maximum & Minimum
    assert maximum(10.0, 20.0) == 20.0
    assert minimum(10.0, 20.0) == 10.0
    assert math.isnan(maximum(float("nan"), 10.0))
    assert math.isnan(minimum(10.0, float("nan")))


def test_temporal_builders() -> None:
    """Verify GetDate and GetTime integer encoding."""
    assert get_date(2024, 1, 15) == 20240115
    assert get_date(2016, 12, 31) == 20161231
    assert get_date() == 20160101

    assert get_time(14, 30, 45) == 143045
    assert get_time(9, 5, 0) == 90500
    assert get_time() == 0


def test_rank_extractors() -> None:
    """Verify IndicatorHighest and IndicatorLowest ranking and error bounds."""
    # Data: chronological [10, 15, 12, 18, 14]
    # At shift=0, period=5 window: 14 (shift 0), 18 (shift 1), 12 (shift 2), 15 (shift 3), 10 (shift 4)
    data = np.array([10.0, 15.0, 12.0, 18.0, 14.0])

    # Sorted descending: [18, 15, 14, 12, 10]
    assert indicator_highest(data, period=5, nth_value=0, shift=0) == 18.0
    assert indicator_highest(data, period=5, nth_value=1, shift=0) == 15.0
    assert indicator_highest(data, period=5, nth_value=2, shift=0) == 14.0
    assert indicator_highest(data, period=5, nth_value=3, shift=0) == 12.0
    assert indicator_highest(data, period=5, nth_value=4, shift=0) == 10.0

    # Sorted ascending: [10, 12, 14, 15, 18]
    assert indicator_lowest(data, period=5, nth_value=0, shift=0) == 10.0
    assert indicator_lowest(data, period=5, nth_value=1, shift=0) == 12.0
    assert indicator_lowest(data, period=5, nth_value=2, shift=0) == 14.0
    assert indicator_lowest(data, period=5, nth_value=3, shift=0) == 15.0
    assert indicator_lowest(data, period=5, nth_value=4, shift=0) == 18.0

    # Out of range NthValue returns -1
    assert indicator_highest(data, period=5, nth_value=-1, shift=0) == -1.0
    assert indicator_highest(data, period=5, nth_value=5, shift=0) == -1.0
    assert indicator_lowest(data, period=5, nth_value=-1, shift=0) == -1.0
    assert indicator_lowest(data, period=5, nth_value=5, shift=0) == -1.0

    # Period < 2 or NaN in window
    assert indicator_highest(data, period=1, nth_value=0) == -1.0
    assert indicator_lowest(data, period=1, nth_value=0) == -1.0
    assert indicator_highest(data, period=10, nth_value=0) == -1.0
    assert indicator_lowest(data, period=10, nth_value=0) == -1.0


def test_pip_conversions() -> None:
    """Verify price-to-pip and pip-to-price conversions with various pip sizes."""
    # 5-digit quote (point = 0.00001, pip_size = 0.0001)
    assert resolve_pip_size(point=0.00001, digits=5) == pytest.approx(0.0001)
    assert convert_price_to_pips(0.0020, point=0.00001, digits=5) == pytest.approx(20.0)
    assert convert_pips_to_price(20.0, point=0.00001, digits=5) == pytest.approx(0.0020)

    # 3-digit quote (point = 0.001, pip_size = 0.01)
    assert resolve_pip_size(point=0.001, digits=3) == pytest.approx(0.01)
    assert convert_price_to_pips(0.50, point=0.001, digits=3) == pytest.approx(50.0)
    assert convert_pips_to_price(50.0, point=0.001, digits=3) == pytest.approx(0.50)

    # 4-digit quote (point = 0.0001, digits = 4)
    assert resolve_pip_size(point=0.0001, digits=4) == pytest.approx(0.0001)
    assert convert_price_to_pips(0.0020, point=0.0001, digits=4) == pytest.approx(20.0)

    # Explicit override pip size
    assert convert_price_to_pips(0.05, pip_size=0.01) == pytest.approx(5.0)
    assert convert_pips_to_price(5.0, pip_size=0.01) == pytest.approx(0.05)

    # Default fallback
    assert resolve_pip_size() == 0.0001
    assert convert_price_to_pips(0.0010) == pytest.approx(10.0)
    assert convert_pips_to_price(10.0) == pytest.approx(0.0010)

    # NaN handling
    assert math.isnan(convert_price_to_pips(float("nan")))
    assert math.isnan(convert_pips_to_price(float("nan")))


@pytest.mark.anyio
async def test_async_broker_pip_conversions() -> None:
    """Verify live MT5 broker symbol integration using async symbol.Point()."""

    class AsyncMockSymbol:
        """Simulates native MT5 SymbolInfo proxy."""

        async def Point(self) -> float:  # noqa: N802
            return 0.00001

        async def Digits(self) -> int:  # noqa: N802
            return 5

    mock_sym = AsyncMockSymbol()

    pips = await convert_price_to_pips_symbol(0.0035, mock_sym)
    assert pips == pytest.approx(35.0)

    price = await convert_pips_to_price_symbol(35.0, mock_sym)
    assert price == pytest.approx(0.0035)

    # Sync mock support
    class SyncMockSymbol:
        def Point(self) -> float:  # noqa: N802
            return 0.001

        def Digits(self) -> int:  # noqa: N802
            return 3

    sync_sym = SyncMockSymbol()
    assert await convert_price_to_pips_symbol(0.25, sync_sym) == pytest.approx(25.0)
    assert await convert_pips_to_price_symbol(25.0, sync_sym) == pytest.approx(0.25)


def test_custom_functions() -> None:
    """Verify registration, dispatch, and fallback for custom functions."""
    # Unregistered function raises NotImplementedError
    with pytest.raises(NotImplementedError):
        custom_function("unregistered_fn", 1, 2)

    # Explicit handler parameter
    res = custom_function("adhoc", 3, 4, handler=lambda a, b: a * b + 1)
    assert res == 13

    # Registration in registry
    register_custom_function("cubic", lambda x: x**3)
    assert custom_function("cubic", 3) == 27


def test_functions_facade() -> None:
    """Verify Functions facade class instance methods and broker defaults."""
    funcs = Functions(default_point=0.00001, default_digits=5)

    assert funcs.plus(5.0, 10.0) == 15.0
    assert funcs.minus(10.0, 3.0) == 7.0
    assert funcs.multiplication(3.0, 4.0) == 12.0
    assert funcs.division(12.0, 3.0) == 4.0
    assert funcs.abs_val(-9.0) == 9.0
    assert funcs.round_to_decimals(1.23456, decimals=2) == 1.23
    assert funcs.exponential(0.0) == pytest.approx(1.0)
    assert funcs.logarithm(1.0) == pytest.approx(0.0)
    assert funcs.square_root(16.0) == 4.0
    assert funcs.maximum(5.0, 8.0) == 8.0
    assert funcs.minimum(5.0, 8.0) == 5.0

    assert funcs.get_date(2024, 6, 1) == 20240601
    assert funcs.get_time(12, 0, 0) == 120000

    arr = np.array([10.0, 20.0, 30.0])
    assert funcs.indicator_highest(arr, period=3, nth_value=0) == 30.0
    assert funcs.indicator_lowest(arr, period=3, nth_value=0) == 10.0

    # Uses instance default point=0.00001 and digits=5 -> pip=0.0001
    assert funcs.to_pips(0.0015) == pytest.approx(15.0)
    assert funcs.to_price(15.0) == pytest.approx(0.0015)
