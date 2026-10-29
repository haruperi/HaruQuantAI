"""Consolidated facade for evaluating quantitative comparison blocks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.host.logging import get_logger
from app.include.blocks.comparisons._common import (
    DEFAULT_COMPARISON_PRECISION,
    DEFAULT_COUNT_PRECISION,
    calculate_ma,
    calculate_wma,
)
from app.include.blocks.comparisons.changes_down import changes_down
from app.include.blocks.comparisons.changes_up import changes_up
from app.include.blocks.comparisons.condition_and import condition_and
from app.include.blocks.comparisons.condition_not import condition_not
from app.include.blocks.comparisons.condition_or import condition_or
from app.include.blocks.comparisons.crosses_above import crosses_above
from app.include.blocks.comparisons.crosses_below import crosses_below
from app.include.blocks.comparisons.equals import equals
from app.include.blocks.comparisons.indicator_above_ma import indicator_above_ma
from app.include.blocks.comparisons.indicator_below_ma import indicator_below_ma
from app.include.blocks.comparisons.indicator_crosses_above_ma import (
    indicator_crosses_above_ma,
)
from app.include.blocks.comparisons.indicator_crosses_below_ma import (
    indicator_crosses_below_ma,
)
from app.include.blocks.comparisons.is_falling import is_falling
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.comparisons.is_greater_count import is_greater_count
from app.include.blocks.comparisons.is_greater_or_equal import is_greater_or_equal
from app.include.blocks.comparisons.is_greater_percentile import (
    is_greater_percentile,
)
from app.include.blocks.comparisons.is_lower import is_lower
from app.include.blocks.comparisons.is_lower_count import is_lower_count
from app.include.blocks.comparisons.is_lower_or_equal import is_lower_or_equal
from app.include.blocks.comparisons.is_lower_percentile import is_lower_percentile
from app.include.blocks.comparisons.is_rising import is_rising
from app.include.blocks.comparisons.not_equals import not_equals
from app.include.enums import MAType

logger = get_logger(__name__)


class Comparisons:
    """Consolidated facade for evaluating quantitative comparison blocks."""

    def __init__(
        self,
        left: Any = None,
        right: Any = None,
        precision: int = DEFAULT_COMPARISON_PRECISION,
    ) -> None:
        """Initialize Comparisons facade with optional default operands."""
        self._left = left
        self._right = right
        self._precision = precision
        logger.debug(
            "FR-SERVICES-COMPARISONS-FACADE: Initialized facade (p=%d)",
            precision,
            extra={"fr_id": "FR-SERVICES-COMPARISONS-FACADE", "precision": precision},
        )

    def _ops(
        self, left: Any, right: Any, precision: int | None
    ) -> tuple[Any, Any, int]:
        """Resolve default left, right, and precision operands."""
        return (
            self._left if left is None else left,
            self._right if right is None else right,
            self._precision if precision is None else precision,
        )

    def is_greater(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
        *,
        shift1: int | None = None,
        shift2: int | None = None,
        round_digits: int | None = None,
    ) -> bool:
        """Evaluate whether left > right."""
        l_op, r_op, p = self._ops(left, right, precision)
        return is_greater(
            l_op,
            r_op,
            shift,
            p,
            shift1=shift1,
            shift2=shift2,
            round_digits=round_digits,
        )

    def is_lower(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
        *,
        shift1: int | None = None,
        shift2: int | None = None,
        round_digits: int | None = None,
    ) -> bool:
        """Evaluate whether left < right."""
        l_op, r_op, p = self._ops(left, right, precision)
        return is_lower(
            l_op,
            r_op,
            shift,
            p,
            shift1=shift1,
            shift2=shift2,
            round_digits=round_digits,
        )

    def is_greater_or_equal(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
        *,
        shift1: int | None = None,
        shift2: int | None = None,
        round_digits: int | None = None,
    ) -> bool:
        """Evaluate whether left >= right."""
        l_op, r_op, p = self._ops(left, right, precision)
        return is_greater_or_equal(
            l_op,
            r_op,
            shift,
            p,
            shift1=shift1,
            shift2=shift2,
            round_digits=round_digits,
        )

    def is_lower_or_equal(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
        *,
        shift1: int | None = None,
        shift2: int | None = None,
        round_digits: int | None = None,
    ) -> bool:
        """Evaluate whether left <= right."""
        l_op, r_op, p = self._ops(left, right, precision)
        return is_lower_or_equal(
            l_op,
            r_op,
            shift,
            p,
            shift1=shift1,
            shift2=shift2,
            round_digits=round_digits,
        )

    def equals(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
        *,
        shift1: int | None = None,
        shift2: int | None = None,
        round_digits: int | None = None,
    ) -> bool:
        """Evaluate whether left == right."""
        l_op, r_op, p = self._ops(left, right, precision)
        return equals(
            l_op,
            r_op,
            shift,
            p,
            shift1=shift1,
            shift2=shift2,
            round_digits=round_digits,
        )

    def not_equals(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
        *,
        shift1: int | None = None,
        shift2: int | None = None,
        round_digits: int | None = None,
    ) -> bool:
        """Evaluate whether left != right."""
        l_op, r_op, p = self._ops(left, right, precision)
        return not_equals(
            l_op,
            r_op,
            shift,
            p,
            shift1=shift1,
            shift2=shift2,
            round_digits=round_digits,
        )

    def crosses_above(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
        *,
        round_digits: int | None = None,
    ) -> bool:
        """Evaluate whether left crosses above right."""
        l_op, r_op, p = self._ops(left, right, precision)
        return crosses_above(l_op, r_op, shift, p, round_digits=round_digits)

    def crosses_below(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
        *,
        round_digits: int | None = None,
    ) -> bool:
        """Evaluate whether left crosses below right."""
        l_op, r_op, p = self._ops(left, right, precision)
        return crosses_below(l_op, r_op, shift, p, round_digits=round_digits)

    @staticmethod
    def is_rising(
        indicator: Any,
        bars: int = 2,
        shift: int = 0,
        not_strict: bool = False,
        precision: int = DEFAULT_COMPARISON_PRECISION,
        *,
        round_digits: int | None = None,
    ) -> bool:
        """Evaluate whether indicator is rising monotonically."""
        return is_rising(
            indicator, bars, shift, not_strict, precision, round_digits=round_digits
        )

    @staticmethod
    def is_falling(
        indicator: Any,
        bars: int = 2,
        shift: int = 0,
        not_strict: bool = False,
        precision: int = DEFAULT_COMPARISON_PRECISION,
        *,
        round_digits: int | None = None,
    ) -> bool:
        """Evaluate whether indicator is falling monotonically."""
        return is_falling(
            indicator, bars, shift, not_strict, precision, round_digits=round_digits
        )

    @staticmethod
    def changes_up(
        indicator: Any,
        shift: int = 0,
        not_strict: bool = False,
        precision: int = DEFAULT_COMPARISON_PRECISION,
        *,
        round_digits: int | None = None,
    ) -> bool:
        """Evaluate 3-bar upward turn."""
        return changes_up(
            indicator, shift, not_strict, precision, round_digits=round_digits
        )

    @staticmethod
    def changes_down(
        indicator: Any,
        shift: int = 0,
        not_strict: bool = False,
        precision: int = DEFAULT_COMPARISON_PRECISION,
        *,
        round_digits: int | None = None,
    ) -> bool:
        """Evaluate 3-bar downward turn."""
        return changes_down(
            indicator, shift, not_strict, precision, round_digits=round_digits
        )

    def is_greater_count(
        self,
        left: Any = None,
        right: Any = None,
        bars: int = 2,
        *,
        shift: int = 0,
        not_strict: bool = False,
        precision: int = DEFAULT_COUNT_PRECISION,
    ) -> bool:
        """Evaluate whether left > right remains true across a window of bars."""
        l_op, r_op, _ = self._ops(left, right, None)
        return is_greater_count(
            l_op, r_op, bars, shift=shift, not_strict=not_strict, precision=precision
        )

    def is_lower_count(
        self,
        left: Any = None,
        right: Any = None,
        bars: int = 2,
        *,
        shift: int = 0,
        not_strict: bool = False,
        precision: int = DEFAULT_COUNT_PRECISION,
    ) -> bool:
        """Evaluate whether left < right remains true across a window of bars."""
        l_op, r_op, _ = self._ops(left, right, None)
        return is_lower_count(
            l_op, r_op, bars, shift=shift, not_strict=not_strict, precision=precision
        )

    @staticmethod
    def is_greater_percentile(
        indicator: Any,
        percentile: float = 50.0,
        bars: int = 10,
        shift: int = 0,
        precision: int = DEFAULT_COUNT_PRECISION,
    ) -> bool:
        """Evaluate whether indicator value exceeds percentile rank."""
        return is_greater_percentile(indicator, percentile, bars, shift, precision)

    @staticmethod
    def is_lower_percentile(
        indicator: Any,
        percentile: float = 50.0,
        bars: int = 10,
        shift: int = 0,
        precision: int = DEFAULT_COUNT_PRECISION,
    ) -> bool:
        """Evaluate whether indicator value falls below percentile rank."""
        return is_lower_percentile(indicator, percentile, bars, shift, precision)

    @staticmethod
    def calculate_wma(
        indicator: Any,
        period: int,
        shift: int = 0,
        precision: int = DEFAULT_COMPARISON_PRECISION,
    ) -> float:
        """Calculate Weighted Moving Average (WMA)."""
        return calculate_wma(indicator, period, shift, precision)

    @staticmethod
    def calculate_ma(
        indicator: Any,
        period: int,
        ma_type: int | MAType = MAType.SMA,
        shift: int = 0,
        precision: int = DEFAULT_COMPARISON_PRECISION,
    ) -> float:
        """Calculate Moving Average."""
        return calculate_ma(indicator, period, ma_type, shift, precision)

    @staticmethod
    def indicator_above_ma(
        indicator: Any,
        period: int = 14,
        ma_type: int | MAType = MAType.SMA,
        shift: int = 0,
        precision: int = DEFAULT_COMPARISON_PRECISION,
    ) -> bool:
        """Evaluate whether indicator is above its Moving Average."""
        return indicator_above_ma(indicator, period, ma_type, shift, precision)

    @staticmethod
    def indicator_below_ma(
        indicator: Any,
        period: int = 14,
        ma_type: int | MAType = MAType.SMA,
        shift: int = 0,
        precision: int = DEFAULT_COMPARISON_PRECISION,
    ) -> bool:
        """Evaluate whether indicator is below its Moving Average."""
        return indicator_below_ma(indicator, period, ma_type, shift, precision)

    @staticmethod
    def indicator_crosses_above_ma(
        indicator: Any,
        period: int = 14,
        ma_type: int | MAType = MAType.SMA,
        shift: int = 0,
        precision: int = DEFAULT_COMPARISON_PRECISION,
    ) -> bool:
        """Evaluate whether indicator crosses above its MA."""
        return indicator_crosses_above_ma(indicator, period, ma_type, shift, precision)

    @staticmethod
    def indicator_crosses_below_ma(
        indicator: Any,
        period: int = 14,
        ma_type: int | MAType = MAType.SMA,
        shift: int = 0,
        precision: int = DEFAULT_COMPARISON_PRECISION,
    ) -> bool:
        """Evaluate whether indicator crosses below its MA."""
        return indicator_crosses_below_ma(indicator, period, ma_type, shift, precision)

    @staticmethod
    def condition_and(*conditions: bool | Callable[[], Any] | Any) -> bool:
        """Evaluate short-circuit logical AND."""
        return condition_and(*conditions)

    @staticmethod
    def condition_or(*conditions: bool | Callable[[], Any] | Any) -> bool:
        """Evaluate short-circuit logical OR."""
        return condition_or(*conditions)

    @staticmethod
    def condition_not(condition: bool | float | Callable[[], Any] | Any) -> bool:
        """Evaluate logical NOT."""
        return condition_not(condition)


__all__ = ["Comparisons"]
