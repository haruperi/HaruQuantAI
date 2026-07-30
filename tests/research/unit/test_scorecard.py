"""Unit tests for Research scorecard (FR-RES-089)."""

from app.services.research import (
    build_research_scorecard,
    create_research_value,
    is_research_value,
)
from app.utils import get_logger

logger = get_logger(__name__)

_HASH = "e" * 64


def _metric_profile() -> object:
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
    return create_research_value(
        "CoreMetricProfile",
        "v1",
        metrics,
        create_research_value("DataQualityReport", (), (), ("schema",), ()),
        _HASH,
        _HASH,
        (),
    )


def _edge() -> object:
    """Build a confirmed advisory edge result."""
    return create_research_value(
        "EdgeResult", "v1", "mean_reversion", {}, {}, "confirmed", 7, (), True
    )


def _structure() -> object:
    """Build a trending market-structure profile."""
    return create_research_value(
        "MarketStructureProfile",
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
    assert is_research_value(scorecard, "ResearchScorecard")
    assert scorecard.schema_version == "v1"
    assert 0.0 <= scorecard.final_score <= 100.0
    assert scorecard.readiness in ("REVIEW_READY", "INSUFFICIENT_EVIDENCE", "BLOCKED")
    assert scorecard.advisory_only is True
    assert scorecard.reasons


def test_scorecard_covers_optional_evidence_and_readiness_paths() -> None:
    """Cover missing evidence, attached performance, and complete evidence paths."""
    partial = build_research_scorecard(
        metric_profile=_metric_profile(),
        seasonality=None,
        edges=(),
        market_structure=None,
        modeling=None,
        performance=object(),
    )
    assert partial.readiness == "INSUFFICIENT_EVIDENCE"
    assert "performance_evidence_attached" in partial.reasons
    modeling = create_research_value(
        "UnsupervisedResearchResult",
        "v1",
        {"scaled": True},
        {"components": 2},
        {"clusters": 2},
        {"summary": "bounded"},
        7,
        (),
        True,
    )
    complete = build_research_scorecard(
        metric_profile=_metric_profile(),
        seasonality={"sessions": [{}, {}, {}]},
        edges=(_edge(),),
        market_structure=_structure(),
        modeling=modeling,
    )
    assert complete.readiness == "REVIEW_READY"
    assert complete.reasons == ("all_available_evidence_assembled",)
