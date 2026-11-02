"""Formula negater conforming to StrategyQuant FormulaNegater snippet.

Description:
    Swaps arithmetic signs (+ <-> -) in mathematical formula blocks while
    preserving operand structure.

Purpose:
    FEAT-NEGATER-FORMULA: StrategyQuant donor-faithful formula sign inversion.

Key Capabilities:
    - FR-NEGATER-FORMULA-SIGNS: Invert addition and subtraction arithmetic signs.

Python API Usage:
    from app.extend.negater.formula_negater import FormulaNegater
    negated = FormulaNegater.negate("A + B - C")

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater

logger = get_logger(__name__)


class FormulaNegater(Negater):
    """Swaps arithmetic signs (+ <-> -) in formulas (SortOrder=8000)."""

    order: ClassVar[int] = 8_000

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Swap addition and subtraction signs across string or dict representations.

        Args:
            node: Target formula representation.
            strategy: Optional StrategyBase context.

        Returns:
            Inverted formula representation.
        """
        logger.debug("FR-NEGATER-FORMULA-SIGNS: inverting formula signs")

        if isinstance(node, str):
            res_str = re.sub(r"\+", "__TEMP_PLUS__", node)
            res_str = re.sub(r"-", "+", res_str)
            return re.sub(r"__TEMP_PLUS__", "-", res_str)

        if isinstance(node, dict):
            res = dict(node)
            op = res.get("operator")
            if op == "+":
                res["operator"] = "-"
            elif op == "-":
                res["operator"] = "+"
            return res

        return node
