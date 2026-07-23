"""Executable Research data usage example.

Demonstrates dataset validation, cleaning, enrichment, and preparation.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.contracts import DataQualityReport as SourceQualityReport
from app.services.data.contracts import (
    MarketDataset,
    OHLCVRecord,
)
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

REQUEST_ID = "req-2123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def _dataset() -> MarketDataset:
    """Build the usage dataset."""
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
        request_id=REQUEST_ID,
    )


def example_data() -> None:
    """Demonstrate dataset preparation, cleaning, enrichment, and validation."""
    print("=" * 80)
    print("Research Example 2: Dataset Preparation and Cleaning")
    print("=" * 80)

    dataset = _dataset()
    cleaning_cfg = CleaningConfig("UTC", "error", "none", "keep_warn", "error")
    enrichment_cfg = EnrichmentConfig("TEST", True, True, False, True)
    limits = ResearchResourceLimits(100, 10.0, 1024)

    # 1. Validate dataset
    validation_report = validate_dataset(dataset, limits=limits)
    print(f"Validation report fatal issues: {len(validation_report.fatal_issues)}")

    # 2. Clean dataset
    df_clean, clean_report = clean_dataset(
        dataset,
        config=cleaning_cfg,
        report=validation_report,
        limits=limits,
    )
    print(
        f"Cleaned DataFrame rows: {len(df_clean)}, clean report fatal issues: {len(clean_report.fatal_issues)}"
    )

    # 3. Enrich dataset
    df_enriched, _ = enrich_dataset(
        df_clean, config=enrichment_cfg, report=clean_report
    )
    print(f"Enriched DataFrame columns: {list(df_enriched.columns)}")

    # 4. Full pipeline preparation
    prepared = prepare_research_dataset(
        dataset, cleaning=cleaning_cfg, enrichment=enrichment_cfg, limits=limits
    )
    print(f"PreparedDataset record count: {len(prepared.data)}")


def main() -> None:
    """Run Research data usage example."""
    example_data()


if __name__ == "__main__":
    main()
