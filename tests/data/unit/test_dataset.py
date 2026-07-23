"""Unit tests for the FEAT-DATA-01 canonical dataset envelope."""

from decimal import Decimal

import pytest
from app.services.data.contracts import (
    DataError,
    DataQualityReport,
    DataRange,
    MarketDataset,
    QualityIssue,
)

from tests.data.helpers import AVAILABLE, END, START, make_dataset


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
            quality_status="passed_with_warnings",
            quality_score=Decimal("0.5"),
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
