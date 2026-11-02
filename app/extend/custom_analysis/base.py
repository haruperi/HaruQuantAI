"""Custom analysis base contracts and strategy result containers.

Description:
    Implements CustomAnalysisMethod base class, method type constants,
    and lightweight trading result abstractions (ResultsGroup, OrdersList,
    CustomAnalysisOrder) mirroring StrategyQuant CustomAnalysis architecture.

Purpose:
    FEAT-EXTEND-CUSTOM-ANALYSIS: Custom analysis extension contracts.

Key Capabilities:
    - FR-custom-analysis-base: CustomAnalysisMethod contract with types.
    - FR-custom-analysis-results-group: ResultsGroup with fitness and orders.
    - FR-custom-analysis-orders: OrdersList and CustomAnalysisOrder.

Python API Usage:
    from app.extend.custom_analysis.base import (
        CustomAnalysisMethod,
        ResultsGroup,
        CustomAnalysisOrder,
        OrdersList,
        TYPE_PROCESS_DATABANK,
        TYPE_FILTER_STRATEGY,
    )

CLI Usage:
    uv run python -m pytest tests/extend/test_custom_analysis.py
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

TYPE_PROCESS_DATABANK: int = 10
TYPE_FILTER_STRATEGY: int = 20
TYPE_BOTH: int = 30


@dataclass(slots=True)
class CustomAnalysisOrder:
    """Historical or candidate order execution record for custom analysis."""

    ticket: int = 0
    pl: float = 0.0
    is_balance: bool = False
    open_time_ms: int = 0
    close_time_ms: int = 0
    result_key: str = "Main"
    direction: int = 0  # 0: Both, 1: Long, -1: Short
    sample_type: str = "InSample"  # InSample, OutOfSample, All

    def is_balance_order(self) -> bool:
        """Return True if this order is a balance transaction."""
        return self.is_balance

    def clone(self) -> CustomAnalysisOrder:
        """Return an independent copy of this order record."""
        return CustomAnalysisOrder(
            ticket=self.ticket,
            pl=self.pl,
            is_balance=self.is_balance,
            open_time_ms=self.open_time_ms,
            close_time_ms=self.close_time_ms,
            result_key=self.result_key,
            direction=self.direction,
            sample_type=self.sample_type,
        )


class OrdersList:
    """Collection of CustomAnalysisOrder objects with filtering and cloning."""

    def __init__(self, orders: Sequence[CustomAnalysisOrder] | None = None) -> None:
        """Initialize orders list from an optional sequence."""
        self._orders: list[CustomAnalysisOrder] = (
            [o.clone() for o in orders] if orders else []
        )

    def size(self) -> int:
        """Return number of orders in list."""
        return len(self._orders)

    def __len__(self) -> int:
        """Return number of orders in list."""
        return len(self._orders)

    def get(self, index: int) -> CustomAnalysisOrder:
        """Return order at zero-based index."""
        return self._orders[index]

    def __getitem__(self, index: int) -> CustomAnalysisOrder:
        """Return order at zero-based index."""
        return self._orders[index]

    def add(self, order: CustomAnalysisOrder) -> None:
        """Append an order to the list."""
        self._orders.append(order)

    def __iter__(self) -> Iterator[CustomAnalysisOrder]:
        """Iterate over contained orders."""
        return iter(self._orders)

    def filter_with_clone(
        self,
        result_key: str = "Main",
        direction: int = 0,
        sample_type: str = "InSample",
    ) -> OrdersList:
        """Filter orders by result key, direction, and sample type, returning clones.

        Args:
            result_key: Target result identifier (empty string matches any).
            direction: 0 for Both, 1 for Long, -1 for Short.
            sample_type: Sample partition ("InSample", "OutOfSample", "All").

        Returns:
            New OrdersList instance with cloned matching orders.
        """
        filtered: list[CustomAnalysisOrder] = []
        for o in self._orders:
            if result_key and o.result_key != result_key:
                continue
            if direction not in (0, o.direction):
                continue
            if sample_type not in ("All", o.sample_type):
                continue
            filtered.append(o.clone())
        return OrdersList(filtered)

    def clone(self) -> OrdersList:
        """Return a deep copy of this orders collection."""
        return OrdersList(self._orders)


class ResultsGroup:
    """Container holding strategy results, fitness, and orders for custom analysis."""

    def __init__(
        self,
        name: str,
        fitness: float = 0.0,
        orders: OrdersList | Sequence[CustomAnalysisOrder] | None = None,
        main_result_key: str = "Main",
        main_result_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ResultsGroup strategy container."""
        self._name = name
        self._fitness = fitness
        if isinstance(orders, OrdersList):
            self._orders = orders.clone()
        elif orders is not None:
            self._orders = OrdersList(orders)
        else:
            self._orders = OrdersList()
        self._main_result_key = main_result_key
        self._main_result_data = (
            dict(main_result_data) if main_result_data is not None else {}
        )

    def get_name(self) -> str:
        """Return strategy name."""
        return self._name

    @property
    def name(self) -> str:
        """Strategy name property."""
        return self._name

    def get_fitness(self) -> float:
        """Return strategy fitness score."""
        return self._fitness

    @property
    def fitness(self) -> float:
        """Strategy fitness score property."""
        return self._fitness

    def set_fitness(self, value: float) -> None:
        """Set strategy fitness score."""
        self._fitness = value

    def orders(self) -> OrdersList:
        """Return contained OrdersList."""
        return self._orders

    def get_main_result_key(self) -> str:
        """Return main result key identifier."""
        return self._main_result_key

    def main_result(self) -> dict[str, Any]:
        """Return main result dictionary representation."""
        return self._main_result_data

    def clone(self) -> ResultsGroup:
        """Return independent clone of this ResultsGroup."""
        return ResultsGroup(
            name=self._name,
            fitness=self._fitness,
            orders=self._orders.clone(),
            main_result_key=self._main_result_key,
            main_result_data=dict(self._main_result_data),
        )


