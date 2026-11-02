"""Fractal negater conforming to StrategyQuant FractalNegater snippet.

Description:
    Swaps UpFractal and DownFractal indicator lines, toggling OutputIndex
    between 0 and 1.

Purpose:
    FEAT-NEGATER-FRACTAL: StrategyQuant donor-faithful Fractal line inversion.

Key Capabilities:
    - FR-NEGATER-FRACTAL-SWAP: Toggle UpFractal and DownFractal output lines.

Python API Usage:
    from app.extend.negater.fractal_negater import FractalNegater
    negated = FractalNegater.negate("UpFractal")

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater

logger = get_logger(__name__)


class FractalNegater(Negater):
    """Swaps UpFractal and DownFractal (SortOrder=900000)."""

    order: ClassVar[int] = 900_000

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Swap UpFractal and DownFractal across representations.

        Args:
            node: Target Fractal indicator representation.
            strategy: Optional StrategyBase context.

        Returns:
            Inverted Fractal indicator representation.
        """
        logger.debug("FR-NEGATER-FRACTAL-SWAP: swapping Fractal output")

        if isinstance(node, str):
            res_str = re.sub(r"\bUpFractal\b", "__TEMP_FRACTAL__", node)
            res_str = re.sub(r"\bDownFractal\b", "UpFractal", res_str)
            return re.sub(r"\b__TEMP_FRACTAL__\b", "DownFractal", res_str)

        if isinstance(node, dict):
            res = dict(node)
            if "output_index" in res and isinstance(res["output_index"], int):
                res["output_index"] = 0 if res["output_index"] == 1 else 1
            if "direction" in res:
                res["direction"] = "Down" if res["direction"] == "Up" else "Up"
            return res

        if hasattr(node, "OutputIndex"):
            idx = int(node.OutputIndex)
            node.OutputIndex = 0 if idx == 1 else 1
            return node

        return node
