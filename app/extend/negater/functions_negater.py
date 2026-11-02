"""Functions negater conforming to StrategyQuant FunctionsNegater snippet.

Description:
    Swaps directional value and statistical functions (Highest <-> Lowest)
    in PriceOrNumber calculation blocks.

Purpose:
    FEAT-NEGATER-FUNCTIONS: Directional functions inversion.

Key Capabilities:
    - FR-NEGATER-FUNCTIONS-SWAP: Invert Highest and Lowest function identifiers.

Python API Usage:
    from app.extend.negater.functions_negater import FunctionsNegater
    negated = FunctionsNegater.negate("Highest(Close, 20)")

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater

logger = get_logger(__name__)


def _invert_name(name: str) -> str:
    """Invert Highest <-> Lowest."""
    if name == "Highest":
        return "Lowest"
    if name == "Lowest":
        return "Highest"
    return name


class FunctionsNegater(Negater):
    """Swaps directional functions (Highest <-> Lowest) (SortOrder=9000)."""

    order: ClassVar[int] = 9_000

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Swap Highest and Lowest across string, dict, or object representations.

        Args:
            node: Target function representation.
            strategy: Optional StrategyBase context.

        Returns:
            Inverted function representation.
        """
        logger.debug("FR-NEGATER-FUNCTIONS-SWAP: swapping directional functions")

        if isinstance(node, str):
            res_str = re.sub(r"\bHighest\b", "__TEMP_HIGHEST__", node)
            res_str = re.sub(r"\bLowest\b", "Highest", res_str)
            return re.sub(r"\b__TEMP_HIGHEST__\b", "Lowest", res_str)

        if isinstance(node, dict):
            res = dict(node)
            for key in ("function", "name"):
                if key in res and isinstance(res[key], str):
                    res[key] = _invert_name(res[key])
            return res

        if hasattr(node, "function") and isinstance(node.function, str):
            node.function = _invert_name(node.function)
            return node

        return node
