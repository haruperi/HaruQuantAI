"""Tests for QuantDataManager MarketDataReferenceRepository operations."""

from __future__ import annotations

from uuid import uuid7

import pytest
from app.contracts.data.models import BrowseReferenceRequest, BrowseReferenceSuccess
from app.services.data.market_data_store.reference_repository import (
    MarketDataReferenceRepository,
)


@pytest.fixture
def repository() -> MarketDataReferenceRepository:
    """Fixture providing reference repository."""
    return MarketDataReferenceRepository()


@pytest.mark.asyncio
async def test_list_series(repository: MarketDataReferenceRepository) -> None:
    """Verify list_series returns database records."""
    req = BrowseReferenceRequest(
        request_id=str(uuid7()),
        operation="LIST_SERIES",
        limit=10,
    )
    res = await repository.browse_reference(req)
    assert isinstance(res, BrowseReferenceSuccess)
    assert isinstance(res.data, list)
    if res.data:
        first = res.data[0]
        assert "symbol" in first
        assert "timeframe" in first


@pytest.mark.asyncio
async def test_read_parquet_bars(repository: MarketDataReferenceRepository) -> None:
    """Verify reading bars from Dukascopy Parquet archives."""
    req = BrowseReferenceRequest(
        request_id=str(uuid7()),
        operation="READ_BARS",
        symbol="EURUSD",
        timeframe="M1",
        limit=50,
    )
    res = await repository.browse_reference(req)
    assert isinstance(res, BrowseReferenceSuccess)
    assert isinstance(res.data, list)
    if res.data:
        bar = res.data[0]
        assert "open" in bar
        assert "high" in bar
        assert "low" in bar
        assert "close" in bar
        assert "time" in bar


@pytest.mark.asyncio
async def test_inspect_quality(repository: MarketDataReferenceRepository) -> None:
    """Verify anomaly detection on historical bars."""
    req = BrowseReferenceRequest(
        request_id=str(uuid7()),
        operation="INSPECT_QUALITY",
        symbol="EURUSD",
        timeframe="M1",
    )
    res = await repository.browse_reference(req)
    assert isinstance(res, BrowseReferenceSuccess)
    assert isinstance(res.data, dict)
    assert "problems" in res.data
    assert "timeline" in res.data
    assert "details" in res.data


@pytest.mark.asyncio
async def test_export_data_csv(repository: MarketDataReferenceRepository) -> None:
    """Verify CSV data export generation."""
    req = BrowseReferenceRequest(
        request_id=str(uuid7()),
        operation="EXPORT_DATA",
        symbol="EURUSD",
        timeframe="H1",
        payload={"format": "csv"},
    )
    res = await repository.browse_reference(req)
    assert isinstance(res, BrowseReferenceSuccess)
    assert isinstance(res.data, dict)
    assert res.data["format"] == "csv"
    assert "<DATE>" in res.data["content"]
