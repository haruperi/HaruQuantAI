"""Approved expectancy governance state machine and exact-match eligibility.

Implements ``feature`` (governance) and ``feature`` (eligibility).
The state machine enforces the approved lifecycle:
``draft -> under_review -> approved -> {suspended, expired, revoked}``.
Eligibility requires an exact match on strategy/instrument/regime/session
against a currently ``approved``, unexpired, non-superseded profile and
never returns an inferred approval (settled decision D-4 / change-control 3).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal, cast

from app.services.research.contracts.errors import (
    ValidationError,
)
from app.services.research.expectancy.contracts import (
    GovernanceState,
    build_approved_expectancy_profile,
    parse_approved_expectancy_profile,
)
from app.utils import canonical_json, derive_stable_id, get_logger

logger = get_logger(__name__)

# Approved transitions: each state may advance only to its listed successors.
# ``revoked`` is terminal; a supersession records ``superseded_by`` and lands in
# ``revoked`` so the audit trail is preserved (financial records are append-only).
_TRANSITIONS: dict[GovernanceState, frozenset[GovernanceState]] = {
    "draft": frozenset({"under_review", "revoked"}),
    "under_review": frozenset({"approved", "draft", "revoked"}),
    "approved": frozenset({"suspended", "expired", "revoked"}),
    "suspended": frozenset({"approved", "revoked"}),
    "expired": frozenset({"revoked"}),
    "revoked": frozenset(),
}


def _derive_profile_id(
    *,
    exact_version: str,
    strategy_ref: str,
    hypothesis: str,
) -> str:
    """Derive a stable surrogate profile identity (OD-RES-01).

    Args:
        exact_version: Version-exact identity.
        strategy_ref: Covered strategy identity.
        hypothesis: Tested hypothesis.

    Returns:
        Stable ``exp-`` prefixed surrogate identity.
    """
    material = canonical_json(
        {
            "exact_version": exact_version,
            "strategy_ref": strategy_ref,
            "hypothesis": hypothesis,
        }
    )
    return derive_stable_id("id", material)


def build_expectancy_profile(
    *,
    exact_version: str,
    hypothesis: str,
    strategy_ref: str,
    instruments: tuple[str, ...],
    regimes: tuple[str, ...],
    sessions: tuple[str, ...],
    sample_from_utc: datetime,
    sample_to_utc: datetime,
    sample_size: int,
    out_of_sample_status: Literal["in_sample", "out_of_sample", "walk_forward"],
    win_rate: float,
    avg_win_r: float,
    avg_loss_r: float,
    expected_value_r: float,
    max_drawdown_r: float,
    min_reward_risk: float,
    evidence_ref: str,
    next_review_at_utc: datetime | None = None,
    expires_at_utc: datetime | None = None,
) -> dict[str, object]:
    """Build one expectancy profile in the ``draft`` governance state.

    Args:
        exact_version: Version-exact identity referenced by Strategy/Risk.
        hypothesis: Tested question or declared research objective.
        strategy_ref: Strategy identity covered by the profile.
        instruments: Exact instrument scope of the approved edge.
        regimes: Exact regime scope of the approved edge.
        sessions: Exact session scope of the approved edge.
        sample_from_utc: Inclusive start of the approved sample window.
        sample_to_utc: Inclusive end of the approved sample window.
        sample_size: Number of observations backing the statistics.
        out_of_sample_status: Declared out-of-sample evidence status.
        win_rate: Observed win probability in ``[0, 1]``.
        avg_win_r: Average winning outcome in R-multiples.
        avg_loss_r: Average losing outcome in R-multiples (non-positive).
        expected_value_r: Expected value per trade in R-multiples.
        max_drawdown_r: Observed maximum drawdown in R-multiples (non-positive).
        min_reward_risk: Minimum reward/risk override carried to Risk.
        evidence_ref: Bounded evidence reference backing the profile.
        next_review_at_utc: Scheduled next review instant, or ``None``.
        expires_at_utc: Expiry instant, or ``None`` when not expiring.

    Returns:
        JSON-safe ``draft`` profile mapping with a derived surrogate identity.

    Raises:
        ValidationError: If profile statistics or lifecycle are invalid.
        ConfigurationError: If canonical hashing fails.
    """
    logger.info("Building draft Research expectancy profile for %s", strategy_ref)
    profile_id = _derive_profile_id(
        exact_version=exact_version,
        strategy_ref=strategy_ref,
        hypothesis=hypothesis,
    )
    return build_approved_expectancy_profile(
        profile_id=profile_id,
        exact_version=exact_version,
        hypothesis=hypothesis,
        strategy_ref=strategy_ref,
        instruments=instruments,
        regimes=regimes,
        sessions=sessions,
        sample_from_utc=sample_from_utc,
        sample_to_utc=sample_to_utc,
        sample_size=sample_size,
        out_of_sample_status=out_of_sample_status,
        win_rate=win_rate,
        avg_win_r=avg_win_r,
        avg_loss_r=avg_loss_r,
        expected_value_r=expected_value_r,
        max_drawdown_r=max_drawdown_r,
        min_reward_risk=min_reward_risk,
        governance_state="draft",
        approved_at_utc=None,
        next_review_at_utc=next_review_at_utc,
        expires_at_utc=expires_at_utc,
        superseded_by=None,
        evidence_ref=evidence_ref,
    )


def transition_expectancy_governance(
    profile: dict[str, object],
    *,
    target_state: GovernanceState,
    reviewer: str,
    decision: str,
    reason: str,
    now_utc: datetime,
    superseded_by: str | None = None,
) -> dict[str, object]:
    """Advance one expectancy profile to an approved successor governance state.

    Args:
        profile: Validated profile mapping.
        target_state: Approved target lifecycle state.
        reviewer: Reviewer principal recording the transition.
        decision: Recorded governance decision label.
        reason: Recorded governance decision reason.
        now_utc: Timezone-aware UTC instant of the transition.
        superseded_by: Surrogate identity superseding this profile, if revoking.

    Returns:
        JSON-safe profile mapping in the target state.

    Raises:
        ValidationError: If the transition is not permitted for the state.
        ConfigurationError: If canonical hashing fails.
    """
    if now_utc.tzinfo is None or now_utc.utcoffset() != UTC.utcoffset(now_utc):
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_TIME_NOT_UTC")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_REVIEWER_EMPTY")
    if not isinstance(decision, str) or not decision.strip():
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_DECISION_EMPTY")
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_REASON_EMPTY")
    parsed = parse_approved_expectancy_profile(profile)
    current = cast("GovernanceState", str(parsed["governance_state"]))
    if target_state not in _TRANSITIONS.get(current, frozenset()):
        logger.warning(
            "Rejecting expectancy transition %s -> %s", current, target_state
        )
        raise ValidationError(
            "RES_GOVERNANCE_TRANSITION_INVALID", "TRANSITION_NOT_PERMITTED"
        )
    approved_at = parsed.get("approved_at_utc")
    if target_state == "approved":
        approved_at = now_utc.isoformat()
    return build_approved_expectancy_profile(
        profile_id=str(parsed["profile_id"]),
        exact_version=str(parsed["exact_version"]),
        hypothesis=str(parsed["hypothesis"]),
        strategy_ref=str(parsed["strategy_ref"]),
        instruments=tuple(parsed["instruments"]),
        regimes=tuple(parsed["regimes"]),
        sessions=tuple(parsed["sessions"]),
        sample_from_utc=datetime.fromisoformat(str(parsed["sample_from_utc"])),
        sample_to_utc=datetime.fromisoformat(str(parsed["sample_to_utc"])),
        sample_size=int(parsed["sample_size"]),
        out_of_sample_status=cast(
            "Literal['in_sample', 'out_of_sample', 'walk_forward']",
            str(parsed["out_of_sample_status"]),
        ),
        win_rate=float(parsed["win_rate"]),
        avg_win_r=float(parsed["avg_win_r"]),
        avg_loss_r=float(parsed["avg_loss_r"]),
        expected_value_r=float(parsed["expected_value_r"]),
        max_drawdown_r=float(parsed["max_drawdown_r"]),
        min_reward_risk=float(parsed["min_reward_risk"]),
        governance_state=target_state,
        approved_at_utc=(
            None if approved_at is None else datetime.fromisoformat(str(approved_at))
        ),
        next_review_at_utc=(
            None
            if parsed.get("next_review_at_utc") is None
            else datetime.fromisoformat(str(parsed["next_review_at_utc"]))
        ),
        expires_at_utc=(
            None
            if parsed.get("expires_at_utc") is None
            else datetime.fromisoformat(str(parsed["expires_at_utc"]))
        ),
        superseded_by=superseded_by,
        evidence_ref=str(parsed["evidence_ref"]),
    )


def is_governance_transition_permitted(
    current: GovernanceState,
    target: GovernanceState,
) -> bool:
    """Return whether one governance transition is permitted.

    Args:
        current: Current lifecycle state.
        target: Candidate target lifecycle state.

    Returns:
        ``True`` if the transition is permitted.
    """
    return target in _TRANSITIONS.get(current, frozenset())


def _exact_match(
    profile: dict[str, object],
    *,
    strategy_ref: str,
    instrument: str,
    regime: str,
    session: str,
) -> bool:
    """Return whether a profile exactly matches the requested scope.

    Exact match is required on every key; partial or wildcard matches are
    rejected so a profile never authorizes an edge it did not evaluate.

    Args:
        profile: Validated profile mapping.
        strategy_ref: Requested strategy identity.
        instrument: Requested instrument identity.
        regime: Requested regime label.
        session: Requested session label.

    Returns:
        ``True`` if every key matches exactly.
    """
    instruments = cast("tuple[str, ...]", profile["instruments"])
    regimes = cast("tuple[str, ...]", profile["regimes"])
    sessions = cast("tuple[str, ...]", profile["sessions"])
    return (
        profile["strategy_ref"] == strategy_ref
        and instrument in instruments
        and regime in regimes
        and session in sessions
    )


def _is_currently_active(
    profile: dict[str, object],
    *,
    now_utc: datetime,
) -> bool:
    """Return whether a profile is approved, unexpired, and not superseded.

    Args:
        profile: Validated profile mapping.
        now_utc: Evaluation instant.

    Returns:
        ``True`` if the profile is currently active.
    """
    if profile["governance_state"] != "approved":
        return False
    if profile.get("superseded_by") is not None:
        return False
    expires = profile.get("expires_at_utc")
    not_expired = expires is None or datetime.fromisoformat(str(expires)) >= now_utc
    return not_expired


def evaluate_expectancy_eligibility(
    profile: dict[str, object] | None,
    *,
    strategy_ref: str,
    instrument: str,
    regime: str,
    session: str,
    now_utc: datetime,
) -> str:
    """Return exact-match eligibility for one profile.

    Implements the Strategy/Risk consumer port contract: ``ELIGIBLE`` only when
    an exact-match approved, unexpired, non-superseded profile is supplied;
    ``NOT_ELIGIBLE`` otherwise. Never returns an inferred approval (change-
    control rule 3): a missing, expired, suspended, revoked, superseded, or
    scope-mismatched profile resolves to ``NOT_ELIGIBLE``.

    Args:
        profile: Validated profile mapping, or ``None`` when no provider exists.
        strategy_ref: Requested strategy identity.
        instrument: Requested instrument identity.
        regime: Requested regime label.
        session: Requested session label.
        now_utc: Evaluation instant.

    Returns:
        ``ELIGIBLE`` or ``NOT_ELIGIBLE``.

    Raises:
        ValidationError: If ``now_utc`` is naive.
    """
    if now_utc.tzinfo is None or now_utc.utcoffset() != UTC.utcoffset(now_utc):
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_TIME_NOT_UTC")
    if profile is None:
        logger.info("Expectancy provider unavailable; returning NOT_ELIGIBLE")
        return "NOT_ELIGIBLE"
    if not _is_currently_active(profile, now_utc=now_utc):
        logger.info("Expectancy profile not currently active; NOT_ELIGIBLE")
        return "NOT_ELIGIBLE"
    if not _exact_match(
        profile,
        strategy_ref=strategy_ref,
        instrument=instrument,
        regime=regime,
        session=session,
    ):
        logger.info("Expectancy profile scope mismatch; NOT_ELIGIBLE")
        return "NOT_ELIGIBLE"
    return "ELIGIBLE"


def get_min_reward_risk_override(
    profile: dict[str, object] | None,
    *,
    strategy_ref: str,
    now_utc: datetime,
) -> Decimal | None:
    """Return the Risk min-R/R override for an eligible approved profile.

    Implements Risk's ``ExpectancyProvider = Callable[[str], Decimal | None]``
    consumer port: returns the profile's ``min_reward_risk`` only when the
    profile is currently active and covers the strategy; ``None`` otherwise so
    Risk falls back to the normal configured minimum (fail-closed).

    Args:
        profile: Validated profile mapping, or ``None`` when no provider exists.
        strategy_ref: Requested strategy identity.
        now_utc: Evaluation instant.

    Returns:
        Minimum reward/risk override, or ``None`` for fail-closed fallback.

    Raises:
        ValidationError: If ``now_utc`` is naive.
    """
    if profile is None:
        return None
    if not _is_currently_active(profile, now_utc=now_utc):
        return None
    if profile["strategy_ref"] != strategy_ref:
        return None
    return Decimal(str(cast("Any", profile["min_reward_risk"])))


__all__ = (
    "build_expectancy_profile",
    "evaluate_expectancy_eligibility",
    "get_min_reward_risk_override",
    "is_governance_transition_permitted",
    "transition_expectancy_governance",
)
