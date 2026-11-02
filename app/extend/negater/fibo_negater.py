"""Fibonacci negater conforming to StrategyQuant FiboNegater snippet.

Description:
    Inverts Fibonacci retracement levels around 1.0 (e.g. 0.382 <-> 0.618,
    0.236 <-> 0.764) for symmetric Fibonacci indicator rules.

Purpose:
    FEAT-NEGATER-FIBO: StrategyQuant donor-faithful Fibonacci level reflection.

Key Capabilities:
    - FR-NEGATER-FIBO-REFLECT: Mirror Fibonacci levels around 1.0.

Python API Usage:
    from app.extend.negater.fibo_negater import FiboNegater
    negated = FiboNegater.negate({"indicator": "Fibo", "level": 0.382})

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import FIBO_MAX, Negater

logger = get_logger(__name__)


class FiboNegater(Negater):
    """Inverts Fibonacci retracement levels around 1.0 (SortOrder=900000)."""

    order: ClassVar[int] = 900_000

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Invert Fibonacci ratio across dict, object, or string representations.

        Args:
            node: Target Fibonacci indicator representation.
            strategy: Optional StrategyBase context.

        Returns:
            Reflected Fibonacci indicator representation.
        """
        logger.debug("FR-NEGATER-FIBO-REFLECT: reflecting Fibonacci level")

        if isinstance(node, dict) and "level" in node:
            res = dict(node)
            level = float(res["level"])
            res["level"] = round(FIBO_MAX - level, 4)
            return res

        if isinstance(node, str) and "Fibo" in node:
            m = re.search(r"Fibo(?:Level)?\s*=\s*([0-9.]+)", node)
            if m:
                val = float(m.group(1))
                new_val = round(FIBO_MAX - val, 4)
                return node.replace(m.group(1), str(new_val))

        if hasattr(node, "FiboLevel"):
            val = float(node.FiboLevel)
            node.FiboLevel = round(FIBO_MAX - val, 4)
            return node

        if hasattr(node, "level"):
            val = float(node.level)
            node.level = round(FIBO_MAX - val, 4)
            return node

        return node
