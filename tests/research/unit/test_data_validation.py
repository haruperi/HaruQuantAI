"""Unit tests for Research dataset validation."""

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
from app.services.research import create_research_value, validate_dataset
from app.services.research.data.validation import _enforce_memory_budget

logger = get_logger(__name__)

_REQUEST_ID = "req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def _dataset():
    """Build a canonical bar dataset with spread evidence.

    Returns:
        Valid Data-owned dataset.
    """
    logger.debug("Building Research validation test dataset")
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
        request_id=_REQUEST_ID,
    )


def test_validate_dataset_reports_fatal_ohlc_issue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify invalid OHLC relationships become fatal evidence.

    Args:
        monkeypatch: Pytest patch helper.
    """
    logger.debug("Testing fatal Research OHLC validation")
    index = pd.date_range("2026-01-05", periods=5, freq="min", tz="UTC")
    frame = pd.DataFrame(
        {
            "open": [10.0] * 5,
            "high": [9.0] * 5,
            "low": [8.0] * 5,
            "close": [10.0] * 5,
            "volume": [100.0] * 5,
            "spread": [0.1] * 5,
        },
        index=index,
    )
    monkeypatch.setattr(
        "app.services.research.data.validation.to_ohlcv_dataframe", lambda _: frame
    )
    report = validate_dataset(
        _dataset(),
        limits=create_research_value("ResearchResourceLimits", 100, 10.0, 1024),
    )
    assert any(issue["code"] == "INVALID_OHLC" for issue in report.fatal_issues)


def test_validate_dataset_rejects_wrong_contract_limits_and_nonbars() -> None:
    """Cover boundary, resource, and data-kind refusal paths."""
    limits = create_research_value("ResearchResourceLimits", 100, 10.0, 1_024)
    with pytest.raises(ValueError, match="MARKET_DATASET_REQUIRED"):
        validate_dataset(object(), limits=limits)
    with pytest.raises(ValueError, match="ROW_LIMIT_EXCEEDED"):
        validate_dataset(
            _dataset(),
            limits=create_research_value("ResearchResourceLimits", 1, 10.0, 1_024),
        )
    nonbars = _dataset().model_copy(update={"data_kind": "ticks"})
    with pytest.raises(ValueError, match="NONEMPTY_BAR_DATASET_REQUIRED"):
        validate_dataset(nonbars, limits=limits)


def test_validate_dataset_reports_nonfinite_irregular_and_missing_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preserve multiple independent quality findings in one report."""
    index = pd.to_datetime(
        [
            "2026-01-05T00:00:00Z",
            "2026-01-05T00:01:00Z",
            "2026-01-05T00:03:00Z",
            "2026-01-05T00:04:00Z",
            "2026-01-05T00:05:00Z",
        ]
    )
    frame = pd.DataFrame(
        {
            "open": [10.0] * 5,
            "high": [11.0] * 5,
            "low": [9.0] * 5,
            "close": [10.0, 10.1, float("nan"), 10.3, 10.4],
            "volume": [100.0] * 5,
            "spread": [0.1] * 5,
        },
        index=index,
    )
    monkeypatch.setattr(
        "app.services.research.data.validation.to_ohlcv_dataframe",
        lambda _dataset: frame,
    )
    dataset = _dataset().model_copy(update={"source_metadata": {}})
    report = validate_dataset(
        dataset,
        limits=create_research_value("ResearchResourceLimits", 100, 10.0, 1_024),
    )
    assert {item["code"] for item in report.fatal_issues} >= {
        "NONFINITE_VALUE",
        "MISSING_SOURCE_METADATA",
    }
    assert any(warning.code == "IRREGULAR_INTERVALS" for warning in report.warnings)


def test_memory_admission_fails_before_over_budget_work() -> None:
    """FR-RES-001: deterministic deep-memory admission fails closed."""
    frame = pd.DataFrame({"payload": ("x" * 600_000, "y" * 600_000)})
    limits = create_research_value("ResearchResourceLimits", 100, 10.0, 1_024, 1)
    with pytest.raises(ValueError, match="MEMORY_BUDGET_EXCEEDED"):
        _enforce_memory_budget(frame, limits, allocation_multiplier=1)
