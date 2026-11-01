"""Standard strategy verification checkers.

Description:
    Implements comparison, indicator period hierarchy, and property matching
    checkers to validate strategy parameter configurations and consistency.

Purpose:
    FEAT-RETESTER-CHECKER: Strategy parameter and property verification.

Key Capabilities:
    - FR-checker-comparison: Compare scalar values using standard operators.
    - FR-checker-fast-slow: Verify that fast indicator periods are less than slow.
    - FR-checker-property: Verify that strategy properties match required constraints.

Python API Usage:
    from app.extend.checker.checkers import IndicatorFastSlowChecker
    valid = IndicatorFastSlowChecker.check({"FastPeriod": 12, "SlowPeriod": 26})

CLI Usage:
    python -m app.cli checker fast-slow --fast 12 --slow 26
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal

from app.core.host.logging import get_logger

logger = get_logger(__name__)

OperatorType = Literal["<", "<=", ">", ">=", "==", "!="]
FLOAT_TOLERANCE = 1e-9


class ComparisonChecker:
    """Evaluates scalar comparison expressions."""

    @staticmethod
    def check(left_value: float, operator: OperatorType, right_value: float) -> bool:
        """Compare left and right float values with given operator.

        Args:
            left_value: Left-hand operand.
            operator: Comparison operator.
            right_value: Right-hand operand.

        Returns:
            Boolean evaluation result.
        """
        ops = {
            "<": left_value < right_value,
            "<=": left_value <= right_value,
            ">": left_value > right_value,
            ">=": left_value >= right_value,
            "==": abs(left_value - right_value) < FLOAT_TOLERANCE,
            "!=": abs(left_value - right_value) >= FLOAT_TOLERANCE,
        }
        res = ops.get(operator, False)

        logger.debug(
            "FR-checker-comparison: %.4f %s %.4f -> %s",
            left_value,
            operator,
            right_value,
            res,
        )
        return res


class IndicatorFastSlowChecker:
    """Verifies that fast indicator periods are strictly less than slow periods."""

    @staticmethod
    def check(
        parameters: Mapping[str, int | float],
        pairs: Sequence[tuple[str, str]] = (("FastPeriod", "SlowPeriod"),),
    ) -> bool:
        """Check all present (fast_key, slow_key) pairs satisfy fast < slow.

        Args:
            parameters: Strategy parameter dictionary.
            pairs: Sequence of parameter key pairs to check.

        Returns:
            True if for every present pair, parameters[fast] < parameters[slow].
        """
        for fast_key, slow_key in pairs:
            if fast_key in parameters and slow_key in parameters:
                fast_val = float(parameters[fast_key])
                slow_val = float(parameters[slow_key])
                if fast_val >= slow_val:
                    logger.info(
                        "FR-checker-fast-slow: failed constraint %s (%.1f) >= "
                        "%s (%.1f)",
                        fast_key,
                        fast_val,
                        slow_key,
                        slow_val,
                    )
                    return False

        logger.debug("FR-checker-fast-slow: all fast/slow period constraints satisfied")
        return True


class PropertyChecker:
    """Verifies strategy property dictionary against required properties."""

    @staticmethod
    def check(
        strategy_properties: Mapping[str, Any],
        required: Mapping[str, Any],
    ) -> bool:
        """Check that all required properties exist and match strategy properties.

        Args:
            strategy_properties: Existing strategy properties.
            required: Required property key/value map.

        Returns:
            True if all required items match, otherwise False.
        """
        for key, expected_value in required.items():
            if key not in strategy_properties:
                logger.info("FR-checker-property: missing required property %s", key)
                return False
            actual_value = strategy_properties[key]
            if actual_value != expected_value:
                logger.info(
                    "FR-checker-property: mismatch for %s: expected %r, got %r",
                    key,
                    expected_value,
                    actual_value,
                )
                return False

        logger.debug(
            "FR-checker-property: all %d required properties matched", len(required)
        )
        return True
