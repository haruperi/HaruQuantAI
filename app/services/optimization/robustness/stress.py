"""Explicit execution-cost stress transformations."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from decimal import Decimal

from app.services.optimization.robustness.contracts import (  # noqa: TC001
    ExecutionStressRequest,
)
from app.utils import logger


def apply_execution_cost_stress(
    outcomes: Sequence[Mapping[str, object]], request: ExecutionStressRequest
) -> tuple[dict[str, object], ...]:
    """Copy and stress outcome ``pnl`` values without hidden conversion.

    Cost stress values are absolute amounts in the same unit as each outcome's
    Decimal ``pnl``. Skip-trade values are probabilities in ``[0, 1]``.

    Args:
        outcomes: Outcome records containing finite Decimal ``pnl`` values.
        request: Explicit stress assumption.

    Returns:
        Copied stressed outcome records.

    Raises:
        ValueError: If an outcome or its unit is invalid.
    """
    logger.info("Applying explicit Optimization execution-cost stress")
    if not outcomes:
        raise ValueError("execution stress outcomes cannot be empty")
    rng = random.Random(request.seed) if request.kind == "skip_trade" else None
    stressed: list[dict[str, object]] = []
    for outcome in outcomes:
        copied = dict(outcome)
        pnl = copied.get("pnl")
        if not isinstance(pnl, Decimal) or not pnl.is_finite():
            raise ValueError("execution stress requires finite Decimal pnl")
        if request.kind == "skip_trade":
            if rng is None:
                raise ValueError("skip-trade stress requires a seed")
            copied["pnl"] = (
                Decimal(0) if Decimal(str(rng.random())) < request.value else pnl
            )
        else:
            copied["pnl"] = pnl - request.value
        stressed.append(copied)
    return tuple(stressed)


__all__ = ["apply_execution_cost_stress"]
