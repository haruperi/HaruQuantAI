"""Performance drift monitoring and advisory suspension proposals."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from app.services.research.contracts.errors import ValidationError
from app.services.research.drift.contracts import (
    build_performance_drift_evidence,
)
from app.services.research.expectancy.contracts import (
    parse_approved_expectancy_profile,
)
from app.utils import get_logger

logger = get_logger(__name__)

# Default advisory drift thresholds: a 25% relative win-rate or EV drop, or any
# drawdown breach, proposes suspension. These are advisory starting points; the
# owner may override them per evaluation.
_DEFAULT_THRESHOLDS = {"win_rate": 0.25, "expected_value": 0.25, "drawdown": 0.01}


def monitor_performance_drift(
    *,
    approved_profile: Mapping[str, object],
    observed_from_utc: datetime,
    observed_to_utc: datetime,
    observed_win_rate: float,
    observed_expected_value_r: float,
    observed_max_drawdown_r: float,
    thresholds: Mapping[str, float] | None = None,
    generated_at_utc: datetime,
) -> dict[str, Any]:
    """Build drift evidence from observed outcomes vs an approved envelope.

    Args:
        approved_profile: Approved expectancy profile mapping (the envelope).
        observed_from_utc: Inclusive start of the observation window.
        observed_to_utc: Inclusive end of the observation window.
        observed_win_rate: Observed live-sim/paper win rate.
        observed_expected_value_r: Observed live-sim/paper EV in R.
        observed_max_drawdown_r: Observed drawdown magnitude in R.
        thresholds: Optional drift thresholds; defaults to 25% relative drops.
        generated_at_utc: Evidence generation instant.

    Returns:
        JSON-safe performance drift evidence mapping.

    Raises:
        ValidationError: If the approved profile is not approved or stats invalid.
    """
    logger.info(
        "Monitoring performance drift for %s", approved_profile.get("profile_id")
    )
    profile = parse_approved_expectancy_profile(approved_profile)
    if profile["governance_state"] != "approved":
        raise ValidationError(
            "RES_DRIFT_INSUFFICIENT_EVIDENCE", "ENVELOPE_NOT_APPROVED"
        )
    effective_thresholds = dict(thresholds) if thresholds else dict(_DEFAULT_THRESHOLDS)
    return build_performance_drift_evidence(
        profile_id=str(profile["profile_id"]),
        observed_from_utc=observed_from_utc,
        observed_to_utc=observed_to_utc,
        observed_win_rate=observed_win_rate,
        observed_expected_value_r=observed_expected_value_r,
        observed_max_drawdown_r=observed_max_drawdown_r,
        envelope_win_rate=float(profile["win_rate"]),
        envelope_expected_value_r=float(profile["expected_value_r"]),
        envelope_max_drawdown_r=float(profile["max_drawdown_r"]),
        thresholds=effective_thresholds,
        generated_at_utc=generated_at_utc,
    )


def propose_drift_suspension(
    evidence: Mapping[str, object],
) -> Mapping[str, object]:
    """Return an advisory suspension proposal from drift evidence.

    The proposal is advisory only: it never mutates governance state. The owner
    (or an automated governance caller) decides whether to apply the
    ``suspended`` transition. A no-breach evidence produces no proposal.

    Args:
        evidence: Validated performance drift evidence mapping.

    Returns:
        Advisory proposal mapping with ``proposal``/``profile_id``/``breach``.

    Raises:
        ValidationError: If the evidence has no suspension proposal when one is
            expected, or the evidence is structurally invalid.
    """
    logger.info(
        "Proposing advisory drift suspension for %s", evidence.get("profile_id")
    )
    if not isinstance(evidence, Mapping):
        raise ValidationError("RES_INPUT_INVALID", "DRIFT_NOT_MAPPING")
    breach = evidence.get("breach")
    if not isinstance(breach, (tuple, list)):
        raise ValidationError("RES_INPUT_INVALID", "DRIFT_BREACH_INVALID")
    if not breach:
        return {
            "proposal": "no_suspension",
            "profile_id": evidence.get("profile_id"),
            "breach": [],
            "advisory_only": True,
        }
    return {
        "proposal": "suspend",
        "profile_id": evidence.get("profile_id"),
        "breach": tuple(breach),
        "reason": "PERFORMANCE_DRIFT_THRESHOLD_BREACHED",
        "advisory_only": True,
    }


__all__ = (
    "monitor_performance_drift",
    "propose_drift_suspension",
)
