"""Ulcer Index negater conforming to StrategyQuant UlcerNegater snippet.

Description:
    Toggles the calculation Mode (1 <-> 2) for UlcerIndex indicator blocks
    and inverts associated relational comparisons.

Purpose:
    FEAT-NEGATER-ULCER: StrategyQuant donor-faithful Ulcer Index mode toggle.

Key Capabilities:
    - FR-NEGATER-ULCER-MODE: Toggle UlcerIndex Mode parameter (1 <-> 2).

Python API Usage:
    from app.extend.negater.ulcer_negater import UlcerNegater
    negated = UlcerNegater.negate({"indicator": "UlcerIndex", "mode": 1})

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater
from app.extend.negater.comparisons_negater import ComparisonsNegater

logger = get_logger(__name__)


class UlcerNegater(Negater):
    """Negates Ulcer index conditions and mode (SortOrder=900000)."""

    order: ClassVar[int] = 900_000

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Invert comparison or toggle mode for UlcerIndex representation.

        Args:
            node: Target UlcerIndex node or representation.
            strategy: Optional StrategyBase context.

        Returns:
            Inverted UlcerIndex representation.
        """
        logger.debug("FR-NEGATER-ULCER-MODE: negating UlcerIndex node")

        if isinstance(node, dict):
            res = dict(node)
            if "mode" in res and isinstance(res["mode"], int):
                res["mode"] = 2 if res["mode"] == 1 else 1
            if "Mode" in res and isinstance(res["Mode"], int):
                res["Mode"] = 2 if res["Mode"] == 1 else 1
            return ComparisonsNegater.negate(res, strategy=strategy)

        if hasattr(node, "Mode"):
            mode = node.Mode
            if isinstance(mode, int):
                node.Mode = 2 if mode == 1 else 1
            return node

        return ComparisonsNegater.negate(node, strategy=strategy)
