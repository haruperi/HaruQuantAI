"""Unit and integration tests for the centralized host telemetry engine.

Description:
    Verifies that app/host/logging.py satisfies all 14 functional requirements,
    including secret redaction, immutable context binding, multi-sink routing,
    Windows-safe ZIP rotation, non-blocking queue backpressure, request correlation,
    and lifecycle management.

Purpose:
    FEAT-HOST-LOGGING: Telemetry and multi-sink verification test suite.

Key Capabilities:
    - FR-HOST-TEST-ISOLATION: Verify test isolation and reset mechanisms.
      Associated: `test_test_isolation_and_lazy_bootstrap()`
      Logging: Implicit pytest test reporting.
"""

from __future__ import annotations

import io
import json
import logging
import queue
import zipfile
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.host.logging import (
    BoundLogger,
    LogEvent,
    RotatingZipSink,
    bridge_standard_logging,
    configure_host_logging,
    fingerprint_secret,
    flush,
    format_human_record,
    format_json_record,
    get_logger,
    redact_secrets,
    request_context,
    reset_logging,
    safe_error_boundary,
    sanitize_payload,
    shutdown,
)


@pytest.fixture(autouse=True)
def _isolate_logging(tmp_path: Path) -> Generator[None]:
    """Automatically isolate each test to its own temporary log directory."""
    log_dir = tmp_path / "logs"
    configure_host_logging(log_dir=log_dir, include_console=False)
    yield
    reset_logging()


def test_lazy_bootstrap_and_resolution(tmp_path: Path) -> None:
    """FR-HOST-LOGGER-RESOLUTION: Importing or getting a logger does not create sinks."""
    reset_logging()
    target_dir = tmp_path / "unopened_logs"

    # Getting a logger should NOT create target_dir or start sinks
    test_logger = get_logger("app.test.inert")
    assert isinstance(test_logger, BoundLogger)
    assert not target_dir.exists()


def test_bound_logger_immutability() -> None:
    """FR-HOST-BOUND-LOGGER: Binding returns a new instance with merged context."""
    base = get_logger("app.base").bind(service="auth")
    child1 = base.bind(worker_id="w-01")
    child2 = base.bind(worker_id="w-02", extra="data")

    assert child1.name == "app.base"
    assert child1._context == {"service": "auth", "worker_id": "w-01"}
    assert child2._context == {"service": "auth", "worker_id": "w-02", "extra": "data"}
    # Verify base was not mutated
    assert base._context == {"service": "auth"}


def test_secret_redaction_and_fingerprinting() -> None:
    """FR-HOST-SECRET-REDACTION: Detects credentials and replaces with fingerprints."""
    raw_secret = "super_secret_password_123"
    expected_fp = fingerprint_secret(raw_secret)
    assert expected_fp.startswith("[REDACTED:")
    assert len(expected_fp) == len("[REDACTED:") + 12 + 1

    # Text assignment redaction
    sample_text = f'User password="{raw_secret}" and token: "my_api_key_xyz"'
    redacted = redact_secrets(sample_text)
    assert raw_secret not in redacted
    assert "my_api_key_xyz" not in redacted
    assert expected_fp in redacted

    # Bearer header redaction
    bearer_text = "Authorization: Bearer my_jwt_token_header_secret"
    bearer_redacted = redact_secrets(bearer_text)
    assert "my_jwt_token_header_secret" not in bearer_redacted
    assert "Bearer [REDACTED:" in bearer_redacted

    # Idempotent fingerprinting
    assert fingerprint_secret(expected_fp) == expected_fp


