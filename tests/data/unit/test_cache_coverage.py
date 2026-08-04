"""
Targeted unit tests to bring app/services/data/persistence/cache.py to >80% coverage.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.data.contracts import DataQualityReport, MarketDataset
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.persistence.cache import (
    _filter_cached_keys,
    clear_cache_entry,
    clear_data_cache,
    get_cache_entry,
    put_cache_entry,
)
from app.services.data.persistence.contracts import (
    CacheClearRequest,
    CacheReadRequest,
    CacheWriteRequest,
)

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.persistence.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def _sample_dataset() -> MarketDataset:
    """Construct a minimal valid MarketDataset for testing."""
    now = datetime.now(UTC)
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal("1.0"),
        issues=(),
        warnings=(),
        record_count=0,
        checked_count=0,
        truncated=False,
        sample_limit=100,
        schema_version="v1",
        generated_at=now,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="M5",
        start=now - timedelta(days=1),
        end=now,
        available_at=now,
        records=(),
        record_count=0,
        quality_report=quality,
        source_metadata={"source_id": "fixture"},
        license_metadata={"status": "approved"},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id=_REQ_ID,
    )


def test_get_cache_entry_handles_stale_and_expiration() -> None:
    """Test get_cache_entry expired entry behavior with allow_stale True/False."""
    read_req_no_stale = CacheReadRequest(
        key="key1",
        allow_stale=False,
        request_id=_REQ_ID,
    )
    read_req_stale = CacheReadRequest(
        key="key1",
        allow_stale=True,
        request_id=_REQ_ID,
    )

    past = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    expired = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    ds_json = _sample_dataset().model_dump_json()

    mock_row = {
        "dataset_json": ds_json,
        "created_at": past,
        "expires_at": expired,
        "source_revision": "rev1",
        "raw_data_hash": "hash1",
        "schema_version": "v1",
        "normalization_version": "v1",
        "request_id": _REQ_ID,
    }

    mock_res = MagicMock()
    mock_res.rows = (mock_row,)

    with patch(
        "app.services.data.persistence.cache.read_cache_record",
        return_value=mock_res,
    ):
        # Allow stale False -> returns None
        entry = _unwrap(get_cache_entry(read_req_no_stale))
        assert entry is None

        # Allow stale True -> returns CacheEntry with stale_warning
        entry_stale = _unwrap(get_cache_entry(read_req_stale))
        assert entry_stale is not None
        assert entry_stale.dataset.cache_status == "stale_warning"


def test_get_cache_entry_error_handling() -> None:
    """Test get_cache_entry error handling for corrupt json and general exceptions."""
    read_req = CacheReadRequest(key="key1", allow_stale=False, request_id=_REQ_ID)

    # Corrupt dataset_json
    mock_row = {
        "dataset_json": "{invalid_json",
        "created_at": datetime.now(UTC).isoformat(),
        "expires_at": None,
        "source_revision": "rev1",
        "raw_data_hash": "hash1",
        "schema_version": "v1",
        "normalization_version": "v1",
        "request_id": _REQ_ID,
    }
    mock_res = MagicMock()
    mock_res.rows = (mock_row,)

    with patch(
        "app.services.data.persistence.cache.read_cache_record",
        return_value=mock_res,
    ):
        response = get_cache_entry(read_req)
        assert response.status == "error"
        assert response.error is not None
        assert response.error.code == "FILE_CORRUPTED"

    # Database exception
    with patch(
        "app.services.data.persistence.cache.read_cache_record",
        side_effect=RuntimeError("DB query failed"),
    ):
        response = get_cache_entry(read_req)
        assert response.status == "error"
        assert response.error is not None
        assert response.error.code == "DATABASE_ERROR"


def test_put_cache_entry_uncommitted_row() -> None:
    """Test put_cache_entry raising DB_WRITE_FAILED when row not written."""
    ds = _sample_dataset()
    write_req = CacheWriteRequest(
        key="key1",
        dataset=ds,
        ttl_seconds=3600,
        source_revision="rev1",
        raw_data_hash="hash1",
        request_id=_REQ_ID,
    )

    mock_res = MagicMock()
    mock_res.committed = False
    mock_res.affected_rows = 0

    with patch(
        "app.services.data.persistence.cache.update_cache_record",
        return_value=mock_res,
    ):
        response = put_cache_entry(write_req)
        assert response.status == "error"
        assert response.error is not None
        assert response.error.code == "DB_WRITE_FAILED"


def test_clear_cache_entry_filters_and_dry_run() -> None:
    """Test clear_cache_entry namespace check, filters, and deletion."""
    # Non-data namespace returns 0
    other_req = CacheClearRequest(
        namespace="other", dry_run=True, max_entries=10, request_id=_REQ_ID
    )
    res_other = _unwrap(clear_cache_entry(other_req))
    assert res_other.matched_count == 0

    # Test filtering rows
    rows = (
        {
            "key": "k1",
            "dataset_json": '{"symbol": "EURUSD", "data_kind": "bars", "records": [{"source": "mt5"}]}',
        },
        {
            "key": "k2",
            "dataset_json": '{"symbol": "GBPUSD", "data_kind": "ticks", "source_metadata": {"source_id": "dukascopy"}}',
        },
    )
    req_filter = CacheClearRequest(
        namespace="data",
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        dry_run=True,
        max_entries=10,
        request_id=_REQ_ID,
    )
    matched = _filter_cached_keys(rows, req_filter)
    assert matched == ["k1"]

    # Test clear_cache_entry with actual delete
    mock_select_res = MagicMock()
    mock_select_res.rows = rows

    mock_delete_res = MagicMock()
    mock_delete_res.committed = True
    mock_delete_res.affected_rows = 1

    req_delete = CacheClearRequest(
        namespace="data",
        source_id="mt5",
        dry_run=False,
        max_entries=10,
        request_id=_REQ_ID,
    )

    with (
        patch(
            "app.services.data.persistence.cache.read_cache_records",
            return_value=mock_select_res,
        ),
        patch(
            "app.services.data.persistence.cache.delete_cache_records",
            return_value=mock_delete_res,
        ),
    ):
        res_del = _unwrap(clear_cache_entry(req_delete))
        assert res_del.matched_count == 1
        assert res_del.deleted_count == 1


def test_clear_data_cache_mixed_styles() -> None:
    """Test clear_data_cache with mixed call style raises DataError."""
    req = CacheClearRequest(
        namespace="data", dry_run=True, max_entries=10, request_id=_REQ_ID
    )
    response = clear_data_cache(req, symbol="EURUSD")
    assert response.status == "error"
    assert response.error is not None
