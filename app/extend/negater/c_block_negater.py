"""Custom block negater conforming to StrategyQuant CBlockNegater snippet.

Description:
    Inverts custom block directions and handles left-right comparison blocks
    comparing numbers against oscillator indicators, adjusting thresholds around
    the oscillator midpoint.

Purpose:
    FEAT-NEGATER-CBLOCK: StrategyQuant donor-faithful custom block negation.

Key Capabilities:
    - FR-NEGATER-CBLOCK-DIR: Invert custom block directional parameters.
    - FR-NEGATER-CBLOCK-OSC: Mirror threshold around oscillator midpoint.

Python API Usage:
    from app.extend.negater.c_block_negater import CBlockNegater
    negated_block = CBlockNegater.negate({"type": "CBlock", "direction": 1})

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater

logger = get_logger(__name__)

_DEFAULT_OSC_MIDPOINTS: dict[str, float] = {
    "RSI": 50.0,
    "Stochastic": 50.0,
    "MFI": 50.0,
    "CCI": 0.0,
    "MACD": 0.0,
}


def _get_oscillator_middle_value(indicator_name: str) -> float:
    """Return the midpoint value for an oscillator indicator."""
    for key, val in _DEFAULT_OSC_MIDPOINTS.items():
        if key.lower() in indicator_name.lower():
            return val
    return 0.0


class CBlockNegater(Negater):
    """Negates custom block directional parameters and comparisons (SortOrder=1000)."""

    order: ClassVar[int] = 1_000

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Invert direction and mirror oscillator comparisons in custom blocks.

        Args:
            node: Target custom block representation.
            strategy: Optional StrategyBase context.

        Returns:
            Negated custom block representation.
        """
        logger.debug("FR-NEGATER-CBLOCK-DIR: negating custom block node")

        if isinstance(node, dict):
            res = dict(node)
            if "direction" in res:
                d = res["direction"]
                if isinstance(d, int):
                    res["direction"] = -d
                else:
                    res["direction"] = "Short" if d == "Long" else "Long"

            # Check for left-right oscillator comparison
            left = res.get("left")
            right = res.get("right")
            if isinstance(left, (int, float)) and isinstance(right, str):
                mid = _get_oscillator_middle_value(right)
                diff = mid - float(left)
                res["left"] = mid + diff
            elif isinstance(right, (int, float)) and isinstance(left, str):
                mid = _get_oscillator_middle_value(left)
                diff = mid - float(right)
                res["right"] = mid + diff

            return res

        if hasattr(node, "direction"):
            d = node.direction
            if isinstance(d, int):
                node.direction = -d
            elif d == "Long":
                node.direction = "Short"
            elif d == "Short":
                node.direction = "Long"
            return node

        return node
