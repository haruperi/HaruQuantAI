"""Multi-objective candidate evaluation (feature).

Extends ``FEAT-OPT-02``: combine the enabled core objective (risk-adjusted
performance) with process-adherence, stability, safety, and execution-realism
dimensions so that raw profit is never the sole objective. Analytics owns process
scoring (``feature`` → ``FEAT-ANLT-06``), consumed here only through its
documented JSON-safe ``analytics.process_score.v1`` mapping transport; Optimization
never imports Analytics internals (DEEP gate) and never redefines a metric.

The evaluation produces an advisory, deterministic composite score per candidate. The
composite never replaces the canonical ``CandidateScore``; it layers process/stability
evidence on top of an already-ranked objective score, and an unsafe candidate (a
critical process failure) is capped regardless of objective performance.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_json, to_json_safe

logger = get_logger(__name__)

MULTI_OBJECTIVE_CONTRACT_VERSION: Literal["v1"] = "v1"
MULTI_OBJECTIVE_SCHEMA_ID: Literal["optimization.multi_objective_evaluation.v1"] = (
    "optimization.multi_objective_evaluation.v1"
)

# Canonical non-performance dimensions. Names align with Analytics process-score
# dimension keys; performance is carried separately as the core objective.
CANONICAL_DIMENSIONS: tuple[str, ...] = (
    "preparation",
    "risk",
    "execution",
    "plan_adherence",
    "portfolio_management",
    "emergency",
    "discipline",
    "post_review",
)

_CRITICAL_FAILURE_OVERRIDE = "critical_failure_override"


class _MultiObjectiveEvaluation(BaseModel):
    """Private immutable multi-objective composite evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal["v1"] = MULTI_OBJECTIVE_CONTRACT_VERSION
    schema_id: Literal["optimization.multi_objective_evaluation.v1"] = (
        MULTI_OBJECTIVE_SCHEMA_ID
    )
    candidate_hash: str
    core_objective: str
    core_objective_value: float | None
    dimension_weights: Mapping[str, float]
    dimension_scores: Mapping[str, float]
    composite_score: float
    profit_sole_driver: bool
    overridden_by_critical_failure: bool
    caveats: tuple[str, ...]
    non_binding: Literal[True] = True

    @field_validator("candidate_hash", "core_objective")
    @classmethod
    def _validate_required_text(cls, value: str) -> str:
        """Validate required text is non-empty.

        Args:
            value: Text to validate.

        Returns:
            Validated non-blank text.

        Raises:
            ValueError: If text is blank.
        """
        if not value or value != value.strip():
            raise ValueError("evaluation text fields must be non-empty")
        return value

    @model_validator(mode="after")
    def _validate_evaluation(self) -> _MultiObjectiveEvaluation:
        """Validate weight normalization, finiteness, and the no-raw-profit rule.

        Returns:
            The validated evaluation.

        Raises:
            ValueError: If weights/scores are invalid or raw profit is the sole
                objective driver.
            TypeError: If a dimension value is not a finite number.
        """
        weights = self.dimension_weights
        scores = self.dimension_scores
        if not weights or not scores:
            raise ValueError("dimension weights and scores must be non-empty")
        if set(weights) != set(scores):
            raise ValueError("dimension weights and scores must cover the same keys")
        total_weight = sum(weights.values())
        if not math.isfinite(total_weight) or total_weight <= 0:
            raise ValueError("dimension weights must sum to a positive finite value")
        for value in (*weights.values(), *scores.values()):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError("dimension values must be finite numbers")
            if not math.isfinite(float(value)):
                raise ValueError("dimension values must be finite")
        if not math.isfinite(self.composite_score):
            raise ValueError("composite score must be finite")
        if self.profit_sole_driver:
            raise ValueError("raw profit may not be the sole objective driver")
        return self


