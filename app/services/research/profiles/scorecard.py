"""Deterministic advisory Research scorecard assembly."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.research.contracts import (
    ResearchScorecard,
    ResearchWarning,
)
from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from app.services.analytics import PerformanceReport
    from app.services.research.contracts import (
        CoreMetricProfile,
        EdgeResult,
        MarketStructureProfile,
        UnsupervisedResearchResult,
    )

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)

_MAX_SCORE = 100.0
_WEIGHT_METRICS = 20.0
_WEIGHT_SEASONALITY = 15.0
_WEIGHT_EDGES = 25.0
_WEIGHT_STRUCTURE = 20.0
_WEIGHT_MODELING = 20.0
_REVIEW_READY_THRESHOLD = 60.0
_INSUFFICIENT_THRESHOLD = 20.0


def build_research_scorecard(
    *,
    metric_profile: CoreMetricProfile,
    seasonality: Mapping[str, JSONValue] | None,
    edges: Sequence[EdgeResult],
    market_structure: MarketStructureProfile | None,
    modeling: UnsupervisedResearchResult | None,
    performance: PerformanceReport | None = None,
) -> ResearchScorecard:
    """Build a deterministic advisory scorecard from approved evidence.

    Args:
        metric_profile: Seven-family metric evidence.
        seasonality: Optional seasonality evidence.
        edges: Advisory edge-study results.
        market_structure: Optional market-structure profile.
        modeling: Optional unsupervised research result.
        performance: Optional Analytics performance report.

    Returns:
        Advisory ``ResearchScorecard`` with score rows and readiness.

    Raises:
        ValidationError: If prerequisites are absent or incompatible.
    """
    logger.info("Building Research scorecard")
    score_rows: list[Mapping[str, JSONValue]] = []
    reasons: list[str] = []
    warnings: list[ResearchWarning] = []
    score = 0.0

    metric_count = len(metric_profile.metrics)
    metric_score = min(_WEIGHT_METRICS, metric_count / 7 * _WEIGHT_METRICS)
    score += metric_score
    score_rows.append(
        {"criterion": "metrics", "score": metric_score, "families": metric_count}
    )

    if seasonality is not None:
        session_count = len(seasonality.get("sessions", []))  # type: ignore[arg-type]
        seasonal_score = (
            min(_WEIGHT_SEASONALITY, session_count * _WEIGHT_SEASONALITY / 3)
            if session_count
            else 0.0
        )
    else:
        seasonal_score = 0.0
        reasons.append("seasonality_not_supplied")
    score += seasonal_score
    score_rows.append({"criterion": "seasonality", "score": seasonal_score})

    confirmed_edges = sum(1 for e in edges if e.classification == "confirmed")
    edge_score = min(_WEIGHT_EDGES, confirmed_edges * _WEIGHT_EDGES)
    score += edge_score
    score_rows.append(
        {"criterion": "edges", "score": edge_score, "confirmed": confirmed_edges}
    )

    if market_structure is not None:
        structure_score = market_structure.score / _MAX_SCORE * _WEIGHT_STRUCTURE
    else:
        structure_score = 0.0
        reasons.append("market_structure_not_supplied")
    score += structure_score
    score_rows.append({"criterion": "market_structure", "score": structure_score})

    if modeling is not None:
        modeling_score = _WEIGHT_MODELING
    else:
        modeling_score = 0.0
        reasons.append("modeling_not_supplied")
    score += modeling_score
    score_rows.append({"criterion": "modeling", "score": modeling_score})

    final_score = min(_MAX_SCORE, score)
    if performance is not None:
        reasons.append("performance_evidence_attached")
    if final_score >= _REVIEW_READY_THRESHOLD:
        readiness = "REVIEW_READY"
    elif final_score >= _INSUFFICIENT_THRESHOLD:
        readiness = "INSUFFICIENT_EVIDENCE"
        reasons.append("score_below_review_threshold")
    else:
        readiness = "BLOCKED"
        reasons.append("insufficient_advisory_evidence")
    if not reasons:
        reasons.append("all_available_evidence_assembled")
    return ResearchScorecard(
        "v1",
        tuple(score_rows),
        final_score,
        readiness,
        tuple(reasons),
        tuple(warnings),
        True,
    )


__all__ = ("build_research_scorecard",)