class CustomAnalysisMethod:
    """Base class for custom analysis methods matching donor architecture."""

    def __init__(self, name: str, analysis_type: int) -> None:
        """Initialize custom analysis method with name and method type."""
        self.name: str = name
        self.type: int = analysis_type
        self.project_log_message: str = ""
        self.input_args: str = ""

    def get_type(self) -> int:
        """Return analysis method type (10, 20, or 30)."""
        return self.type

    def get_name(self) -> str:
        """Return analysis method name."""
        return self.name

    def filter_strategy(
        self,
        project: str,
        task: str,
        databank_name: str,
        rg: ResultsGroup,
    ) -> bool:
        """Filter a single strategy candidate.

        Args:
            project: Project name.
            task: Task name.
            databank_name: Target databank name.
            rg: ResultsGroup representing the strategy.

        Returns:
            True if strategy passes analysis filter; False to reject.
        """
        logger.debug(
            "FR-custom-analysis-base: filter_strategy on %s in %s/%s/%s",
            rg.get_name(),
            project,
            task,
            databank_name,
        )
        return True

    def process_databank(
        self,
        project_name: str,
        task: str,
        databank_name: str,
        databank_rg: list[ResultsGroup],
    ) -> list[ResultsGroup]:
        """Process databank strategies collectively and return pruned or modified list.

        Args:
            project_name: Project name.
            task: Task name.
            databank_name: Target databank name.
            databank_rg: Source strategy results in databank.

        Returns:
            Processed list of ResultsGroup instances.
        """
        logger.debug(
            "FR-custom-analysis-base: process_databank for %s/%s/%s with %d records",
            project_name,
            task,
            databank_name,
            len(databank_rg),
        )
        return databank_rg

    def set_project_log(self, string: str) -> None:
        """Set project log message string."""
        self.project_log_message = string

    def get_project_log(self) -> str:
        """Return project log message string."""
        return self.project_log_message

    def get_input_args(self) -> str:
        """Return input arguments configuration string."""
        return self.input_args

    def set_input_args(self, string: str) -> None:
        """Set input arguments configuration string."""
        self.input_args = string
