"""Portfolio Master PctStagnation fitness metric selector.

Description:
    Extracts the StagnationPct metric from portfolio statistics mapping.
Purpose:
    FEAT-PORTFOLIO-MASTER: Select % Stagnation fitness metric.
Key Capabilities:
    - FR-master-fitness-pct-stagnation: Extract StagnationPct or default 0.0.
Python API Usage:
    from app.extend.portfolio_master_fitness.pct_stagnation import PctStagnation
    val = PctStagnation.compute({"StagnationPct": 12.5})
CLI Usage:
    uv run python -m pytest tests/extend/portfolio_master_fitness/test_pct_stagnation.py
"""

from __future__ import annotations

from collections.abc import Mapping

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class PctStagnation:
    """Selector extracting StagnationPct from portfolio statistics."""

    @staticmethod
    def compute(stats: Mapping[str, float]) -> float:
        """Extract StagnationPct numeric value or return 0.0 when absent.

        Args:
            stats: Read-only mapping of metric keys to floating-point values.

        Returns:
            Extracted StagnationPct float value or 0.0.
        """
        val = stats.get("StagnationPct", 0.0)
        logger.debug("Computed StagnationPct fitness metric: %f", val)
        return float(val)
