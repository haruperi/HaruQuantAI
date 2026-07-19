"""Unit tests for immutable Research result contracts."""

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest
from app.services.research.contracts import (
    ArtifactReference,
    CoreMetricProfile,
    DataQualityReport,
    EdgeResult,
    LeakageReport,
    MarketStructureProfile,
    MarketStructureQualityReport,
    PreparedDataset,
    ResearchProfileSnapshot,
    ResearchReport,
    ResearchScorecard,
    ResearchWarning,
    TimeSplitResult,
    UnsupervisedResearchResult,
)
from app.utils import logger
from app.utils.errors import SecurityError, ValidationError

_HASH = "a" * 64


def _quality() -> DataQualityReport:
    """Build empty valid quality evidence.

    Returns:
        Valid quality report.
    """
    logger.debug("Building test quality evidence")
    return DataQualityReport((), (), ("schema",), ())


def _scorecard() -> ResearchScorecard:
    """Build a valid advisory scorecard.

    Returns:
        Valid scorecard.
    """
    logger.debug("Building test Research scorecard")
    return ResearchScorecard(
        "v1",
        ({"criterion": "quality", "score": 20},),
        20.0,
        "INSUFFICIENT_EVIDENCE",
        ("more evidence required",),
        (),
        True,
    )


def test_prepared_dataset_rejects_provider_object() -> None:
    """Verify prepared evidence requires a DataFrame."""
    logger.debug("Testing prepared dataset frame validation")
    with pytest.raises(ValidationError):
        PreparedDataset(object(), "v1", _quality(), _HASH, _HASH, ("source",))  # type: ignore[arg-type]


def test_quality_report_distinguishes_fatal_warning() -> None:
    """Verify fatal and warning evidence remain distinct."""
    logger.debug("Testing quality severity separation")
    warning = ResearchWarning("SPARSE", "Sparse sample", "warning")
    report = DataQualityReport(({"code": "BAD_OHLC"},), (warning,), (), ())
    assert report.fatal_issues
    assert report.warnings


def test_leakage_report_requires_evidence() -> None:
    """Verify suspected columns require evidence."""
    logger.debug("Testing leakage evidence requirement")
    with pytest.raises(ValidationError):
        LeakageReport(("forward_5",), "high", {}, "remove", (), None, ())


def test_time_split_rejects_overlap() -> None:
    """Verify chronological partitions cannot overlap."""
    logger.debug("Testing time-split overlap")
    index = pd.date_range("2026-01-01", periods=3, tz="UTC")
    frame = pd.DataFrame({"close": [1.0, 2.0, 3.0]}, index=index)
    with pytest.raises(ValidationError):
        TimeSplitResult(frame, frame, frame, {"start": index[0].to_pydatetime()}, _HASH)


def test_metric_profile_requires_units() -> None:
    """Verify every metric family carries units."""
    logger.debug("Testing metric metadata")
    metrics = {
        name: {"sample_size": 2}
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
    with pytest.raises(ValidationError):
        CoreMetricProfile("v1", metrics, _quality(), _HASH, _HASH, ())


def test_edge_result_is_advisory() -> None:
    """Verify edge results preserve advisory status."""
    logger.debug("Testing advisory edge result")
    result = EdgeResult("v1", "mean_reversion", {}, {}, "inconclusive", 1, (), True)
    assert result.advisory_only is True


def test_market_structure_uses_canonical_score() -> None:
    """Verify market-structure scores are bounded."""
    logger.debug("Testing canonical market-structure score")
    with pytest.raises(ValidationError):
        MarketStructureProfile("v1", {}, 101.0, "trending", {}, ())


def test_quality_report_records_windows() -> None:
    """Verify quality evidence retains window metadata."""
    logger.debug("Testing market quality windows")
    report = MarketStructureQualityReport("v1", {"windows": [20, 40]}, {}, {}, 1.0, ())
    assert report.stability["windows"] == [20, 40]


def test_unsupervised_result_records_seed() -> None:
    """Verify modeling results retain the effective seed."""
    logger.debug("Testing modeling result seed")
    result = UnsupervisedResearchResult("v1", {}, {}, {}, {}, 7, (), True)
    assert result.seed == 7


def test_scorecard_readiness_has_reasons() -> None:
    """Verify readiness always includes reasons."""
    logger.debug("Testing scorecard readiness reasons")
    with pytest.raises(ValidationError):
        ResearchScorecard("v1", (), 0.0, "BLOCKED", (), (), True)


def test_snapshot_rejects_unversioned_stage() -> None:
    """Verify snapshot stages carry structural versions."""
    logger.debug("Testing snapshot stage version")
    with pytest.raises(ValidationError):
        ResearchProfileSnapshot(
            "v1",
            {"metrics": {}},
            _scorecard(),
            _HASH,
            _HASH,
            datetime.now(UTC),
            (),
            True,
        )


def test_warning_details_are_bounded() -> None:
    """Verify warning details enforce the approved bound."""
    logger.debug("Testing warning details bound")
    with pytest.raises(ValidationError):
        ResearchWarning(
            "TOO_MANY", "Too many", "warning", details={str(i): i for i in range(33)}
        )


def test_research_report_v1_contract() -> None:
    """Verify high-severity leakage blocks report publication."""
    logger.debug("Testing ResearchReport leakage gate")
    with pytest.raises(SecurityError):
        ResearchReport(
            "v1",
            "research.report.v1",
            "report-1",
            "hypothesis",
            {"leakage": {"severity": "high"}},
            {},
            _HASH,
            _HASH,
            ("source",),
            (),
            datetime.now(UTC),
            {"python": "3.14"},
            1.0,
            True,
        )


def test_artifact_reference_is_relative() -> None:
    """Verify artifact references cannot expose absolute paths."""
    logger.debug("Testing artifact reference path")
    with pytest.raises(ValidationError):
        ArtifactReference(Path("C:/secret.json"), "json", 1, _HASH, True, "v1", "evt-1")
