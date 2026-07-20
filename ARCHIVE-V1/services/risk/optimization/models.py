"""Normalized recommendation models for the risk optimization layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.risk.core import GovernanceReport
    from app.services.risk.metrics import RiskSnapshot
    from app.services.risk.scoring import RiskScorecard


@dataclass(frozen=True)
class RecommendationAction:
    """One hypothetical portfolio action."""

    action_type: str
    symbol: str
    delta_lots: float
    current_lots: float
    projected_lots: float
    rationale: str = ""
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecommendationScore:
    """Explainable scoring components for one recommendation."""

    usefulness_score: float
    score_delta: float = 0.0
    var_delta: float = 0.0
    es_delta: float = 0.0
    worst_scenario_loss_delta: float = 0.0
    margin_used_delta: float = 0.0
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecommendationResult:
    """One ranked recommendation with projected impact."""

    action: RecommendationAction
    recommendation_score: RecommendationScore
    governance_feasible: bool
    explanation: str
    governance_report: GovernanceReport | None = None
    projected_snapshot: RiskSnapshot | None = None
    projected_scorecard: RiskScorecard | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecommendationBatch:
    """Ranked recommendation set for one current snapshot."""

    snapshot: RiskSnapshot
    scorecard: RiskScorecard
    recommendations: list[RecommendationResult]
    summary: dict[str, Any] = field(default_factory=dict)
