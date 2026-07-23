"""Unit tests for Research dataset validation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytest
from app.services.data.contracts import DataQualityReport as SourceQualityReport
from app.services.data.contracts import (
    MarketDataset,
    OHLCVRecord,
)
from app.services.research.contracts import ResearchResourceLimits
from app.services.research.data import validate_dataset
from app.utils import logger

_REQUEST_ID = "req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def _dataset() -> MarketDataset:
    """Build a canonical bar dataset with spread evidence.

    Returns:
        Valid Data-owned dataset.
    """
    logger.debug("Building Research validation test dataset")
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
        _dataset(), limits=ResearchResourceLimits(100, 10.0, 1024)
    )
    assert any(issue["code"] == "INVALID_OHLC" for issue in report.fatal_issues)
