"""Shared deterministic Research test fixtures."""

from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from app.services.data import DataQualityReport, MarketDataset, OHLCVRecord
from app.services.research import (
    ArtifactWriteConfig,
    CleaningConfig,
    EdgeLabConfig,
    EnrichmentConfig,
    FeatureConfig,
    MarketStructureConfig,
    ResearchResourceLimits,
    SessionConfig,
    StatisticalConfig,
    StudyConfig,
    UnsupervisedResearchConfig,
)

_REQUEST_ID = "req-21234567-89ab-4def-8123-456789abcdef"


def make_dataset() -> MarketDataset:
    """Build bounded canonical Research input.

    Returns:
        Five-row Data-owned market dataset.
    """
    start = datetime(2026, 1, 5, tzinfo=UTC)
    records = tuple(
        OHLCVRecord(
            timestamp=start + timedelta(minutes=index),
            source="research-fixture",
            source_symbol="TEST",
            available_at=start + timedelta(minutes=index, seconds=1),
            open=Decimal(10),
            high=Decimal(11),
            low=Decimal(9),
            close=Decimal(str(10 + index / 10)),
            volume=Decimal(100),
            spread=Decimal("0.1"),
            price_unit="USD",
            volume_unit="units",
            spread_unit="price",
        )
        for index in range(5)
    )
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=len(records),
        checked_count=len(records),
        truncated=False,
        sample_limit=len(records),
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="TEST",
        timeframe="M1",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=quality,
        source_metadata={"provider": "research-fixture"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=_REQUEST_ID,
    )


def make_edge_lab_config(
    artifact_root: Path,
    *,
    selected_stages: tuple[str, ...] = ("data",),
) -> EdgeLabConfig:
    """Build complete explicit Edge Lab settings.

    Args:
        artifact_root: Absolute test-only artifact root.
        selected_stages: Exact stages selected for the run.

    Returns:
        Validated Edge Lab configuration.
    """
    return EdgeLabConfig(
        cleaning=CleaningConfig("UTC", "error", "none", "keep_warn", "error"),
        enrichment=EnrichmentConfig("TEST", True, True, False, True),
        features=FeatureConfig({"sma": 2}, (1,), ("forward_return_1",), "preserve"),
        statistics=StatisticalConfig(7, 20, 20, 2, 20, "benjamini_hochberg"),
        studies=StudyConfig({}, {}, {}),
        sessions=SessionConfig(
            "UTC",
            {"all": (time(0), time(23, 59))},
            ("all",),
        ),
        market_structure=MarketStructureConfig({}, False, (2,), 1, 1),
        modeling=UnsupervisedResearchConfig(
            ("close", "volume"),
            True,
            2,
            2,
            20,
            7,
        ),
        artifacts=ArtifactWriteConfig(artifact_root.resolve(), "json"),
        limits=ResearchResourceLimits(100, 10.0, 1024 * 1024),
        selected_stages=selected_stages,
    )
