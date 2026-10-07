"""Unit tests for app/host/logging.py.

Verifies centralized telemetry, secret/path redaction, rotating ZIP storage,
bounded ring buffer with cursor tracking, DebugConsole FastAPI projections,
request correlation contextvars, and standard library handler bridges.
"""

from __future__ import annotations

import json
import logging
import zipfile
from pathlib import Path
from typing import Any

import pytest
from app.host.logging import (
    BoundLogger,
    LogRingBuffer,
    RotatingZipSink,
    TelemetryEngine,
    bridge_standard_logging,
    configure_host_logging,
    create_debug_console_router,
    fingerprint_secret,
    flush,
    get_logger,
    parse_log_level,
    redact_paths,
    redact_secrets,
    request_context,
    reset_logging,
    safe_error_boundary,
    sanitize_payload,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clean_logging_state() -> Any:
    """Ensure telemetry engine is reset before and after every test."""
    reset_logging()
    yield
    reset_logging()


def test_parse_log_level() -> None:
    """Verify string and integer log level parsing."""
    assert parse_log_level("DEBUG") == logging.DEBUG
    assert parse_log_level("info") == logging.INFO
    assert parse_log_level("WARNING") == logging.WARNING
    assert parse_log_level("ERROR") == logging.ERROR
    assert parse_log_level("CRITICAL") == logging.CRITICAL
    assert parse_log_level("UNKNOWN") == logging.INFO
    assert parse_log_level(logging.DEBUG) == logging.DEBUG


def test_secret_fingerprinting_and_redaction() -> None:
    """Verify deterministic SHA-256 fingerprinting and credential redaction."""
    raw_secret = "mySuperSecretPassword123"
    fp = fingerprint_secret(raw_secret)
    assert fp.startswith("[REDACTED:")
    assert fp.endswith("]")
    assert len(fp) == 23  # [REDACTED: + 12 hex chars + ]

    # Idempotent
    assert fingerprint_secret(fp) == fp

    # Redact key-value assignment patterns
    text1 = 'Connecting with password="mySuperSecretPassword123" to host'
    redacted1 = redact_secrets(text1)
    assert 'password="' in redacted1
    assert "mySuperSecretPassword123" not in redacted1
    assert fp in redacted1

    text2 = "API call with api_key: 'sk_live_998877665544'"
    redacted2 = redact_secrets(text2)
    assert "sk_live_998877665544" not in redacted2
    assert "[REDACTED:" in redacted2

    # Redact Bearer tokens
    text3 = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    redacted3 = redact_secrets(text3)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted3
    assert "Bearer [REDACTED:" in redacted3

    # Empty string handling
    assert redact_secrets("") == ""


def test_path_redaction() -> None:
    """Verify physical filesystem path redaction across Windows and POSIX."""
    win_path = r"Error loading model from C:\Users\rharu\AppData\secret\weights.bin"
    redacted_win = redact_paths(win_path)
    assert r"C:\Users\rharu" not in redacted_win
    assert "[PATH:weights.bin]" in redacted_win

    posix_path = "Reading config from /home/ubuntu/production/secret.env"
    redacted_posix = redact_paths(posix_path)
    assert "/home/ubuntu" not in redacted_posix
    assert "[PATH:secret.env]" in redacted_posix

    # Combined with redact_secrets
    combined = r'Failed for token="secret_tok" at C:\Users\admin\Desktop\run.py'
    redacted_combined = redact_secrets(combined)
    assert "secret_tok" not in redacted_combined
    assert "[REDACTED:" in redacted_combined
    assert "[PATH:run.py]" in redacted_combined


def test_sanitize_payload_recursive() -> None:
    """Verify recursive data structure sanitization and depth limiting."""
    payload: dict[str, Any] = {
        "password": "plain_password",
        "api_key": "raw_api_key",
        "nested": {
            "token": "nested_token",
            "safe_val": 42,
            "path": r"C:\data\trade.csv",
        },
        "items": [
            "normal_item",
            {"secret": "item_secret"},
        ],
    }

    sanitized = sanitize_payload(payload)
    assert isinstance(sanitized, dict)
    assert sanitized["password"].startswith("[REDACTED:")
    assert sanitized["api_key"].startswith("[REDACTED:")
    assert sanitized["nested"]["safe_val"] == 42
    assert sanitized["nested"]["token"].startswith("[REDACTED:")
    assert "[PATH:trade.csv]" in sanitized["nested"]["path"]
    assert sanitized["items"][1]["secret"].startswith("[REDACTED:")

    # Test depth limiting
    deep: dict[str, Any] = {}
    curr = deep
    for _ in range(12):
        curr["next"] = {}
        curr = curr["next"]
    deep_sanitized = sanitize_payload(deep)
    assert isinstance(deep_sanitized, dict)


def test_safe_error_boundary() -> None:
    """Verify exception diagnostics extraction and secret scrubbing."""
    try:
        raise ValueError(
            'Failed connecting with password="super_secret_db_pass" at line 1'
        )
    except ValueError as exc:
        diag = safe_error_boundary(exc)

    assert diag["type"] == "ValueError"
    assert "super_secret_db_pass" not in str(diag["message"])
    assert "[REDACTED:" in str(diag["message"])
    assert isinstance(diag["frames"], list)
    assert len(diag["frames"]) > 0


def test_rotating_zip_sink(tmp_path: Path) -> None:
    """Verify byte-limit rotation, deflated ZIP compression, and retention."""
    log_file = tmp_path / "test.log"
    # Small max_bytes to trigger rotation after a few lines
    sink = RotatingZipSink(log_file, max_bytes=150, retention_days=10)

    # Write multiple lines
    for i in range(15):
        sink.write(f"Log line number {i:03d} with padding data to exceed size")

    sink.close()

    # Verify at least one zip file was created in tmp_path
    zip_files = list(tmp_path.glob("test_*.zip"))
    assert len(zip_files) > 0

    # Verify zip content
    with zipfile.ZipFile(zip_files[0], "r") as zf:
        namelist = zf.namelist()
        assert len(namelist) == 1
        assert namelist[0].startswith("test_")
        assert namelist[0].endswith(".log")

    # Verify pruning expired archives
    sink.prune_expired_archives()


def test_ring_buffer_cursors_and_gaps() -> None:
    """Verify in-memory ring buffer monotonic cursors, capacity, and gap flags."""
    buffer = LogRingBuffer(capacity=5)

    assert buffer.get_categories() == ["All", "Application", "System"]

    # Emitting events
    from datetime import UTC, datetime

    from app.host.logging import LogEvent

    for i in range(3):
        buffer.append(
            LogEvent(
                timestamp=datetime.now(UTC),
                level="INFO",
                namespace="test",
                module="test_mod",
                function="test_fn",
                line=10,
                message=f"Message {i}",
                context={},
                error=None,
                category="Jobs",
            )
        )

    assert "Jobs" in buffer.get_categories()

    # Query snapshot
    snap1 = buffer.get_snapshot(after_cursor=None, category="All")
    assert snap1.total_retained == 3
    assert snap1.oldest_cursor == 1
    assert snap1.newest_cursor == 3
    assert not snap1.has_gap
    assert len(snap1.entries) == 3
    assert snap1.entries[0].cursor == 1
    assert snap1.entries[0].id == "log-1"

    # Query with after_cursor=1
    snap2 = buffer.get_snapshot(after_cursor=1)
    assert len(snap2.entries) == 2
    assert snap2.entries[0].cursor == 2
    assert not snap2.has_gap

    # Overflow buffer (capacity is 5; push 5 more events, total 8)
    for i in range(3, 8):
        buffer.append(
            LogEvent(
                timestamp=datetime.now(UTC),
                level="INFO",
                namespace="test",
                module="test_mod",
                function="test_fn",
                line=10,
                message=f"Message {i}",
                context={},
                error=None,
                category="Engine",
            )
        )

    # Now oldest_cursor should have advanced to 4
    snap3 = buffer.get_snapshot(after_cursor=1)
    assert snap3.has_gap  # cursor 1 < (oldest_cursor - 1)
    assert snap3.total_retained == 5
    assert snap3.oldest_cursor == 4
    assert snap3.newest_cursor == 8

    # Query with category filter
    snap_engine = buffer.get_snapshot(category="Engine")
    assert all(e.category == "Engine" for e in snap_engine.entries)

    # Query with text query
    snap_query = buffer.get_snapshot(query="message 7")
    assert len(snap_query.entries) == 1
    assert snap_query.entries[0].message == "Message 7"

    # Clear buffer
    high_watermark = buffer.clear()
    assert high_watermark == 8
    snap_after_clear = buffer.get_snapshot()
    assert len(snap_after_clear.entries) == 0


def test_telemetry_engine_multi_sink_routing(tmp_path: Path) -> None:
    """Verify asynchronous dispatching across app, access, debug, and error sinks."""
    engine = configure_host_logging(tmp_path, level="DEBUG")

    log_app = get_logger("app.core")
    log_access = get_logger("uvicorn.access")
    log_err = get_logger("app.error")

    log_app.debug("Debug telemetry message")
    log_app.info("Application started successfully")
    log_access.info("GET /api/v1/health HTTP/1.1", category="access")
    log_err.error("Database connection failure")

    assert flush(timeout=5.0)

    # Check file sink existence
    app_log = tmp_path / "app.log"
    debug_log = tmp_path / "debug.log"
    access_log = tmp_path / "access.log"
    errors_log = tmp_path / "errors.log"

    assert app_log.exists()
    assert debug_log.exists()
    assert access_log.exists()
    assert errors_log.exists()

    app_lines = [
        json.loads(line) for line in app_log.read_text(encoding="utf-8").splitlines()
    ]
    assert len(app_lines) == 4

    debug_lines = [
        json.loads(line) for line in debug_log.read_text(encoding="utf-8").splitlines()
    ]
    assert len(debug_lines) == 1
    assert debug_lines[0]["message"] == "Debug telemetry message"

    access_lines = [
        json.loads(line) for line in access_log.read_text(encoding="utf-8").splitlines()
    ]
    assert len(access_lines) == 1
    assert "/api/v1/health" in access_lines[0]["message"]

    error_lines = [
        json.loads(line) for line in errors_log.read_text(encoding="utf-8").splitlines()
    ]
    assert len(error_lines) == 1
    assert "Database connection failure" in error_lines[0]["message"]

    engine.shutdown()


def test_bound_logger_binding_and_context(tmp_path: Path) -> None:
    """Verify BoundLogger immutability, context merging, and extra attributes."""
    configure_host_logging(tmp_path)

    base_logger: BoundLogger = get_logger("test.bound")
    worker_logger = base_logger.bind(worker_id="w-01", env="test")

    # base_logger remains unchanged
    assert "worker_id" not in base_logger._context
    assert worker_logger._context.get("worker_id") == "w-01"

    worker_logger.info("Starting worker execution", extra={"task": "backtest"})
    assert flush(timeout=5.0)

    app_log = tmp_path / "app.log"
    lines = [
        json.loads(line_str)
        for line_str in app_log.read_text(encoding="utf-8").splitlines()
    ]
    assert len(lines) == 1
    ctx = lines[0].get("context", {})
    assert ctx.get("worker_id") == "w-01"
    assert ctx.get("task") == "backtest"


def test_request_context_propagation(tmp_path: Path) -> None:
    """Verify request correlation context propagates across async execution."""
    configure_host_logging(tmp_path)
    log = get_logger("test.correlation")

    log.info("Before correlation")

    with request_context(request_id="req-12345", user_id="u-88"):
        log.info("Inside correlated scope")

    log.info("After correlation")
    assert flush(timeout=5.0)

    app_log = tmp_path / "app.log"
    lines = [
        json.loads(line_str)
        for line_str in app_log.read_text(encoding="utf-8").splitlines()
    ]
    assert len(lines) == 3

    assert "request_id" not in lines[0].get("context", {})
    assert lines[1].get("context", {}).get("request_id") == "req-12345"
    assert lines[1].get("context", {}).get("user_id") == "u-88"
    assert "request_id" not in lines[2].get("context", {})


def test_host_bridge_handler_and_standard_logging(tmp_path: Path) -> None:
    """Verify interception and sanitization of standard-library loggers."""
    configure_host_logging(tmp_path)
    bridge_standard_logging(("third_party_lib", "uvicorn.error"))

    stdlib_logger = logging.getLogger("third_party_lib")
    stdlib_logger.info('Third party message with password="secret_library_pass"')

    assert flush(timeout=5.0)

    app_log = tmp_path / "app.log"
    lines = [
        json.loads(line_str)
        for line_str in app_log.read_text(encoding="utf-8").splitlines()
    ]
    assert len(lines) >= 1
    msg = lines[0]["message"]
    assert "secret_library_pass" not in msg
    assert "[REDACTED:" in msg


def test_debug_console_fastapi_router(tmp_path: Path) -> None:
    """Verify FastAPI DebugConsole REST endpoints and queries."""
    engine = configure_host_logging(tmp_path)
    router = create_debug_console_router(engine)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    log = get_logger("ui.test")
    log.info("First UI log entry", category="System")
    log.warning("Second UI warning", category="Engine")
    log.error("Third UI error", category="Jobs")
    assert flush(timeout=5.0)

    # 1. Query logs
    res1 = client.get("/api/v1/debugconsole/logs")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total_retained"] == 3
    assert len(data1["entries"]) == 3
    assert data1["entries"][0]["category"] == "System"

    # 2. Query with category filter
    res_cat = client.get("/api/v1/debugconsole/logs?category=Engine")
    assert res_cat.status_code == 200
    data_cat = res_cat.json()
    assert len(data_cat["entries"]) == 1
    assert data_cat["entries"][0]["message"] == "Second UI warning"

    # 3. Query with text query
    res_q = client.get("/api/v1/debugconsole/logs?query=third")
    assert res_q.status_code == 200
    data_q = res_q.json()
    assert len(data_q["entries"]) == 1
    assert data_q["entries"][0]["level"] == "ERROR"

    # 4. Query categories
    res_cats = client.get("/api/v1/debugconsole/categories")
    assert res_cats.status_code == 200
    cats = res_cats.json()
    assert "All" in cats
    assert "System" in cats
    assert "Engine" in cats
    assert "Jobs" in cats

    # 5. Clear logs
    res_clear = client.post("/api/v1/debugconsole/clear")
    assert res_clear.status_code == 200
    assert res_clear.json()["cleared"] is True

    # 6. Verify cleared logs
    res_after = client.get("/api/v1/debugconsole/logs")
    assert res_after.status_code == 200
    assert len(res_after.json()["entries"]) == 0

    # 7. Check legacy alias endpoint
    res_alias = client.get("/debugconsole/logs")
    assert res_alias.status_code == 200


def test_bound_logger_levels_and_formatting(tmp_path: Path) -> None:
    """Verify all levels, exception logging, and color-aware formatting."""
    configure_host_logging(tmp_path, level="DEBUG", use_color=True)

    log = get_logger("test.levels")
    log.critical("Critical security incident: breach detected")

    try:
        raise RuntimeError("Something exploded violently")
    except RuntimeError:
        log.exception("Encountered fatal crash")

    # Positional args formatting
    log.info("Formatted %s with count %d", "item", 42)

    assert flush(timeout=5.0)

    app_log = tmp_path / "app.log"
    errors_log = tmp_path / "errors.log"

    app_lines = [
        json.loads(line_str)
        for line_str in app_log.read_text(encoding="utf-8").splitlines()
    ]
    assert len(app_lines) == 3

    # Check critical in errors.log
    err_lines = [
        json.loads(line_str)
        for line_str in errors_log.read_text(encoding="utf-8").splitlines()
    ]
    assert len(err_lines) == 2
    assert err_lines[0]["level"] == "CRITICAL"
    assert err_lines[1]["level"] == "ERROR"
    assert err_lines[1]["error"]["type"] == "RuntimeError"


def test_telemetry_engine_state_and_backpressure(tmp_path: Path) -> None:
    """Verify engine singleton status, drops on saturated queue, and shutdown."""
    assert not TelemetryEngine.is_active()

    engine = configure_host_logging(tmp_path)
    assert TelemetryEngine.is_active()
    assert TelemetryEngine.is_configured()

    # Fill queue to simulate worker saturation
    from datetime import UTC, datetime

    from app.host.logging import LogEvent

    dummy_event = LogEvent(
        timestamp=datetime.now(UTC),
        level="INFO",
        namespace="test",
        module="test",
        function="test",
        line=1,
        message="dummy",
        context={},
        error=None,
        category="test",
    )

    # Put until queue is full
    for _ in range(engine.queue.maxsize + 20):
        engine.enqueue(dummy_event)

    # dropped_events should be non-zero
    assert engine.dropped_events > 0

    # Idempotent repeated shutdown
    assert engine.shutdown()
    assert engine.shutdown()
    assert not TelemetryEngine.is_active()
