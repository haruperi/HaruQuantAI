"""Conditions negater conforming to StrategyQuant ConditionsNegater snippet.

Description:
    Composite condition negater that detects oscillator-based conditions,
    bands, and directional indicators to apply suitable mathematical reflections
    and operator inversions.

Purpose:
    FEAT-NEGATER-COND: StrategyQuant donor-faithful condition node negation.

Key Capabilities:
    - FR-NEGATER-COND-DISPATCH: Dispatch condition to specialized negater.
    - FR-NEGATER-COND-OSC: Mirror oscillator threshold around midpoint.

Python API Usage:
    from app.extend.negater.conditions_negater import ConditionsNegater
    negated = ConditionsNegater.negate("RSI(14) > 70")

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import Negater
from app.extend.negater.comparisons_negater import ComparisonsNegater

logger = get_logger(__name__)

_BAND_KEYWORDS = ("BollingerBands", "Bands", "Keltner")
_OSC_KEYWORDS = ("RSI", "Stochastic", "MFI", "CCI", "MACD")


def _get_target_negater(text: str) -> type[Negater]:
    """Identify which negater class should handle the condition text."""
    if any(x in text for x in _BAND_KEYWORDS):
        from app.extend.negater.upper_lower_negater import UpperLowerNegater

        return UpperLowerNegater
    if any(x in text for x in _OSC_KEYWORDS):
        from app.extend.negater.oscillator_comparisons_negater import (
            OscillatorComparisonsNegater,
        )

        return OscillatorComparisonsNegater
    return ComparisonsNegater


class ConditionsNegater(Negater):
    """Composite conditions negater (SortOrder=10000)."""

    order: ClassVar[int] = 10_000

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Negate condition node across string, dict, or object representations.

        Args:
            node: Target condition node.
            strategy: Optional StrategyBase context.

        Returns:
            Negated condition representation.
        """
        logger.debug("FR-NEGATER-COND-DISPATCH: negating condition node")
        if isinstance(node, str):
            target_cls = _get_target_negater(node)
            return target_cls.negate(node, strategy=strategy)

        if isinstance(node, dict):
            indicator = str(node.get("indicator", ""))
            target_cls = _get_target_negater(indicator)
            return target_cls.negate(node, strategy=strategy)

        return ComparisonsNegater.negate(node, strategy=strategy)
