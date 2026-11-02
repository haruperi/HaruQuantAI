"""Standard strategy verification checkers facade.

Description:
    Implements comparison, indicator period hierarchy, and property matching
    checkers to validate strategy parameter configurations, AST blocks, and
    parameter consistency matching donor SQ.Checker snippets.

Purpose:
    FEAT-RETESTER-CHECKER: Strategy parameter and property verification.

Key Capabilities:
    - FR-checker-comparison: Compare scalar values and AST comparison blocks.
    - FR-checker-fast-slow: Verify that fast indicator periods are less than slow.
    - FR-checker-property: Verify that strategy properties match required constraints.

Python API Usage:
    from app.extend.checker.checkers import (
        ComparisonChecker,
        IndicatorFastSlowChecker,
        PropertyChecker,
    )
    valid = IndicatorFastSlowChecker.check({"FastPeriod": 12, "SlowPeriod": 26})

CLI Usage:
    python -m app.cli checker fast-slow --fast 12 --slow 26
"""

from __future__ import annotations

from app.extend.checker.comparison_checker import (
    FLOAT_TOLERANCE,
    ComparisonChecker,
    OperatorType,
)
from app.extend.checker.indicator_fast_slow_checker import IndicatorFastSlowChecker
from app.extend.checker.property_checker import PropertyChecker

__all__ = [
    "FLOAT_TOLERANCE",
    "ComparisonChecker",
    "IndicatorFastSlowChecker",
    "OperatorType",
    "PropertyChecker",
]