def evaluate_multi_objective_candidate(
    *,
    candidate_hash: str,
    core_objective: str,
    core_objective_value: float | None,
    dimension_weights: Mapping[str, float],
    process_score_mapping: Mapping[str, object],
) -> dict[str, Any]:
    """Evaluate one candidate under a multi-objective composite.

    The composite combines the enabled core objective with a weighted average of the
    Analytics process-score dimensions. A critical safety/integrity/replay failure
    overrides the composite to zero (capped) regardless of objective performance, so a
    profitable but unsafe candidate cannot outrank a disciplined one. The result is
    advisory and never confers promotion authority.

    Args:
        candidate_hash: Candidate provenance hash.
        core_objective: Enabled core objective name (e.g. ``sharpe_ratio``).
        core_objective_value: Normalized core objective value in ``[0, 1]``, or
            ``None`` when unavailable (treated as ``0.0`` with a caveat).
        dimension_weights: Positive weights over the process-score dimensions, summing
            to one. Names must match the Analytics canonical dimensions.
        process_score_mapping: Validated ``analytics.process_score.v1`` mapping
            produced by Analytics. Carries dimension scores and critical failures.

    Returns:
        Deterministic JSON-safe ``optimization.multi_objective_evaluation.v1``
        mapping.

    Raises:
        ValueError: If weights/scores are invalid or the contract mapping is
            incompatible.
        TypeError: If the serialized payload is not a JSON-safe mapping.
    """
    logger.info("Evaluating multi-objective candidate | objective=%s", core_objective)
    dimension_scores = _extract_dimension_scores(process_score_mapping)
    # Align weights to only the dimensions present in the process score so the
    # evaluation uses applicable evidence; a caller may weight a subset.
    aligned_weights = {
        key: value
        for key, value in dimension_weights.items()
        if key in dimension_scores
    }
    if not aligned_weights:
        raise ValueError("no supplied dimension weights match the process score")
    critical_failures = _has_critical_failure(process_score_mapping)
    core_value = _normalize_core_value(core_objective_value)
    composite = _composite_score(
        core_value=core_value,
        dimension_weights=aligned_weights,
        dimension_scores=dimension_scores,
    )
    caveats: list[str] = []
    if core_objective_value is None:
        caveats.append("core_objective_unavailable")
    if critical_failures:
        composite = 0.0
        caveats.append(_CRITICAL_FAILURE_OVERRIDE)
    if core_value <= 0 and not critical_failures:
        caveats.append("performance_floor_applied")
    aligned_scores = {key: dimension_scores[key] for key in aligned_weights}
    evaluation = _MultiObjectiveEvaluation(
        candidate_hash=candidate_hash,
        core_objective=core_objective,
        core_objective_value=core_objective_value,
        dimension_weights=aligned_weights,
        dimension_scores=aligned_scores,
        composite_score=composite,
        profit_sole_driver=False,
        overridden_by_critical_failure=critical_failures,
        caveats=tuple(caveats),
    )
    safe = to_json_safe(evaluation.model_dump(mode="json"))
    if not isinstance(safe, dict):
        raise TypeError("multi-objective evaluation serialization is unsafe")
    return dict(safe)


def build_multi_objective_mapping(
    *,
    candidate_hash: str,
    core_objective: str,
    core_objective_value: float | None,
    dimension_weights: Mapping[str, float],
    process_score_mapping: Mapping[str, object],
) -> dict[str, Any]:
    """Build a validated JSON-safe multi-objective evaluation mapping.

    Alias of :func:`evaluate_multi_objective_candidate` expressing the build/parse
    contract pair explicitly.

    Args:
        candidate_hash: Candidate provenance hash.
        core_objective: Enabled core objective name.
        core_objective_value: Normalized core objective value in ``[0, 1]``.
        dimension_weights: Positive weights summing to one.
        process_score_mapping: Validated ``analytics.process_score.v1`` mapping.

    Returns:
        Deterministic JSON-safe ``optimization.multi_objective_evaluation.v1``
        mapping.
    """
    return evaluate_multi_objective_candidate(
        candidate_hash=candidate_hash,
        core_objective=core_objective,
        core_objective_value=core_objective_value,
        dimension_weights=dimension_weights,
        process_score_mapping=process_score_mapping,
    )


def parse_multi_objective_mapping(mapping: Mapping[str, object]) -> dict[str, Any]:
    """Validate a strict multi-objective evaluation mapping and return it JSON-safe.

    Args:
        mapping: Contract mapping to validate.

    Returns:
        Deterministic JSON-safe mapping.

    Raises:
        ValueError: If the mapping is incompatible or non-canonical.
        TypeError: If the serialized payload is not a JSON-safe mapping.
    """
    logger.info("Validating multi-objective evaluation mapping")
    data = dict(mapping)
    if data.get("contract_version") != MULTI_OBJECTIVE_CONTRACT_VERSION:
        raise ValueError("multi-objective contract version is unsupported")
    if data.get("schema_id") != MULTI_OBJECTIVE_SCHEMA_ID:
        raise ValueError("multi-objective schema id is unsupported")
    model = _MultiObjectiveEvaluation.model_validate(data)
    safe = to_json_safe(model.model_dump(mode="json"))
    if not isinstance(safe, dict):
        raise TypeError("multi-objective evaluation serialization is unsafe")
    canonical_json(safe)
    return dict(safe)


