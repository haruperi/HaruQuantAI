"""Tests for the Phase 2.1-2.9 brownfield upgrade (DATA-UPG-016..054).

Covers: deterministic error mapping, official tool wrappers, import-safety/lazy
initialization, gateway hardening, persistence hardening, feed observability,
data quality/lineage metadata, and transform hardening. `contracts.py`'s
`BrokerMarketDataPort`/`SourceAdapterPort` protocols are covered separately in
`test_contracts_and_boundaries.py`.
"""

import time
from datetime import UTC, datetime
from typing import Any

import pandas as pd
import pytest
from app.services.data.errors import DATA_ERROR_CODES, to_data_error_payload
from app.services.data.feeds import (
    DEFAULT_FEED_BUFFER_CAPACITY,
    DEFAULT_HEARTBEAT_TIMEOUT_SECONDS,
    DEFAULT_RECONNECT_POLICY,
    ReconnectPolicy,
    check_feed_buffer_capacity,
    check_feed_heartbeat_timeout,
    compute_reconnect_delay,
    record_feed_heartbeat,
    register_mock_feed,
)
from app.services.data.gateway import get_data, get_data_with_metadata
from app.services.data.models import DataLineage, DataQualitySummary
from app.services.data.normalization import (
    build_data_quality_flags,
    resolve_volume_kind,
    summarize_data_quality,
)
from app.services.data.public_api import (
    get_data_tool,
    get_feed_status_tool,
    get_market_hours_tool,
    list_symbols_tool,
)
from app.services.data.scheduler import (
    initialize_data_scheduler,
    recover_data_jobs_on_startup,
)
from app.services.data.storage import (
    DatabaseHelper,
    PersistenceResult,
    compute_raw_hash,
    generate_cache_key,
    get_db_helper,
    set_cached_data,
)
from app.services.data.transforms import resample_ohlcv
from app.services.data.validation import (
    RESAMPLE_PERFORMANCE_BENCHMARK_BARS,
    RESAMPLE_PERFORMANCE_THRESHOLD_SECONDS,
    validate_stale_data_behavior,
    validate_workflow_context,
)
from app.utils.errors import APPROVED_ERROR_CODES, ValidationError
from app.utils.standard import StandardErrorPayload, validate_standard_response


def _as_dict(value: object) -> dict[str, Any]:
    """Narrow a standard-envelope `data` payload to a typed dict for assertions."""
    assert isinstance(value, dict)
    return value


def _as_error(value: StandardErrorPayload | None) -> StandardErrorPayload:
    """Narrow a standard-envelope `error` payload for assertions."""
    assert value is not None
    return value


# --- DATA-UPG-017: errors.py deterministic mapping ---------------------------
def test_data_error_codes_are_approved_and_mapping_is_redacted() -> None:
    """Verify DATA_ERROR_CODES is a subset of the approved registry."""
    assert DATA_ERROR_CODES.issubset(APPROVED_ERROR_CODES)
    assert "UNSUPPORTED_TIMEFRAME" in DATA_ERROR_CODES
    assert "DATA_SERIALIZATION_FAILED" in APPROVED_ERROR_CODES

    payload = to_data_error_payload(
        ValidationError("secret password=hunter2 leaked"), request_id="err-test"
    )
    assert payload["code"] == "VALIDATION_FAILED"
    assert "hunter2" not in payload["details"]


# --- DATA-UPG-018/019: public_api.py official wrappers -----------------------
def test_get_data_tool_returns_success_envelope_with_lineage() -> None:
    """Verify get_data_tool returns a valid standard envelope with metadata."""
    response = get_data_tool(
        symbol="EURUSD",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T02:00:00Z",
        data_kind="ohlcv",
        timeframe="M30",
        source="synthetic",
        request_id="tool-test",
    )
    validate_standard_response(response)
    assert response["status"] == "success"
    data = _as_dict(response["data"])
    assert isinstance(data["records"], list)
    assert data["result_metadata"]["source"] == "synthetic"
    assert response["metadata"]["tool_name"] == "get_data_tool"
    assert response["metadata"]["request_id"] == "tool-test"


