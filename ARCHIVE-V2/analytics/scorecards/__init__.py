"""Strategy quality scorecards package for Analytics.

Exposes evaluation rules, quality score calculators, and policy boundaries.
"""

from __future__ import annotations

from app.services.analytics.scorecards.labels import scorecards_policy_boundary
from app.services.analytics.scorecards.quality import (
    NonBindingRecommendation,
    ScorecardResult,
    ScorecardRule,
    StrategyQualityAssessment,
    StrategyQualityConfig,
    evaluate_strategy_quality,
    sample_size_warning,
    sqn,
)

__all__ = [
    "NonBindingRecommendation",
    "ScorecardResult",
    "ScorecardRule",
    "StrategyQualityAssessment",
    "StrategyQualityConfig",
    "evaluate_strategy_quality",
    "sample_size_warning",
    "scorecards_policy_boundary",
    "sqn",
]
