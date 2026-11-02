"""Consolidated facade for function building blocks.

Description:
    Provides an object-oriented and namespace-bound API facade over discrete
    StrategyQuant-faithful quantitative arithmetic, mathematical, temporal,
    ranking, and pip conversion building blocks.
Purpose:
    FEAT-FUNCTIONS-BLOCKS: Quantitative function block library and facade.
Key Capabilities:
    - FR-function-facade: Unified object interface for all function blocks.
    - FR-function-arithmetic: Arithmetic operations (plus, minus, mult, div).
    - FR-function-pips: Broker-aware pip scaling and conversion methods.
Python API Usage:
    from app.extend.blocks.functions import Functions
    f = Functions(default_point=0.00001, default_digits=5)
    res = f.plus(10.0, 5.0)
CLI Usage:
    uv run pytest tests/extend/blocks/test_functions.py --no-cov
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.host.logging import get_logger
from app.extend.blocks.functions._common import (
    register_custom_function,
    resolve_pip_size,
)
from app.extend.blocks.functions.abs_val import abs_val
from app.extend.blocks.functions.convert_pips_to_price import (
    convert_pips_to_price,
    convert_pips_to_price_symbol,
)
from app.extend.blocks.functions.convert_price_to_pips import (
    convert_price_to_pips,
    convert_price_to_pips_symbol,
)
from app.extend.blocks.functions.custom_function import custom_function
from app.extend.blocks.functions.division import division
from app.extend.blocks.functions.exponential import exponential
from app.extend.blocks.functions.get_date import get_date
from app.extend.blocks.functions.get_time import get_time
from app.extend.blocks.functions.indicator_highest import indicator_highest
from app.extend.blocks.functions.indicator_lowest import indicator_lowest
from app.extend.blocks.functions.logarithm import logarithm
from app.extend.blocks.functions.maximum import maximum
from app.extend.blocks.functions.minimum import minimum
from app.extend.blocks.functions.minus import minus
from app.extend.blocks.functions.multiplication import multiplication
from app.extend.blocks.functions.plus import plus
from app.extend.blocks.functions.round_to_decimals import round_to_decimals
from app.extend.blocks.functions.square_root import square_root

logger = get_logger(__name__)

__all__ = ["Functions"]


class Functions:
    """Consolidated facade for function building blocks."""

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

    def resolve_pip_size(
        self,
        *,
        point: float | None = None,
        digits: int | None = None,
        pip_size: float | None = None,
    ) -> float:
        """Resolve effective pip size using instance defaults if omitted."""
        pt = self._point if point is None else point
        dig = self._digits if digits is None else digits
        return resolve_pip_size(point=pt, digits=dig, pip_size=pip_size)

    def to_pips(
        self,
        price_diff: Any,
        shift: int = 0,
        *,
        point: float | None = None,
        digits: int | None = None,
        pip_size: float | None = None,
    ) -> float:
        """Convert price difference to pips using instance defaults if omitted."""
        pt = self._point if point is None else point
        dig = self._digits if digits is None else digits
        return convert_price_to_pips(
            price_diff, shift=shift, point=pt, digits=dig, pip_size=pip_size
        )

    def to_price(
        self,
        pips: Any,
        shift: int = 0,
        *,
        point: float | None = None,
        digits: int | None = None,
        pip_size: float | None = None,
    ) -> float:
        """Convert pips to real price level using instance defaults if omitted."""
        pt = self._point if point is None else point
        dig = self._digits if digits is None else digits
        return convert_pips_to_price(
            pips, shift=shift, point=pt, digits=dig, pip_size=pip_size
        )

    @staticmethod
    async def to_pips_symbol(price_diff: Any, symbol: Any, shift: int = 0) -> float:
        """Convert price difference to pips querying broker symbol properties."""
        return await convert_price_to_pips_symbol(price_diff, symbol, shift=shift)

    @staticmethod
    async def to_price_symbol(pips: Any, symbol: Any, shift: int = 0) -> float:
        """Convert pips to real price querying broker symbol properties."""
        return await convert_pips_to_price_symbol(pips, symbol, shift=shift)

    @staticmethod
    def register_custom_function(name: str, handler: Callable[..., Any]) -> None:
        """Register custom function handler."""
        register_custom_function(name, handler)

    @staticmethod
    def custom_function(
        function_name: str,
        *args: Any,
        handler: Callable[..., Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Execute registered custom function by identifier."""
        return custom_function(function_name, *args, handler=handler, **kwargs)
