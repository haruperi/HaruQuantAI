"""Base definitions and contract interfaces for StrategyQuant formula snippets.

Description:
    Defines the abstract FormulaBlock and MMFormulaBlock base classes
    matching StrategyQuant SQ.Internal.FormulaBlock and MMFormulaBlock,
    along with standard order sentinels.
Purpose:
    FEAT-FORMULAS: StrategyQuant donor-faithful formula models.
Key Capabilities:
    - FR-formulas-base: Abstract base contracts for formula and sizing blocks.
Python API Usage:
    from app.extend.formulas.base import FormulaBlock, MMFormulaBlock, ORDER_NOT_DEFINED
CLI Usage:
    uv run pytest tests/extend/formulas/test_formulas_catalog.py --no-cov
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

ORDER_NOT_DEFINED: float = -1.0


class FormulaBlock(ABC):
    """Abstract base class for all standard StrategyQuant formula snippets."""

    def __init__(
        self,
        name: str,
        group: str,
        order: int = 100,
        *,
        price_level: bool = False,
        none_value: bool = False,
    ) -> None:
        """Initialize formula block descriptor metadata."""
        self.name: str = name
        self.group: str = group
        self.order: int = order
        self.price_level: bool = price_level
        self.none_value: bool = none_value
        logger.debug(
            "Initialized FormulaBlock: group=%s, name=%s, order=%d",
            self.group,
            self.name,
            self.order,
        )

    @abstractmethod
    def evaluate_formula(
        self,
        strategy: Any,
        symbol: str,
        price: float,
        direction: int,
    ) -> float:
        """Evaluate formula output value.

        Args:
            strategy: Execution context or StrategyBase instance.
            symbol: Target market symbol.
            price: Current decision price.
            direction: Trade direction (1 for Long, -1 for Short).

        Returns:
            Computed numerical formula value or sentinel.
        """
        ...

    def is_boolean_value(self) -> bool:
        """Return True if block value is boolean, False otherwise."""
        return False


class MMFormulaBlock(ABC):
    """Abstract base class for position sizing formulas."""

    def __init__(self, name: str, group: str = "Size", order: int = 100) -> None:
        """Initialize money management formula descriptor metadata."""
        self.name: str = name
        self.group: str = group
        self.order: int = order
        logger.debug(
            "Initialized MMFormulaBlock: group=%s, name=%s, order=%d",
            self.group,
            self.name,
            self.order,
        )

    @abstractmethod
    def compute_size(
        self,
        strategy: Any,
        symbol: str,
        order_type: int,
        price: float,
        sl: float,
    ) -> float:
        """Compute position lot size.

        Args:
            strategy: Execution context or StrategyBase instance.
            symbol: Target market symbol.
            order_type: Engine order type byte/int code.
            price: Execution entry price.
            sl: Stop Loss price level.

        Returns:
            Calculated trade lot size.
        """
        ...
