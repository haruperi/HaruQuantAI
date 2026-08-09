"""Deterministic process-first scoring evidence (FEAT-ANLT-06).

Implements the approved Phase 0 process scoring behavior:
process-first dimension scoring, critical-failure override (a critical safety,
integrity, or replay failure caps or invalidates the score regardless of P&L),
score reproducibility (identical inputs + profile version rebuild an identical
hash), comparative leaderboard ranking (process/safety/risk-adjusted ranking
with profit only secondary), and no-trade scoring.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import TypeVar, cast

from pydantic import ValidationError

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.evidence import to_report_json_safe
from app.services.analytics.scoring.models import (
    SCORING_CONTRACT_VERSION,
    SCORING_DIMENSIONS,
    SCORING_PROFILE_SCHEMA_ID,
    SCORING_SCHEMA_ID,
    CriticalFailureRecord,
    LeaderboardRank,
    ProcessScoringProfile,
    SessionScore,
    compute_reproducibility_hash,
)
from app.utils import get_logger

logger = get_logger(__name__)


_ModelT = TypeVar("_ModelT")


def _build_model(model: type[_ModelT], **values: object) -> _ModelT:
    """Construct one validated model, mapping validation failures to Analytics.

    Pydantic wraps ``__post_init__`` failures in :class:`ValidationError`; the
    Analytics boundary must classify every input failure as
    ``AnalyticsValidationError`` (fail-closed, never a silent execution error).

    Args:
        model: Model type to construct.
        **values: Validated field values.

    Returns:
        The constructed immutable model instance.

    Raises:
        AnalyticsValidationError: If model validation fails.
    """
    try:
        return model(**values)
    except ValidationError as error:
        message = str(error).splitlines()[0] if str(error) else "invalid model input"
        raise AnalyticsValidationError(message) from error


def create_process_scoring_profile(
    profile_version: str,
    dimension_weights: Mapping[str, float],
    *,
    critical_failure_policy: str = "invalidate",
    critical_failure_cap: float = 0.0,
) -> ProcessScoringProfile:
    """Construct a validated process scoring profile.

    Args:
        profile_version: Version folded into every reproducibility hash.
        dimension_weights: Positive normalized weights covering every canonical
            scoring dimension.
        critical_failure_policy: ``invalidate`` or ``cap`` override policy.
        critical_failure_cap: Ceiling used only under the ``cap`` policy.

    Returns:
        Immutable validated scoring profile.

    Raises:
        AnalyticsValidationError: If profile inputs are invalid.
    """
    logger.info("Creating a validated process scoring profile")
    return _build_model(
        ProcessScoringProfile,
        profile_version=profile_version,
        dimension_weights=dict(dimension_weights),
        critical_failure_policy=critical_failure_policy,
        critical_failure_cap=critical_failure_cap,
    )


def create_critical_failure_record(
    kind: str,
    severity: str,
    detail: str,
) -> CriticalFailureRecord:
    """Construct one validated critical-failure observation.

    Args:
        kind: One of ``safety``, ``integrity``, ``replay``.
        severity: One of ``info``, ``warning``, ``error``, ``critical``.
        detail: Redacted, bounded failure detail.

    Returns:
        Immutable critical-failure record.

    Raises:
        AnalyticsValidationError: If the record is invalid.
    """
    logger.info("Creating a critical-failure observation record")
    return _build_model(
        CriticalFailureRecord,
        kind=kind,
        severity=severity,
        detail=detail,
    )


def _validate_scored_at(value: datetime) -> datetime:
    """Validate an aware UTC scoring timestamp.

    Args:
        value: Candidate scoring timestamp.

    Returns:
        The validated aware UTC timestamp.

    Raises:
        AnalyticsValidationError: If the timestamp is not aware UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise AnalyticsValidationError("scored_at must be aware UTC")
    return value


