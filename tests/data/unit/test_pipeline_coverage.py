"""Unit tests for market_data/pipeline.py to reach >80% coverage."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.market_data.pipeline import (
    _cached_dataset,
    _default_ttl,
    _max_limit,
    _normalize,
    _reject_mixed,
    _require_acceptable_quality,
    _validate_record_limit,
    availability_request,
    fetch_market_dataset,
    get_market_data,
    get_spread_data,
    get_tick_data,
    market_request,
    volume_request,
)
from app.services.data.market_data.requests import MarketDataRequest

_REQ_ID = "req-11111111-1111-4111-8111-111111111111"
_NOW = datetime.now(UTC)
_PAST = _NOW - timedelta(days=1)


def _unwrap(response):
    """Extract the raw payload from a StandardResponse for assertions."""
    return unwrap_data_response(
        response, operation="data.market_data.test", request_id=_REQ_ID
    )


def _make_market_data_req(**kwargs) -> MarketDataRequest:
    defaults = {
        "source_id": "mt5",
        "symbol": "EURUSD",
        "data_kind": "bars",
        "timeframe": "M1",
        "start": _PAST,
        "end": _NOW,
        "limit": 100,
        "use_cache": True,
        "quality_failure_behavior": "warn",
        "workflow_context": "research",
        "precision_policy": "decimal_string",
        "request_id": _REQ_ID,
    }
    defaults.update(kwargs)
    return MarketDataRequest(**defaults)


def test_default_ttl() -> None:
    """Test _default_ttl for ticks, daily bars, and intraday bars."""
    assert _default_ttl("ticks", None) == 900
    assert _default_ttl("bars", "D1") == 86400
    assert _default_ttl("bars", "M5") == 3600


def test_max_limit_unsupported_kind() -> None:
    """Test _max_limit raises UNSUPPORTED_OPERATION for invalid data_kind."""
    with pytest.raises(DataError) as exc_info:
        _max_limit("unsupported_kind")
    assert exc_info.value.code == "UNSUPPORTED_OPERATION"


def test_validate_record_limit_exceeded() -> None:
    """Test _validate_record_limit raises LIMIT_EXCEEDED when limit > max."""
    req = _make_market_data_req(
        data_kind="ticks",
        timeframe=None,
        limit=300_000,  # TICK_MAX_LIMIT is 250_000
    )
    with pytest.raises(DataError) as exc_info:
        _validate_record_limit(req)
    assert exc_info.value.code == "LIMIT_EXCEEDED"


def test_normalize_empty_records() -> None:
    """Test _normalize raises EMPTY_RESULT when raw_batch has no records."""
    raw_batch = MagicMock()
    raw_batch.records = ()

    req = _make_market_data_req()
    with pytest.raises(DataError) as exc_info:
        _normalize(raw_batch, req)
    assert exc_info.value.code == "EMPTY_RESULT"


def test_normalize_out_of_order_timestamps() -> None:
    """Test _normalize raises DATA_QUALITY_FAILED for out-of-order timestamps."""
    bar1 = {
        "timestamp": _NOW,
        "source": "mt5",
        "source_symbol": "EURUSD",
        "source_revision": "v1",
        "available_at": _NOW,
        "open": Decimal("1.0800"),
        "high": Decimal("1.0850"),
        "low": Decimal("1.0790"),
        "close": Decimal("1.0820"),
        "volume": Decimal(500),
        "price_unit": "USD",
        "volume_unit": "units",
    }
    bar2 = {**bar1, "timestamp": _NOW - timedelta(minutes=5)}  # Out of order timestamp

    raw_batch = MagicMock()
    raw_batch.records = (bar1, bar2)

    req = _make_market_data_req()
    with pytest.raises(DataError) as exc_info:
        _normalize(raw_batch, req)
    assert exc_info.value.code == "DATA_QUALITY_FAILED"


def test_require_acceptable_quality_reject() -> None:
    """
    Test _require_acceptable_quality raises DATA_QUALITY_FAILED when behavior is 'reject'.
    """
    ds = MagicMock()
    ds.quality_report.quality_status = "failed"
    issue = MagicMock()
    issue.code = "DUPLICATE_BARS"
    ds.quality_report.issues = [issue]
    ds.quality_report.quality_score = Decimal("0.0")
    ds.symbol = "EURUSD"
    ds.request_id = _REQ_ID

    with pytest.raises(DataError) as exc_info:
        _require_acceptable_quality(ds, "reject")
    assert exc_info.value.code == "DATA_QUALITY_FAILED"


def test_cached_dataset_incompatible_entry() -> None:
    """Test _cached_dataset returns None when entry source_revision is incompatible."""
    mock_entry = MagicMock()
    mock_entry.source_revision = "old_rev"  # Incompatible revision

    with patch(
        "app.services.data.market_data.pipeline.get_cache_entry",
        return_value=mock_entry,
    ):
        req = _make_market_data_req()
        assert _cached_dataset(req, "key1", "new_rev") is None


def test_fetch_market_dataset_ttl_exceeded() -> None:
    """Test fetch_market_dataset fails closed with LIMIT_EXCEEDED when cache_ttl_seconds > max."""
    req = _make_market_data_req(
        cache_ttl_seconds=1_000_000,  # CACHE_TTL_MAX_SECONDS is 604_800
    )
    response = fetch_market_dataset(req)
    assert response.status != "success"
    assert response.error is not None
    assert response.error.code == "LIMIT_EXCEEDED"


def test_reject_mixed_calls() -> None:
    """
    Test _reject_mixed raises VALIDATION_FAILED when request and keywords are both supplied.
    """
    req = _make_market_data_req()
    with pytest.raises(DataError) as exc_info:
        _reject_mixed(req, (None, "mt5"), _REQ_ID)
    assert exc_info.value.code == "VALIDATION_FAILED"


def test_market_request_kinds() -> None:
    """Test market_request resolution for ticks, spreads, and mismatched kind."""
    req_ticks = market_request(
        None,
        data_kind="ticks",
        source_id="mt5",
        symbol="EURUSD",
        timeframe=None,
        start=None,
        end=None,
        limit=10,
        use_cache=None,
        cache_ttl_seconds=None,
        quality_failure_behavior=None,
        workflow_context=None,
        precision_policy=None,
        stale_cache_policy=None,
        fallback_sources=None,
        source_timezone=None,
        request_id=_REQ_ID,
    )
    assert req_ticks.data_kind == "ticks"
    assert req_ticks.timeframe is None

    req_spreads = market_request(
        None,
        data_kind="spreads",
        source_id="mt5",
        symbol="EURUSD",
        timeframe=None,
        start=None,
        end=None,
        limit=10,
        use_cache=None,
        cache_ttl_seconds=None,
        quality_failure_behavior=None,
        workflow_context=None,
        precision_policy=None,
        stale_cache_policy=None,
        fallback_sources=None,
        source_timezone=None,
        request_id=_REQ_ID,
    )
    assert req_spreads.data_kind == "spreads"

    # Mismatched request.data_kind vs data_kind parameter
    req_bars = _make_market_data_req(data_kind="bars")
    with pytest.raises(DataError) as exc_info:
        market_request(
            req_bars,
            data_kind="ticks",
            source_id=None,
            symbol=None,
            timeframe=None,
            start=None,
            end=None,
            limit=None,
            use_cache=None,
            cache_ttl_seconds=None,
            quality_failure_behavior=None,
            workflow_context=None,
            precision_policy=None,
            stale_cache_policy=None,
            fallback_sources=None,
            source_timezone=None,
            request_id=_REQ_ID,
        )
    assert exc_info.value.code == "VALIDATION_FAILED"


def test_volume_request_missing_start_end() -> None:
    """Test volume_request raises VALIDATION_FAILED when start or end is missing."""
    with pytest.raises(DataError) as exc_info:
        volume_request(
            None,
            source_id="mt5",
            symbol="EURUSD",
            start=None,
            end=None,
            mode="summary",
            bucket_seconds=None,
            limit=10,
            request_id=_REQ_ID,
        )
    assert exc_info.value.code == "VALIDATION_FAILED"


def test_availability_request_creation() -> None:
    """Test availability_request helper with keyword args."""
    req = availability_request(
        None,
        source_id="mt5",
        symbol="EURUSD",
        data_kind="ohlcv",
        timeframe="M1",
        start=_PAST,
        end=_NOW,
        max_probe_records=500,
        request_id=_REQ_ID,
    )
    assert req.source_id == "mt5"
    assert req.symbol == "EURUSD"
    assert req.max_probe_records == 500


def test_public_facades_keyword_style() -> None:
    """Test get_market_data, get_tick_data, get_spread_data keyword invocations."""
    mock_ds = MagicMock()
    with (
        patch(
            "app.services.data.market_data.pipeline._fetch_market_dataset_raw",
            return_value=mock_ds,
        ),
        patch("app.services.data.sources.composition.ensure_storage"),
        patch("app.services.data.sources.composition.ensure_identity"),
    ):
        res1 = _unwrap(
            get_market_data(
                source_id="mt5", symbol="EURUSD", timeframe="M1", request_id=_REQ_ID
            )
        )
        assert res1 == mock_ds

        res2 = _unwrap(
            get_tick_data(source_id="mt5", symbol="EURUSD", request_id=_REQ_ID)
        )
        assert res2 == mock_ds

        res3 = _unwrap(
            get_spread_data(source_id="mt5", symbol="EURUSD", request_id=_REQ_ID)
        )
        assert res3 == mock_ds
