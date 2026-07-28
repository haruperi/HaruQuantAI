"""Unit tests for symbol_discovery.py to reach >80% coverage."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from app.services.data.contracts import DataError, OHLCVRecord
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.market_data.requests import AvailabilityRequest, VolumeRequest
from app.services.data.market_data.symbol_discovery import (
    _compute_overlap_and_gaps,
    _compute_volume_buckets,
    _compute_volume_summary,
    _configured_limit,
    _load_local_manifest,
    discover_symbols,
    fetch_historical_volume,
    fetch_symbol_metadata,
    get_symbol_metadata,
    inspect_availability,
    list_symbols,
)
from app.services.data.market_data.symbol_metadata import (
    SymbolListRequest,
    SymbolMetadataRequest,
    VolumeRecord,
)

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)


def _unwrap(response):
    """Extract the raw payload from a StandardResponse for assertions."""
    return unwrap_data_response(
        response, operation="data.market_data.test", request_id=_REQ_ID
    )


def test_configured_limit_invalid_name() -> None:
    """Test _configured_limit raises DataError for invalid limit name."""
    with pytest.raises(DataError) as exc_info:
        _configured_limit("INVALID_LIMIT_NAME", _REQ_ID)
    assert exc_info.value.code == "INVALID_INPUT"


def test_discover_symbols_limit_exceeded() -> None:
    """Test discover_symbols fails closed with LIMIT_EXCEEDED when limit > max."""
    req = SymbolListRequest(source_id="mt5", limit=20000, request_id=_REQ_ID)
    response = discover_symbols(req)
    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "LIMIT_EXCEEDED"


def test_discover_symbols_disabled_source() -> None:
    """Test discover_symbols fails closed with SOURCE_UNAVAILABLE for disabled source."""
    mock_desc = MagicMock()
    mock_desc.readiness = "disabled"

    with patch(
        "app.services.data.market_data.symbol_discovery._get_source_descriptor_raw",
        return_value=mock_desc,
    ):
        req = SymbolListRequest(source_id="disabled_src", limit=10, request_id=_REQ_ID)
        response = discover_symbols(req)
        assert response.status != "success"
        assert response.error is not None
        assert response.error.code == "SOURCE_UNAVAILABLE"


def test_fetch_symbol_metadata_disabled_source() -> None:
    """Test fetch_symbol_metadata fails closed with SOURCE_UNAVAILABLE for disabled source."""
    mock_desc = MagicMock()
    mock_desc.readiness = "disabled"

    with patch(
        "app.services.data.market_data.symbol_discovery._get_source_descriptor_raw",
        return_value=mock_desc,
    ):
        req = SymbolMetadataRequest(
            source_id="disabled_src", symbol="EURUSD", request_id=_REQ_ID
        )
        response = fetch_symbol_metadata(req)
        assert response.status != "success"
        assert response.error is not None
        assert response.error.code == "SOURCE_UNAVAILABLE"


def test_load_local_manifest_missing_file() -> None:
    """Test _load_local_manifest raises DATA_NOT_FOUND when manifest missing."""
    req = AvailabilityRequest(
        source_id="local",
        symbol="NONEXISTENT_SYM",
        data_kind="ohlcv",
        timeframe="M1",
        start=_NOW - timedelta(hours=1),
        end=_NOW,
        max_probe_records=100,
        request_id=_REQ_ID,
    )
    with pytest.raises(DataError) as exc_info:
        _load_local_manifest(req)
    assert exc_info.value.code == "DATA_NOT_FOUND"


def test_compute_overlap_and_gaps_invalid_range() -> None:
    """Test _compute_overlap_and_gaps raises INVALID_INPUT when start >= end."""
    mock_req = MagicMock()
    mock_req.start = _NOW
    mock_req.end = _NOW - timedelta(hours=1)
    mock_req.request_id = _REQ_ID

    with pytest.raises(DataError) as exc_info:
        _compute_overlap_and_gaps(mock_req, _NOW - timedelta(hours=2), _NOW)
    assert exc_info.value.code == "INVALID_INPUT"


def test_inspect_availability_limit_exceeded() -> None:
    """Test inspect_availability fails closed with LIMIT_EXCEEDED when probe records > max."""
    req = AvailabilityRequest(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="ohlcv",
        timeframe="M1",
        start=_NOW - timedelta(hours=1),
        end=_NOW,
        max_probe_records=2_000_000,
        request_id=_REQ_ID,
    )
    response = inspect_availability(req)
    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "LIMIT_EXCEEDED"


def test_inspect_availability_disabled_source() -> None:
    """Test inspect_availability fails closed with SOURCE_UNAVAILABLE for disabled source."""
    mock_desc = MagicMock()
    mock_desc.readiness = "disabled"

    with patch(
        "app.services.data.market_data.symbol_discovery._get_source_descriptor_raw",
        return_value=mock_desc,
    ):
        req = AvailabilityRequest(
            source_id="disabled_src",
            symbol="EURUSD",
            data_kind="ohlcv",
            timeframe="M1",
            start=_NOW - timedelta(hours=1),
            end=_NOW,
            max_probe_records=100,
            request_id=_REQ_ID,
        )
        response = inspect_availability(req)
        assert response.status != "success"
        assert response.error is not None
        assert response.error.code == "SOURCE_UNAVAILABLE"


def test_fetch_historical_volume_records_mode() -> None:
    """Test fetch_historical_volume with mode='records'."""
    ohlcv = OHLCVRecord(
        timestamp=_NOW,
        source="mt5",
        source_symbol="EURUSD",
        source_revision="v1",
        available_at=_NOW,
        open=Decimal("1.0800"),
        high=Decimal("1.0850"),
        low=Decimal("1.0790"),
        close=Decimal("1.0820"),
        volume=Decimal(500),
        price_unit="USD",
        volume_unit="units",
    )
    mock_ds = MagicMock()
    mock_ds.records = (ohlcv,)
    mock_ds.source_metadata = {"source": "mt5"}

    with patch(
        "app.services.data.market_data.symbol_discovery._fetch_market_dataset_raw",
        return_value=mock_ds,
    ):
        req = VolumeRequest(
            source_id="mt5",
            symbol="EURUSD",
            mode="records",
            start=_NOW - timedelta(hours=1),
            end=_NOW,
            limit=100,
            request_id=_REQ_ID,
        )
        res = _unwrap(fetch_historical_volume(req))
        assert res.mode == "records"
        assert len(res.records) == 1
        assert res.records[0].volume == Decimal(500)


def test_public_get_symbol_metadata_and_list_symbols_keyword_style() -> None:
    """Test public get_symbol_metadata and list_symbols with keyword parameters."""
    mock_meta = MagicMock()
    mock_page = MagicMock()

    with (
        patch(
            "app.services.data.market_data.symbol_discovery._fetch_symbol_metadata_raw",
            return_value=mock_meta,
        ),
        patch(
            "app.services.data.market_data.symbol_discovery._discover_symbols_raw",
            return_value=mock_page,
        ),
        patch(
            "app.services.data.market_data.symbol_discovery._ensure_source_access_raw"
        ),
    ):
        meta = _unwrap(
            get_symbol_metadata(source_id="mt5", symbol="EURUSD", request_id=_REQ_ID)
        )
        assert meta == mock_meta

        page = _unwrap(list_symbols(source_id="mt5", limit=10, request_id=_REQ_ID))
        assert page == mock_page


def test_compute_volume_summary_and_buckets() -> None:
    """Test _compute_volume_summary and _compute_volume_buckets helpers."""
    v_rec = VolumeRecord(timestamp=_NOW, volume=Decimal("100.5"))
    v_req_summary = VolumeRequest(
        source_id="mt5",
        symbol="EURUSD",
        mode="summary",
        start=_NOW - timedelta(hours=1),
        end=_NOW,
        limit=100,
        request_id=_REQ_ID,
    )
    prov = {"source": "mt5"}
    res_summary = _compute_volume_summary(v_req_summary, (v_rec,), "units", prov)
    assert res_summary.summary is not None
    assert res_summary.summary.total == Decimal("100.5")

    v_req_buckets = VolumeRequest(
        source_id="mt5",
        symbol="EURUSD",
        mode="buckets",
        bucket_seconds=60,
        start=_NOW - timedelta(hours=1),
        end=_NOW,
        limit=100,
        request_id=_REQ_ID,
    )
    res_buckets = _compute_volume_buckets(v_req_buckets, (v_rec,), "units", prov)
    assert len(res_buckets.records) == 1
    assert res_buckets.records[0].volume == Decimal("100.5")