def build_session_score(
    profile: ProcessScoringProfile,
    dimension_scores: Mapping[str, float],
    *,
    session_id: str,
    scored_at: datetime,
    critical_failures: Sequence[CriticalFailureRecord] = (),
    no_trade: bool = False,
) -> SessionScore:
    """Compute one deterministic process-first session score.

    A critical safety/integrity/replay failure invokes the profile's override
    policy: ``invalidate`` nulls the weighted total (the score is not
    leaderboard eligible) and ``cap`` bounds the total to the profile ceiling,
    independent of any P&L.

    Args:
        profile: Validated scoring profile.
        dimension_scores: One score per canonical dimension within ``[0, 1]``.
        session_id: Identifier of the scored session.
        scored_at: Aware UTC scoring timestamp.
        critical_failures: Observed safety/integrity/replay failures.
        no_trade: Whether the session was a correct stand-down / controlled-loss
            no-trade outcome.

    Returns:
        Immutable session score with a deterministic reproducibility hash.

    Raises:
        AnalyticsValidationError: If any scoring input is invalid.
    """
    logger.info("Building a deterministic process session score")
    _validate_scored_at(scored_at)
    scores = dict(dimension_scores)
    if set(scores) != SCORING_DIMENSIONS:
        raise AnalyticsValidationError(
            "dimension_scores must cover every scoring dimension exactly"
        )
    failures = tuple(critical_failures)
    critical_present = any(
        failure.severity == "critical"
        and failure.kind in {"safety", "integrity", "replay"}
        for failure in failures
    )
    weighted_total = sum(
        profile.dimension_weights[dimension] * scores[dimension]
        for dimension in SCORING_DIMENSIONS
    )
    score_status: str
    final_total: float | None
    if critical_present and profile.critical_failure_policy == "invalidate":
        score_status, final_total = "invalidated", None
    elif critical_present and profile.critical_failure_policy == "cap":
        score_status, final_total = (
            "complete",
            min(weighted_total, profile.critical_failure_cap),
        )
    else:
        score_status, final_total = "complete", weighted_total
    hash_value = compute_reproducibility_hash(
        profile_version=profile.profile_version,
        dimension_scores=scores,
        critical_failures=failures,
        no_trade=no_trade,
        critical_failure_policy=profile.critical_failure_policy,
    )
    return _build_model(
        SessionScore,
        session_id=session_id,
        profile_version=profile.profile_version,
        dimension_scores=scores,
        weighted_total=final_total,
        score_status=score_status,
        critical_failures=failures,
        no_trade=bool(no_trade),
        leaderboard_eligible=score_status == "complete",
        reproducibility_hash=hash_value,
        scored_at=scored_at,
        non_binding=True,
    )


def compute_leaderboard_ranking(
    scores: Sequence[SessionScore],
    profits: Mapping[str, str] | None = None,
    *,
    limit: int | None = None,
) -> tuple[LeaderboardRank, ...]:
    """Rank sessions with process/safety/risk-adjusted score primary.

    Profit is only a deterministic secondary tiebreaker, and sessions are never
    ranked above their deterministic eligibility.

    Args:
        scores: Session scores to rank.
        profits: Optional mapping of session_id to canonical profit text.
        limit: Optional positive cap on the number of ranked rows.

    Returns:
        Ordered deterministic ranking rows.

    Raises:
        AnalyticsValidationError: If ranking inputs are invalid.
    """
    logger.info("Computing deterministic leaderboard ranking")
    if limit is not None and limit <= 0:
        raise AnalyticsValidationError("limit must be a positive integer when set")
    profit_map = dict(profits) if profits is not None else {}
    keyed = []
    for score in scores:
        raw_profit = profit_map.get(score.session_id)
        numeric_profit: float | None = None
        if raw_profit is not None:
            try:
                numeric_profit = float(raw_profit)
            except (TypeError, ValueError) as error:
                raise AnalyticsValidationError(
                    "leaderboard profit is not a finite number"
                ) from error
            if not math.isfinite(numeric_profit):
                raise AnalyticsValidationError(
                    "leaderboard profit is not a finite number"
                )
        keyed.append((score, numeric_profit))
    # Eligible first; process score descending; profit descending; id ascending.
    keyed.sort(
        key=lambda item: (
            0 if item[0].leaderboard_eligible else 1,
            -(item[0].weighted_total if item[0].weighted_total is not None else -1.0),
            -(item[1] if item[1] is not None else -1.0),
            item[0].session_id,
        )
    )
    ranked = []
    for index, item in enumerate(keyed[:limit] if limit is not None else keyed):
        ranked.append(
            _build_model(
                LeaderboardRank,
                session_id=item[0].session_id,
                rank=index + 1,
                process_score=item[0].weighted_total,
                profit=profit_map.get(item[0].session_id),
                eligible=item[0].leaderboard_eligible,
            )
        )
    return tuple(ranked)


def build_process_score_mapping(score: SessionScore) -> Mapping[str, object]:
    """Serialize one session score to a validated JSON-safe v1 mapping.

    Args:
        score: Session score to serialize.

    Returns:
        Deterministic JSON-safe contract mapping.

    Raises:
        AnalyticsValidationError: If serialization is unsafe.
    """
    logger.info("Building a process-score v1 JSON-safe mapping")
    payload = {
        "contract_version": SCORING_CONTRACT_VERSION,
        "schema_id": SCORING_SCHEMA_ID,
        "session_id": score.session_id,
        "profile_version": score.profile_version,
        "dimension_scores": dict(score.dimension_scores),
        "weighted_total": score.weighted_total,
        "score_status": score.score_status,
        "critical_failures": [
            {"kind": item.kind, "severity": item.severity, "detail": item.detail}
            for item in score.critical_failures
        ],
        "no_trade": score.no_trade,
        "leaderboard_eligible": score.leaderboard_eligible,
        "reproducibility_hash": score.reproducibility_hash,
        "scored_at": score.scored_at.isoformat(),
        "non_binding": score.non_binding,
    }
    safe = to_report_json_safe(payload)
    if not isinstance(safe, dict):
        raise AnalyticsValidationError("process score mapping is unsafe")
    return dict(safe)


