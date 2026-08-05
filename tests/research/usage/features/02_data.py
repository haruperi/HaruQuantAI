"""Executable Research data usage example.

Demonstrates dataset validation, cleaning, enrichment, and preparation.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_quality_report,
    build_market_dataset,
    build_ohlcv_record,
)
from app.services.research import (
    clean_dataset,
    create_research_value,
    enrich_dataset,
    prepare_research_dataset,
    validate_dataset,
)

REQUEST_ID = "req-2123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _dataset():
    """Build the bounded usage market dataset."""
    start = datetime(2026, 1, 5, tzinfo=UTC)
    records = tuple(
        build_ohlcv_record(
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
    quality = build_data_quality_report(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        record_count=5,
        checked_count=5,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return build_market_dataset(
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


def _limits() -> object:
    """Build the bounded Research resource limits."""
    return create_research_value("ResearchResourceLimits", 100, 10.0, 1024)


def _cleaning_cfg() -> object:
    """Build the explicit cleaning configuration."""
    return create_research_value(
        "CleaningConfig", "UTC", "error", "none", "keep_warn", "error"
    )


def _enrichment_cfg() -> object:
    """Build the explicit enrichment configuration."""
    return create_research_value("EnrichmentConfig", "TEST", True, True, False, True)


def fr_res_027() -> None:
    """FR-RES-027.

    The system shall validate required columns, UTC/time ordering,
    duplicates, gaps, OHLC consistency, spread quality, volume, finite
    values, and source metadata without mutating input.
    """
    _header(
        "FR-RES-027. The system shall validate required columns, UTC/time ordering, duplicates, gaps, OHLC consistency, spread quality, volume, finite values, and source metadata without mutating input."
    )
    report = validate_dataset(_dataset(), limits=_limits())
    print(f"FR-RES-027 fatal_issues={len(report.fatal_issues)}")


def fr_res_028() -> None:
    """FR-RES-028.

    The system shall clean a copy using only explicit approved strategies
    and record every action and unresolved warning.
    """
    _header(
        "FR-RES-028. The system shall clean a copy using only explicit approved strategies and record every action and unresolved warning."
    )
    dataset = _dataset()
    limits = _limits()
    validation_report = validate_dataset(dataset, limits=limits)
    df_clean, _ = clean_dataset(
        dataset,
        config=_cleaning_cfg(),
        report=validation_report,
        limits=limits,
    )
    print(f"FR-RES-028 cleaned_rows={len(df_clean)}")


def fr_res_029() -> None:
    """FR-RES-029.

    The system shall enrich a copy with selected pip/geometry/return-label/
    calendar fields, label forward fields as research-only, and preserve row
    alignment; session tagging is a later seasonality/ operation.
    """
    _header(
        "FR-RES-029. The system shall enrich a copy with selected pip/geometry/return-label/ calendar fields, label forward fields as research-only, and preserve row alignment; session tagging is a later seasonality/ operation."
    )
    dataset = _dataset()
    limits = _limits()
    validation_report = validate_dataset(dataset, limits=limits)
    df_clean, clean_report = clean_dataset(
        dataset,
        config=_cleaning_cfg(),
        report=validation_report,
        limits=limits,
    )
    df_enriched, _ = enrich_dataset(
        df_clean, config=_enrichment_cfg(), report=clean_report
    )
    print(f"FR-RES-029 enriched_columns={list(df_enriched.columns)}")


def fr_res_030() -> None:
    """FR-RES-030.

    The system shall execute validate -> clean -> revalidate -> enrich
    deterministically and return hashes, provenance, and quality evidence,
    never fetching provider data.
    """
    _header(
        "FR-RES-030. The system shall execute validate -> clean -> revalidate -> enrich deterministically and return hashes, provenance, and quality evidence, never fetching provider data."
    )
    prepared = prepare_research_dataset(
        _dataset(),
        cleaning=_cleaning_cfg(),
        enrichment=_enrichment_cfg(),
        limits=_limits(),
    )
    print(f"FR-RES-030 prepared_rows={len(prepared.data)}")


def main() -> None:
    """Run every Research data requirement demonstration in order."""
    _feature_header(
        "FEATURE: FEAT-RES-02 — data/ — Deterministic Dataset Preparation\n\n"
        "Purpose: Validate OHLCV market datasets, compute data quality reports, clean records, and produce research-ready dataset bundles.\n\n"
        "Module flow:\n"
        "-> Stage 1: Input dataset loading and schema validation\n-> Stage 2: Fail-closed data quality inspection and invalid row filtering\n-> Stage 3: Research-ready dataset bundle construction"
    )

    print("Research Example 2: Dataset Preparation and Cleaning")
    fr_res_027()
    fr_res_028()
    fr_res_029()
    fr_res_030()


if __name__ == "__main__":
    main()
