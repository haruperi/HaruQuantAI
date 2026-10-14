"""Quantitative arithmetic, math, temporal, ranking, and pip conversion blocks.

Description:
    Provides consolidated function building blocks matching StrategyQuant X:
    - Arithmetic operators: Plus, Minus, Multiplication, and Division with
      safe Double.MAX_VALUE ceiling on division by zero.
    - Mathematical primitives: Abs, Round, Exponential, Logarithm, SquareRoot,
      Maximum, Minimum.
    - Temporal numeric builders: GetDate (YYYYMMDD integer) and GetTime (HHMMSS
      integer).
    - Window rank extractors: IndicatorHighest and IndicatorLowest returning the
      Nth-ranked value over a historical rolling period.
    - Pip conversions: ConvertToPips and ConvertToRealPips integrating live MT5
      broker symbol point resolution (`symbol.Point()`) with 3/5-digit scaling.
    - Custom function: Extensible registry and dispatcher for user functions.
    - Functions: Unified facade class providing consolidated function evaluation.

Purpose:
    FEAT-SERVICES-FUNCTIONS: Quantitative arithmetic, math, temporal, ranking,
    and pip conversion building blocks.

Key Capabilities:
    - FR-SERVICES-FUNCTION-ARITHMETIC: Basic arithmetic building blocks
      with zero-division safeguard.
      Associated: `plus()`, `minus()`, `multiplication()`, `division()`.
      Logging: DEBUG on operation execution with operand values and result.
    - FR-SERVICES-FUNCTION-MATH: Standard mathematical primitives.
      Associated: `abs_val()`, `round_to_decimals()`, `exponential()`,
      `logarithm()`, `square_root()`, `maximum()`, `minimum()`.
      Logging: DEBUG on math evaluation.
    - FR-SERVICES-FUNCTION-TEMPORAL: Calendar date and clock time numeric builders.
      Associated: `get_date()`, `get_time()`.
      Logging: DEBUG on temporal encoding.
    - FR-SERVICES-FUNCTION-RANK: Rolling window Nth-highest and Nth-lowest
      value extractors.
      Associated: `indicator_highest()`, `indicator_lowest()`.
      Logging: DEBUG on window rank extraction.
    - FR-SERVICES-FUNCTION-PIPS: Price-to-pips and pips-to-price conversions
      using broker `symbol.Point()` and pip sizing.
      Associated: `convert_price_to_pips()`, `convert_pips_to_price()`,
      `convert_price_to_pips_symbol()`, `convert_pips_to_price_symbol()`.
      Logging: DEBUG on price/pip conversion with point, digits, and pip size.
    - FR-SERVICES-FUNCTION-CUSTOM: Custom user-defined function invocation wrapper.
      Associated: `custom_function()`, `register_custom_function()`.
      Logging: DEBUG on custom function dispatch or registration.
    - FR-SERVICES-FUNCTIONS-FACADE: Consolidated Functions facade class.
      Associated: `Functions`.
      Logging: DEBUG on facade execution.

Python API Usage:
    ```python
    from app.services.utils.functions import (
        convert_price_to_pips,
        get_date,
        get_time,
        indicator_highest,
        plus,
    )

    total = plus(10.5, 2.5)  # 13.0
    dt_num = get_date(2024, 1, 15)  # 20240115
    tm_num = get_time(14, 30, 0)  # 143000
    pips = convert_price_to_pips(0.0020, point=0.00001, digits=5)  # 20.0
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_functions.py --no-cov
    ```
"""

from __future__ import annotations

import inspect
import math
from collections.abc import Callable
from typing import Any

from app.host.logging import get_logger
from app.services.utils.comparisons import resolve_shift_value

logger = get_logger(__name__)

SQX_MAX_VALUE: float = 1.7976931348623157e308
DEFAULT_PIP_SIZE: float = 0.0001
MIN_RANK_PERIOD: int = 2
DATE_YEAR_MULTIPLIER: int = 10000
DATE_MONTH_MULTIPLIER: int = 100
TIME_HOUR_MULTIPLIER: int = 10000
TIME_MINUTE_MULTIPLIER: int = 100
POINT_TO_PIP_MULTIPLIER: float = 10.0
POINT_TOLERANCE: float = 1e-9
POINT_5_DIGIT: float = 1e-5
POINT_3_DIGIT: float = 1e-3

