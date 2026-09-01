"""Immutable analytic process-scoring models (internal to the scoring feature).

Contracts here are private to :mod:`app.services.analytics.scoring` and travel
across domains only as validated JSON-safe mappings behind the ``build_*`` /
``parse_*`` function pairs exposed from the package root.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from app.composition.logging import get_logger
from app.services.analytics.contracts.errors import AnalyticsValidationError

logger = get_logger(__name__)

SCORING_CONTRACT_VERSION = "v1"
SCORING_SCHEMA_ID = "analytics.process_score.v1"
SCORING_PROFILE_SCHEMA_ID = "analytics.scoring_profile.v1"

#: Canonical process-first dimensions; every profile and session score must
#: cover exactly this set or fail closed.
SCORING_DIMENSIONS = frozenset(
    {
        "preparation",
        "risk",
        "execution",
        "plan_adherence",
        "portfolio_management",
        "emergency",
        "discipline",
        "post_review",
    }
)

_SHA256_LENGTH = 64
_WEIGHT_TOLERANCE = 1e-9
CriticalFailureKind = Literal["safety", "integrity", "replay"]
CriticalFailureSeverity = Literal["info", "warning", "error", "critical"]
ScoreStatus = Literal["complete", "invalidated"]


def _require_text(value: str, field_name: str) -> str:
    """Validate required trimmed text.

    Args:
        value: Candidate text.
        field_name: Field name used in failure messages.

    Returns:
        The validated trimmed text.

    Raises:
        AnalyticsValidationError: If the value is blank or untrimmed.
    """
    if not value or value != value.strip():
        message = f"{field_name} must be non-empty trimmed text"
        raise AnalyticsValidationError(message)
    return value


def _require_utc(value: datetime, field_name: str) -> datetime:
    """Validate an aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        field_name: Field name used in failure messages.

    Returns:
        The validated aware UTC timestamp.

    Raises:
        AnalyticsValidationError: If the timestamp is not aware UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field_name} must be aware UTC"
        raise AnalyticsValidationError(message)
    return value


def _require_fraction(value: float, field_name: str) -> float:
    """Validate one finite fraction within the closed unit interval.

    Args:
        value: Candidate fraction.
        field_name: Field name used in failure messages.

    Returns:
        The validated value.

    Raises:
        AnalyticsValidationError: If the value is not a finite fraction in
            ``[0, 1]``.
    """
    if (
        not isinstance(value, float)
        or not math.isfinite(value)
        or not (0.0 <= value <= 1.0)
    ):
        message = f"{field_name} must be a finite fraction within [0, 1]"
        raise AnalyticsValidationError(message)
    return value


