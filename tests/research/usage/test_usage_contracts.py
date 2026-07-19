"""Runnable usage examples for the public Research contract API."""

from datetime import UTC, datetime, time
from pathlib import Path

import pandas as pd
from app.services.research.contracts import (
    PUBLIC_API_CLASSIFICATIONS,
    ArtifactReference,
    ArtifactWriteConfig,
    CleaningConfig,
    CoreMetricProfile,
    DataQualityReport,
    EdgeLabConfig,
    EdgeResult,
    EnrichmentConfig,
    FeatureConfig,
    LeakageReport,
    MarketStructureConfig,
    MarketStructureProfile,
    MarketStructureQualityReport,
    PreparedDataset,
    ResearchProfileSnapshot,
    ResearchReport,
    ResearchResourceLimits,
    ResearchScorecard,
    ResearchWarning,
    SessionConfig,
    StatisticalConfig,
    StudyConfig,
    TimeSplitResult,
    UnsupervisedResearchConfig,
    UnsupervisedResearchResult,
)
from app.utils import logger

_HASH = "b" * 64


def _quality() -> DataQualityReport:
    """Build valid usage quality evidence.

    Returns:
        Valid quality report.
    """
    logger.debug("Building usage quality report")
    return DataQualityReport((), (), ("schema",), ())


def _frame() -> pd.DataFrame:
    """Build a small UTC-indexed usage frame.

    Returns:
        Detached example frame.
    """
    logger.debug("Building usage Research frame")
    index = pd.date_range("2026-01-01", periods=9, tz="UTC")
    return pd.DataFrame({"close": range(9)}, index=index)


def _scorecard() -> ResearchScorecard:
    """Build a valid usage scorecard.

    Returns:
        Advisory scorecard.
    """
    logger.debug("Building usage scorecard")
    return ResearchScorecard(
        "v1",
        ({"criterion": "quality", "score": 20},),
        20.0,
        "INSUFFICIENT_EVIDENCE",
        ("More evidence required",),
        (),
        True,
    )


def test_usage_configurations_resource_limits() -> None:
    """Construct bounded resource limits."""
    logger.debug("Running resource-limit usage")
    assert ResearchResourceLimits(500_000, 600.0, 52_428_800).max_rows == 500_000


def test_usage_configurations_cleaning() -> None:
    """Construct explicit cleaning policy."""
    logger.debug("Running cleaning-config usage")
    assert (
        CleaningConfig("UTC", "error", "none", "keep_warn", "error").timezone == "UTC"
    )


def test_usage_configurations_enrichment() -> None:
    """Construct explicit enrichment policy."""
    logger.debug("Running enrichment-config usage")
    assert EnrichmentConfig("EURUSD", True, True, False, True).symbol == "EURUSD"


def test_usage_configurations_features() -> None:
    """Construct explicit feature policy."""
    logger.debug("Running feature-config usage")
    assert FeatureConfig({"returns": 20}, (5,), (), "preserve").forward_horizons == (5,)


def test_usage_configurations_statistics() -> None:
    """Construct bounded seeded statistics policy."""
    logger.debug("Running statistics-config usage")
    assert StatisticalConfig(7, 100, 100, 5, 100, None).seed == 7


def test_usage_configurations_studies() -> None:
    """Construct fail-closed study policy."""
    logger.debug("Running study-config usage")
    assert StudyConfig({}, {}, {}).continue_on_study_error is False


def test_usage_configurations_sessions() -> None:
    """Construct canonical session policy."""
    logger.debug("Running session-config usage")
    config = SessionConfig("UTC", {"london": (time(8), time(16))}, ("london",))
    assert config.overlap_precedence == ("london",)


def test_usage_configurations_market_structure() -> None:
    """Construct bounded market-structure policy."""
    logger.debug("Running structure-config usage")
    assert MarketStructureConfig({}, False, (20,), 4, 5).validation_horizon == 5


def test_usage_configurations_modeling() -> None:
    """Construct seeded modeling policy."""
    logger.debug("Running modeling-config usage")
    assert UnsupervisedResearchConfig(("a", "b"), True, 2, 2, 20, 7).clusters == 2


def test_usage_configurations_artifacts(tmp_path: Path) -> None:
    """Construct safe artifact policy.

    Args:
        tmp_path: Pytest temporary directory.
    """
    logger.debug("Running artifact-config usage")
    assert ArtifactWriteConfig(tmp_path.resolve(), "json").encoding == "utf-8"


def test_usage_configurations_edge_lab(tmp_path: Path) -> None:
    """Construct the complete Edge Lab configuration.

    Args:
        tmp_path: Pytest temporary directory.
    """
    logger.debug("Running Edge Lab config usage")
    config = EdgeLabConfig(
        CleaningConfig("UTC", "error", "none", "keep_warn", "error"),
        EnrichmentConfig("EURUSD", True, True, False, True),
        FeatureConfig({"returns": 20}, (), (), "preserve"),
        StatisticalConfig(7, 100, 100, 5, 100, None),
        StudyConfig({}, {}, {}),
        SessionConfig("UTC", {"london": (time(8), time(16))}, ("london",)),
        MarketStructureConfig({}, False, (), 4, 5),
        UnsupervisedResearchConfig(("a", "b"), True, 2, 2, 20, 7),
        ArtifactWriteConfig(tmp_path.resolve(), "json"),
        ResearchResourceLimits(500_000, 600.0, 52_428_800),
        ("metrics", "profiles"),
    )
    assert config.selected_stages[-1] == "profiles"


