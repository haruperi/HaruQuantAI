"""Unit tests for discrete function building blocks and Functions facade."""

from __future__ import annotations

import asyncio
import math
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.include.blocks.functions import (
    DATE_MONTH_MULTIPLIER,
    DATE_YEAR_MULTIPLIER,
    DEFAULT_PIP_SIZE,
    FLOAT_MAX_VALUE,
    POINT_3_DIGIT,
    POINT_5_DIGIT,
    POINT_TO_PIP_MULTIPLIER,
    Functions,
    abs_val,
    abs_val_spec,
    convert_pips_to_price,
    convert_pips_to_price_spec,
    convert_pips_to_price_symbol,
    convert_price_to_pips,
    convert_price_to_pips_spec,
    convert_price_to_pips_symbol,
    custom_function,
    custom_function_spec,
    division,
    division_spec,
    exponential,
    exponential_spec,
    get_date,
    get_date_spec,
    get_time,
    get_time_spec,
    indicator_highest,
    indicator_highest_spec,
    indicator_lowest,
    indicator_lowest_spec,
    logarithm,
    logarithm_spec,
    maximum,
    maximum_spec,
    minimum,
    minimum_spec,
    minus,
    minus_spec,
    multiplication,
    multiplication_spec,
    plus,
    plus_spec,
    register_custom_function,
    resolve_pip_size,
    round_to_decimals,
    round_to_decimals_spec,
    square_root,
    square_root_spec,
)


def test_arithmetic_blocks_scalar_and_series() -> None:
    """Verify plus, minus, multiplication, division scalar and series shift evaluations."""
    # plus
    assert plus(10.0, 5.0) == 15.0
    assert math.isnan(plus(float("nan"), 5.0))
    # In time series convention, newest bar is at end (index -1 = shift 0).
    # shift=1 selects index len-1-1 = 1 (value 2.0).
    assert plus([1.0, 2.0, 3.0], [10.0, 10.0, 10.0], shift=1) == 12.0
    assert plus([1.0, 2.0, 3.0], 10.0, shift=0) == 13.0

    # minus
    assert minus(10.0, 3.0) == 7.0
    assert minus([10.0, 20.0, 30.0], [1.0, 2.0, 3.0], shift=0) == 27.0
    assert minus([10.0, 20.0, 30.0], [1.0, 2.0, 3.0], shift=2) == 9.0
    assert math.isnan(minus(float("nan"), 5.0))

    # multiplication
    assert multiplication(4.0, 2.5) == 10.0
    assert multiplication([2.0, 3.0, 4.0], [2.0, 2.0, 2.0], shift=1) == 6.0
    assert multiplication([2.0, 3.0, 4.0], 2.0, shift=0) == 8.0
    assert math.isnan(multiplication(5.0, float("nan")))

    # division
    assert division(10.0, 2.0) == 5.0
    assert division(10.0, 0.0) == FLOAT_MAX_VALUE
    assert division([10.0, 20.0], [2.0, 4.0], shift=1) == 5.0
    assert division([10.0, 20.0], [2.0, 4.0], shift=0) == 5.0
    assert math.isnan(division(float("nan"), 2.0))


def test_math_blocks_elementary() -> None:
    """Verify abs_val, round_to_decimals, exponential, logarithm, square_root."""
    # abs_val
    assert abs_val(-42.5) == 42.5
    assert abs_val(42.5) == 42.5
    assert math.isnan(abs_val(float("nan")))
    # For [-10.0, -20.0]: shift 0 is -20.0, shift 1 is -10.0
    assert abs_val([-10.0, -20.0], shift=0) == 20.0
    assert abs_val([-10.0, -20.0], shift=1) == 10.0

    # round_to_decimals
    assert round_to_decimals(1.234567, decimals=2) == 1.23
    assert round_to_decimals(1.234567, decimals=4) == 1.2346
    assert math.isnan(round_to_decimals(float("nan")))

    # exponential
    assert math.isclose(exponential(1.0), math.e, rel_tol=1e-9)
    assert exponential(1000.0) == FLOAT_MAX_VALUE
    assert math.isnan(exponential(float("nan")))

    # logarithm
    assert math.isclose(logarithm(math.e), 1.0, rel_tol=1e-9)
    assert math.isnan(logarithm(0.0))
    assert math.isnan(logarithm(-5.0))
    assert math.isnan(logarithm(float("nan")))

    # square_root
    assert square_root(16.0) == 4.0
    assert square_root(0.0) == 0.0
    assert math.isnan(square_root(-1.0))
    assert math.isnan(square_root(float("nan")))