_CUSTOM_REGISTRY: dict[str, Callable[..., Any]] = {}


def plus(left: Any, right: Any, shift: int = 0) -> float:
    """Evaluate addition of two operands at historical bar shift.

    Args:
        left: Left operand (scalar, series, array, or callable).
        right: Right operand (scalar, series, array, or callable).
        shift: Historical bar offset.

    Returns:
        Sum as float, or NaN if either operand is invalid.
    """
    v1 = resolve_shift_value(left, shift)
    v2 = resolve_shift_value(right, shift)
    if math.isnan(v1) or math.isnan(v2):
        return float("nan")
    res = v1 + v2
    logger.debug(
        "FR-SERVICES-FUNCTION-ARITHMETIC: plus(shift=%d) %s + %s = %s",
        shift,
        v1,
        v2,
        res,
    )
    return res


def minus(left: Any, right: Any, shift: int = 0) -> float:
    """Evaluate subtraction of two operands at historical bar shift.

    Args:
        left: Left operand.
        right: Right operand.
        shift: Historical bar offset.

    Returns:
        Difference as float, or NaN if either operand is invalid.
    """
    v1 = resolve_shift_value(left, shift)
    v2 = resolve_shift_value(right, shift)
    if math.isnan(v1) or math.isnan(v2):
        return float("nan")
    res = v1 - v2
    logger.debug(
        "FR-SERVICES-FUNCTION-ARITHMETIC: minus(shift=%d) %s - %s = %s",
        shift,
        v1,
        v2,
        res,
    )
    return res


def multiplication(left: Any, right: Any, shift: int = 0) -> float:
    """Evaluate multiplication of two operands at historical bar shift.

    Args:
        left: Left operand.
        right: Right operand.
        shift: Historical bar offset.

    Returns:
        Product as float, or NaN if either operand is invalid.
    """
    v1 = resolve_shift_value(left, shift)
    v2 = resolve_shift_value(right, shift)
    if math.isnan(v1) or math.isnan(v2):
        return float("nan")
    res = v1 * v2
    logger.debug(
        "FR-SERVICES-FUNCTION-ARITHMETIC: mult(shift=%d) %s * %s = %s",
        shift,
        v1,
        v2,
        res,
    )
    return res


def division(left: Any, right: Any, shift: int = 0) -> float:
    """Evaluate division of two operands matching StrategyQuant X Division.

    When the divisor is 0, returns safe SQX_MAX_VALUE (Double.MAX_VALUE).

    Args:
        left: Dividend operand.
        right: Divisor operand.
        shift: Historical bar offset.

    Returns:
        Quotient as float, SQX_MAX_VALUE on division by zero, or NaN on invalid input.
    """
    v1 = resolve_shift_value(left, shift)
    v2 = resolve_shift_value(right, shift)
    if math.isnan(v1) or math.isnan(v2):
        return float("nan")
    res = v1 / v2 if v2 != 0.0 else SQX_MAX_VALUE
    logger.debug(
        "FR-SERVICES-FUNCTION-ARITHMETIC: div(shift=%d) %s / %s = %s",
        shift,
        v1,
        v2,
        res,
    )
    return res


def abs_val(val: Any, shift: int = 0) -> float:
    """Calculate absolute value matching SQX Abs.

    Args:
        val: Numeric operand.
        shift: Historical bar offset.

    Returns:
        Absolute float value, or NaN.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v):
        return float("nan")
    res = abs(v)
    logger.debug("FR-SERVICES-FUNCTION-MATH: abs_val(%s) = %s", v, res)
    return res


def round_to_decimals(val: Any, decimals: int = 5, shift: int = 0) -> float:
    """Round operand to specified decimal places matching SQX Round.

    Args:
        val: Numeric operand.
        decimals: Number of decimal places (default 5).
        shift: Historical bar offset.

    Returns:
        Rounded float value, or NaN.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v):
        return float("nan")
    res = round(v, decimals)
    logger.debug(
        "FR-SERVICES-FUNCTION-MATH: round_to_decimals(%s, dec=%d) = %s",
        v,
        decimals,
        res,
    )
    return res


