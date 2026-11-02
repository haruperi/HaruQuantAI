"""Comparisons negater conforming to StrategyQuant ComparisonsNegater snippet.

Description:
    Inverts relational operators and directional trends across Comparison
    and Property AST blocks.

Purpose:
    FEAT-NEGATER-COMP: StrategyQuant donor-faithful comparison operator reversal.

Key Capabilities:
    - FR-NEGATER-COMP-INVERT: Invert relational operators and crossover trends.

Python API Usage:
    from app.extend.negater.comparisons_negater import ComparisonsNegater
    negated = ComparisonsNegater.negate("Close[1] CrossesAbove Open[1]")

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater

logger = get_logger(__name__)


class ComparisonsNegater(Negater):
    """Inverts comparison operators and directional trends (SortOrder=10000)."""

    order: ClassVar[int] = 10_000

    OP_MAP: ClassVar[dict[str, str]] = {
        ">": "<",
        "<": ">",
        ">=": "<=",
        "<=": ">=",
        "==": "==",
        "!=": "!=",
        "IsGreater": "IsLower",
        "IsLower": "IsGreater",
        "CrossesAbove": "CrossesBelow",
        "CrossesBelow": "CrossesAbove",
        "IsRising": "IsFalling",
        "IsFalling": "IsRising",
    }

    _STR_OPS: ClassVar[list[tuple[str, str]]] = [
        ("CrossesAbove", "CrossesBelow"),
        ("CrossesBelow", "CrossesAbove"),
        ("IsRising", "IsFalling"),
        ("IsFalling", "IsRising"),
        ("IsGreater", "IsLower"),
        ("IsLower", "IsGreater"),
        (">=", "<="),
        ("<=", ">="),
        (">", "<"),
        ("<", ">"),
    ]

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Invert comparison operator across string, dict, or object representations.

        Args:
            node: Target comparison node or string.
            strategy: Optional StrategyBase context.

        Returns:
            Inverted comparison representation.
        """
        logger.debug("FR-NEGATER-COMP-INVERT: negating comparison operator")

        if isinstance(node, str):
            res_str = node
            for op, inv in cls._STR_OPS:
                if op in res_str:
                    return res_str.replace(op, inv)
            return res_str

        if isinstance(node, dict):
            dict_node: dict[str, Any] = dict(node)
            dict_op = dict_node.get("operator")
            if isinstance(dict_op, str) and dict_op in cls.OP_MAP:
                dict_node["operator"] = cls.OP_MAP[dict_op]
            return dict_node

        if hasattr(node, "operator"):
            op = node.operator
            if isinstance(op, str) and op in cls.OP_MAP:
                node.operator = cls.OP_MAP[op]
            return node

        return node
