"""Executable Research contracts usage example.

Demonstrates Research contract dataclasses, configurations, results,
scorecards, reports, artifact references, and public API classifications.
"""

import sys
from datetime import UTC, datetime, time
from pathlib import Path

import pandas as pd

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research import (
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

_HASH = "e" * 64


def _quality() -> DataQualityReport:
    """Build a minimal valid Research data-quality report."""
    return DataQualityReport((), (), ("schema",), ())


def fr_res_001() -> None:
    """FR-RES-001.

    The system shall define bounded row, duration, artifact-size, and
    advisory memory budgets without claiming unverified production
    performance.
    """
    limits = ResearchResourceLimits(500_000, 600.0, 52_428_800)
    print(f"FR-RES-001 max_rows={limits.max_rows}")


def fr_res_002() -> None:
    """FR-RES-002.

    The system shall require explicit timestamp, duplicate, missing-bar,
    non-trading-period, and spread-cleaning policies and shall never silently
    fill or drop data.
    """
    cleaning = CleaningConfig("UTC", "error", "none", "keep_warn", "error")
    print(f"FR-RES-002 timezone={cleaning.timezone}")


def fr_res_003() -> None:
    """FR-RES-003.

    The system shall define explicit pip, geometry, return-label, and
    calendar enrichment selections; canonical session tagging remains owned
    by seasonality/.
    """
    enrichment = EnrichmentConfig("EURUSD", True, True, False, True)
    print(f"FR-RES-003 symbol={enrichment.symbol}")


def fr_res_004() -> None:
    """FR-RES-004.

    The system shall define feature windows, declared forward columns,
    warm-up/NaN policy, and non-mutation behavior.
    """
    features = FeatureConfig(
        {"sma": 20}, (1, 5), ("forward_1", "forward_5"), "preserve"
    )
    print(f"FR-RES-004 windows={dict(features.windows)}")


def fr_res_005() -> None:
    """FR-RES-005.

    The system shall define bootstrap, permutation, null, correction,
    effective-seed, and bounded-iteration settings in one statistical
    contract.
    """
    statistics = StatisticalConfig(7, 20, 20, 2, 20, "benjamini_hochberg")
    print(f"FR-RES-005 seed={statistics.seed}")


def fr_res_006() -> None:
    """FR-RES-006.

    The system shall define mean-reversion, trend-persistence,
    session-study, confirmation, and explicit isolated-failure policy.
    """
    studies = StudyConfig({}, {}, {})
    print(f"FR-RES-006 continue_on_study_error={studies.continue_on_study_error}")


def fr_res_007() -> None:
    """FR-RES-007.

    The system shall define one timezone-aware set of named windows and
    deterministic overlap precedence for all session consumers.
    """
    sessions = SessionConfig("UTC", {"london": (time(8), time(17))}, ("london",))
    print(f"FR-RES-007 timezone={sessions.timezone}")


def fr_res_008() -> None:
    """FR-RES-008.

    The system shall define bounded structure detection, canonical scoring,
    quality, validation, and calibration settings.
    """
    structure = MarketStructureConfig({}, False, (20,), 5, 20)
    print(f"FR-RES-008 quality_windows={structure.quality_windows}")


def fr_res_009() -> None:
    """FR-RES-009.

    The system shall define feature columns, PCA components, cluster count,
    minimum samples, and seed for deterministic unsupervised research.
    """
    modeling = UnsupervisedResearchConfig(
        ("close", "high", "low", "volume"), True, 3, 5, 50, 7
    )
    print(f"FR-RES-009 pca_components={modeling.pca_components}")


def fr_res_010() -> None:
    """FR-RES-010.

    The system shall define allowed root, format, overwrite, encoding, and
    atomic-replacement policy for safe artifact persistence.
    """
    artifacts = ArtifactWriteConfig(Path("research").resolve(), "json")
    print(f"FR-RES-010 format={artifacts.format}")


def fr_res_011() -> None:
    """FR-RES-011.

    The system shall require complete explicit configuration for every
    selected stage, reject absent or incompatible dependencies, and never
    apply defaults for selected stages.
    """
    config = EdgeLabConfig(
        cleaning=CleaningConfig("UTC", "error", "none", "keep_warn", "error"),
        enrichment=EnrichmentConfig("EURUSD", True, True, False, True),
        features=FeatureConfig(
            {"sma": 20}, (1, 5), ("forward_1", "forward_5"), "preserve"
        ),
        statistics=StatisticalConfig(7, 20, 20, 2, 20, "benjamini_hochberg"),
        studies=StudyConfig({}, {}, {}),
        sessions=SessionConfig("UTC", {"london": (time(8), time(17))}, ("london",)),
        market_structure=MarketStructureConfig({}, False, (20,), 5, 20),
        modeling=UnsupervisedResearchConfig(
            ("close", "high", "low", "volume"), True, 3, 5, 50, 7
        ),
        artifacts=ArtifactWriteConfig(Path("research").resolve(), "json"),
        limits=ResearchResourceLimits(500_000, 600.0, 52_428_800),
        selected_stages=("data",),
    )
    print(f"FR-RES-011 selected_stages={len(config.selected_stages)}")


def fr_res_012() -> None:
    """FR-RES-012.

    The system shall carry prepared records, canonical schema metadata,
    quality evidence, dataset/config hashes, and provenance without provider
    objects.
    """
    index = pd.date_range("2026-01-05", periods=2, freq="min", tz="UTC")
    frame = pd.DataFrame(
        {
            "open": [10.0, 10.1],
            "high": [11.0, 11.1],
            "low": [9.0, 9.1],
            "close": [10.5, 10.6],
            "volume": [100.0, 101.0],
            "spread": [0.1, 0.1],
        },
        index=index,
    )
    prepared = PreparedDataset(frame, "v1", _quality(), _HASH, _HASH, ("fixture",))
    print(f"FR-RES-012 rows={len(prepared.data)}")


def fr_res_013() -> None:
    """FR-RES-013.

    The system shall distinguish fatal issues, warnings, checks, and
    explicit cleaning actions with machine-readable codes.
    """
    quality = DataQualityReport((), (), ("schema",), ())
    print(f"FR-RES-013 checks={len(quality.checks)}")


def fr_res_014() -> None:
    """FR-RES-014.

    The system shall identify suspected lookahead columns, severity,
    evidence, recommendation, allowed forward columns, target, and source
    metadata.
    """
    leakage = LeakageReport(
        (), "none", {"checked": 1}, "No suspected lookahead", (), None, ("fixture",)
    )
    print(f"FR-RES-014 severity={leakage.severity}")


def fr_res_015() -> None:
    """FR-RES-015.

    The system shall represent deterministic chronological
    train/validation/test partitions and boundary identities.
    """
    train = pd.DataFrame(
        {"close": [10.0, 10.1]},
        index=pd.date_range("2026-01-05 08:00", periods=2, freq="min", tz="UTC"),
    )
    validation = pd.DataFrame(
        {"close": [10.2, 10.3]},
        index=pd.date_range("2026-01-05 09:00", periods=2, freq="min", tz="UTC"),
    )
    test = pd.DataFrame(
        {"close": [10.4, 10.5]},
        index=pd.date_range("2026-01-05 10:00", periods=2, freq="min", tz="UTC"),
    )
    boundaries = {
        "validation_start": datetime(2026, 1, 5, 9, tzinfo=UTC),
        "test_start": datetime(2026, 1, 5, 10, tzinfo=UTC),
    }
    split = TimeSplitResult(train, validation, test, boundaries, _HASH)
    print(f"FR-RES-015 train_rows={len(split.train)}")


def fr_res_016() -> None:
    """FR-RES-016.

    The system shall represent seven-family metric values with units, sample
    size, undefined-value reason, warnings, and reproducibility metadata.
    """
    metrics = {
        family: {"unit": "ratio", "sample_size": 1}
        for family in (
            "returns",
            "roc",
            "candles",
            "ranges",
            "volatility",
            "spread",
            "activity",
        )
    }
    profile = CoreMetricProfile("v1", metrics, _quality(), _HASH, _HASH, ())
    print(f"FR-RES-016 schema_version={profile.schema_version}")


def fr_res_017() -> None:
    """FR-RES-017.

    The system shall represent one advisory edge study with sample,
    rule/config, split identity, null evidence, uncertainty, confirmation,
    seed, warnings, and provenance.
    """
    edge = EdgeResult(
        "v1", "mean_reversion", {"mean": 0.5}, {}, "confirmed", 7, (), True
    )
    print(f"FR-RES-017 classification={edge.classification}")


def fr_res_018() -> None:
    """FR-RES-018.

    The system shall represent detected structure, regime, scoring, quality,
    and advisory fit.
    """
    profile = MarketStructureProfile("v1", {}, 50.0, "mixed", {}, ())
    print(f"FR-RES-018 verdict={profile.verdict}")


def fr_res_019() -> None:
    """FR-RES-019.

    The system shall represent stability windows, robustness,
    forward-validation outcome, and consolidated calibration evidence.
    """
    quality = MarketStructureQualityReport("v1", {}, {}, {}, 1.0, ())
    print(f"FR-RES-019 schema_version={quality.schema_version}")


def fr_res_020() -> None:
    """FR-RES-020.

    The system shall represent preprocessing, features, dropped columns,
    scaler, PCA, clusters, factor/cluster evidence, seed, parameters,
    diagnostics, and advisory status.
    """
    result = UnsupervisedResearchResult("v1", {}, {}, {}, {}, 7, (), True)
    print(f"FR-RES-020 seed={result.seed}")


def fr_res_021() -> None:
    """FR-RES-021.

    The system shall represent deterministic score rows, uncertainty, final
    score, readiness reasons, versions, and advisory status.
    """
    scorecard = ResearchScorecard(
        "v1",
        ({"criterion": "quality", "score": 20},),
        20.0,
        "INSUFFICIENT_EVIDENCE",
        ("More evidence required",),
        (),
        True,
    )
    print(f"FR-RES-021 readiness={scorecard.readiness}")


def fr_res_022() -> None:
    """FR-RES-022.

    The system shall normalize approved stage outputs into one versioned
    snapshot with hashes, versions, warnings, and advisory status.
    """
    scorecard = ResearchScorecard(
        "v1",
        (),
        0.0,
        "INSUFFICIENT_EVIDENCE",
        ("No approved stage evidence yet",),
        (),
        True,
    )
    snapshot = ResearchProfileSnapshot(
        "v1",
        {"data": {"schema_version": "v1"}},
        scorecard,
        _HASH,
        _HASH,
        datetime.now(UTC),
        (),
        True,
    )
    print(f"FR-RES-022 schema_version={snapshot.schema_version}")


def fr_res_023() -> None:
    """FR-RES-023.

    The system shall expose bounded structured warnings with code, message,
    severity, optional field path, and bounded details.
    """
    warning = ResearchWarning(
        "MISSING_DATA", "Some bars missing", "warning", "close", {"count": 1}
    )
    print(f"FR-RES-023 code={warning.code}")


def fr_res_024() -> None:
    """FR-RES-024.

    The system shall produce the fully defined ResearchReport v1 contract
    with advisory_only=True and complete reproducibility metadata.
    """
    report = ResearchReport(
        contract_version="v1",
        schema_id="research.report.v1",
        report_id="research-report-test",
        hypothesis="Test hypothesis",
        evidence={"data": {"rows": 1}},
        seeds={"statistics": 7},
        configuration_hash=_HASH,
        dataset_hash=_HASH,
        source_references=("fixture",),
        warnings=(),
        generated_at=datetime.now(UTC),
        dependency_versions={"research": "v1"},
        duration_ms=1.0,
        advisory_only=True,
    )
    print(f"FR-RES-024 report_id={report.report_id}")


def fr_res_025() -> None:
    """FR-RES-025.

    The system shall return a safe artifact reference containing relative
    location, format, byte size, content hash, atomicity, schema version,
    and audit identity.
    """
    reference = ArtifactReference(
        Path("report.json"), "json", 100, _HASH, True, "v1", "audit-001"
    )
    print(f"FR-RES-025 format={reference.format}")


def fr_res_026() -> None:
    """FR-RES-026.

    The system shall expose a unique immutable mapping for every __all__
    name with stable classification and lazy import target, without
    recursive scanning or callable wrapping.
    """
    stable = all(value == "stable" for value in PUBLIC_API_CLASSIFICATIONS.values())
    print(
        f"FR-RES-026 classified_names={len(PUBLIC_API_CLASSIFICATIONS)} "
        f"all_stable={stable}"
    )


def main() -> None:
    """Run every Research contract requirement demonstration in order."""
    print("=" * 80)
    print("Research Example 1: Contracts and Results")
    print("=" * 80)
    fr_res_001()
    fr_res_002()
    fr_res_003()
    fr_res_004()
    fr_res_005()
    fr_res_006()
    fr_res_007()
    fr_res_008()
    fr_res_009()
    fr_res_010()
    fr_res_011()
    fr_res_012()
    fr_res_013()
    fr_res_014()
    fr_res_015()
    fr_res_016()
    fr_res_017()
    fr_res_018()
    fr_res_019()
    fr_res_020()
    fr_res_021()
    fr_res_022()
    fr_res_023()
    fr_res_024()
    fr_res_025()
    fr_res_026()


if __name__ == "__main__":
    main()
