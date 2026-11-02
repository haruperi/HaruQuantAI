"""Upper/Lower negater conforming to StrategyQuant UpperLowerNegater snippet.

Description:
    Swaps Upper and Lower bands (OutputIndex 0 <-> 1, UpperBand <-> LowerBand)
    for band indicator blocks and inverts associated relational comparisons.

Purpose:
    FEAT-NEGATER-UPPERLOWER: StrategyQuant donor-faithful band indicators inversion.

Key Capabilities:
    - FR-NEGATER-UPPERLOWER-SWAP: Invert Upper and Lower bands and output indices.

Python API Usage:
    from app.extend.negater.upper_lower_negater import UpperLowerNegater
    negated = UpperLowerNegater.negate(
        "Close[1] CrossesAbove BollingerBands.Upper(20, 2)"
    )

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater
from app.extend.negater.comparisons_negater import ComparisonsNegater

logger = get_logger(__name__)


class UpperLowerNegater(Negater):
    """Swaps UpperBand and LowerBand in band indicators (SortOrder=10100)."""

    order: ClassVar[int] = 10_100

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Swap Upper and Lower bands and invert comparison.

        Args:
            node: Target band indicator representation.
            strategy: Optional StrategyBase context.

        Returns:
            Inverted band indicator representation.
        """
        logger.debug("FR-NEGATER-UPPERLOWER-SWAP: swapping band indicators")

        if isinstance(node, str):
            res_str = ComparisonsNegater.negate(node, strategy=strategy)
            res_str = re.sub(r"\bUpperBand\b", "__TEMP_UPPER__", res_str)
            res_str = re.sub(r"\bLowerBand\b", "UpperBand", res_str)
            res_str = re.sub(r"\b__TEMP_UPPER__\b", "LowerBand", res_str)
            res_str = re.sub(r"\.Upper\(", ".__TEMP_UPPER_CALL__(", res_str)
            res_str = re.sub(r"\.Lower\(", ".Upper(", res_str)
            return re.sub(r"\.__TEMP_UPPER_CALL__\(", ".Lower(", res_str)

        if isinstance(node, dict):
            dict_node: dict[str, Any] = dict(node)
            band = dict_node.get("band")
            if band == "Upper":
                dict_node["band"] = "Lower"
            elif band == "Lower":
                dict_node["band"] = "Upper"

            if "output_index" in dict_node and isinstance(
                dict_node["output_index"], int
            ):
                dict_node["output_index"] = 0 if dict_node["output_index"] == 1 else 1

            return ComparisonsNegater.negate(dict_node, strategy=strategy)

        if hasattr(node, "OutputIndex"):
            idx = int(node.OutputIndex)
            node.OutputIndex = 0 if idx == 1 else 1
            return node

        return node