def test_usage_results_prepared_dataset() -> None:
    """Construct detached prepared evidence."""
    logger.debug("Running PreparedDataset usage")
    assert (
        PreparedDataset(
            _frame(), "v1", _quality(), _HASH, _HASH, ("data",)
        ).schema_version
        == "v1"
    )


def test_usage_results_quality_report() -> None:
    """Construct quality evidence."""
    logger.debug("Running DataQualityReport usage")
    assert not _quality().fatal_issues


def test_usage_results_leakage_report() -> None:
    """Construct leakage evidence."""
    logger.debug("Running LeakageReport usage")
    assert (
        LeakageReport((), "none", {}, "continue", (), None, ("data",)).severity
        == "none"
    )


def test_usage_results_time_split() -> None:
    """Construct chronological split evidence."""
    logger.debug("Running TimeSplitResult usage")
    frame = _frame()
    result = TimeSplitResult(
        frame.iloc[:3],
        frame.iloc[3:6],
        frame.iloc[6:],
        {"train_start": frame.index[0].to_pydatetime()},
        _HASH,
    )
    assert len(result.test) == 3


def test_usage_results_core_metric_profile() -> None:
    """Construct seven-family metric evidence."""
    logger.debug("Running CoreMetricProfile usage")
    metrics = {
        name: {"value": 0.0, "unit": "ratio", "sample_size": 3}
        for name in (
            "returns",
            "roc",
            "candles",
            "ranges",
            "volatility",
            "spread",
            "activity",
        )
    }
    assert (
        len(CoreMetricProfile("v1", metrics, _quality(), _HASH, _HASH, ()).metrics) == 7
    )


def test_usage_results_edge_result() -> None:
    """Construct advisory edge evidence."""
    logger.debug("Running EdgeResult usage")
    assert EdgeResult("v1", "trend", {}, {}, "inconclusive", 7, (), True).advisory_only


def test_usage_results_market_structure() -> None:
    """Construct market-structure evidence."""
    logger.debug("Running MarketStructureProfile usage")
    assert MarketStructureProfile("v1", {}, 50.0, "mixed", {}, ()).verdict == "mixed"


def test_usage_results_market_quality() -> None:
    """Construct market-quality evidence."""
    logger.debug("Running MarketStructureQualityReport usage")
    assert MarketStructureQualityReport("v1", {}, {}, {}, 0.0, ()).duration_ms == 0.0


def test_usage_results_unsupervised() -> None:
    """Construct seeded unsupervised evidence."""
    logger.debug("Running UnsupervisedResearchResult usage")
    assert UnsupervisedResearchResult("v1", {}, {}, {}, {}, 7, (), True).seed == 7


def test_usage_results_scorecard() -> None:
    """Construct evidence-readiness scorecard."""
    logger.debug("Running ResearchScorecard usage")
    assert _scorecard().readiness == "INSUFFICIENT_EVIDENCE"


def test_usage_results_snapshot() -> None:
    """Construct canonical profile snapshot."""
    logger.debug("Running ResearchProfileSnapshot usage")
    snapshot = ResearchProfileSnapshot(
        "v1",
        {"metrics": {"schema_version": "v1"}},
        _scorecard(),
        _HASH,
        _HASH,
        datetime.now(UTC),
        (),
        True,
    )
    assert snapshot.advisory_only


def test_usage_results_warning() -> None:
    """Construct bounded warning evidence."""
    logger.debug("Running ResearchWarning usage")
    assert ResearchWarning("SPARSE", "Sparse sample", "warning").severity == "warning"


def test_usage_results_research_report() -> None:
    """Construct the registered ResearchReport v1 contract."""
    logger.debug("Running ResearchReport usage")
    report = ResearchReport(
        "v1",
        "research.report.v1",
        "report-1",
        "Does evidence persist?",
        {"metrics": {"schema_version": "v1"}},
        {"statistics": 7},
        _HASH,
        _HASH,
        ("data",),
        (),
        datetime.now(UTC),
        {"python": "3.14"},
        1.0,
        True,
    )
    assert report.schema_id == "research.report.v1"


def test_usage_results_artifact_reference() -> None:
    """Construct a safe relative artifact reference."""
    logger.debug("Running ArtifactReference usage")
    reference = ArtifactReference(
        Path("report.json"), "json", 2, _HASH, True, "v1", "evt-1"
    )
    assert not reference.relative_path.is_absolute()


def test_usage_api_classifications() -> None:
    """Inspect immutable public API classifications."""
    logger.debug("Running API classification usage")
    assert PUBLIC_API_CLASSIFICATIONS["ResearchReport"] == "stable"