def exponential(val: Any, shift: int = 0) -> float:
    """Calculate natural exponential (e^x) matching SQX Exponential.

    Args:
        val: Numeric exponent.
        shift: Historical bar offset.

    Returns:
        e^val as float, or NaN.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v):
        return float("nan")
    try:
        res = math.exp(v)
    except OverflowError:
        res = SQX_MAX_VALUE
    logger.debug("FR-SERVICES-FUNCTION-MATH: exp(%s) = %s", v, res)
    return res


def logarithm(val: Any, shift: int = 0) -> float:
    """Calculate natural logarithm ln(x) matching SQX Logarithm.

    Args:
        val: Numeric operand (> 0).
        shift: Historical bar offset.

    Returns:
        ln(val) as float, or NaN if val <= 0.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v) or v <= 0.0:
        return float("nan")
    res = math.log(v)
    logger.debug("FR-SERVICES-FUNCTION-MATH: log(%s) = %s", v, res)
    return res


def square_root(val: Any, shift: int = 0) -> float:
    """Calculate square root matching SQX SquareRoot.

    Args:
        val: Numeric operand (>= 0).
        shift: Historical bar offset.

    Returns:
        sqrt(val) as float, or NaN if val < 0.
    """
    v = resolve_shift_value(val, shift)
    if math.isnan(v) or v < 0.0:
        return float("nan")
    res = math.sqrt(v)
    logger.debug("FR-SERVICES-FUNCTION-MATH: sqrt(%s) = %s", v, res)
    return res


def maximum(val1: Any, val2: Any, shift: int = 0) -> float:
    """Calculate maximum of two operands matching SQX Maximum.

    Args:
        val1: First operand.
        val2: Second operand.
        shift: Historical bar offset.

    Returns:
        Larger value as float, or NaN.
    """
    v1 = resolve_shift_value(val1, shift)
    v2 = resolve_shift_value(val2, shift)
    if math.isnan(v1) or math.isnan(v2):
        return float("nan")
    res = max(v1, v2)
    logger.debug("FR-SERVICES-FUNCTION-MATH: max(%s, %s) = %s", v1, v2, res)
    return res


def minimum(val1: Any, val2: Any, shift: int = 0) -> float:
    """Calculate minimum of two operands matching SQX Minimum.

    Args:
        val1: First operand.
        val2: Second operand.
        shift: Historical bar offset.

    Returns:
        Smaller value as float, or NaN.
    """
    v1 = resolve_shift_value(val1, shift)
    v2 = resolve_shift_value(val2, shift)
    if math.isnan(v1) or math.isnan(v2):
        return float("nan")
    res = min(v1, v2)
    logger.debug("FR-SERVICES-FUNCTION-MATH: min(%s, %s) = %s", v1, v2, res)
    return res


def get_date(year: int = 2016, month: int = 1, day: int = 1) -> int:
    """Encode date as integer YYYYMMDD matching SQX GetDate.

    Args:
        year: Full calendar year (e.g. 2024).
        month: Month number 1..12.
        day: Day number 1..31.

    Returns:
        Integer encoded as YYYYMMDD.
    """
    res = year * DATE_YEAR_MULTIPLIER + month * DATE_MONTH_MULTIPLIER + day
    logger.debug(
        "FR-SERVICES-FUNCTION-TEMPORAL: get_date(%04d-%02d-%02d) = %d",
        year,
        month,
        day,
        res,
    )
    return res


def get_time(hour: int = 0, minute: int = 0, second: int = 0) -> int:
    """Encode time as integer HHMMSS matching SQX GetTime.

    Args:
        hour: Hour number 0..23.
        minute: Minute number 0..59.
        second: Second number 0..59.

    Returns:
        Integer encoded as HHMMSS.
    """
    res = hour * TIME_HOUR_MULTIPLIER + minute * TIME_MINUTE_MULTIPLIER + second
    logger.debug(
        "FR-SERVICES-FUNCTION-TEMPORAL: get_time(%02d:%02d:%02d) = %d",
        hour,
        minute,
        second,
        res,
    )
    return res


