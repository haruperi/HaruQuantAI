"""Runnable usage examples for Research dataset preparation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data.contracts import DataQualityReport as SourceQualityReport
from app.services.data.contracts import MarketDataset, OHLCVRecord
from app.services.research.contracts import (
    CleaningConfig,
    EnrichmentConfig,
    ResearchResourceLimits,
)
from app.services.research.data import (
    clean_dataset,
    enrich_dataset,
    prepare_research_dataset,
    validate_dataset,
)
from app.utils import logger

_REQUEST_ID = "req-2123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def _dataset() -> MarketDataset:
    """Build the usage dataset.

    Returns:
        Valid canonical dataset.
    """
    logger.debug("Building Research data usage dataset")
    start = datetime(2026, 1, 5, tzinfo=UTC)
    records = tuple(
        OHLCVRecord(
            timestamp=start + timedelta(minutes=index),
            open=Decimal(10),
            high=Decimal(11),
            low=Decimal(9),
            close=Decimal(str(10 + index / 10)),
            volume=Decimal(100),
            spread=Decimal("0.1"),
            price_unit="USD",
            volume_unit="units",
            spread_unit="price",
            source="fixture",
            source_symbol="TEST",
            available_at=start + timedelta(minutes=index, seconds=1),
        )
        for index in range(5)
    )
    quality = SourceQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=5,
        checked_count=5,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="TEST",
        timeframe="1m",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=5,
        quality_report=quality,
        source_metadata={"provider": "fixture"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=_REQUEST_ID,
    )


def _inputs() -> tuple[CleaningConfig, EnrichmentConfig, ResearchResourceLimits]:
    """Build usage configuration inputs.

    Returns:
        Cleaning, enrichment, and resource settings.
    """
    logger.debug("Building Research data usage inputs")
    return (
        CleaningConfig("UTC", "error", "none", "keep_warn", "error"),
        EnrichmentConfig("TEST", True, True, False, True),
        ResearchResourceLimits(100, 10.0, 1024),
    )


def test_usage_validation_validate_dataset() -> None:
    """Validate canonical dataset quality."""
    logger.debug("Running Research validation usage")
    _, _, limits = _inputs()
    assert not validate_dataset(_dataset(), limits=limits).fatal_issues


def test_usage_preparation_clean_dataset() -> None:
    """Clean one canonical dataset explicitly."""
    logger.debug("Running Research cleaning usage")
    cleaning, _, limits = _inputs()
    report = validate_dataset(_dataset(), limits=limits)
    frame, _ = clean_dataset(_dataset(), config=cleaning, report=report, limits=limits)
    assert len(frame) == 5


def test_usage_preparation_enrich_dataset() -> None:
    """Enrich one detached dataset explicitly."""
    logger.debug("Running Research enrichment usage")
    cleaning, enrichment, limits = _inputs()
    report = validate_dataset(_dataset(), limits=limits)
    frame, report = clean_dataset(
        _dataset(), config=cleaning, report=report, limits=limits
    )
    enriched, _ = enrich_dataset(frame, config=enrichment, report=report)
    assert "log_return" in enriched


def test_usage_preparation_prepare_research_dataset() -> None:
    """Prepare one complete Research dataset."""
    logger.debug("Running complete Research preparation usage")
    cleaning, enrichment, limits = _inputs()
    prepared = prepare_research_dataset(
        _dataset(), cleaning=cleaning, enrichment=enrichment, limits=limits
    )
    assert prepared.schema_version == "v1"