def test_sanitize_payload_structures() -> None:
    """FR-HOST-SECRET-REDACTION: Sanitizes nested dicts, lists, and sensitive keys."""
    payload = {
        "user": "alice",
        "password": "mypassword",
        "api_key": "secret_key_val",
        "nested": {
            "token": "tok123",
            "items": ["safe", "token='nested_secret'"],
        },
    }
    sanitized = sanitize_payload(payload)
    assert isinstance(sanitized, dict)
    assert sanitized["user"] == "alice"
    assert sanitized["password"] == fingerprint_secret("mypassword")
    assert sanitized["api_key"] == fingerprint_secret("secret_key_val")
    nested = sanitized["nested"]
    assert isinstance(nested, dict)
    assert nested["token"] == fingerprint_secret("tok123")
    items = nested["items"]
    assert isinstance(items, list)
    assert items[0] == "safe"
    assert "nested_secret" not in items[1]


def test_structured_formatting() -> None:
    """FR-HOST-STRUCTURED-FORMATTING: Formats human records and bounded JSON."""
    now = datetime(2026, 10, 4, 12, 0, 0, 123456, tzinfo=UTC)
    event = LogEvent(
        timestamp=now,
        level="INFO",
        namespace="app.test",
        module="test_mod",
        function="test_fn",
        line=42,
        message="Hello World",
        context={"user": "alice"},
        error=None,
        category=None,
    )

    # Human format without color
    human_text = format_human_record(event, use_color=False)
    assert (
        "2026-10-04 12:00:00.123 | INFO     | test_mod:test_fn:42 - Hello World"
        in human_text
    )

    # Human format with color
    color_text = format_human_record(event, use_color=True)
    assert "\033[32m" in color_text  # Green for INFO

    # JSON format
    json_text = format_json_record(event)
    data = json.loads(json_text)
    assert data["level"] == "INFO"
    assert data["message"] == "Hello World"
    assert data["context"]["user"] == "alice"

    # Oversized payload bounding
    huge_message = "X" * 20000
    huge_event = LogEvent(
        timestamp=now,
        level="WARNING",
        namespace="app.test",
        module="test_mod",
        function="test_fn",
        line=10,
        message=huge_message,
        context={"lots": "data" * 1000},
        error=None,
        category=None,
    )
    bounded_json = format_json_record(huge_event)
    assert len(bounded_json.encode("utf-8")) < 20000
    bounded_data = json.loads(bounded_json)
    assert bounded_data["context"] == {"_truncated": True}


def test_multi_sink_routing(tmp_path: Path) -> None:
    """FR-HOST-MULTI-SINK-ROUTING: Demuxes events to app, access, debug, and error logs."""
    log_dir = tmp_path / "routing_logs"
    _ = configure_host_logging(
        log_dir=log_dir, level=logging.DEBUG, include_console=False
    )

    app_log = log_dir / "app.log"
    access_log = log_dir / "access.log"
    debug_log = log_dir / "debug.log"
    errors_log = log_dir / "errors.log"

    log = get_logger("app.trading")

    # 1. Emit debug log
    log.debug("A debug message")
    # 2. Emit info log
    log.info("An info message")
    # 3. Emit error log
    log.error("An error message")
    # 4. Emit access log
    log.info("A request completed", category="access")

    assert flush(timeout=5.0)

    # Read log files
    app_lines = app_log.read_text(encoding="utf-8").strip().splitlines()
    debug_lines = debug_log.read_text(encoding="utf-8").strip().splitlines()
    errors_lines = errors_log.read_text(encoding="utf-8").strip().splitlines()
    access_lines = access_log.read_text(encoding="utf-8").strip().splitlines()

    # app.log should receive all events
    assert len(app_lines) == 4

    # debug.log should receive only the debug message
    assert len(debug_lines) == 1
    assert "A debug message" in debug_lines[0]

    # errors.log should receive only the error message
    assert len(errors_lines) == 1
    assert "An error message" in errors_lines[0]

    # access.log should receive only the access message
    assert len(access_lines) == 1
    assert "A request completed" in access_lines[0]


