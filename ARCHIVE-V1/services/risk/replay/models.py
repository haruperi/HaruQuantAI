"""Replay contracts for simulator-backed risk playback."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.risk.core.timeline_reconstructor import TimelinePoint
    from app.services.risk.domain import PortfolioState
    from app.services.risk.metrics import RiskSnapshot
    from app.services.risk.optimization import RecommendationBatch
    from app.services.risk.scoring import RiskScorecard

    from .cockpit_state import CockpitStatePayload
    from .hypothetical_orders import HypotheticalOrderAction


@dataclass(frozen=True)
class ReplayFrame:
    """One replay frame with normalized risk outputs."""

    frame_index: int
    timestamp: Any
    capture_timestamp: Any
    state: PortfolioState
    snapshot: RiskSnapshot
    scorecard: RiskScorecard
    recommendations: RecommendationBatch | None = None
    cockpit_state: CockpitStatePayload | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReplayRun:
    """Whole replay output for one simulator-backed run."""

    timeline: list[TimelinePoint]
    frames: list[ReplayFrame]
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WhatIfComparison:
    """Before/after comparison for one replay-frame hypothetical action set."""

    baseline_frame: ReplayFrame
    actions: list[HypotheticalOrderAction]
    projected_state: PortfolioState
    projected_snapshot: RiskSnapshot
    projected_scorecard: RiskScorecard
    projected_recommendations: RecommendationBatch | None = None
    summary: dict[str, Any] = field(default_factory=dict)
