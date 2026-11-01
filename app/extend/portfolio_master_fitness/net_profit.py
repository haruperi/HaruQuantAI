"""Portfolio Master NetProfit fitness metric selector.

Description:
    Extracts the NetProfit metric from portfolio statistics mapping.
Purpose:
    FEAT-PORTFOLIO-MASTER: Select Net Profit fitness metric.
Key Capabilities:
    - FR-master-fitness-net-profit: Extract NetProfit or default 0.0.
Python API Usage:
    from app.extend.portfolio_master_fitness.net_profit import NetProfit
    val = NetProfit.compute({"NetProfit": 12.5})
CLI Usage:
    uv run python -m pytest tests/extend/portfolio_master_fitness/test_net_profit.py
"""

from __future__ import annotations

from collections.abc import Mapping

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class NetProfit:
    """Selector extracting NetProfit from portfolio statistics."""

    @staticmethod
    def compute(stats: Mapping[str, float]) -> float:
        """Extract NetProfit numeric value or return 0.0 when absent.

        Args:
            stats: Read-only mapping of metric keys to floating-point values.

        Returns:
            Extracted NetProfit float value or 0.0.
        """
        val = stats.get("NetProfit", 0.0)
        logger.debug("Computed NetProfit fitness metric: %f", val)
        return float(val)
