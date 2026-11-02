"""Default negater conforming to StrategyQuant DefaultNegater snippet.

Description:
    Fallback negater operating at the lowest priority (SortOrder=1000000),
    providing comparison operator negation when no specialized negater matches.

Purpose:
    FEAT-NEGATER-DEFAULT: StrategyQuant donor-faithful fallback negation.

Key Capabilities:
    - FR-NEGATER-DEFAULT-FALLBACK: Fallback negation via comparisons handler.

Python API Usage:
    from app.extend.negater.default_negater import DefaultNegater
    negated = DefaultNegater.negate("A > B")

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater
from app.extend.negater.comparisons_negater import ComparisonsNegater

logger = get_logger(__name__)


class DefaultNegater(Negater):
    """Fallback negater applying comparison negation (SortOrder=1000000)."""

    order: ClassVar[int] = 1_000_000

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Apply default fallback negation.

        Args:
            node: Target node representation.
            strategy: Optional StrategyBase context.

        Returns:
            Negated node representation.
        """
        logger.debug("FR-NEGATER-DEFAULT-FALLBACK: applying default negater")
        return ComparisonsNegater.negate(node, strategy=strategy)
