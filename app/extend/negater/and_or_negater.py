"""And/Or negater conforming to StrategyQuant AndOrNegater snippet.

Description:
    Preserves boolean conjunction and disjunction operators (AND, OR) while
    recursively traversing and negating child sub-trees.

Purpose:
    FEAT-NEGATER-ANDOR: StrategyQuant donor-faithful boolean tree recursion.

Key Capabilities:
    - FR-NEGATER-ANDOR-RECURSE: Preserve AND/OR operators and recurse on children.

Python API Usage:
    from app.extend.negater.and_or_negater import AndOrNegater
    negated_tree = AndOrNegater.negate({"operator": "AND", "children": [...]})

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater

logger = get_logger(__name__)


class AndOrNegater(Negater):
    """Preserves AND/OR structure while recursing on children (SortOrder=100)."""

    order: ClassVar[int] = 100

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Recurse on boolean tree operands while preserving AND/OR.

        Args:
            node: Target boolean tree node or representation.
            strategy: Optional StrategyBase context.

        Returns:
            Tree with inverted condition leaves.
        """
        logger.debug("FR-NEGATER-ANDOR-RECURSE: negating boolean tree children")

        if isinstance(node, dict) and "children" in node:
            from app.extend.negater.conditions_negater import ConditionsNegater

            res = dict(node)
            res["children"] = [
                ConditionsNegater.negate(child, strategy=strategy)
                for child in node["children"]
            ]
            return res

        return node