def test_get_data_tool_returns_deterministic_error_envelope() -> None:
    """Verify get_data_tool never leaks a raw exception to the boundary."""
    response = get_data_tool(
        symbol="EURUSD",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T02:00:00Z",
        data_kind="unsupported_kind",
        source="synthetic",
    )
    validate_standard_response(response)
    assert response["status"] == "error"
    assert _as_error(response["error"])["code"] == "UNSUPPORTED_OPERATION"


def test_list_symbols_tool_and_get_market_hours_tool_success() -> None:
    """Verify list_symbols_tool and get_market_hours_tool succeed."""
    symbols_response = list_symbols_tool(source="synthetic")
    validate_standard_response(symbols_response)
    assert symbols_response["status"] == "success"
    assert "EURUSD" in _as_dict(symbols_response["data"])["symbols"]

    hours_response = get_market_hours_tool("EURUSD")
    validate_standard_response(hours_response)
    assert _as_dict(hours_response["data"])["symbol"] == "EURUSD"


def test_get_feed_status_tool_success_and_error() -> None:
    """Verify get_feed_status_tool wraps native feed status both ways."""
    register_mock_feed("tool_feed", "mt5", "EURUSD", "ticks")
    ok = get_feed_status_tool(feed_id="tool_feed")
    validate_standard_response(ok)
    assert ok["status"] == "success"
    assert _as_dict(ok["data"])["feeds"][0]["feed_id"] == "tool_feed"

    err = get_feed_status_tool(feed_id="does_not_exist_feed")
    validate_standard_response(err)
    assert err["status"] == "error"
    assert _as_error(err["error"])["code"] == "DATA_NOT_FOUND"


# --- DATA-UPG-020: __init__ OFFICIAL_DATA_TOOLS catalog -----------------------
def test_official_data_tools_catalog_matches_official_tool_names() -> None:
    """Verify OFFICIAL_DATA_TOOLS catalog covers exactly the official tool names."""
    import app.services.data as data_service

    assert (
        set(data_service.OFFICIAL_DATA_TOOLS) == data_service.OFFICIAL_DATA_TOOL_NAMES
    )
    for wrapper in data_service.OFFICIAL_DATA_TOOLS.values():
        assert callable(wrapper)
    # Adding the catalog must not perturb the frozen native export surface.
    assert len(data_service.__all__) == 23


# --- DATA-UPG-021/022/023: import safety and lazy initialization -------------
def test_database_helper_construction_performs_no_io(tmp_path: object) -> None:
    """Verify constructing DatabaseHelper performs no filesystem I/O."""
    from pathlib import Path

    db_path = Path(str(tmp_path)) / "nested" / "lazy_test.db"
    helper = DatabaseHelper(db_path=str(db_path))
    assert not db_path.parent.exists()
    with helper.get_connection() as conn:
        conn.execute("SELECT 1;")
    assert db_path.parent.exists()
    assert db_path.exists()


def test_get_db_helper_returns_shared_singleton() -> None:
    """Verify get_db_helper() returns the same compatibility singleton."""
    from app.services.data.storage import db_helper

    assert get_db_helper() is db_helper


def test_recover_data_jobs_on_startup_is_explicit_and_aliased() -> None:
    """Verify startup recovery is explicit and returns a count."""
    assert initialize_data_scheduler is recover_data_jobs_on_startup
    count = recover_data_jobs_on_startup()
    assert isinstance(count, int)
    assert count >= 0