def _freeze_mapping(mapping: Mapping[str, object]) -> Mapping[str, object]:
    """Return an immutable string-keyed mapping snapshot.

    Args:
        mapping: Candidate mapping.

    Returns:
        An immutable, string-keyed mapping proxy.
    """
    return MappingProxyType({str(key): value for key, value in mapping.items()})


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class CriticalFailureRecord:
    """One deterministic critical-failure observation.

    A critical safety, integrity, or replay failure drives the override that
    caps or invalidates a score regardless of P&L.
    """

    kind: CriticalFailureKind
    severity: CriticalFailureSeverity
    detail: str

    def __post_init__(self) -> None:
        """Validate immutable failure-record invariants.

        Raises:
            AnalyticsValidationError: If a field violates its contract.
        """
        _require_text(self.detail, "detail")
        if self.kind not in {"safety", "integrity", "replay"}:
            raise AnalyticsValidationError("critical failure kind is invalid")
        if self.severity not in {"info", "warning", "error", "critical"}:
            raise AnalyticsValidationError("critical failure severity is invalid")


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class ProcessScoringProfile:
    """A versioned profile governing deterministic process scoring.

    Args:
        profile_version: Version folded into the reproducibility hash.
        dimension_weights: Positive normalized weights covering every dimension,
            summing to one within tolerance.
        critical_failure_policy: ``invalidate`` nulls the weighted total on a
            critical failure; ``cap`` bounds it to a ceiling.
        critical_failure_cap: Ceiling used only when the policy is ``cap``.
    """

    profile_version: str
    dimension_weights: Mapping[str, float]
    critical_failure_policy: Literal["cap", "invalidate"]
    critical_failure_cap: float

    def __post_init__(self) -> None:
        """Validate immutable profile invariants.

        Raises:
            AnalyticsValidationError: If a field violates its contract.
        """
        _require_text(self.profile_version, "profile_version")
        if self.critical_failure_policy not in {"cap", "invalidate"}:
            raise AnalyticsValidationError("critical_failure_policy is invalid")
        _require_fraction(self.critical_failure_cap, "critical_failure_cap")
        weights = dict(self.dimension_weights)
        if set(weights) != SCORING_DIMENSIONS:
            raise AnalyticsValidationError(
                "dimension_weights must cover every scoring dimension exactly"
            )
        for dimension, weight in weights.items():
            if (
                not isinstance(weight, float)
                or not math.isfinite(weight)
                or not 0.0 < weight <= 1.0
            ):
                message = f"dimension weight is invalid: {dimension}"
                raise AnalyticsValidationError(message)
        if abs(sum(weights.values()) - 1.0) > _WEIGHT_TOLERANCE:
            raise AnalyticsValidationError(
                "dimension_weights must sum to one within tolerance"
            )
        object.__setattr__(self, "dimension_weights", _freeze_mapping(weights))


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class SessionScore:
    """Deterministic process-first score for one trading session.

    ``weighted_total`` is ``None`` when a critical safety/integrity/replay
    failure invalidates the score. ``reproducibility_hash`` is a SHA-256 over the
    deterministic scoring inputs, so rebuilding from the same inputs and profile
    version yields an identical hash.
    """

    session_id: str
    profile_version: str
    dimension_scores: Mapping[str, float]
    weighted_total: float | None
    score_status: ScoreStatus
    critical_failures: tuple[CriticalFailureRecord, ...]
    no_trade: bool
    leaderboard_eligible: bool
    reproducibility_hash: str
    scored_at: datetime
    non_binding: bool

    def __post_init__(self) -> None:
        """Validate immutable session-score invariants.

        Raises:
            AnalyticsValidationError: If a field violates its contract.
        """
        _require_text(self.session_id, "session_id")
        _require_text(self.profile_version, "profile_version")
        _require_text(self.reproducibility_hash, "reproducibility_hash")
        if len(self.reproducibility_hash) != _SHA256_LENGTH:
            raise AnalyticsValidationError("reproducibility_hash must be a SHA-256")
        try:
            int(self.reproducibility_hash, 16)
        except ValueError as error:
            raise AnalyticsValidationError(
                "reproducibility_hash must be hex"
            ) from error
        if self.score_status not in {"complete", "invalidated"}:
            raise AnalyticsValidationError("score_status is invalid")
        if self.weighted_total is not None:
            _require_fraction(self.weighted_total, "weighted_total")
        if (self.weighted_total is None) != (self.score_status == "invalidated"):
            raise AnalyticsValidationError(
                "weighted_total must be absent if and only if score is invalidated"
            )
        if self.leaderboard_eligible and self.score_status == "invalidated":
            raise AnalyticsValidationError(
                "an invalidated score is never leaderboard eligible"
            )
        scores = dict(self.dimension_scores)
        if set(scores) != SCORING_DIMENSIONS:
            raise AnalyticsValidationError(
                "dimension_scores must cover every scoring dimension exactly"
            )
        for dimension, value in scores.items():
            _require_fraction(value, f"dimension_scores.{dimension}")
        if any(
            not isinstance(item, CriticalFailureRecord)
            for item in self.critical_failures
        ):
            raise AnalyticsValidationError(
                "critical_failures must contain only failure records"
            )
        object.__setattr__(self, "dimension_scores", _freeze_mapping(scores))


@dataclass(config=ConfigDict(frozen=True, extra="forbid"))
class LeaderboardRank:
    """One deterministic comparative ranking row.

    Process and safety/risk-adjusted scores rank above raw profit, which is only
    a deterministic secondary tiebreaker.
    """

    session_id: str
    rank: int
    process_score: float | None
    profit: str | None
    eligible: bool

    def __post_init__(self) -> None:
        """Validate immutable ranking-row invariants.

        Raises:
            AnalyticsValidationError: If a field violates its contract.
        """
        _require_text(self.session_id, "session_id")
        if self.rank < 1:
            raise AnalyticsValidationError("rank must be a positive integer")
        if self.process_score is not None and not (
            isinstance(self.process_score, float) and math.isfinite(self.process_score)
        ):
            raise AnalyticsValidationError("process_score must be a finite float")


def compute_reproducibility_hash(
    *,
    profile_version: str,
    dimension_scores: Mapping[str, float],
    critical_failures: tuple[CriticalFailureRecord, ...],
    no_trade: bool,
    critical_failure_policy: str,
) -> str:
    """Compute the deterministic scoring reproducibility hash.

    Args:
        profile_version: Scored profile version.
        dimension_scores: Dimension scores folded into the hash.
        critical_failures: Failure records folded in sorted order.
        no_trade: Whether the session was a no-trade stand-down.
        critical_failure_policy: Active override policy.

    Returns:
        A SHA-256 hex digest over canonical ordered inputs.
    """
    from hashlib import sha256

    from app.kernel.serialization import canonical_json

    material = {
        "contract_version": SCORING_CONTRACT_VERSION,
        "schema_id": SCORING_SCHEMA_ID,
        "profile_version": profile_version,
        "dimension_scores": sorted(dimension_scores.items()),
        "critical_failures": sorted(
            (failure.kind, failure.severity, failure.detail)
            for failure in critical_failures
        ),
        "no_trade": bool(no_trade),
        "critical_failure_policy": critical_failure_policy,
    }
    return sha256(canonical_json(material).encode("utf-8")).hexdigest()


__all__ = [
    "SCORING_CONTRACT_VERSION",
    "SCORING_DIMENSIONS",
    "SCORING_PROFILE_SCHEMA_ID",
    "SCORING_SCHEMA_ID",
    "CriticalFailureRecord",
    "LeaderboardRank",
    "ProcessScoringProfile",
    "SessionScore",
    "compute_reproducibility_hash",
]