def indicator_highest(
    indicator: Any,
    period: int = 5,
    nth_value: int = 0,
    shift: int = 0,
) -> float:
    """Extract Nth highest indicator value in a period matching SQX IndicatorHighest.

    NthValue=0 means highest, 1 means second highest, etc.

    Args:
        indicator: Indicator series or callable.
        period: Period (bars back) checked (minimum 2).
        nth_value: 0-indexed ranking position.
        shift: Historical bar offset.

    Returns:
        Nth highest value as float, or -1.0 if out of bounds or invalid.
    """
    if period < MIN_RANK_PERIOD or nth_value < 0 or nth_value >= period:
        logger.debug(
            "FR-SERVICES-FUNCTION-RANK: indicator_highest invalid "
            "period=%d, nth=%d -> -1.0",
            period,
            nth_value,
        )
        return -1.0

    vals: list[float] = []
    for i in range(period):
        v = resolve_shift_value(indicator, shift + i)
        if math.isnan(v):
            return -1.0
        vals.append(v)

    vals.sort(reverse=True)
    res = vals[nth_value]
    logger.debug(
        "FR-SERVICES-FUNCTION-RANK: indicator_highest(period=%d, nth=%d, "
        "shift=%d) = %s",
        period,
        nth_value,
        shift,
        res,
    )
    return res


def indicator_lowest(
    indicator: Any,
    period: int = 5,
    nth_value: int = 0,
    shift: int = 0,
) -> float:
    """Extract Nth lowest indicator value in a period matching SQX IndicatorLowest.

    NthValue=0 means lowest, 1 means second lowest, etc.

    Args:
        indicator: Indicator series or callable.
        period: Period (bars back) checked (minimum 2).
        nth_value: 0-indexed ranking position.
        shift: Historical bar offset.

    Returns:
        Nth lowest value as float, or -1.0 if out of bounds or invalid.
    """
    if period < MIN_RANK_PERIOD or nth_value < 0 or nth_value >= period:
        logger.debug(
            "FR-SERVICES-FUNCTION-RANK: indicator_lowest invalid "
            "period=%d, nth=%d -> -1.0",
            period,
            nth_value,
        )
        return -1.0

    vals: list[float] = []
    for i in range(period):
        v = resolve_shift_value(indicator, shift + i)
        if math.isnan(v):
            return -1.0
        vals.append(v)

    vals.sort()
    res = vals[nth_value]
    logger.debug(
        "FR-SERVICES-FUNCTION-RANK: indicator_lowest(period=%d, nth=%d, shift=%d) = %s",
        period,
        nth_value,
        shift,
        res,
    )
    return res


def resolve_pip_size(
    point: float | None = None,
    digits: int | None = None,
    pip_size: float | None = None,
) -> float:
    """Resolve effective pip size from point, digits, or explicit pip size.

    Scaling logic:
    - If pip_size > 0 is provided, uses it directly.
    - If point is provided: for 3-digit and 5-digit broker quotes,
      pip size = point * 10.0; for others, pip size = point.
    - Defaults to standard Forex pip size 0.0001.

    Args:
        point: Instrument minimum price point (e.g. from symbol.Point()).
        digits: Quote precision digits (e.g. from symbol.Digits()).
        pip_size: Explicit override pip size.

    Returns:
        Effective pip size as float.
    """
    if pip_size is not None and pip_size > 0.0:
        return float(pip_size)

    if point is not None and point > 0.0:
        is_scaled_digits = digits in (3, 5)
        is_scaled_point = (
            abs(point - POINT_5_DIGIT) < POINT_TOLERANCE
            or abs(point - POINT_3_DIGIT) < POINT_TOLERANCE
        )
        if is_scaled_digits or (digits is None and is_scaled_point):
            return float(point * POINT_TO_PIP_MULTIPLIER)
        return float(point)

    return DEFAULT_PIP_SIZE


def convert_price_to_pips(
    price_diff: float,
    *,
    point: float | None = None,
    digits: int | None = None,
    pip_size: float | None = None,
) -> float:
    """Convert price difference to pips matching SQX ConvertPriceToPips.

    Example: converts 0.002 to 20 pips for 5-digit quote with point=0.00001.

    Args:
        price_diff: Raw price difference (e.g. 0.0020).
        point: Instrument point (e.g. from MT5 symbol.Point()).
        digits: Instrument digits.
        pip_size: Explicit pip size override.

    Returns:
        Pip value as float, or NaN on invalid pip sizing.
    """
    eff_pip = resolve_pip_size(point=point, digits=digits, pip_size=pip_size)
    if eff_pip <= 0.0 or math.isnan(price_diff):
        return float("nan")
    res = float(price_diff / eff_pip)
    logger.debug(
        "FR-SERVICES-FUNCTION-PIPS: convert_price_to_pips(%f, pip=%f) = %f",
        price_diff,
        eff_pip,
        res,
    )
    return res