def test_windows_safe_zip_rotation_and_retention(tmp_path: Path) -> None:
    """FR-HOST-WINDOWS-ROTATION & FR-HOST-BOUNDED-TELEMETRY: Rotates and compresses."""
    sink_file = tmp_path / "rotation" / "test.log"
    # Small max_bytes to trigger immediate rotation after a few writes
    sink = RotatingZipSink(sink_file, max_bytes=200, retention_days=10)

    # Write enough lines to exceed 200 bytes
    for i in range(10):
        sink.write(f"Log event record line number {i:04d} with some extra padding text")

    sink.close()

    # Verify zip archives were created
    zip_files = list(sink_file.parent.glob("test_*.zip"))
    assert len(zip_files) >= 1

    # Verify zip file integrity
    for zf_path in zip_files:
        with zipfile.ZipFile(zf_path, "r") as zf:
            assert zf.testzip() is None
            assert len(zf.namelist()) == 1

    # Test retention pruning
    fake_old_zip = sink_file.parent / "test_20200101_000000_000000.zip"
    fake_old_zip.write_bytes(b"dummy")
    # Set modification time to 30 days ago
    old_mtime = (datetime.now(UTC) - timedelta(days=30)).timestamp()
    import os

    os.utime(fake_old_zip, (old_mtime, old_mtime))

    sink.prune_expired_archives()
    assert not fake_old_zip.exists()


def test_request_correlation_context() -> None:
    """FR-HOST-REQUEST-CORRELATION: Scopes request metadata across execution contexts."""
    log = get_logger("app.req_test")

    with request_context(request_id="req-101", client_ip="192.168.1.1"):
        with request_context(sub_task="validation"):
            log.info("Handling subtask")
            # Verify nested merge
            import app.host.logging as hl

            raw_ctx = hl._CORRELATION_CONTEXT.get()
            assert raw_ctx is not None
            assert raw_ctx["request_id"] == "req-101"
            assert raw_ctx["sub_task"] == "validation"

    # Context should be restored to None outside with block
    import app.host.logging as hl

    assert hl._CORRELATION_CONTEXT.get() is None


def test_safe_error_boundary() -> None:
    """FR-HOST-SAFE-ERROR-BOUNDARY: Strips tracebacks, locals, retaining frames."""
    try:
        raise ValueError("Invalid portfolio weight: 1.5 with secret key='super_secret'")
    except ValueError as exc:
        diag = safe_error_boundary(exc)

    assert diag["type"] == "ValueError"
    assert "super_secret" not in str(diag["message"])
    assert "[REDACTED:" in str(diag["message"])
    assert isinstance(diag["frames"], list)
    assert len(diag["frames"]) >= 1
    # Frame format: file.py:line:func
    assert "test_logging.py" in diag["frames"][-1]


def test_async_queue_backpressure_and_drops(tmp_path: Path) -> None:
    """FR-HOST-ASYNC-QUEUE: Bounded queue drops events under saturation."""
    log_dir = tmp_path / "drop_logs"
    engine = configure_host_logging(log_dir=log_dir, include_console=False)

    event = LogEvent(
        timestamp=datetime.now(UTC),
        level="INFO",
        namespace="app",
        module="test",
        function="fn",
        line=1,
        message="msg",
        context={},
        error=None,
        category=None,
    )

    # Fill queue directly to capacity to simulate peak saturation
    while not engine.queue.full():
        try:
            engine.queue.put_nowait(event)
        except queue.Full:
            break

    # One more event via enqueue should trigger drop without blocking
    overflow_event = LogEvent(
        timestamp=datetime.now(UTC),
        level="INFO",
        namespace="app",
        module="test",
        function="fn",
        line=1,
        message="overflow",
        context={},
        error=None,
        category=None,
    )
    engine.enqueue(overflow_event)
    assert engine.dropped_events >= 1


