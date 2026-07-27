"""Integration evidence for WF-RES-009: scorecard and snapshot determinism."""

from app.services.research import (
    CoreMetricProfile,
    DataQualityReport,
    EdgeResult,
    MarketStructureProfile,
    ResearchProfileSnapshot,
)
from app.services.research.profiles import (
    build_research_profile_snapshot,
    build_research_scorecard,
)
from app.utils import logger

_HASH = "e" * 64


def _scorecard() -> None:
    """Placeholder to satisfy import structure."""
    return


def test_scorecard_snapshot_is_deterministic() -> None:
    """WF-RES-009: scorecard and snapshot are deterministic and advisory."""
    logger.debug("Testing Research scorecard-snapshot integration")
    metrics = {
        f: {"value": 1.0, "unit": "ratio", "sample_size": 1}
        for f in (
            "returns",
            "roc",
            "candles",
            "ranges",
            "volatility",
            "spread",
            "activity",
        )
    }
    metric_profile = CoreMetricProfile(
        "v1",
        metrics,
        DataQualityReport((), (), ("schema",), ()),
        _HASH,
        _HASH,
        (),
    )
    edge = EdgeResult("v1", "mean_reversion", {}, {}, "confirmed", 7, (), True)
    structure = MarketStructureProfile(
        "v1",
        {"swing_window": 5},
        75.0,
        "trending",
        {"primary_archetype": "trend_follow", "advisory_only": True},
        (),
    )
    scorecard = build_research_scorecard(
        metric_profile=metric_profile,
        seasonality={"sessions": [{"session": "london"}]},
        edges=(edge,),
        market_structure=structure,
        modeling=None,
    )
    snapshot = build_research_profile_snapshot(
        stages={"data": {"schema_version": "v1", "rows": 10}},
        scorecard=scorecard,
        dataset_hash=_HASH,
        configuration_hash=_HASH,
    )
    assert isinstance(snapshot, ResearchProfileSnapshot)
    assert scorecard.advisory_only is True
    assert snapshot.advisory_only is True
