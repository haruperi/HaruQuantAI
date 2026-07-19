"""Availability-aware robustness assessment."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from app.services.optimization.robustness.contracts import (
    MonteCarloResult,  # noqa: TC001
)
from app.utils import logger


def assess_strategy_robustness(
    *,
    monte_carlo: MonteCarloResult | None,
    stress_checks: Sequence[Mapping[str, object]],
    additional_evidence: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Combine only supplied applicable pass/fail robustness checks.

    Args:
        monte_carlo: Optional Monte Carlo evidence.
        stress_checks: Explicit records with Boolean ``passed`` values.
        additional_evidence: Optional owner-supplied JSON-safe evidence.

    Returns:
        Robustness percentage, availability, warnings, and supplied evidence.

    Raises:
        ValueError: If checks are absent, malformed, or contradictory.
    """
    logger.info("Assessing supplied Optimization robustness evidence")
    checks: list[bool] = []
    normalized: list[dict[str, object]] = []
    for check in stress_checks:
        name = check.get("name")
        passed = check.get("passed")
        if (
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(passed, bool)
        ):
            raise ValueError("robustness checks require name and Boolean passed")
        score = check.get("score")
        if score is not None and (
            not isinstance(score, (int, float))
            or isinstance(score, bool)
            or not math.isfinite(float(score))
        ):
            raise ValueError("robustness check score must be finite")
        checks.append(passed)
        normalized.append(dict(check))
    if monte_carlo is not None and monte_carlo.ruin_probability is not None:
        checks.append(monte_carlo.ruin_probability == 0)
    if not checks:
        raise ValueError("at least one applicable robustness check is required")
    percentage = 100.0 * sum(checks) / len(checks)
    warnings = [] if monte_carlo is not None else ["monte_carlo_evidence_missing"]
    return {
        "robustness_percentage": percentage,
        "applicable_check_count": len(checks),
        "monte_carlo_available": monte_carlo is not None,
        "stress_checks": tuple(normalized),
        "additional_evidence": dict(additional_evidence or {}),
        "warnings": tuple(warnings),
    }


__all__ = ["assess_strategy_robustness"]
