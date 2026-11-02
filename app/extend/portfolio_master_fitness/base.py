"""Portfolio Master fitness base contracts and helper types.

Description:
    Defines the PortfolioMasterFitness base class, ValueTypes optimization
    direction enums, PlTypes formatting rules, and StatsKey constants
    matching StrategyQuant donor architecture.

Purpose:
    FEAT-PORTFOLIO-MASTER: Base abstractions for portfolio fitness evaluations.

Key Capabilities:
    - FR-master-fitness-core: Base class and contract for fitness evaluations.
    - FR-master-fitness-types: Optimization direction and display types.
    - FR-master-fitness-formatting: P/L value formatting for metrics.

Python API Usage:
    from app.extend.portfolio_master_fitness.base import (
        PortfolioMasterFitness,
        ValueTypes,
        PlTypes,
        StatsKey,
    )
    fitness = PortfolioMasterFitness("CustomMetric", ValueTypes.Maximize)
    val = fitness.compute({"CustomMetric": 100.0})
    formatted = fitness.print(val)

CLI Usage:
    python -m pytest tests/extend/portfolio_master_fitness/test_base.py
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class ValueTypes:
    """Optimization direction flags matching SQX ValueTypes."""

    Maximize: int = 1
    Minimize: int = 2
    Approximate: int = 3


class PlTypes:
    """Display and formatting types matching SQX PlTypes."""

    Money: int = 1
    Percent: int = 2
    Pips: int = 3

    @classmethod
    def printPL(cls, value: float, pl_type: int) -> str:  # noqa: N802
        """Donor compatibility alias for print_pl."""
        return cls.print_pl(value, pl_type)

    @classmethod
    def print_pl(cls, value: float, pl_type: int) -> str:
        """Format numeric value according to P/L display type."""
        if pl_type == cls.Percent:
            return f"{value:.2f}%"
        if pl_type == cls.Money:
            sign = "-" if value < 0 else ""
            return f"{sign}${abs(value):,.2f}"
        if pl_type == cls.Pips:
            return f"{value:.1f} pips"
        return f"{value:.2f}"


class StatsKey:
    """Standard statistics metric key identifiers matching SQX StatsKey."""

    NET_PROFIT: str = "NetProfit"
    STAGNATION_PERIOD_PCT: str = "StagnationPct"
    RETURN_DD_RATIO: str = "ReturnDDRatio"


class PortfolioMasterFitness:
    """Base class for all Portfolio Master fitness metrics."""

    name: str = "PortfolioMasterFitness"
    value_type: int = ValueTypes.Maximize
    target_value: float = 0.0
    range_min: float = -10000.0
    range_max: float = 10000.0
    stats_key: str = StatsKey.NET_PROFIT
    pl_type: int = PlTypes.Money

    def __init__(  # noqa: PLR0917
        self,
        name: str = "PortfolioMasterFitness",
        value_type: int = ValueTypes.Maximize,
        target_value: float = 0.0,
        range_min: float = -10000.0,
        range_max: float = 10000.0,
        stats_key: str = StatsKey.NET_PROFIT,
        pl_type: int = PlTypes.Money,
    ) -> None:
        self.name = name
        self.value_type = value_type
        self.target_value = target_value
        self.range_min = range_min
        self.range_max = range_max
        self.stats_key = stats_key
        self.pl_type = pl_type
        logger.info(
            "FR-master-fitness-core: initialized %s (target=%.2f, range=[%.2f, %.2f])",
            self.name,
            self.target_value,
            self.range_min,
            self.range_max,
        )

    @property
    def maximize(self) -> bool:
        """Whether metric optimization direction is Maximize."""
        return self.value_type == ValueTypes.Maximize

    def compute(self, result: Mapping[str, Any] | Any, sample_type: int = 0) -> float:
        """Extract fitness metric from stats mapping or ResultsGroup."""
        del sample_type
        key = getattr(self, "stats_key", StatsKey.NET_PROFIT)
        name = getattr(self, "name", "PortfolioMasterFitness")

        if isinstance(result, Mapping):
            raw_val = result.get(key, 0.0)
            try:
                val = float(raw_val)
            except ValueError, TypeError:
                val = 0.0
        elif hasattr(result, "portfolio") and callable(result.portfolio):
            portfolio_obj = result.portfolio()
            if hasattr(portfolio_obj, "stats") and callable(portfolio_obj.stats):
                stats_obj = portfolio_obj.stats()
                if isinstance(stats_obj, Mapping):
                    val = float(stats_obj.get(key, 0.0))
                else:
                    val = float(getattr(stats_obj, key, 0.0))
            else:
                val = 0.0
        elif hasattr(result, key):
            val = float(getattr(result, key, 0.0))
        else:
            val = 0.0

        logger.debug("Computed %s fitness metric: %f", name, val)
        return val

    def print(self, value: float) -> str:
        """Format metric value using assigned P/L display type."""
        pl_type = getattr(self, "pl_type", PlTypes.Money)
        return PlTypes.print_pl(value, pl_type)