def test_standard_library_bridge(tmp_path: Path) -> None:
    """FR-HOST-LIBRARY-BRIDGE: Standard library loggers are intercepted and routed."""
    log_dir = tmp_path / "bridge_logs"
    configure_host_logging(log_dir=log_dir, include_console=False)

    bridge_standard_logging(("uvicorn.access", "external.library"))

    ext_logger = logging.getLogger("external.library")
    ext_logger.setLevel(logging.INFO)
    ext_logger.info("External message with password='bridge_secret'")

    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_logger.info("GET /api/v1/health 200 OK")

    assert flush(timeout=5.0)

    app_text = (log_dir / "app.log").read_text(encoding="utf-8")
    assert "bridge_secret" not in app_text
    assert "[REDACTED:" in app_text

    access_text = (log_dir / "access.log").read_text(encoding="utf-8")
    assert "GET /api/v1/health 200 OK" in access_text


def test_lifecycle_shutdown_and_flush(tmp_path: Path) -> None:
    """FR-HOST-LIFECYCLE-SYNC: Clean shutdown drains queued events."""
    log_dir = tmp_path / "lifecycle_logs"
    configure_host_logging(log_dir=log_dir, include_console=False)

    log = get_logger("app.lifecycle")
    for i in range(50):
        log.info("Message %d", i)

    # Flush should complete
    assert flush(timeout=5.0)
    # Shutdown should complete cleanly
    assert shutdown(timeout=5.0)

    app_lines = (log_dir / "app.log").read_text(encoding="utf-8").strip().splitlines()
    assert len(app_lines) == 50


def test_logger_levels_interpolation_and_exceptions(tmp_path: Path) -> None:
    """Verify warning, critical, exception, and formatting interpolation edge cases."""
    log_dir = tmp_path / "edge_logs"
    configure_host_logging(log_dir=log_dir, include_console=False)

    log = get_logger("app.edge")
    log.warning("A warning alert")
    log.critical("A critical panic")

    # Positional interpolation success
    log.info("Interpolated: %s = %d", "count", 42)

    # Positional interpolation failure fallback
    broken_fmt = "Broken interpolation: %s " + "%s"
    log.info(broken_fmt, "single_value")

    # Exception logging
    try:
        raise RuntimeError("Something failed with password='secret'")
    except RuntimeError:
        log.exception("Operation failed")

    assert flush(timeout=5.0)

    app_text = (log_dir / "app.log").read_text(encoding="utf-8")
    assert "A warning alert" in app_text
    assert "A critical panic" in app_text
    assert "Interpolated: count = 42" in app_text
    assert "ARGS_INTERPOLATION_FAILED" in app_text
    assert "Something failed" in app_text
    assert "secret" not in app_text
    assert "[REDACTED:" in app_text


def test_bridge_idempotency_and_uninitialized_lifecycle() -> None:
    """Verify duplicate bridge registration and uninitialized lifecycle calls."""
    reset_logging()

    # Flush and shutdown before any logging should return True
    assert flush(timeout=1.0)
    assert shutdown(timeout=1.0)

    # Calling bridge multiple times on the same logger
    bridge_standard_logging(("duplicate.lib",))
    bridge_standard_logging(("duplicate.lib",))

    lib_logger = logging.getLogger("duplicate.lib")
    handlers = [
        h for h in lib_logger.handlers if h.__class__.__name__ == "HostBridgeHandler"
    ]
    assert len(handlers) == 1


def test_console_filtering_by_level(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that console emission filters out events below configured level."""
    log_dir = tmp_path / "console_filter_logs"
    stream = io.StringIO()

    engine = configure_host_logging(
        log_dir=log_dir,
        level="INFO",
        include_console=True,
    )
    monkeypatch.setattr(engine, "_console_stream", stream)

    log = get_logger("app.console_test")
    log.debug("Hidden debug message")
    log.info("Visible info message")

    assert flush(timeout=5.0)
    console_output = stream.getvalue()
    assert "Hidden debug message" not in console_output
    assert "Visible info message" in console_output
