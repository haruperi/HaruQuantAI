"""Unit tests for deterministic Research dataset preparation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytest
from app.composition.logging import get_logger
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
)

logger = get_logger(__name__)

_REQUEST_ID = "req-1123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def _dataset():
    """Build a deterministic canonical dataset.

    Returns:
        Valid Data-owned dataset.
    """
    logger.debug("Building Research preparation test dataset")
    start = datetime(2026, 1, 5, tzinfo=UTC)
    records = tuple(
        build_ohlcv_record(
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
        request_id=_REQUEST_ID,
    )


def _limits() -> object:
    """Build test limits.

    Returns:
        Valid limits.
    """
    logger.debug("Building Research preparation test limits")
    return create_research_value("ResearchResourceLimits", 100, 10.0, 1024)


def test_clean_dataset_never_fills_implicitly() -> None:
    """Verify explicit no-fill cleaning preserves the row count."""
    logger.debug("Testing no implicit Research filling")
    frame, report = clean_dataset(
        _dataset(),
        config=create_research_value(
            "CleaningConfig", "UTC", "error", "none", "keep_warn", "error"
        ),
        report=create_research_value("DataQualityReport", (), (), ("schema",), ()),
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
        config=create_research_value(
            "EnrichmentConfig", "TEST", False, True, True, False
        ),
        report=create_research_value("DataQualityReport", (), (), (), ()),
    )
    assert enriched.attrs["research_only_columns"] == ("forward_return_1",)
    assert pd.isna(enriched["forward_return_1"].iloc[-1])


def test_prepare_dataset_is_deterministic_and_provider_free() -> None:
    """Verify repeated preparation produces equal hashes and detached frames."""
    logger.debug("Testing deterministic Research preparation")
    cleaning = create_research_value(
        "CleaningConfig", "UTC", "error", "none", "keep_warn", "error"
    )
    enrichment = create_research_value(
        "EnrichmentConfig", "TEST", True, True, False, True
    )
    first = prepare_research_dataset(
        _dataset(), cleaning=cleaning, enrichment=enrichment, limits=_limits()
    )
    second = prepare_research_dataset(
        _dataset(), cleaning=cleaning, enrichment=enrichment, limits=_limits()
    )
    assert first.dataset_hash == second.dataset_hash
    assert first.configuration_hash == second.configuration_hash
    assert first.data.equals(second.data)


def test_clean_dataset_applies_declared_duplicate_calendar_and_spread_policies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise explicit cleaning actions without implicit filling."""
    saturday = pd.Timestamp("2026-01-03T00:00:00Z")
    index = pd.DatetimeIndex(
        [
            saturday,
            saturday,
            pd.Timestamp("2026-01-05T00:00:00Z"),
            pd.Timestamp("2026-01-05T00:01:00Z"),
        ]
    )
    frame = pd.DataFrame(
        {
            "open": [1.0] * 4,
            "high": [2.0] * 4,
            "low": [0.5] * 4,
            "close": [1.5] * 4,
            "volume": [1.0] * 4,
            "spread": [0.1, 0.1, -0.1, 0.1],
        },
        index=index,
    )
    monkeypatch.setattr(
        "app.services.research.data.preparation.to_ohlcv_dataframe",
        lambda _dataset: frame,
    )
    cleaned, report = clean_dataset(
        _dataset(),
        config=create_research_value(
            "CleaningConfig",
            "UTC",
            "drop",
            "none",
            "drop",
            "drop_invalid",
        ),
        report=create_research_value("DataQualityReport", (), (), (), ()),
        limits=_limits(),
    )
    assert cleaned.empty is False
    assert {action["code"] for action in report.cleaning_actions} == {
        "DUPLICATES_REMOVED",
        "NON_TRADING_ROWS_REMOVED",
        "INVALID_SPREAD_ROWS_REMOVED",
    }


def test_clean_dataset_rejects_limits_fatal_quality_and_empty_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cover resource, quality, duplicate, and empty-result guards."""
    with pytest.raises(ValueError, match="ROW_LIMIT_EXCEEDED"):
        clean_dataset(
            _dataset(),
            config=create_research_value(
                "CleaningConfig", "UTC", "error", "none", "keep_warn", "error"
            ),
            report=create_research_value("DataQualityReport", (), (), (), ()),
            limits=create_research_value("ResearchResourceLimits", 1, 10.0, 1_024),
        )
    with pytest.raises(ValueError, match="FATAL_QUALITY_ISSUES"):
        clean_dataset(
            _dataset(),
            config=create_research_value(
                "CleaningConfig", "UTC", "error", "none", "keep_warn", "error"
            ),
            report=create_research_value(
                "DataQualityReport",
                ({"code": "INVALID", "field": "close"},),
                (),
                (),
                (),
            ),
            limits=_limits(),
        )
    empty = pd.DataFrame(
        columns=("open", "high", "low", "close", "volume", "spread"),
        index=pd.DatetimeIndex([], tz="UTC"),
    )
    monkeypatch.setattr(
        "app.services.research.data.preparation.to_ohlcv_dataframe",
        lambda _dataset: empty,
    )
    with pytest.raises(ValueError, match="NO_ROWS_AFTER_CLEANING"):
        clean_dataset(
            _dataset(),
            config=create_research_value(
                "CleaningConfig", "UTC", "error", "none", "drop", "error"
            ),
            report=create_research_value("DataQualityReport", (), (), (), ()),
            limits=_limits(),
        )


def test_enrich_dataset_covers_geometry_returns_calendar_and_guards() -> None:
    """Cover all declared enrichment branches and structural refusals."""
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
        config=create_research_value(
            "EnrichmentConfig", "TEST", True, True, False, True
        ),
        report=create_research_value("DataQualityReport", (), (), (), ()),
    )
    assert {
        "candle_range",
        "upper_wick",
        "simple_return",
        "calendar_hour",
    } <= set(enriched)
    with pytest.raises(ValueError, match="OHLCVS_COLUMNS_REQUIRED"):
        enrich_dataset(
            frame.drop(columns=["spread"]),
            config=create_research_value(
                "EnrichmentConfig", "TEST", False, False, False, False
            ),
            report=create_research_value("DataQualityReport", (), (), (), ()),
        )
    with pytest.raises(ValueError, match="UTC_TIME_INDEX_REQUIRED"):
        enrich_dataset(
            frame.set_axis(frame.index.tz_localize(None)),
            config=create_research_value(
                "EnrichmentConfig", "TEST", False, False, False, True
            ),
            report=create_research_value("DataQualityReport", (), (), (), ()),
        )