# --- DATA-UPG-024/025/026/028: gateway validation hardening -------------------
def test_validate_workflow_context_accepts_approved_and_rejects_unknown() -> None:
    """Verify workflow_context validation is exhaustive and deterministic."""
    assert validate_workflow_context("risk") == "risk"
    with pytest.raises(ValidationError) as exc_info:
        validate_workflow_context("not_a_context")
    assert exc_info.value.code == "INVALID_INPUT"


def test_validate_stale_data_behavior_accepts_approved_and_rejects_unknown() -> None:
    """Verify stale_data_behavior validation is exhaustive and deterministic."""
    assert validate_stale_data_behavior("return_stale") == "return_stale"
    with pytest.raises(ValidationError) as exc_info:
        validate_stale_data_behavior("bogus_policy")
    assert exc_info.value.code == "INVALID_INPUT"


def test_get_data_rejects_reversed_or_equal_time_range() -> None:
    """Verify start_time must be strictly before end_time."""
    with pytest.raises(ValidationError, match="strictly before"):
        get_data(
            symbol="EURUSD",
            start_time="2026-06-02T00:00:00Z",
            end_time="2026-06-01T00:00:00Z",
            data_kind="ohlcv",
            timeframe="M1",
            source="synthetic",
        )
    with pytest.raises(ValidationError, match="strictly before"):
        get_data(
            symbol="EURUSD",
            start_time="2026-06-01T00:00:00Z",
            end_time="2026-06-01T00:00:00Z",
            data_kind="ticks",
            source="synthetic",
        )


def test_get_data_rejects_invalid_workflow_context_and_stale_behavior() -> None:
    """Verify get_data enforces workflow_context/stale_data_behavior at the boundary."""
    with pytest.raises(ValidationError):
        get_data(
            symbol="EURUSD",
            start_time="2026-06-01T00:00:00Z",
            end_time="2026-06-01T01:00:00Z",
            data_kind="ohlcv",
            timeframe="M1",
            source="synthetic",
            workflow_context="not_a_context",
        )
    with pytest.raises(ValidationError):
        get_data(
            symbol="EURUSD",
            start_time="2026-06-01T00:00:00Z",
            end_time="2026-06-01T01:00:00Z",
            data_kind="ohlcv",
            timeframe="M1",
            source="synthetic",
            stale_data_behavior="not_a_policy",
        )


# --- DATA-UPG-027/029/046/047: gateway result metadata + lineage -------------
def test_get_data_with_metadata_reports_lineage_without_changing_native_shape() -> None:
    """Verify get_data_with_metadata wraps get_data without altering its shape."""
    native_records = get_data(
        symbol="EURUSD",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T02:00:00Z",
        data_kind="ohlcv",
        timeframe="M30",
        source="synthetic",
        request_id="meta-test-native",
    )
    records, meta = get_data_with_metadata(
        symbol="EURUSD",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T02:00:00Z",
        data_kind="ohlcv",
        timeframe="M30",
        source="synthetic",
        request_id="meta-test-native",
    )
    assert isinstance(records, list)
    assert isinstance(native_records, list)
    assert records
    assert native_records
    assert set(records[0]) == set(native_records[0])

    for key in (
        "source",
        "symbol",
        "timeframe",
        "data_kind",
        "record_count",
        "volume_kind",
        "schema_version",
        "normalization_version",
        "raw_hash",
        "cache_status",
        "data_quality",
        "retrieval_timestamp",
        "license",
        "warnings",
    ):
        assert key in meta

    assert meta["record_count"] == len(records)
    assert meta["cache_status"] in ("hit", "miss")
    # DataLineage validates the disclosed lineage subset of the metadata.
    lineage = DataLineage(
        source=meta["source"],
        symbol=meta["symbol"],
        timeframe=meta["timeframe"],
        data_kind=meta["data_kind"],
        record_count=meta["record_count"],
        volume_kind=meta["volume_kind"],
        schema_version=meta["schema_version"],
        normalization_version=meta["normalization_version"],
        raw_hash=meta["raw_hash"],
        cache_status=meta["cache_status"],
        retrieval_timestamp=meta["retrieval_timestamp"],
    )
    assert lineage.source == "synthetic"

    quality_summary = DataQualitySummary(**meta["data_quality"])
    assert quality_summary.flagged_record_count >= 0