def test_extrema_blocks() -> None:
    """Verify maximum and minimum blocks."""
    assert maximum(5.0, 10.0) == 10.0
    assert maximum(12.0, -3.0) == 12.0
    assert math.isnan(maximum(float("nan"), 1.0))

    assert minimum(5.0, 10.0) == 5.0
    assert minimum(12.0, -3.0) == -3.0
    assert math.isnan(minimum(1.0, float("nan")))

    # Series shift: s1[-1]=30 (shift 0), s1[0]=10 (shift 2)
    s1 = [10.0, 20.0, 30.0]
    s2 = [15.0, 15.0, 15.0]
    assert maximum(s1, s2, shift=0) == 30.0
    assert maximum(s1, s2, shift=2) == 15.0
    assert minimum(s1, s2, shift=0) == 15.0
    assert minimum(s1, s2, shift=2) == 10.0


def test_temporal_encoding_blocks() -> None:
    """Verify get_date and get_time encoding logic."""
    # YYYYMMDD
    assert get_date(year=2024, month=10, day=28) == 20241028
    assert get_date() == 20160101
    assert DATE_YEAR_MULTIPLIER == 10000
    assert DATE_MONTH_MULTIPLIER == 100

    # HHMMSS
    assert get_time(hour=14, minute=30, second=45) == 143045
    assert get_time() == 0


def test_ranking_blocks_highest_lowest() -> None:
    """Verify indicator_highest and indicator_lowest rolling rankings."""
    # In time series convention, indices are [0, 1, 2, 3, 4] -> shift 0 is series[4]=30,
    # shift 1 is series[3]=40, shift 2 is series[2]=20, shift 3 is series[1]=50, shift 4 is series[0]=10.
    # Window of size 5 backward from shift 0 is [30, 40, 20, 50, 10].
    # Sorted descending: [50, 40, 30, 20, 10].
    series = [10.0, 50.0, 20.0, 40.0, 30.0]

    assert indicator_highest(series, period=5, nth_value=0, shift=0) == 50.0
    assert indicator_highest(series, period=5, nth_value=1, shift=0) == 40.0
    assert indicator_highest(series, period=5, nth_value=4, shift=0) == 10.0

    # Sorted ascending: [10, 20, 30, 40, 50].
    assert indicator_lowest(series, period=5, nth_value=0, shift=0) == 10.0
    assert indicator_lowest(series, period=5, nth_value=1, shift=0) == 20.0
    assert indicator_lowest(series, period=5, nth_value=4, shift=0) == 50.0

    # Out of range period or rank
    assert indicator_highest(series, period=1, nth_value=0) == -1.0
    assert indicator_highest(series, period=5, nth_value=5) == -1.0
    assert indicator_highest(series, period=5, nth_value=-1) == -1.0
    assert indicator_lowest(series, period=1, nth_value=0) == -1.0
    assert indicator_lowest(series, period=5, nth_value=5) == -1.0
    assert indicator_lowest(series, period=5, nth_value=-1) == -1.0

    # NaN handling
    series_nan = [10.0, float("nan"), 20.0]
    assert indicator_highest(series_nan, period=3, nth_value=0) == -1.0
    assert indicator_lowest(series_nan, period=3, nth_value=0) == -1.0


def test_pip_size_resolution() -> None:
    """Verify resolve_pip_size for various instruments and precision."""
    # Default Forex
    assert resolve_pip_size() == DEFAULT_PIP_SIZE

    # Explicit override
    assert resolve_pip_size(pip_size=0.01) == 0.01

    # 5-digit quote scaling (EURUSD point=0.00001 -> pip=0.0001)
    assert resolve_pip_size(point=0.00001, digits=5) == 0.0001
    assert (
        resolve_pip_size(point=POINT_5_DIGIT) == POINT_5_DIGIT * POINT_TO_PIP_MULTIPLIER
    )

    # 3-digit quote scaling (USDJPY point=0.001 -> pip=0.01)
    assert resolve_pip_size(point=0.001, digits=3) == 0.01
    assert (
        resolve_pip_size(point=POINT_3_DIGIT) == POINT_3_DIGIT * POINT_TO_PIP_MULTIPLIER
    )

    # 4-digit or 2-digit quote unscaled (point = pip)
    assert resolve_pip_size(point=0.0001, digits=4) == 0.0001
    assert resolve_pip_size(point=0.01, digits=2) == 0.01


def test_pip_conversion_blocks() -> None:
    """Verify convert_price_to_pips and convert_pips_to_price calculations."""
    # 0.002 on 5-digit quote (point=0.00001 -> pip=0.0001) is 20.0 pips
    assert convert_price_to_pips(0.002, point=0.00001, digits=5) == 20.0
    assert convert_pips_to_price(20.0, point=0.00001, digits=5) == 0.002

    # Series operand: [0.001, 0.003], shift 0 is 0.003 (30 pips), shift 1 is 0.001 (10 pips)
    assert convert_price_to_pips([0.001, 0.003], shift=0, pip_size=0.0001) == 30.0
    assert convert_price_to_pips([0.001, 0.003], shift=1, pip_size=0.0001) == 10.0
    assert convert_pips_to_price([10.0, 30.0], shift=0, pip_size=0.0001) == 0.003
    assert convert_pips_to_price([10.0, 30.0], shift=1, pip_size=0.0001) == 0.001

    # NaN operand
    assert math.isnan(convert_price_to_pips(float("nan")))
    assert math.isnan(convert_pips_to_price(float("nan")))


