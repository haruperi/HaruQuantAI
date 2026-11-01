"""Optimization test-count and period parameter label formatting helper.

Description:
    Provides OptimizationLabels with maximum-test formatting and walk-forward
    period parameter label lookup based on observed SQX optimization services.

Purpose:
    FEAT-OPTIMIZER-LABELS: Optimization parameter and test-count label formatting.

Key Capabilities:
    - FR-optimizer-max-tests-labels: Format integer test counts to strings.
    - FR-optimizer-period-param-labels: Format parameter period labels.

Python API Usage:
    from app.workspace.optimizer.labels import OptimizationLabels
    label = OptimizationLabels.max_tests(1000)  # "1.000"
    p_label = OptimizationLabels.period_parameter(1, "percent")  # "Out of Sample %"

CLI Usage:
    python -m app.cli optimizer format-label --tests 1000
"""

from __future__ import annotations

from typing import Final

from app.core.host.logging import get_logger

logger = get_logger(__name__)

_MAX_TESTS_MAP: Final[dict[int, str]] = {
    100: "100",
    500: "500",
    1000: "1.000",
    3000: "3.000",
    7500: "7.500",
    10000: "10.000",
    15000: "15.000",
    50000: "50.000",
    100000: "100.000",
    200000: "200.000",
    500000: "500.000",
    1000000: "1.000.000",
    10000000: "10.000.000",
    100000000: "100.000.000",
    1000000000: "1.000.000.000",
    1000000001: "Exhaustive (all combinations)",
}

_PARAM_1_MAP: Final[dict[str, str]] = {
    "percent": "Out of Sample %",
    "days": "In Sample days",
    "bars": "In Sample bars",
}

_PARAM_OTHER_MAP: Final[dict[str, str]] = {
    "percent": "Walk Forward runs",
    "days": "Out of Sample days",
    "bars": "Out of Sample bars",
}


class OptimizationLabels:
    """Format maximum test counts and walk-forward period parameter labels."""

    @staticmethod
    def max_tests(value: int) -> str | int:
        """Map maximum optimization test counts to canonical string forms.

        Args:
            value: Integer maximum test count.

        Returns:
            Mapped string representation if recognized, else unchanged integer.

        Raises:
            TypeError: If value is not an integer or is a boolean.
        """
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("value must be an integer")
        mapped = _MAX_TESTS_MAP.get(value)
        if mapped is not None:
            logger.debug("Mapped max tests %d to %s", value, mapped)
            return mapped
        return value

    @staticmethod
    def period_parameter(parameter: int, period_type: str) -> str | None:
        """Map parameter index and period type to human-readable label.

        Args:
            parameter: Parameter index (1 for primary/OOS, other integers for WF).
            period_type: Period unit ('percent', 'days', or 'bars').

        Returns:
            Descriptive string label, or None if period_type is unmapped.

        Raises:
            TypeError: If parameter is not an integer or period_type is not a string.
        """
        if isinstance(parameter, bool) or not isinstance(parameter, int):
            raise TypeError("parameter must be an integer")
        if not isinstance(period_type, str):
            raise TypeError("period_type must be a string")

        if parameter == 1:
            return _PARAM_1_MAP.get(period_type)
        return _PARAM_OTHER_MAP.get(period_type)