def test_get_data_availability_reports_gap_windows_from_cache(monkeypatch) -> None:
    """Verify get_data_availability surfaces internal gap windows."""
    from app.services.data.gateway import get_data_availability

    get_data(
        symbol="GAPTEST",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T01:00:00Z",
        data_kind="ohlcv",
        timeframe="M1",
        source="synthetic",
    )
    availability = get_data_availability(
        symbol="GAPTEST", timeframe="M1", source="synthetic"
    )
    assert availability["symbol"] == "GAPTEST"
    assert isinstance(availability["gap_windows"], list)
    assert availability["gap_count"] == len(availability["gap_windows"])


# --- DATA-UPG-034/035/036/038: storage persistence hardening -----------------
def test_set_cached_data_distinguishes_insert_update_no_op() -> None:
    """Verify set_cached_data reports insert/update/no_op outcomes."""
    key = generate_cache_key("csv", "PERSISTTEST", "M1", "2026-01-01", "2026-01-02")
    records_a = [{"timestamp": "2026-01-01T00:00:00Z", "close": 1.0}]
    records_b = [{"timestamp": "2026-01-01T00:00:00Z", "close": 2.0}]

    first = set_cached_data(
        key, "csv", "PERSISTTEST", "M1", "2026-01-01", "2026-01-02", records_a, 60
    )
    assert isinstance(first, PersistenceResult)
    assert first.operation == "insert"

    same = set_cached_data(
        key, "csv", "PERSISTTEST", "M1", "2026-01-01", "2026-01-02", records_a, 60
    )
    assert same.operation == "no_op"

    changed = set_cached_data(
        key, "csv", "PERSISTTEST", "M1", "2026-01-01", "2026-01-02", records_b, 60
    )
    assert changed.operation == "update"


def test_compute_raw_hash_is_deterministic_and_order_sensitive() -> None:
    """Verify compute_raw_hash is deterministic and content-sensitive."""
    records = [{"close": 1.0, "timestamp": "2026-01-01T00:00:00Z"}]
    first_hash = compute_raw_hash(records)
    second_hash = compute_raw_hash(records)
    assert first_hash == second_hash

    different_hash = compute_raw_hash(
        [{"close": 2.0, "timestamp": "2026-01-01T00:00:00Z"}]
    )
    assert different_hash != first_hash


def test_get_data_propagates_raw_hash_into_cache() -> None:
    """Verify execute_gateway_request writes a computed raw_hash into the cache row."""
    from app.services.data.storage import db_helper

    get_data(
        symbol="RAWHASHTEST",
        start_time="2026-06-01T00:00:00Z",
        end_time="2026-06-01T01:00:00Z",
        data_kind="ohlcv",
        timeframe="M1",
        source="synthetic",
    )
    with db_helper.get_connection() as conn:
        cursor = conn.execute(
            "SELECT raw_hash FROM data_cache WHERE source='synthetic' "
            "AND symbol='RAWHASHTEST';"
        )
        row = cursor.fetchone()
    assert row is not None
    assert row["raw_hash"] is not None


def test_sys_migrations_records_audit_columns() -> None:
    """Verify migration auditing records source/target version and rollback notes."""
    from app.services.data.storage import db_helper

    with db_helper.get_connection() as conn:
        cursor = conn.execute(
            "SELECT migration_id, source_version, target_version, rollback_notes "
            "FROM sys_migrations WHERE migration_id = 'mig_002_migration_audit';"
        )
        row = cursor.fetchone()
    assert row is not None
    assert row["source_version"] == 1
    assert row["target_version"] == 2
    assert row["rollback_notes"]


