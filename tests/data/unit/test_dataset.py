"""Unit tests for the FEAT-DATA-01 canonical dataset envelope."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.contracts import (
    DataError,
    DataQualityReport,
    DataRange,
    MarketDataset,
    OHLCVRecord,
    QualityIssue,
)

START = datetime(2026, 1, 1, tzinfo=UTC)
END = START + timedelta(minutes=1)
AVAILABLE = END + timedelta(seconds=1)


def make_bar(timestamp=START):
    """Return one exact canonical OHLCV record."""
    return OHLCVRecord(
        timestamp=timestamp,
        open=Decimal("10.0"),
        high=Decimal("11.0"),
        low=Decimal("9.0"),
        close=Decimal("10.5"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="shares",
        source="fixture",
        source_symbol="ABC",
        source_revision="rev-1",
        available_at=timestamp + timedelta(seconds=1),
    )


def make_quality(count=1):
    """Return passing bounded quality evidence."""
    return DataQualityReport(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        issues=(),
        warnings=(),
        record_count=count,
        checked_count=count,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=AVAILABLE,
    )


def make_dataset():
    """Return one immutable provider-neutral market dataset."""
    bar = make_bar()
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="ABC",
        timeframe="1m",
        records=(bar,),
        start=START,
        end=START,
        available_at=AVAILABLE,
        record_count=1,
        quality_report=make_quality(),
        source_metadata={"source": "fixture"},
        license_metadata={"status": "approved"},
        cache_status="miss",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id="req-491e2e64ca4b441c7f08620130e0e40d107775c753ca238bea74d87a1dd9f667",
    )


def test_quality_report_bounds_samples() -> None:
    """Issue samples cannot exceed the declared bound."""
    issue = QualityIssue(
        code="GAP",
        severity="warning",
        message="gap",
        samples=("one", "two"),
        blocking_workflows=(),
    )
    with pytest.raises(DataError):
        DataQualityReport(
            quality_status="critical",
            quality_decision="rejected",
            quality_score=Decimal("50.00"),
            issues=(issue,),
            warnings=(),
            record_count=2,
            checked_count=2,
            truncated=False,
            sample_limit=1,
            schema_version="v1",
            generated_at=AVAILABLE,
        )


def test_market_dataset_rejects_provider_objects() -> None:
    """Only canonical records can inhabit a market dataset."""
    dataset = make_dataset()
    values = {name: getattr(dataset, name) for name in MarketDataset.model_fields}
    values["records"] = ({"provider": object()},)
    with pytest.raises(DataError):
        MarketDataset(**values)


def test_data_range_rejects_reversed_bounds() -> None:
    """Canonical measured ranges remain ordered."""
    with pytest.raises(DataError):
        DataRange(start=END, end=START)
