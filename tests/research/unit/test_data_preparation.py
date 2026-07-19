"""Unit tests for deterministic Research dataset preparation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd
from app.services.data.contracts import (
    DataQualityReport as SourceQualityReport,
)
from app.services.data.contracts import (
    MarketDataset,
    OHLCVRecord,
)
from app.services.research.contracts import (
    CleaningConfig,
    DataQualityReport,
    EnrichmentConfig,
    ResearchResourceLimits,
)
from app.services.research.data import (
    clean_dataset,
    enrich_dataset,
    prepare_research_dataset,
)
from app.utils import logger

_REQUEST_ID = "req-1123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def _dataset() -> MarketDataset:
    """Build a deterministic canonical dataset.

    Returns:
        Valid Data-owned dataset.
    """
    logger.debug("Building Research preparation test dataset")
    start = datetime(2026, 1, 5, tzinfo=UTC)
    records = tuple(
        OHLCVRecord(
            timestamp=start + timedelta(minutes=index),
            open=Decimal(str(10 + index / 10)),
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


def _limits() -> ResearchResourceLimits:
    """Build test limits.

    Returns:
        Valid limits.
    """
    logger.debug("Building Research preparation test limits")
    return ResearchResourceLimits(100, 10.0, 1024)


def test_clean_dataset_never_fills_implicitly() -> None:
    """Verify explicit no-fill cleaning preserves the row count."""
    logger.debug("Testing no implicit Research filling")
    frame, report = clean_dataset(
        _dataset(),
        config=CleaningConfig("UTC", "error", "none", "keep_warn", "error"),
        report=DataQualityReport((), (), ("schema",), ()),
        limits=_limits(),
    )
    assert len(frame) == 5
    assert not report.cleaning_actions


def test_enrich_dataset_labels_forward_columns() -> None:
    """Verify forward labels are explicit research-only columns."""
    logger.debug("Testing Research forward-label metadata")
    index = pd.date_range("2026-01-05", periods=3, freq="min", tz="UTC")
    frame = pd.DataFrame(
        {
            "open": [1.0, 2.0, 3.0],
            "high": [2.0, 3.0, 4.0],
            "low": [0.5, 1.5, 2.5],
            "close": [1.5, 2.5, 3.5],
            "volume": [1.0] * 3,
            "spread": [0.1] * 3,
        },
        index=index,
    )
    enriched, _ = enrich_dataset(
        frame,
        config=EnrichmentConfig("TEST", False, True, True, False),
        report=DataQualityReport((), (), (), ()),
    )
    assert enriched.attrs["research_only_columns"] == ("forward_return_1",)
    assert pd.isna(enriched["forward_return_1"].iloc[-1])


def test_prepare_dataset_is_deterministic_and_provider_free() -> None:
    """Verify repeated preparation produces equal hashes and detached frames."""
    logger.debug("Testing deterministic Research preparation")
    cleaning = CleaningConfig("UTC", "error", "none", "keep_warn", "error")
    enrichment = EnrichmentConfig("TEST", True, True, False, True)
    first = prepare_research_dataset(
        _dataset(), cleaning=cleaning, enrichment=enrichment, limits=_limits()
    )
    second = prepare_research_dataset(
        _dataset(), cleaning=cleaning, enrichment=enrichment, limits=_limits()
    )
    assert first.dataset_hash == second.dataset_hash
    assert first.configuration_hash == second.configuration_hash
    assert first.data.equals(second.data)