def test_database_connection_closes_on_success_and_failure() -> None:
    """Verify get_connection closes the underlying sqlite3 connection either way."""
    import sqlite3

    from app.services.data.storage import db_helper
    from app.utils.errors import DataError

    captured: list[sqlite3.Connection] = []
    with db_helper.get_connection() as conn:
        captured.append(conn)
        conn.execute("SELECT 1;")
    with pytest.raises(sqlite3.ProgrammingError):
        captured[0].execute("SELECT 1;")  # closed after success

    captured.clear()

    def _fail_inside_transaction() -> None:
        with db_helper.get_connection() as conn:
            captured.append(conn)
            conn.execute("SELECT * FROM this_table_does_not_exist;")

    with pytest.raises(DataError):
        _fail_inside_transaction()
    with pytest.raises(sqlite3.ProgrammingError):
        captured[0].execute("SELECT 1;")  # closed after failure too


# --- DATA-UPG-039..043: feeds.py bounded buffer/heartbeat/reconnect ----------
def test_check_feed_buffer_capacity_bounds() -> None:
    """Verify buffer capacity check flags over-capacity feeds."""
    assert check_feed_buffer_capacity({"buffer_depth": 0}) is True
    assert (
        check_feed_buffer_capacity({"buffer_depth": DEFAULT_FEED_BUFFER_CAPACITY})
        is True
    )
    assert (
        check_feed_buffer_capacity({"buffer_depth": DEFAULT_FEED_BUFFER_CAPACITY + 1})
        is False
    )


def test_check_feed_heartbeat_timeout_detects_stale_and_missing() -> None:
    """Verify heartbeat timeout detection for fresh, stale, and missing feeds."""
    now = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)
    fresh = {"last_heartbeat": now.isoformat()}
    assert check_feed_heartbeat_timeout(fresh, now=now) is False

    stale = {"last_heartbeat": "2020-01-01T00:00:00+00:00"}
    assert check_feed_heartbeat_timeout(stale, now=now) is True

    assert check_feed_heartbeat_timeout({}, now=now) is True


def test_reconnect_policy_backoff_grows_and_rejects_exhausted_attempts() -> None:
    """Verify reconnect delay grows with attempt number and enforces max_retries."""
    policy = ReconnectPolicy(
        max_retries=3,
        base_backoff_seconds=1.0,
        max_backoff_seconds=10.0,
        jitter_ratio=0.0,
    )
    delay_0 = compute_reconnect_delay(0, policy)
    delay_1 = compute_reconnect_delay(1, policy)
    assert delay_0 == pytest.approx(1.0)
    assert delay_1 == pytest.approx(2.0)
    with pytest.raises(ValidationError) as exc_info:
        compute_reconnect_delay(policy.max_retries, policy)
    assert exc_info.value.code == "FEED_RECONCILIATION_FAILED"

    assert DEFAULT_RECONNECT_POLICY.max_retries == 5


def test_record_feed_heartbeat_renews_timestamp_and_rejects_unknown_feed() -> None:
    """Verify record_feed_heartbeat renews an existing feed's heartbeat."""
    register_mock_feed("heartbeat_feed", "mt5", "EURUSD", "ticks")
    updated = record_feed_heartbeat("heartbeat_feed")
    assert updated["feed_id"] == "heartbeat_feed"

    with pytest.raises(ValidationError):
        record_feed_heartbeat("no_such_feed_at_all")


def test_handle_feed_overflow_rejects_unsupported_policy() -> None:
    """Verify handle_feed_overflow rejects a policy outside the approved set."""
    from app.services.data.feeds import handle_feed_overflow

    register_mock_feed("bad_policy_feed", "mt5", "EURUSD", "ticks")
    with pytest.raises(ValidationError, match="Unsupported overflow policy"):
        handle_feed_overflow("bad_policy_feed", "not_a_real_policy")  # type: ignore[arg-type]


