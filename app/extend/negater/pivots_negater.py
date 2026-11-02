"""Pivots negater conforming to StrategyQuant PivotsNegater snippet.

Description:
    Swaps Support and Resistance pivot levels (R1 <-> S1, R2 <-> S2, R3 <-> S3)
    while preserving the central Pivot line (0 <-> 0), conforming to the
    StrategyQuant pivot level rotation index table.

Purpose:
    FEAT-NEGATER-PIVOTS: StrategyQuant donor-faithful pivot levels inversion.

Key Capabilities:
    - FR-NEGATER-PIVOTS-MAP: Map R1-R3 <-> S1-S3 lines and output indices.

Python API Usage:
    from app.extend.negater.pivots_negater import PivotsNegater
    negated = PivotsNegater.negate("High > R1")

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater

logger = get_logger(__name__)


class PivotsNegater(Negater):
    """Swaps Support and Resistance pivot levels (SortOrder=900000)."""

    order: ClassVar[int] = 900_000

    _PIVOT_INDEX_MAP: ClassVar[dict[int, int]] = {
        0: 0,  # Pivot
        1: 4,  # R1 -> S1
        2: 5,  # R2 -> S2
        3: 6,  # R3 -> S3
        4: 1,  # S1 -> R1
        5: 2,  # S2 -> R2
        6: 3,  # S3 -> R3
    }

    _PIVOT_NAME_MAP: ClassVar[dict[str, str]] = {
        "R1": "S1",
        "R2": "S2",
        "R3": "S3",
        "S1": "R1",
        "S2": "R2",
        "S3": "R3",
    }

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Swap Resistance and Support pivots across representations.

        Args:
            node: Target Pivots representation.
            strategy: Optional StrategyBase context.

        Returns:
            Inverted Pivots representation.
        """
        logger.debug("FR-NEGATER-PIVOTS-MAP: swapping pivot levels")

        if isinstance(node, str):
            res_str = re.sub(r"\bR1\b", "__TEMP_R1__", node)
            res_str = re.sub(r"\bS1\b", "R1", res_str)
            res_str = re.sub(r"\b__TEMP_R1__\b", "S1", res_str)
            res_str = re.sub(r"\bR2\b", "__TEMP_R2__", res_str)
            res_str = re.sub(r"\bS2\b", "R2", res_str)
            res_str = re.sub(r"\b__TEMP_R2__\b", "S2", res_str)
            res_str = re.sub(r"\bR3\b", "__TEMP_R3__", res_str)
            res_str = re.sub(r"\bS3\b", "R3", res_str)
            return re.sub(r"\b__TEMP_R3__\b", "S3", res_str)

        if isinstance(node, dict):
            res = dict(node)
            if "output_index" in res and isinstance(res["output_index"], int):
                idx = res["output_index"]
                res["output_index"] = cls._PIVOT_INDEX_MAP.get(idx, idx)

            if "line_name" in res and isinstance(res["line_name"], str):
                name = res["line_name"]
                res["line_name"] = cls._PIVOT_NAME_MAP.get(name, name)
            return res

        if hasattr(node, "OutputIndex"):
            idx = int(node.OutputIndex)
            node.OutputIndex = cls._PIVOT_INDEX_MAP.get(idx, idx)
            return node

        return node
