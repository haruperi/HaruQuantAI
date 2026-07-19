"""Evidence-only overfit assessment."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from app.utils import logger

if TYPE_CHECKING:
    from app.services.optimization.scoring.contracts import CandidateScore


def assess_overfit_evidence(
    *,
    in_sample: CandidateScore,
    out_of_sample: CandidateScore,
    nominal_trials: int,
    deflated_sharpe: float | None,
    minimum_trade_count: int,
    extra_evidence: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Assemble degradation and evidence-adequacy diagnostics.

    Args:
        in_sample: Training-window score.
        out_of_sample: Test-window score.
        nominal_trials: Unique candidate count.
        deflated_sharpe: Optional published-method probability.
        minimum_trade_count: Explicit evidence adequacy threshold.
        extra_evidence: Optional caller-owned JSON-safe evidence.

    Returns:
        Advisory overfit evidence without readiness authority.

    Raises:
        ValueError: If score identities or supplied bounds conflict.
    """
    logger.info("Assessing Optimization overfit evidence")
    if in_sample.objective is not out_of_sample.objective:
        raise ValueError("IS and OOS scores must use the same objective")
    if nominal_trials < 1 or minimum_trade_count <= 0:
        raise ValueError("trial and trade-count bounds must be positive")
    if deflated_sharpe is not None and not 0 <= deflated_sharpe <= 1:
        raise ValueError("Deflated Sharpe evidence must be a probability")
    degradation = None
    if in_sample.value is not None and out_of_sample.value is not None:
        denominator = abs(in_sample.value)
        degradation = (
            None
            if denominator == 0
            else (in_sample.value - out_of_sample.value) / denominator
        )
    observed_trades = out_of_sample.trade_count
    trade_count_adequate = (
        observed_trades is not None and observed_trades >= minimum_trade_count
    )
    caveats = ["nominal_trials_are_not_independent"]
    if deflated_sharpe is None:
        caveats.append("deflated_sharpe_unavailable")
    if not trade_count_adequate:
        caveats.append("insufficient_trade_count")
    return {
        "objective": in_sample.objective.value,
        "degradation": degradation,
        "nominal_trials": nominal_trials,
        "deflated_sharpe": deflated_sharpe,
        "trade_count_adequate": trade_count_adequate,
        "caveats": tuple(caveats),
        "extra_evidence": dict(extra_evidence or {}),
    }


__all__ = ["assess_overfit_evidence"]
