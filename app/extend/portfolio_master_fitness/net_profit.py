"""Portfolio Master NetProfit fitness metric selector.

Description:
    Extracts the NetProfit metric from portfolio statistics mapping or ResultsGroup
    with maximize optimization direction and monetary display formatting.

Purpose:
    FEAT-PORTFOLIO-MASTER: Select Net Profit fitness metric.

Key Capabilities:
    - FR-master-fitness-net-profit: Extract NetProfit or default 0.0.

Python API Usage:
    from app.extend.portfolio_master_fitness.net_profit import NetProfit
    metric = NetProfit()
    val = metric.compute({"NetProfit": 1250.0})
    formatted = metric.print(val)

CLI Usage:
    python -m pytest tests/extend/portfolio_master_fitness/test_net_profit.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.portfolio_master_fitness.base import (
    PlTypes,
    PortfolioMasterFitness,
    StatsKey,
    ValueTypes,
)

logger = get_logger(__name__)


class NetProfit(PortfolioMasterFitness):
    """Selector extracting NetProfit from portfolio statistics."""

    name: str = "Net Profit (Return)"
    value_type: int = ValueTypes.Maximize
    target_value: float = 0.0
    range_min: float = -10000.0
    range_max: float = 10000.0
    stats_key: str = StatsKey.NET_PROFIT
    pl_type: int = PlTypes.Money

    def __init__(self) -> None:
        super().__init__(
            name="Net Profit (Return)",
            value_type=ValueTypes.Maximize,
            target_value=0.0,
            range_min=-10000.0,
            range_max=10000.0,
            stats_key=StatsKey.NET_PROFIT,
            pl_type=PlTypes.Money,
        )

    @classmethod
    @override
    def compute(cls, result: Mapping[str, Any] | Any, sample_type: int = 0) -> float:
        """Extract NetProfit numeric value or return 0.0 when absent.

        Args:
            result: Mapping of metric keys to values or ResultsGroup.
            sample_type: Evaluation sample type index.

        Returns:
            Extracted NetProfit float value or 0.0.
        """
        instance = cls() if isinstance(cls, type) else cls
        return PortfolioMasterFitness.compute(instance, result, sample_type)

    @classmethod
    @override
    def print(cls, value: float) -> str:
        """Format value as monetary string."""
        return PlTypes.printPL(value, PlTypes.Money)