def test_get_feed_status_filters_by_source_symbol_via_database_fallback() -> None:
    """Verify feed lookup falls back to the DB and applies source/symbol filters."""
    from app.services.data.feeds import ACTIVE_FEEDS, _get_feeds_from_db

    register_mock_feed("db_filter_feed", "dukascopy", "USDJPY", "ohlcv")
    # Force the DB fallback path by clearing the in-memory cache for this feed.
    ACTIVE_FEEDS.pop("db_filter_feed", None)

    by_source = _get_feeds_from_db(source="dukascopy")
    assert any(f["feed_id"] == "db_filter_feed" for f in by_source)

    by_symbol = _get_feeds_from_db(symbol="usdjpy")
    assert any(f["feed_id"] == "db_filter_feed" for f in by_symbol)

    by_data_kind = _get_feeds_from_db(data_kind="OHLCV")
    assert any(f["feed_id"] == "db_filter_feed" for f in by_data_kind)

    no_match = _get_feeds_from_db(source="mt5", symbol="usdjpy")
    assert all(f["feed_id"] != "db_filter_feed" for f in no_match)


def test_get_feed_status_exposes_buffer_and_heartbeat_diagnostics() -> None:
    """Verify get_feed_status enriches results with observability diagnostics."""
    from app.services.data.scheduler import get_feed_status

    register_mock_feed("enriched_feed", "ctrader", "GBPUSD", "ticks", buffer_depth=1)
    result = _as_dict(get_feed_status(feed_id="enriched_feed"))
    assert result["buffer_capacity"] == DEFAULT_FEED_BUFFER_CAPACITY
    assert result["within_buffer_capacity"] is True
    assert result["heartbeat_timeout_seconds"] == DEFAULT_HEARTBEAT_TIMEOUT_SECONDS
    assert result["heartbeat_timed_out"] is False


# --- DATA-UPG-044/046: data quality flags + volume kind disclosure -----------
def test_build_data_quality_flags_detects_known_issues() -> None:
    """Verify quality flags detect duplicate/non-monotonic/invalid values."""
    assert build_data_quality_flags({}) == ["missing_field"]

    ok = {"timestamp": "2026-01-01T00:00:00Z", "close": 1.1}
    assert build_data_quality_flags(ok, previous_timestamp="2026-01-01T00:00:00Z") == [
        "duplicate_timestamp"
    ]
    assert build_data_quality_flags(ok, previous_timestamp="2026-01-01T00:05:00Z") == [
        "non_monotonic_timestamp"
    ]

    negative = {"timestamp": "2026-01-01T00:00:00Z", "close": -1.0}
    assert "negative_price" in build_data_quality_flags(negative)

    zero = {"timestamp": "2026-01-01T00:00:00Z", "close": 0.0}
    assert "zero_price" in build_data_quality_flags(zero)

    non_finite = {"timestamp": "2026-01-01T00:00:00Z", "close": float("nan")}
    assert "non_finite_price" in build_data_quality_flags(non_finite)

    bad_ohlc = {"timestamp": "2026-01-01T00:00:00Z", "high": 1.0, "low": 2.0}
    assert "out_of_range_ohlc" in build_data_quality_flags(bad_ohlc)

    inverted = {"timestamp": "2026-01-01T00:00:00Z", "bid": 1.2, "ask": 1.1}
    assert "inverted_bid_ask" in build_data_quality_flags(inverted)


def test_summarize_data_quality_counts_flags_across_batch() -> None:
    """Verify summarize_data_quality aggregates counts across a record batch."""
    records = [
        {"timestamp": "2026-01-01T00:00:00Z", "close": 1.0},
        {"timestamp": "2026-01-01T00:00:00Z", "close": 1.0},  # duplicate timestamp
        {"timestamp": "2026-01-01T00:05:00Z", "close": -1.0},  # negative price
    ]
    summary = summarize_data_quality(records)
    assert summary["flagged_record_count"] == 2
    assert summary["flag_counts"]["duplicate_timestamp"] == 1
    assert summary["flag_counts"]["negative_price"] == 1