def convert_pips_to_price(
    pips: float,
    *,
    point: float | None = None,
    digits: int | None = None,
    pip_size: float | None = None,
) -> float:
    """Convert pips to real price level matching SQX ConvertPipsToPrice.

    Example: converts 20 pips to 0.002 for 5-digit quote with point=0.00001.

    Args:
        pips: Number of pips (e.g. 20.0).
        point: Instrument point (e.g. from MT5 symbol.Point()).
        digits: Instrument digits.
        pip_size: Explicit pip size override.

    Returns:
        Price offset as float, or NaN on invalid pip sizing.
    """
    eff_pip = resolve_pip_size(point=point, digits=digits, pip_size=pip_size)
    if eff_pip <= 0.0 or math.isnan(pips):
        return float("nan")
    res = float(pips * eff_pip)
    logger.debug(
        "FR-SERVICES-FUNCTION-PIPS: convert_pips_to_price(%f, pip=%f) = %f",
        pips,
        eff_pip,
        res,
    )
    return res


async def convert_price_to_pips_symbol(price_diff: float, symbol: Any) -> float:
    """Convert price difference to pips querying real MT5 broker symbol properties.

    Uses `await symbol.Point()` and `await symbol.Digits()` matching
    `example_04_symbol()` in `scripts/examples/brokers.py`.

    Args:
        price_diff: Raw price difference.
        symbol: MT5 SymbolInfo proxy or mock.

    Returns:
        Converted pips as float.
    """
    pt_call = symbol.Point()
    pt = await pt_call if inspect.isawaitable(pt_call) else pt_call

    dig_call = symbol.Digits()
    dig = await dig_call if inspect.isawaitable(dig_call) else dig_call

    return convert_price_to_pips(
        price_diff, point=float(pt), digits=int(dig) if dig is not None else None
    )


async def convert_pips_to_price_symbol(pips: float, symbol: Any) -> float:
    """Convert pips to real price querying real MT5 broker symbol properties.

    Uses `await symbol.Point()` and `await symbol.Digits()` matching
    `example_04_symbol()` in `scripts/examples/brokers.py`.

    Args:
        pips: Pip count.
        symbol: MT5 SymbolInfo proxy or mock.

    Returns:
        Converted price offset as float.
    """
    pt_call = symbol.Point()
    pt = await pt_call if inspect.isawaitable(pt_call) else pt_call

    dig_call = symbol.Digits()
    dig = await dig_call if inspect.isawaitable(dig_call) else dig_call

    return convert_pips_to_price(
        pips, point=float(pt), digits=int(dig) if dig is not None else None
    )


def register_custom_function(name: str, handler: Callable[..., Any]) -> None:
    """Register custom function handler for CustomFunction block evaluation.

    Args:
        name: Unique function identifier.
        handler: Callable implementing the function.
    """
    _CUSTOM_REGISTRY[name] = handler
    logger.debug("FR-SERVICES-FUNCTION-CUSTOM: registered '%s'", name)


