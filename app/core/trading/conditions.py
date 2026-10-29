"""Verified scalar condition comparator for StrategyQuant condition expressions."""

from __future__ import annotations

import math

__all__ = ["ConditionComparator"]


class ConditionComparator:
    """Scalar comparator evaluating delta against zero with verified donor semantics."""

    @staticmethod
    def validate(delta: float, comparator: str) -> bool:
        """Validate delta against zero using the specified operator.

        Supported operators: '>', '<', '=', '>=', '<=', '<>'.
        Raises ValueError for any other comparator.
        """
        if comparator not in (">", "<", "=", ">=", "<=", "<>"):
            raise ValueError(f"Unknown comparator '{comparator}'")

        if math.isnan(delta):
            return comparator == "<>"

        ops = {
            ">": delta > 0.0,
            "<": delta < 0.0,
            "=": delta == 0.0,
            ">=": delta >= 0.0,
            "<=": delta <= 0.0,
            "<>": delta != 0.0,
        }
        return ops[comparator]
