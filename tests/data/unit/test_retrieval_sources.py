"""Focused unit coverage for governed historical retrieval orchestration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.services.data.contracts import DataError, OHLCVRecord
from app.services.data.market_data.pipeline import fetch_market_dataset
from app.services.data.market_data.requests import (
    MarketDataRequest,
)
from app.services.data.sources.contracts import (
    RawSourceBatch,
    SourceDescriptor,
    SourceLicensePolicy,
)
from app.utils import generate_id

_START = datetime(2026, 1, 1, tzinfo=UTC)
_REQUEST_ID = generate_id("req")


def _bar(index: int, minute: int) -> OHLCVRecord:
    """Return one canonical provider bar with explicit series position."""
    timestamp = _START + timedelta(minutes=minute)
    price = Decimal(10 + index)
    return OHLCVRecord(
        timestamp=timestamp,
        open=price,
        high=price + Decimal("0.5"),
        low=price - Decimal("0.5"),
        close=price,
        volume=Decimal(100 + index),
        price_unit="USD",
        volume_unit="lots",
        source="fixture",
        source_symbol="ABC",
        source_revision="rev-1",
        available_at=timestamp + timedelta(seconds=1),
    )


def _descriptor() -> SourceDescriptor:
    """Return an approved source descriptor for isolated retrieval."""
    return SourceDescriptor(
        source_id="fixture",
        readiness="staging",
        capabilities=("bars",),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="v1",
        timezone="UTC",
        revision="rev-1",
        license_policy=SourceLicensePolicy(
            source_id="fixture",
            status="approved",
            permitted_workflows=("research",),
            export_allowed=True,
            attribution_required=False,
        ),
        identity_mapping_revision="mapping-v1",
    )


def _request() -> MarketDataRequest:
    """Return one bounded no-cache historical request."""
    return MarketDataRequest(
        source_id="fixture",
        symbol="ABC",
        data_kind="bars",
        timeframe="M1",
        start=_START,
        end=_START + timedelta(hours=1),
        limit=100,
        use_cache=False,
        quality_failure_behavior="reject",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=_REQUEST_ID,
    )


def _install_runtime(
    monkeypatch: pytest.MonkeyPatch,
    records: tuple[OHLCVRecord, ...],
) -> None:
    """Install one isolated source plan without persistence or provider access."""
    batch = RawSourceBatch(
        source_id="fixture",
        provider_symbol="ABC",
        data_kind="bars",
        records=tuple(record.model_dump() for record in records),
        retrieved_at=records[-1].available_at,
        revision="rev-1",
        request_id=_REQUEST_ID,
    )
    source = SimpleNamespace(fetch=lambda _request: batch)
    monkeypatch.setattr(
        "app.services.data.market_data.pipeline.evaluate_source_policy",
        lambda request: SimpleNamespace(ordered_sources=(request.source_id,)),
    )
    monkeypatch.setattr(
        "app.services.data.market_data.pipeline.get_source_descriptor",
        lambda _source_id: _descriptor(),
    )
    monkeypatch.setattr(
        "app.services.data.market_data.pipeline.resolve_source_identity",
        lambda _request: SimpleNamespace(
            provider_symbol="ABC",
            mapping_revision="mapping-v1",
        ),
    )
    monkeypatch.setattr(
        "app.services.data.market_data.pipeline.resolve_source",
        lambda _source_id: source,
    )
    monkeypatch.setattr(
        "app.services.data.market_data.pipeline.record_source_attempt",
        lambda *_args: None,
    )


def test_fetch_market_dataset_rejects_blocking_quality(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A detected missing-bar gap never crosses the retrieval boundary."""
    _install_runtime(
        monkeypatch,
        (_bar(0, 0), _bar(1, 1), _bar(2, 30)),
    )

    with pytest.raises(DataError) as captured:
        fetch_market_dataset(_request())

    assert captured.value.code == "DATA_QUALITY_FAILED"


def test_fetch_market_dataset_warns_and_returns_blocking_quality(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Warn behavior returns records with failed quality evidence intact."""
    _install_runtime(
        monkeypatch,
        (_bar(0, 0), _bar(1, 1), _bar(2, 30)),
    )
    request = _request().model_copy(
        update={"quality_failure_behavior": "warn"},
    )

    dataset = fetch_market_dataset(request)

    assert dataset.record_count == 3
    assert dataset.quality_report.quality_status == "failed"
    assert {issue.code for issue in dataset.quality_report.issues} == {"MISSING_BARS"}


def test_cached_failed_quality_obeys_warn_and_reject(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cached and fresh datasets use the same quality-failure behavior."""
    _install_runtime(
        monkeypatch,
        (_bar(0, 0), _bar(1, 1), _bar(2, 30)),
    )
    warn_request = _request().model_copy(
        update={"quality_failure_behavior": "warn"},
    )
    failed_dataset = fetch_market_dataset(warn_request)
    monkeypatch.setattr(
        "app.services.data.market_data.pipeline._cached_dataset",
        lambda *_args: failed_dataset,
    )

    cached_warn = warn_request.model_copy(update={"use_cache": True})
    assert fetch_market_dataset(cached_warn) is failed_dataset

    cached_reject = cached_warn.model_copy(
        update={"quality_failure_behavior": "reject"},
    )
    with pytest.raises(DataError) as captured:
        fetch_market_dataset(cached_reject)
    assert captured.value.code == "DATA_QUALITY_FAILED"


def test_fetch_market_dataset_returns_nonblocking_quality(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A contiguous series returns its measured nonblocking quality evidence."""
    _install_runtime(
        monkeypatch,
        tuple(_bar(index, index) for index in range(8)),
    )

    dataset = fetch_market_dataset(_request())

    assert dataset.record_count == 8
    assert dataset.quality_report.quality_status != "failed"
