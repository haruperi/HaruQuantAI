"""Portfolio Master PctStagnation fitness metric selector.

Description:
    Extracts the StagnationPct metric from portfolio statistics mapping or ResultsGroup
    with minimize optimization direction and percentage display formatting.

Purpose:
    FEAT-PORTFOLIO-MASTER: Select % Stagnation fitness metric.

Key Capabilities:
    - FR-master-fitness-pct-stagnation: Extract StagnationPct or default 0.0.

Python API Usage:
    from app.extend.portfolio_master_fitness.pct_stagnation import PctStagnation
    metric = PctStagnation()
    val = metric.compute({"StagnationPct": 12.5})
    formatted = metric.print(val)

CLI Usage:
    python -m pytest tests/extend/portfolio_master_fitness/test_pct_stagnation.py
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


class PctStagnation(PortfolioMasterFitness):
    """Selector extracting StagnationPct from portfolio statistics."""

    name: str = "% Stagnation"
    value_type: int = ValueTypes.Minimize
    target_value: float = 0.0
    range_min: float = 0.0
    range_max: float = 100.0
    stats_key: str = StatsKey.STAGNATION_PERIOD_PCT
    pl_type: int = PlTypes.Percent

    def __init__(self) -> None:
        super().__init__(
            name="% Stagnation",
            value_type=ValueTypes.Minimize,
            target_value=0.0,
            range_min=0.0,
            range_max=100.0,
            stats_key=StatsKey.STAGNATION_PERIOD_PCT,
            pl_type=PlTypes.Percent,
        )

    @classmethod
    @override
    def compute(cls, result: Mapping[str, Any] | Any, sample_type: int = 0) -> float:
        """Extract StagnationPct numeric value or return 0.0 when absent.

        Args:
            result: Mapping of metric keys to values or ResultsGroup.
            sample_type: Evaluation sample type index.

        Returns:
            Extracted StagnationPct float value or 0.0.
        """
        instance = cls() if isinstance(cls, type) else cls
        return PortfolioMasterFitness.compute(instance, result, sample_type)

    @classmethod
    @override
    def print(cls, value: float) -> str:
        """Format value as percentage string."""
        return PlTypes.printPL(value, PlTypes.Percent)
