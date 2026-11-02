"""Order comparator by profit metric (matching donor ComparatorByProfit.java).

Description:
    Implements ComparatorByProfit comparing orders by profit in descending order,
    supporting Money, Pips, and Percent profit modes matching StrategyQuant
    PlTypes.

Purpose:
    FEAT-FUNCTIONS: StrategyQuant donor-faithful functions.

Key Capabilities:
    - FR-FUNCTIONS-COMPARATOR-PROFIT: Compare orders by Money, Pips, or Percent.

Python API Usage:
    from app.extend.functions.comparator_by_profit import (
        ComparatorByProfit,
        PL_TYPE_MONEY,
        PL_TYPE_PIPS,
        PL_TYPE_PERCENT,
    )
    comparator = ComparatorByProfit(PL_TYPE_MONEY)
    result = comparator.compare(order1, order2)

CLI Usage:
    uv run pytest tests/extend/test_functions.py --no-cov
"""

from __future__ import annotations

from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

PL_TYPE_MONEY: int = 0
PL_TYPE_PIPS: int = 1
PL_TYPE_PERCENT: int = 2


def _extract_pl(order: Any, pl_type: int) -> float:
    """Extract numeric profit value from order object based on profit type."""
    if pl_type == PL_TYPE_PIPS:
        val = getattr(
            order,
            "pips_pl",
            getattr(order, "PipsPL", getattr(order, "profit_loss_pips", 0.0)),
        )
        return float(val)
    if pl_type == PL_TYPE_PERCENT:
        val = getattr(
            order,
            "pct_pl",
            getattr(order, "PctPL", getattr(order, "profit_loss_pct", 0.0)),
        )
        return float(val)

    val = getattr(
        order,
        "pl",
        getattr(
            order,
            "PL",
            getattr(
                order,
                "profit_loss",
                getattr(order, "profit", 0.0),
            ),
        ),
    )
    return float(val)


class ComparatorByProfit:
    """Comparator for sorting or comparing trading orders by profit descending."""

    def __init__(self, pl_type: int = PL_TYPE_MONEY) -> None:
        """Initialize ComparatorByProfit with profit type.

        Args:
            pl_type: 0 for Money, 1 for Pips, 2 for Percent.
        """
        self.pl_type = pl_type

    def compare(self, order1: Any, order2: Any) -> int:
        """Compare two orders by profit descending matching donor Comparator contract.

        Args:
            order1: First order candidate.
            order2: Second order candidate.

        Returns:
            -1 if order1 has higher profit than order2 (descending order),
             1 if order1 has lower profit than order2,
             0 if profits are equal.
        """
        v1 = _extract_pl(order1, self.pl_type)
        v2 = _extract_pl(order2, self.pl_type)

        logger.debug(
            "FR-FUNCTIONS-COMPARATOR-PROFIT: comparing %f vs %f (type=%d)",
            v1,
            v2,
            self.pl_type,
        )

        if v1 > v2:
            return -1
        if v1 < v2:
            return 1
        return 0

    def key(self, order: Any) -> float:
        """Return numeric sort key for standard Python descending sort.

        Args:
            order: Order candidate.

        Returns:
            Negative extracted profit value so list.sort(key=...) sorts descending.
        """
        return -_extract_pl(order, self.pl_type)