def custom_function(
    function_name: str,
    *args: Any,
    handler: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> Any:
    """Execute custom function matching StrategyQuant X CustomFunction.

    Args:
        function_name: Identifier of function.
        *args: Positional arguments.
        handler: Optional explicit callable override.
        **kwargs: Keyword arguments.

    Returns:
        Evaluation outcome.

    Raises:
        NotImplementedError: If function is unregistered and no handler is provided.
    """
    fn = handler if handler is not None else _CUSTOM_REGISTRY.get(function_name)
    if fn is None:
        logger.debug("FR-SERVICES-FUNCTION-CUSTOM: '%s' not registered", function_name)
        raise NotImplementedError(
            f"Custom function '{function_name}' is not registered."
        )

    res = fn(*args, **kwargs)
    logger.debug("FR-SERVICES-FUNCTION-CUSTOM: '%s' executed -> %s", function_name, res)
    return res


class Functions:
    """Consolidated facade for StrategyQuant X functions building blocks."""

    def __init__(
        self,
        default_point: float | None = None,
        default_digits: int | None = None,
    ) -> None:
        """Initialize Functions facade with optional broker defaults.

        Args:
            default_point: Default point size (e.g. 0.00001).
            default_digits: Default digits precision (e.g. 5).
        """
        self._point = default_point
        self._digits = default_digits
        logger.debug(
            "FR-SERVICES-FUNCTIONS-FACADE: Initialized facade (point=%s, digits=%s)",
            default_point,
            default_digits,
        )

    def plus(self, left: Any, right: Any, shift: int = 0) -> float:
        """Calculate addition of two operands."""
        return plus(left, right, shift=shift)

    def minus(self, left: Any, right: Any, shift: int = 0) -> float:
        """Calculate subtraction of two operands."""
        return minus(left, right, shift=shift)

    def multiplication(self, left: Any, right: Any, shift: int = 0) -> float:
        """Calculate multiplication of two operands."""
        return multiplication(left, right, shift=shift)

    def division(self, left: Any, right: Any, shift: int = 0) -> float:
        """Calculate division of two operands."""
        return division(left, right, shift=shift)

    def abs_val(self, val: Any, shift: int = 0) -> float:
        """Calculate absolute value."""
        return abs_val(val, shift=shift)

    def round_to_decimals(self, val: Any, decimals: int = 5, shift: int = 0) -> float:
        """Round value to specified decimals."""
        return round_to_decimals(val, decimals=decimals, shift=shift)

    def exponential(self, val: Any, shift: int = 0) -> float:
        """Calculate natural exponential e^x."""
        return exponential(val, shift=shift)

    def logarithm(self, val: Any, shift: int = 0) -> float:
        """Calculate natural logarithm ln(x)."""
        return logarithm(val, shift=shift)

    def square_root(self, val: Any, shift: int = 0) -> float:
        """Calculate square root."""
        return square_root(val, shift=shift)

    def maximum(self, val1: Any, val2: Any, shift: int = 0) -> float:
        """Calculate maximum of two values."""
        return maximum(val1, val2, shift=shift)

    def minimum(self, val1: Any, val2: Any, shift: int = 0) -> float:
        """Calculate minimum of two values."""
        return minimum(val1, val2, shift=shift)

    def get_date(self, year: int = 2016, month: int = 1, day: int = 1) -> int:
        """Encode date as integer YYYYMMDD."""
        return get_date(year=year, month=month, day=day)

    def get_time(self, hour: int = 0, minute: int = 0, second: int = 0) -> int:
        """Encode time as integer HHMMSS."""
        return get_time(hour=hour, minute=minute, second=second)

    def indicator_highest(
        self,
        indicator: Any,
        period: int = 5,
        nth_value: int = 0,
        shift: int = 0,
    ) -> float:
        """Extract Nth highest indicator value in period."""
        return indicator_highest(
            indicator, period=period, nth_value=nth_value, shift=shift
        )

    def indicator_lowest(
        self,
        indicator: Any,
        period: int = 5,
        nth_value: int = 0,
        shift: int = 0,
    ) -> float:
        """Extract Nth lowest indicator value in period."""
        return indicator_lowest(
            indicator, period=period, nth_value=nth_value, shift=shift
        )

    def to_pips(
        self,
        price_diff: float,
        *,
        point: float | None = None,
        digits: int | None = None,
        pip_size: float | None = None,
    ) -> float:
        """Convert price difference to pips using instance defaults if omitted."""
        pt = self._point if point is None else point
        dig = self._digits if digits is None else digits
        return convert_price_to_pips(
            price_diff, point=pt, digits=dig, pip_size=pip_size
        )

    def to_price(
        self,
        pips: float,
        *,
        point: float | None = None,
        digits: int | None = None,
        pip_size: float | None = None,
    ) -> float:
        """Convert pips to real price level using instance defaults if omitted."""
        pt = self._point if point is None else point
        dig = self._digits if digits is None else digits
        return convert_pips_to_price(pips, point=pt, digits=dig, pip_size=pip_size)
