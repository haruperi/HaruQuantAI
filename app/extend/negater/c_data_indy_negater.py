"""Data indicator negater conforming to StrategyQuant CDataIndyNegater snippet.

Description:
    Swaps High and Low price extremes or inverts the value index for data
    indicator blocks.

Purpose:
    FEAT-NEGATER-CDATA: StrategyQuant donor-faithful data indicator negation.

Key Capabilities:
    - FR-NEGATER-CDATA-SWAP: Invert price extremes (High <-> Low) and value indices.

Python API Usage:
    from app.extend.negater.c_data_indy_negater import CDataIndyNegater
    negated = CDataIndyNegater.negate("High")

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater

logger = get_logger(__name__)


class CDataIndyNegater(Negater):
    """Swaps Open/Close or High/Low price extremes (SortOrder=1000)."""

    order: ClassVar[int] = 1_000

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Invert High/Low extremes across string, dict, or object representations.

        Args:
            node: Target data indicator representation.
            strategy: Optional StrategyBase context.

        Returns:
            Inverted data indicator representation.
        """
        logger.debug("FR-NEGATER-CDATA-SWAP: swapping data extremes")

        if isinstance(node, str):
            res_str = re.sub(r"\bHigh\b", "__TEMP_HIGH__", node)
            res_str = re.sub(r"\bLow\b", "High", res_str)
            return re.sub(r"\b__TEMP_HIGH__\b", "Low", res_str)

        if isinstance(node, dict):
            res = dict(node)
            if res.get("field") == "High":
                res["field"] = "Low"
            elif res.get("field") == "Low":
                res["field"] = "High"

            if "value_index" in res and isinstance(res["value_index"], int):
                # Negate / flip value index between 0 (e.g. High) and 1 (e.g. Low)
                res["value_index"] = 1 if res["value_index"] == 0 else 0
            return res

        if hasattr(node, "field"):
            f = node.field
            if f == "High":
                node.field = "Low"
            elif f == "Low":
                node.field = "High"
            return node

        return node
