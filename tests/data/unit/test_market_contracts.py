"""Unit tests for market requests, datasets, quality, and availability."""

from decimal import Decimal

import pytest
from app.services.data.contracts import (
    DataAvailability,
    DataQualityReport,
    MarketDataRequest,
    MarketDataset,
    QualityIssue,
    SyntheticRequest,
)
from app.services.data.contracts.errors import DataError

from tests.data.helpers import AVAILABLE, END, START, make_dataset, make_quality


def test_quality_report_bounds_samples() -> None:
    """Issue samples cannot exceed the caller-declared bound."""
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


def test_market_dataset_never_contains_provider_objects() -> None:
    """Only canonical records can inhabit a MarketDataset."""
    dataset = make_dataset()
    values = {name: getattr(dataset, name) for name in MarketDataset.model_fields}
    values["records"] = ({"provider": object()},)
    with pytest.raises(DataError):
        MarketDataset(**values)


def test_market_requests_require_explicit_bounded_policy() -> None:
    """Request ranges, precision, and generation counts are intrinsic bounds."""
    with pytest.raises(DataError):
        MarketDataRequest(
            source_id="fixture",
            symbol="ABC",
            data_kind="bars",
            timeframe="1m",
            start=END,
            end=START,
            limit=1,
            use_cache=False,
            quality_failure_behavior="fail",
            workflow_context="risk",
            precision_policy="decimal_string",
            request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
        )
    with pytest.raises(DataError):
        SyntheticRequest(
            symbol="ABC",
            data_kind="bars",
            timeframe="1m",
            start=START,
            record_count=0,
            method="gbm",
            parameters={},
            precision_policy="decimal_string",
            request_id="req-a697f8b99a46c8465b9a70e7af44e49a7665cf1ce8e62c3b42678f1c26b21814",
        )


def test_availability_requires_measured_gaps() -> None:
    """Availability ordering and completeness are validated evidence."""
    with pytest.raises(DataError):
        DataAvailability(
            source_id="fixture",
            symbol="ABC",
            data_kind="bars",
            timeframe="1m",
            ranges=(),
            gaps=(),
            completeness=Decimal("1.1"),
            record_count=0,
            source_revision="rev-1",
            source_readiness="staging",
            provenance={"index": "one"},
            request_id="req-bc0e142195cb27a6127a29283e0ccdfb3a51449da848f04abee1c1526184084e",
        )
    assert make_quality().quality_status == "passed"