def test_resolve_volume_kind_disclosure_by_source() -> None:
    """Verify volume kind disclosure differs by source and data kind."""
    assert resolve_volume_kind("synthetic", "ohlcv") == "synthetic_volume"
    assert resolve_volume_kind("mt5", "ohlcv") == "broker_volume"
    assert resolve_volume_kind("csv", "ohlcv") == "tick_volume"
    assert resolve_volume_kind("csv", "ticks") == "unknown"


# --- DATA-UPG-048..051: transform hardening ----------------------------------
def test_align_multitimeframe_data_never_leaks_future_bar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify no-lookahead alignment never exposes an unclosed future bar."""
    from app.services.data.transforms import (
        align_multitimeframe_data,
        generate_synthetic_bars,
    )

    bars = generate_synthetic_bars(
        "EURUSD", "M5", "2026-01-01T00:00:00Z", 3, 1.1, 0.0, 0.01, seed=7
    )
    # Target exactly at the second bar's open time: only the first (closed) bar
    # may be visible, never the second bar that has not closed yet.
    aligned = align_multitimeframe_data(
        {"M5": bars}, [bars[1]["timestamp"]], allow_lookahead=False
    )
    assert aligned["M5"][0]["bar_open_timestamp"] == bars[0]["timestamp"]
    assert aligned["M5"][0]["close"] == bars[0]["close"]


def test_generate_synthetic_bars_deterministic_with_seed() -> None:
    """Verify seeded synthetic generation is fully deterministic."""
    from app.services.data.transforms import generate_synthetic_bars

    first = generate_synthetic_bars(
        "EURUSD", "M1", "2026-01-01T00:00:00Z", 50, 1.1, 0.0001, 0.001, seed=123
    )
    second = generate_synthetic_bars(
        "EURUSD", "M1", "2026-01-01T00:00:00Z", 50, 1.1, 0.0001, 0.001, seed=123
    )
    assert first == second


def test_resample_ohlcv_performance_benchmark() -> None:
    """Verify resampling 100,000 M1 bars to H1 stays under the approved threshold."""
    base = pd.Timestamp("2026-01-01T00:00:00Z")
    records = [
        {
            "timestamp": (base + pd.Timedelta(minutes=i)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "open": 1.1,
            "high": 1.2,
            "low": 1.0,
            "close": 1.15,
            "volume": 10.0,
            "tick_volume": 10.0,
            "real_volume": 0.0,
            "spread": 1.0,
            "symbol": "EURUSD",
            "source": "synthetic",
            "timeframe": "M1",
        }
        for i in range(RESAMPLE_PERFORMANCE_BENCHMARK_BARS)
    ]

    start = time.perf_counter()
    resampled = resample_ohlcv(records, "H1")
    elapsed = time.perf_counter() - start

    assert len(resampled) > 0
    assert elapsed < RESAMPLE_PERFORMANCE_THRESHOLD_SECONDS


def test_transform_outputs_are_json_safe_and_preserve_identity_fields() -> None:
    """Verify transform outputs contain no raw numpy scalars and keep identity
    fields."""
    from app.services.data.transforms import generate_synthetic_bars, resample_ohlcv

    bars = generate_synthetic_bars(
        "EURUSD", "M1", "2026-01-01T00:00:00Z", 20, 1.1, 0.0, 0.001, seed=1
    )
    resampled = resample_ohlcv(bars, "M5")
    assert resampled
    for record in resampled:
        assert record["symbol"] == "EURUSD"
        assert record["timeframe"] == "M5"
        assert record["source"] == "synthetic"
        assert isinstance(record["timestamp"], str)
        for key in ("open", "high", "low", "close", "volume"):
            assert type(record[key]) in (int, float)