def test_pip_conversion_symbol_queries() -> None:
    """Verify async broker symbol conversion methods."""

    async def _run() -> None:
        # Mock synchronous symbol
        mock_sym = MagicMock()
        mock_sym.Point.return_value = 0.00001
        mock_sym.Digits.return_value = 5

        res_pips = await convert_price_to_pips_symbol(0.005, mock_sym)
        assert res_pips == 50.0

        res_price = await convert_pips_to_price_symbol(50.0, mock_sym)
        assert res_price == 0.005

        # Mock async/awaitable symbol
        async_sym = MagicMock()
        async_sym.Point = AsyncMock(return_value=0.001)
        async_sym.Digits = AsyncMock(return_value=3)

        res_pips_async = await convert_price_to_pips_symbol(0.05, async_sym)
        assert res_pips_async == 5.0

        res_price_async = await convert_pips_to_price_symbol(5.0, async_sym)
        assert res_price_async == 0.05

    asyncio.run(_run())


def test_custom_function_execution() -> None:
    """Verify custom function registration and execution."""
    register_custom_function("my_add_ten", lambda x: x + 10)
    assert custom_function("my_add_ten", 5) == 15

    # Explicit handler override
    assert custom_function("anything", 7, handler=lambda x: x * 3) == 21

    # Unregistered raises NotImplementedError
    with pytest.raises(NotImplementedError):
        custom_function("non_existent_func")


def test_functions_facade_complete_interface() -> None:
    """Verify Functions facade matches legacy facade and methods."""
    facade = Functions(default_point=0.00001, default_digits=5)

    assert facade.minus(10.0, 4.0) == 6.0
    assert facade.multiplication(3.0, 4.0) == 12.0
    assert facade.division(20.0, 4.0) == 5.0
    assert facade.abs_val(-99.0) == 99.0
    assert facade.round_to_decimals(3.14159, decimals=2) == 3.14
    assert math.isclose(facade.exponential(0.0), 1.0)
    assert math.isclose(facade.logarithm(1.0), 0.0)
    assert facade.square_root(25.0) == 5.0
    assert facade.maximum(10.0, 20.0) == 20.0
    assert facade.minimum(10.0, 20.0) == 10.0
    assert facade.get_date(2025, 12, 31) == 20251231
    assert facade.get_time(23, 59, 59) == 235959
    assert facade.indicator_highest([1, 5, 3], period=3, nth_value=0) == 5.0
    assert facade.indicator_lowest([1, 5, 3], period=3, nth_value=0) == 1.0

    # Pips via facade defaults
    assert facade.to_pips(0.002) == 20.0
    assert facade.to_price(20.0) == 0.002
    assert facade.resolve_pip_size() == 0.0001

    # Custom function via facade
    facade.register_custom_function("facade_square", lambda x: x * x)
    assert facade.custom_function("facade_square", 8) == 64

    # Functions does NOT have plus attribute
    assert not hasattr(facade, "plus")


def test_functions_facade_async_symbol_methods() -> None:
    """Verify static async methods on Functions facade."""

    async def _run() -> None:
        mock_sym = MagicMock()
        mock_sym.Point.return_value = 0.0001
        mock_sym.Digits.return_value = 4

        pips = await Functions.to_pips_symbol(0.002, mock_sym)
        assert pips == 20.0

        price = await Functions.to_price_symbol(20.0, mock_sym)
        assert price == 0.002

    asyncio.run(_run())


def test_block_specifications_present_and_valid() -> None:
    """Verify all 18 function blocks have valid metadata specs."""
    specs = [
        abs_val_spec,
        convert_pips_to_price_spec,
        convert_price_to_pips_spec,
        custom_function_spec,
        division_spec,
        exponential_spec,
        get_date_spec,
        get_time_spec,
        indicator_highest_spec,
        indicator_lowest_spec,
        logarithm_spec,
        maximum_spec,
        minimum_spec,
        minus_spec,
        multiplication_spec,
        plus_spec,
        round_to_decimals_spec,
        square_root_spec,
    ]
    for spec in specs:
        assert spec.id.startswith("function.")
        assert spec.category == "functions"
        assert len(spec.inputs) >= 1
        assert len(spec.outputs) == 1
        assert spec.is_causal is True
