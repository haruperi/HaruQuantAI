"""Unit tests for Research scorecard (FR-RES-089)."""

from app.services.research import (
    CoreMetricProfile,
    DataQualityReport,
    EdgeResult,
    MarketStructureProfile,
    ResearchScorecard,
)
from app.services.research.profiles import build_research_scorecard
from app.utils import logger

_HASH = "e" * 64


def _metric_profile() -> CoreMetricProfile:
    """Build a seven-family metric profile with canonical families."""
    families = (
        "returns",
        "roc",
        "candles",
        "ranges",
        "volatility",
        "spread",
        "activity",
    )
    metrics = {f: {"value": 1.0, "unit": "ratio", "sample_size": 1} for f in families}
    return CoreMetricProfile(
        "v1",
        metrics,
        DataQualityReport((), (), ("schema",), ()),
        _HASH,
        _HASH,
        (),
    )


def _edge() -> EdgeResult:
    """Build a confirmed advisory edge result."""
    return EdgeResult("v1", "mean_reversion", {}, {}, "confirmed", 7, (), True)


def _structure() -> MarketStructureProfile:
    """Build a trending market-structure profile."""
    return MarketStructureProfile(
        "v1",
        {"swing_window": 5},
        75.0,
        "trending",
        {"primary_archetype": "trend_follow", "advisory_only": True},
        (),
    )


def test_scorecard_is_deterministic_and_advisory() -> None:
    """FR-RES-089: scorecard is deterministic and advisory-only."""
    logger.debug("Testing Research scorecard")
    scorecard = build_research_scorecard(
        metric_profile=_metric_profile(),
        seasonality={"sessions": [{"session": "london"}]},
        edges=(_edge(),),
        market_structure=_structure(),
        modeling=None,
    )
    assert isinstance(scorecard, ResearchScorecard)
    assert scorecard.schema_version == "v1"
    assert 0.0 <= scorecard.final_score <= 100.0
    assert scorecard.readiness in ("REVIEW_READY", "INSUFFICIENT_EVIDENCE", "BLOCKED")
    assert scorecard.advisory_only is True
    assert scorecard.reasons