def parse_process_score_mapping(mapping: Mapping[str, object]) -> SessionScore:
    """Validate and denormalize a v1 process-score mapping into a score.

    Args:
        mapping: Contract mapping produced by ``build_process_score_mapping``.

    Returns:
        Immutable session score.

    Raises:
        AnalyticsValidationError: If the mapping is invalid or a version conflict
            would lead to silent field loss.
    """
    logger.info("Validating a process-score v1 mapping")
    data = dict(mapping)
    if data.get("contract_version") != SCORING_CONTRACT_VERSION:
        raise AnalyticsValidationError("process score contract version is unsupported")
    if data.get("schema_id") != SCORING_SCHEMA_ID:
        raise AnalyticsValidationError("process score schema id is unsupported")
    try:
        scored_at = datetime.fromisoformat(str(data["scored_at"]))
    except (KeyError, ValueError, TypeError) as error:
        raise AnalyticsValidationError(
            "process score mapping scored_at is invalid"
        ) from error
    failures_raw = cast("Sequence[Mapping[str, object]]", data["critical_failures"])
    failures = tuple(
        _build_model(
            CriticalFailureRecord,
            kind=str(item["kind"]),
            severity=str(item["severity"]),
            detail=str(item["detail"]),
        )
        for item in failures_raw
    )
    return _build_model(
        SessionScore,
        session_id=str(data["session_id"]),
        profile_version=str(data["profile_version"]),
        dimension_scores=cast("Mapping[str, float]", data["dimension_scores"]),
        weighted_total=cast("float | None", data.get("weighted_total")),
        score_status=str(data["score_status"]),
        critical_failures=failures,
        no_trade=bool(data["no_trade"]),
        leaderboard_eligible=bool(data["leaderboard_eligible"]),
        reproducibility_hash=str(data["reproducibility_hash"]),
        scored_at=scored_at,
        non_binding=bool(data["non_binding"]),
    )


def build_scoring_profile_mapping(
    profile: ProcessScoringProfile,
) -> Mapping[str, object]:
    """Serialize one scoring profile to a validated JSON-safe v1 mapping.

    Args:
        profile: Scoring profile to serialize.

    Returns:
        Deterministic JSON-safe contract mapping.

    Raises:
        AnalyticsValidationError: If serialization is unsafe.
    """
    payload = {
        "contract_version": SCORING_CONTRACT_VERSION,
        "schema_id": SCORING_PROFILE_SCHEMA_ID,
        "profile_version": profile.profile_version,
        "dimension_weights": dict(profile.dimension_weights),
        "critical_failure_policy": profile.critical_failure_policy,
        "critical_failure_cap": profile.critical_failure_cap,
    }
    safe = to_report_json_safe(payload)
    if not isinstance(safe, dict):
        raise AnalyticsValidationError("scoring profile mapping is unsafe")
    return dict(safe)


def parse_scoring_profile_mapping(
    mapping: Mapping[str, object],
) -> ProcessScoringProfile:
    """Validate and denormalize a v1 scoring-profile mapping.

    Args:
        mapping: Contract mapping produced by ``build_scoring_profile_mapping``.

    Returns:
        Immutable scoring profile.

    Raises:
        AnalyticsValidationError: If the mapping is invalid or a version
            conflict would lead to silent field loss.
    """
    data = dict(mapping)
    if data.get("contract_version") != SCORING_CONTRACT_VERSION:
        raise AnalyticsValidationError(
            "scoring profile contract version is unsupported"
        )
    if data.get("schema_id") != SCORING_PROFILE_SCHEMA_ID:
        raise AnalyticsValidationError("scoring profile schema id is unsupported")
    return _build_model(
        ProcessScoringProfile,
        profile_version=str(data["profile_version"]),
        dimension_weights=cast("Mapping[str, float]", data["dimension_weights"]),
        critical_failure_policy=str(data["critical_failure_policy"]),
        critical_failure_cap=float(str(data["critical_failure_cap"])),
    )


__all__ = [
    "build_process_score_mapping",
    "build_scoring_profile_mapping",
    "build_session_score",
    "compute_leaderboard_ranking",
    "create_critical_failure_record",
    "create_process_scoring_profile",
    "parse_process_score_mapping",
    "parse_scoring_profile_mapping",
]
