"""Portfolio Master ReturnDD fitness metric selector.

Description:
    Extracts the ReturnDDRatio metric from portfolio statistics mapping.
Purpose:
    FEAT-PORTFOLIO-MASTER: Select Return / Drawdown ratio fitness metric.
Key Capabilities:
    - FR-master-fitness-return-dd: Extract ReturnDDRatio or default 0.0.
Python API Usage:
    from app.extend.portfolio_master_fitness.return_dd import ReturnDD
    val = ReturnDD.compute({"ReturnDDRatio": 12.5})
CLI Usage:
    uv run python -m pytest tests/extend/portfolio_master_fitness/test_return_dd.py
"""

from __future__ import annotations

from collections.abc import Mapping

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class ReturnDD:
    """Selector extracting ReturnDDRatio from portfolio statistics."""

    @staticmethod
    def compute(stats: Mapping[str, float]) -> float:
        """Extract ReturnDDRatio numeric value or return 0.0 when absent.

        Args:
            stats: Read-only mapping of metric keys to floating-point values.

        Returns:
            Extracted ReturnDDRatio float value or 0.0.
        """
        val = stats.get("ReturnDDRatio", 0.0)
        logger.debug("Computed ReturnDDRatio fitness metric: %f", val)
        return float(val)