def _extract_dimension_scores(
    process_score_mapping: Mapping[str, object],
) -> dict[str, float]:
    """Extract canonical dimension scores from a process-score mapping.

    Args:
        process_score_mapping: ``analytics.process_score.v1`` mapping.

    Returns:
        Mapping of canonical dimension to score.

    Raises:
        ValueError: If the mapping is incompatible or scores are missing.
        TypeError: If a dimension score is not a finite number.
    """
    raw = process_score_mapping.get("dimension_scores")
    if not isinstance(raw, Mapping) or not raw:
        raise ValueError("process_score_mapping must carry non-empty dimension_scores")
    scores: dict[str, float] = {}
    for dimension in CANONICAL_DIMENSIONS:
        value = raw.get(dimension)
        if value is None:
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            message = f"dimension score {dimension} must be a finite number"
            raise TypeError(message)
        if not math.isfinite(float(value)):
            finite_message = f"dimension score {dimension} must be finite"
            raise ValueError(finite_message)
        scores[dimension] = float(value)
    if not scores:
        raise ValueError("no canonical dimension scores present in process score")
    return scores


def _has_critical_failure(process_score_mapping: Mapping[str, object]) -> bool:
    """Return whether a process-score mapping records any critical failure.

    Args:
        process_score_mapping: ``analytics.process_score.v1`` mapping.

    Returns:
        ``True`` when at least one critical failure is recorded.
    """
    failures = process_score_mapping.get("critical_failures")
    if isinstance(failures, Sequence) and not isinstance(failures, (str, bytes)):
        return len(failures) > 0
    return False


def _normalize_core_value(value: float | None) -> float:
    """Clamp a core objective value to the ``[0, 1]`` composite range.

    Args:
        value: Raw normalized value.

    Returns:
        Clamped value in ``[0, 1]``.
    """
    if value is None:
        return 0.0
    clamped = max(0.0, min(1.0, float(value)))
    return clamped


def _composite_score(
    *,
    core_value: float,
    dimension_weights: Mapping[str, float],
    dimension_scores: Mapping[str, float],
) -> float:
    """Compute the weighted composite of core objective and process dimensions.

    Args:
        core_value: Normalized core objective value.
        dimension_weights: Positive weights over present dimensions.
        dimension_scores: Present dimension scores.

    Returns:
        Finite composite score in ``[0, 1]``.

    Raises:
        ValueError: If applicable dimension weights are not positive and finite.
    """
    total = 0.0
    weight_sum = 0.0
    for dimension, weight in dimension_weights.items():
        if dimension not in dimension_scores:
            continue
        total += float(weight) * dimension_scores[dimension]
        weight_sum += float(weight)
    if weight_sum <= 0 or not math.isfinite(weight_sum):
        raise ValueError("applicable dimension weights must be positive and finite")
    weighted_process = total / weight_sum
    # The core objective and process dimensions contribute equally so neither raw
    # performance nor process alone can dominate.
    composite = (core_value + weighted_process) / 2.0
    return max(0.0, min(1.0, composite))


def get_multi_objective_contract_version() -> str:
    """Return the multi-objective evaluation contract version.

    Returns:
        The canonical ``v1`` version string.
    """
    return MULTI_OBJECTIVE_CONTRACT_VERSION


def get_multi_objective_schema_id() -> str:
    """Return the multi-objective evaluation schema identifier.

    Returns:
        The canonical ``optimization.multi_objective_evaluation.v1`` schema string.
    """
    return MULTI_OBJECTIVE_SCHEMA_ID


__all__ = [
    "CANONICAL_DIMENSIONS",
    "MULTI_OBJECTIVE_CONTRACT_VERSION",
    "MULTI_OBJECTIVE_SCHEMA_ID",
    "build_multi_objective_mapping",
    "evaluate_multi_objective_candidate",
    "get_multi_objective_contract_version",
    "get_multi_objective_schema_id",
    "parse_multi_objective_mapping",
]
