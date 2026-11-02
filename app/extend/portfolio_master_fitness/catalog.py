"""Portfolio Master fitness catalog and descriptor definitions.

Description:
    Maintains registered fitness metrics, descriptors, class instances,
    and computation dispatch for Portfolio Master ranking criteria.

Purpose:
    FEAT-PORTFOLIO-MASTER: Catalog and dispatch portfolio fitness metrics.

Key Capabilities:
    - FR-master-fitness-catalog: Register and look up fitness metric descriptors.
    - FR-master-fitness-dispatch: Delegate compute calls to metric selectors.

Python API Usage:
    from app.extend.portfolio_master_fitness.catalog import (
        PortfolioMasterFitnessCatalog,
    )
    desc = PortfolioMasterFitnessCatalog.get_descriptor("NetProfit")
    val = PortfolioMasterFitnessCatalog.compute("NetProfit", stats)

CLI Usage:
    python -m pytest tests/extend/portfolio_master_fitness/test_catalog.py
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from app.core.host.logging import get_logger
from app.extend.portfolio_master_fitness.base import PortfolioMasterFitness
from app.extend.portfolio_master_fitness.net_profit import NetProfit
from app.extend.portfolio_master_fitness.pct_stagnation import PctStagnation
from app.extend.portfolio_master_fitness.return_dd import ReturnDD

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class PortfolioMasterFitnessDescriptor:
    """Descriptor defining fitness metric bounds, direction, and keys."""

    metric_id: str
    label: str
    stats_key: str
    maximize: bool
    default_target: float
    range_min: float
    range_max: float


class PortfolioMasterFitnessCatalog:
    """Catalog of Portfolio Master fitness metrics and computation dispatch."""

    _CLASSES: ClassVar[dict[str, type[PortfolioMasterFitness]]] = {
        "NetProfit": NetProfit,
        "PctStagnation": PctStagnation,
        "ReturnDD": ReturnDD,
    }

    _DESCRIPTORS: ClassVar[dict[str, PortfolioMasterFitnessDescriptor]] = {
        "NetProfit": PortfolioMasterFitnessDescriptor(
            metric_id="NetProfit",
            label="Net Profit (Return)",
            stats_key="NetProfit",
            maximize=True,
            default_target=0.0,
            range_min=-10000.0,
            range_max=10000.0,
        ),
        "PctStagnation": PortfolioMasterFitnessDescriptor(
            metric_id="PctStagnation",
            label="% Stagnation",
            stats_key="StagnationPct",
            maximize=False,
            default_target=0.0,
            range_min=0.0,
            range_max=100.0,
        ),
        "ReturnDD": PortfolioMasterFitnessDescriptor(
            metric_id="ReturnDD",
            label="Return / Drawdown ratio",
            stats_key="ReturnDDRatio",
            maximize=True,
            default_target=0.0,
            range_min=-20.0,
            range_max=20.0,
        ),
    }

    @classmethod
    def get_fitness_class(cls, metric_id: str) -> type[PortfolioMasterFitness]:
        """Look up the fitness metric class for a metric ID.

        Args:
            metric_id: Unique string identifier for the metric.

        Returns:
            PortfolioMasterFitness subclass.

        Raises:
            ValueError: If metric_id is unknown.
        """
        if metric_id not in cls._CLASSES:
            raise ValueError(f"Unknown portfolio master fitness metric: {metric_id}")
        return cls._CLASSES[metric_id]

    @classmethod
    def create_fitness(cls, metric_id: str) -> PortfolioMasterFitness:
        """Instantiate a fitness metric for a metric ID.

        Args:
            metric_id: Unique string identifier for the metric.

        Returns:
            PortfolioMasterFitness instance.
        """
        fitness_cls = cls.get_fitness_class(metric_id)
        return fitness_cls()

    @classmethod
    def get_descriptor(cls, metric_id: str) -> PortfolioMasterFitnessDescriptor:
        """Get descriptor for given metric ID.

        Args:
            metric_id: Unique string identifier for the metric.

        Returns:
            PortfolioMasterFitnessDescriptor instance.

        Raises:
            ValueError: If metric_id is unknown.
        """
        if metric_id not in cls._DESCRIPTORS:
            raise ValueError(f"Unknown portfolio master fitness metric: {metric_id}")
        return cls._DESCRIPTORS[metric_id]

    @classmethod
    def descriptors(cls) -> tuple[PortfolioMasterFitnessDescriptor, ...]:
        """Return tuple of all registered metric descriptors."""
        return tuple(cls._DESCRIPTORS.values())

    @classmethod
    def compute(
        cls, metric_id: str, stats: Mapping[str, Any] | Any, sample_type: int = 0
    ) -> float:
        """Delegate metric extraction to the registered selector.

        Args:
            metric_id: Target metric ID.
            stats: Mapping of statistic keys to numeric values or ResultsGroup.
            sample_type: Sample type index.

        Returns:
            Extracted floating-point value.

        Raises:
            ValueError: If metric_id is unknown.
        """
        fitness = cls.create_fitness(metric_id)
        return fitness.compute(stats, sample_type=sample_type)

    @classmethod
    def print_value(cls, metric_id: str, value: float) -> str:
        """Format metric value using assigned P/L display type.

        Args:
            metric_id: Target metric ID.
            value: Float value to format.

        Returns:
            Formatted string representation.
        """
        fitness = cls.create_fitness(metric_id)
        return fitness.print(value)
