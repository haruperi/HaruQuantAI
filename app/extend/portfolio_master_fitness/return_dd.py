"""Portfolio Master ReturnDD fitness metric selector.

Description:
    Extracts the ReturnDDRatio metric from portfolio statistics mapping or ResultsGroup
    with maximize optimization direction and numeric/monetary display formatting.

Purpose:
    FEAT-PORTFOLIO-MASTER: Select Return / Drawdown ratio fitness metric.

Key Capabilities:
    - FR-master-fitness-return-dd: Extract ReturnDDRatio or default 0.0.

Python API Usage:
    from app.extend.portfolio_master_fitness.return_dd import ReturnDD
    metric = ReturnDD()
    val = metric.compute({"ReturnDDRatio": 2.5})
    formatted = metric.print(val)

CLI Usage:
    python -m pytest tests/extend/portfolio_master_fitness/test_return_dd.py
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


class ReturnDD(PortfolioMasterFitness):
    """Selector extracting ReturnDDRatio from portfolio statistics."""

    name: str = "Return / Drawdown ratio"
    value_type: int = ValueTypes.Maximize
    target_value: float = 0.0
    range_min: float = -20.0
    range_max: float = 20.0
    stats_key: str = StatsKey.RETURN_DD_RATIO
    pl_type: int = PlTypes.Money

    def __init__(self) -> None:
        super().__init__(
            name="Return / Drawdown ratio",
            value_type=ValueTypes.Maximize,
            target_value=0.0,
            range_min=-20.0,
            range_max=20.0,
            stats_key=StatsKey.RETURN_DD_RATIO,
            pl_type=PlTypes.Money,
        )

    @classmethod
    @override
    def compute(cls, result: Mapping[str, Any] | Any, sample_type: int = 0) -> float:
        """Extract ReturnDDRatio numeric value or return 0.0 when absent.

        Args:
            result: Mapping of metric keys to values or ResultsGroup.
            sample_type: Evaluation sample type index.

        Returns:
            Extracted ReturnDDRatio float value or 0.0.
        """
        instance = cls() if isinstance(cls, type) else cls
        return PortfolioMasterFitness.compute(instance, result, sample_type)

    @classmethod
    @override
    def print(cls, value: float) -> str:
        """Format value as ratio string."""
        return PlTypes.printPL(value, PlTypes.Money)
