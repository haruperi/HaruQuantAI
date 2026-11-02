"""Base classes and execution pipeline for StrategyQuant negaters.

Description:
    Defines the abstract base Negater interface with execution priority
    (SortOrder) and the NegatersList dispatcher that cascades negation
    through registered negater components.

Purpose:
    FEAT-NEGATER-BASE: StrategyQuant donor-faithful negater base architecture.

Key Capabilities:
    - FR-NEGATER-BASE-ORDER: Ordered priority pipeline matching donor @SortOrder.
    - FR-NEGATER-BASE-DISPATCH: Cascading block/AST negation dispatch.

Python API Usage:
    from app.extend.negater.base import Negater, NegatersList
    pipeline = NegatersList()
    short_node = pipeline.negate(long_node)

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from app.core.host.logging import get_logger

logger = get_logger(__name__)

MIDPOINT_50: float = 100.0
FIBO_MAX: float = 1.0


class Negater(ABC):
    """Abstract base class for all StrategyQuant negater components."""

    order: ClassVar[int] = 1_000_000

    @classmethod
    @abstractmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Negate an AST node, dictionary, or code representation.

        Args:
            node: Target node, string, dict, or object representation.
            strategy: Optional StrategyBase context.

        Returns:
            Negated node, or None/original if unhandled.
        """


class NegatersList:
    """Ordered pipeline of Negater components dispatched by SortOrder."""

    def __init__(self, negaters: list[type[Negater]] | None = None) -> None:
        """Initialize pipeline with registered negaters sorted by order."""
        self._negaters: list[type[Negater]] = []
        if negaters:
            for n in negaters:
                self.register(n)

    def register(self, negater_cls: type[Negater]) -> None:
        """Register a negater class into the sorted pipeline."""
        self._negaters.append(negater_cls)
        self._negaters.sort(key=lambda item: item.order)
        logger.debug(
            "FR-NEGATER-BASE-ORDER: registered negater %s with order %d",
            negater_cls.__name__,
            negater_cls.order,
        )

    @property
    def registered_classes(self) -> tuple[type[Negater], ...]:
        """Return registered negater classes in priority order."""
        return tuple(self._negaters)

    def negate(self, node: Any, strategy: Any = None) -> Any:
        """Cascade negation through registered negaters in priority order.

        Args:
            node: Node or rule representation to negate.
            strategy: Optional strategy context.

        Returns:
            Negated node from the first handling negater, or original node.
        """
        for negater_cls in self._negaters:
            result = negater_cls.negate(node, strategy=strategy)
            if result is not None and result != node:
                logger.debug(
                    "FR-NEGATER-BASE-DISPATCH: %s handled negation",
                    negater_cls.__name__,
                )
                return result
        return node
