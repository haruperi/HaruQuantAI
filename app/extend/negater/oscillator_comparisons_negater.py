"""Oscillator comparisons negater conforming to StrategyQuant snippet.

Description:
    Inverts relational comparisons and mirrors numerical thresholds around
    oscillator midpoints (50 for RSI/Stochastic/MFI, 0 for zero-centered oscillators).

Purpose:
    FEAT-NEGATER-OSC: StrategyQuant donor-faithful oscillator comparison negation.

Key Capabilities:
    - FR-NEGATER-OSC-MIRROR: Reflect numerical threshold around oscillator center.
    - FR-NEGATER-OSC-COMP: Invert comparison relational operator.

Python API Usage:
    from app.extend.negater.oscillator_comparisons_negater import (
        OscillatorComparisonsNegater,
    )
    negated = OscillatorComparisonsNegater.negate("RSI(14) > 70")

CLI Usage:
    uv run pytest tests/extend/test_negater.py --no-cov
"""

from __future__ import annotations

import re
from typing import Any, ClassVar, override

from app.core.host.logging import get_logger
from app.extend.negater.base import MIDPOINT_50, Negater
from app.extend.negater.comparisons_negater import ComparisonsNegater

logger = get_logger(__name__)


class OscillatorComparisonsNegater(Negater):
    """Inverts comparisons and mirrors oscillator thresholds (SortOrder=1000)."""

    order: ClassVar[int] = 1_000

    @override
    @classmethod
    def negate(cls, node: Any, strategy: Any = None) -> Any:
        """Invert comparison and mirror oscillator threshold.

        Args:
            node: Target comparison node or string.
            strategy: Optional StrategyBase context.

        Returns:
            Inverted comparison representation.
        """
        logger.debug("FR-NEGATER-OSC-MIRROR: reflecting oscillator comparison")

        if isinstance(node, str):
            m = re.match(
                r"^(.*?)\s*(>|<|>=|<=|CrossesAbove|CrossesBelow)\s*([0-9.-]+)$",
                node.strip(),
            )
            if m:
                indicator, op, thresh_str = m.group(1), m.group(2), m.group(3)
                inv_op = ComparisonsNegater.OP_MAP.get(op, op)
                threshold = float(thresh_str)

                # Midpoint 50 for RSI/Stochastic/MFI
                if any(x in indicator for x in ("RSI", "Stochastic", "MFI")):
                    new_thresh = round(MIDPOINT_50 - threshold, 4)
                else:
                    new_thresh = round(-threshold, 4)

                val_repr = int(new_thresh) if new_thresh.is_integer() else new_thresh
                return f"{indicator} {inv_op} {val_repr}"

        if isinstance(node, dict):
            dict_node: dict[str, Any] = dict(node)
            op = dict_node.get("operator", "")
            dict_node["operator"] = ComparisonsNegater.OP_MAP.get(op, op)
            threshold_val = dict_node.get("threshold")
            indicator = dict_node.get("indicator", "")
            if isinstance(threshold_val, (int, float)):
                if any(x in indicator for x in ("RSI", "Stochastic", "MFI")):
                    dict_node["threshold"] = MIDPOINT_50 - threshold_val
                else:
                    dict_node["threshold"] = -threshold_val
            return dict_node

        return ComparisonsNegater.negate(node, strategy=strategy)
