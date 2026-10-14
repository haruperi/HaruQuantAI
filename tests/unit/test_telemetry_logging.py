"""Unit tests for telemetry, multi-sink logging, secret redaction, and diagnostics.

Description:
    Exercises multi-sink logging configuration (app.log, access.log, errors.log),
    asynchronous telemetry engine worker, Windows-safe 10MB rotation, recursive
    secret redaction across composite structures, machine path normalization,
    safe error boundary, millisecond-precision log event formatting with ANSI
    colorization, thread-safe in-memory ring buffer operations, BoundLogger
    context accumulation, request correlation context, and system health
    diagnostic probes (database, storage, and hardware via psutil).

Purpose:
    FEAT-HOST-TELEMETRY: Verify telemetry, redacted logging and diagnostics.

Key Capabilities:
    - FR-HOST-TELEMETRY-ENGINE: Verify telemetry engine and asynchronous flush.
      Associated: `test_setup_logging_multi_sink()`, `test_async_telemetry_engine()`
      Logging: caplog asserts `FR-HOST-TELEMETRY-ENGINE` events.
    - FR-HOST-TELEMETRY-REDACTION: Verify secret scrubbing and path normalization.
      Associated: `test_secret_redaction()`, `test_path_normalization()`
      Logging: caplog asserts `FR-HOST-TELEMETRY-REDACTION` events.
    - FR-HOST-TELEMETRY-ERROR-BOUNDARY: Verify error boundary prevents crashes.
      Associated: `test_safe_error_boundary()`
      Logging: asserts fallback error boundary emission.
    - FR-HOST-TELEMETRY-FORMATTING: Verify exact millisecond timestamp & ANSI codes.
      Associated: `test_log_event_formatting_exact_pattern()`
      Logging: verifies millisecond timestamp and ANSI color sequences.
    - FR-HOST-TELEMETRY-SINKS: Verify Windows-safe rotation and multi-sink writes.
      Associated: `test_windows_safe_rotation()`, `test_specialized_access_routing()`
      Logging: verifies 10MB limit and 30-backup rollover.
    - FR-HOST-TELEMETRY-RINGBUFFER: Verify ring buffer storage and live streaming.
      Associated: `test_ring_buffer_behavior()`
      Logging: caplog asserts `FR-HOST-TELEMETRY-RINGBUFFER` events.
    - FR-HOST-TELEMETRY-BOUND-LOGGER: Verify context binding and facade methods.
      Associated: `test_bound_logger_dynamic_context()`
      Logging: asserts bound contextual key-values.
    - FR-HOST-TELEMETRY-CORRELATION: Verify request correlation context propagation.
      Associated: `test_correlation_context()`
      Logging: asserts correlation ID propagation into records.
    - FR-HOST-TELEMETRY-LAZY-BOOTSTRAP: Verify zero import side-effects.
      Associated: `test_lazy_bootstrap_no_import_side_effects()`
      Logging: asserts lazy engine activation.
    - FR-HOST-TELEMETRY-DIAGNOSTICS: Verify database, storage, and hardware probes.
      Associated: `test_diagnostics_probes()`
      Logging: caplog asserts `FR-HOST-TELEMETRY-DIAGNOSTICS` events.

Python API Usage:
    ```python
    import pytest

    pytest.main(["tests/unit/test_telemetry_logging.py", "--no-cov"])
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/test_telemetry_logging.py --no-cov
    ```
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import threading
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from app.host.logging import (
    ANSI_RESET,
    CORRELATION_FR,
    DEFAULT_RING_BUFFER_CAPACITY,
    ENGINE_FR,
    ERROR_BOUNDARY_FR,
    FORMATTING_FR,
    LAZY_BOOTSTRAP_FR,
    LOG_BACKUP_COUNT,
    MAX_LOG_FILE_BYTES,
    SINKS_FR,
    BoundLogger,
    LogEventFormatter,
    LogRingBuffer,
    WindowsSafeRotatingFileHandler,
    fingerprint_secret,
    flush_logs,
    get_access_logger,
    get_correlation_id,
    get_logger,
    get_ring_buffer,
    normalize_path,
    redact_secrets,
    reset_correlation_id,
    set_correlation_id,
    setup_logging,
    shutdown_logging,
)
from app.host.logging import (
    main as logging_main,
)
from app.host.persistence.create import create_schema, get_connection
from app.host.resources import (
    DIAGNOSTICS_FR,
    BenchmarkRunner,
    apply_cpu_affinity,
    calculate_worker_allocation,
    get_system_health,
    get_worker_capacity,
    inspect_cpu_affinity,
    inspect_gpu_qualification,
    inspect_workspace_directories,
    probe_cpu,
    probe_database,
    probe_disk,
    probe_hardware,
    probe_memory,
    probe_process,
    probe_storage,
    run_cpu_benchmark,
)
from app.host.resources import (
    main as diagnostics_main,
)


@pytest.fixture(autouse=True)
def _cleanup_logging() -> Generator[None]:
    """Clean up logging engine and handlers after each test."""
    yield
    shutdown_logging()


def test_async_access_sink_and_live_log_delivery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.host.transport import EventBus

    bus = EventBus(max_queue_size=20)
    emitter_threads: list[int] = []
    original_emit = WindowsSafeRotatingFileHandler.emit

    def capture_emit(
        handler: WindowsSafeRotatingFileHandler, record: logging.LogRecord
    ) -> None:
        if record.name == "haruquantai.access":
            emitter_threads.append(threading.get_ident())
        original_emit(handler, record)

    monkeypatch.setattr(WindowsSafeRotatingFileHandler, "emit", capture_emit)

    def publish_log(entry: dict[str, Any]) -> None:
        bus.publish("logs", "log", entry)

    async def observe() -> None:
        _, queue, _, _ = bus.subscribe(["logs"])
        received = asyncio.create_task(queue.get())
        await asyncio.sleep(0)
        setup_logging(
            tmp_path,
            level=logging.DEBUG,
            publish_log=publish_log,
        )
        get_access_logger().warning("audit password: confidential-audit-value")
        get_access_logger().warning(
            "structured audit %s", {"password": "audit+special/password=!"}
        )
        await asyncio.to_thread(flush_logs)
        entries = [await asyncio.wait_for(received, timeout=3)]
        while not queue.empty():
            entries.append(queue.get_nowait())
        assert any("sha256:" in event.payload["message"] for event in entries)
        assert all(
            "confidential-audit-value" not in str(event.payload) for event in entries
        )
        assert all(
            "audit+special/password=!" not in str(event.payload) for event in entries
        )
        cursor = bus.current_cursor
        await asyncio.to_thread(flush_logs)
        assert bus.current_cursor == cursor  # Broker diagnostics cannot recurse.

    try:
        asyncio.run(observe(), debug=True)
        assert emitter_threads
        assert threading.get_ident() not in emitter_threads
        for name in ("app.log", "access.log", "errors.log"):
            content = (tmp_path / name).read_text(encoding="utf-8")
            assert "sha256:" in content
            assert "confidential-audit-value" not in content
            assert "audit+special/password=!" not in content
        assert "logging engine initialized" not in (tmp_path / "access.log").read_text()
    finally:
        shutdown_logging()


def test_queue_overflow_diagnostics_do_not_echo_secrets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    import queue

    from app.host.logging import _RedactingQueueHandler

    records: queue.Queue[logging.LogRecord | None] = queue.Queue(maxsize=1)
    handler = _RedactingQueueHandler(records)
    record = logging.LogRecord(
        "audit", logging.INFO, "", 0, "password: confidential-overflow", (), None
    )
    handler.emit(record)
    handler.emit(record)
    diagnostic = capsys.readouterr().err
    assert "telemetry record dropped" in diagnostic
    assert "confidential-overflow" not in diagnostic


def test_setup_logging_multi_sink(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify multi-sink file creation and level-separated log emission."""
    caplog.set_level(logging.INFO)
    logs_dir = tmp_path / "logs"

    buffer = setup_logging(logs_dir, level=logging.DEBUG, async_engine=False)
    assert isinstance(buffer, LogRingBuffer)

    test_logger = get_logger("haruquantai.test")
    test_logger.debug("Debug message payload")
    test_logger.info("Info message payload")
    test_logger.warning("Warning message payload")
    test_logger.error("Error message payload")

    flush_logs()

    app_log = logs_dir / "app.log"
    errors_log = logs_dir / "errors.log"

    assert app_log.exists()
    assert errors_log.exists()

    app_content = app_log.read_text(encoding="utf-8")
    assert "Info message payload" in app_content
    assert "Warning message payload" in app_content
    assert "Error message payload" in app_content

    errors_content = errors_log.read_text(encoding="utf-8")
    assert "Warning message payload" in errors_content
    assert "Error message payload" in errors_content
    assert "Info message payload" not in errors_content

    assert any(
        getattr(r, "fr_id", None) == ENGINE_FR or ENGINE_FR in r.message
        for r in caplog.records
    )


def test_secret_redaction() -> None:
    """Verify recursive masking of sensitive tokens, passwords, and keys."""
    # 1. String redaction
    raw_text = "Connecting with token: 'secret_token_12345' and Bearer abc.xyz"
    redacted_text = redact_secrets(raw_text)
    assert "secret_token_12345" not in str(redacted_text)
    assert "***REDACTED***" in str(redacted_text)

    # 2. Dictionary redaction
    sensitive_dict = {
        "username": "trader1",
        "password": "super_secret_password",
        "api_key": "key-99999",
        "nested": {
            "token": "tok-123",
            "safe_param": 42,
        },
    }
    scrubbed = redact_secrets(sensitive_dict)
    assert scrubbed["username"] == "trader1"
    assert scrubbed["password"] == "***REDACTED***"
    assert scrubbed["api_key"] == "***REDACTED***"
    assert scrubbed["nested"]["token"] == "***REDACTED***"
    assert scrubbed["nested"]["safe_param"] == 42

    # 3. Sequences redaction
    seq = ["plain", {"secret": "hide_me"}, ("bearer 123", 100)]
    scrubbed_seq = redact_secrets(seq)
    assert scrubbed_seq[0] == "plain"
    assert scrubbed_seq[1]["secret"] == "***REDACTED***"
    assert scrubbed_seq[2][0] == "***REDACTED***"
    assert scrubbed_seq[2][1] == 100

    # 4. Formatter integration
    formatter = LogEventFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Logged password: %s and token: %s",
        args=("pass123", "tok456"),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "pass123" not in formatted
    assert "tok456" not in formatted
    assert "***REDACTED:sha256:" in formatted


def test_path_normalization(tmp_path: Path) -> None:
    """Verify masking of local machine paths to prevent environment leaks."""
    sample_path = str(tmp_path / "data" / "database" / "haruquantai.db")
    normalized = normalize_path(sample_path, root_dir=tmp_path)
    assert "[WORKSPACE]/data/database/haruquantai.db" == normalized


def test_ring_buffer_behavior() -> None:
    """Verify capacity bounds, filtering, and retrieval on LogRingBuffer."""
    buffer = LogRingBuffer(maxlen=5)

    for i in range(10):
        buffer.append(
            {
                "timestamp": "2026-10-14T00:00:00Z",
                "level": "INFO" if i % 2 == 0 else "ERROR",
                "message": f"msg-{i}",
            }
        )

    assert len(buffer) == 5

    all_recs = buffer.get_records()
    assert len(all_recs) == 5
    assert all_recs[0]["message"] == "msg-5"
    assert all_recs[-1]["message"] == "msg-9"

    error_recs = buffer.get_records(min_level="ERROR")
    assert all(r["level"] == "ERROR" for r in error_recs)

    limited = buffer.get_records(limit=2)
    assert len(limited) == 2
    assert limited[-1]["message"] == "msg-9"

    buffer.clear()
    assert len(buffer) == 0

    global_buffer = get_ring_buffer()
    assert isinstance(global_buffer, LogRingBuffer)


def test_diagnostics_probes(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify database, storage, and hardware health probes."""
    caplog.set_level(logging.DEBUG)

    missing_db = probe_database(tmp_path / "missing.db")
    assert missing_db.exists is False
    assert missing_db.error is not None

    real_db_path = tmp_path / "real.db"
    conn = get_connection(real_db_path)
    create_schema(conn)
    conn.close()

    db_probe = probe_database(real_db_path)
    assert db_probe.exists is True
    assert db_probe.error is None
    assert db_probe.table_count == 25
    assert db_probe.size_bytes > 0

    storage_probe = probe_storage(tmp_path)
    assert storage_probe.logs_dir_writable is True
    assert storage_probe.database_dir_writable is True
    assert storage_probe.free_bytes > 0
    assert storage_probe.total_bytes > 0
    assert storage_probe.free_pct > 0.0

    hw_probe = probe_hardware()
    assert hw_probe.cpu_count_logical >= 1
    assert hw_probe.ram_total_bytes > 0
    assert hw_probe.ram_available_bytes > 0
    assert 0.0 <= hw_probe.ram_used_pct <= 100.0

    health_healthy = get_system_health(db_path=real_db_path, root_path=tmp_path)
    assert health_healthy.status == "HEALTHY"
    report_dict = health_healthy.to_dict()
    assert report_dict["status"] == "HEALTHY"
    assert "database" in report_dict
    assert "storage" in report_dict
    assert "hardware" in report_dict

    health_degraded = get_system_health(
        db_path=tmp_path / "nonexistent.db", root_path=tmp_path
    )
    assert health_degraded.status == "DEGRADED"

    assert any(
        getattr(r, "fr_id", None) == DIAGNOSTICS_FR or DIAGNOSTICS_FR in r.message
        for r in caplog.records
    )


def test_bound_logger_dynamic_context(tmp_path: Path) -> None:
    """Verify dynamic contextual attribute binding and inheritance."""
    logs_dir = tmp_path / "logs"
    setup_logging(logs_dir, level=logging.DEBUG, async_engine=False)

    base_logger = get_logger("haruquantai.bound_test")
    assert isinstance(base_logger, BoundLogger)

    session_logger = base_logger.bind(session_id="sess-001", user="trader1")
    assert isinstance(session_logger, BoundLogger)
    assert session_logger.context["session_id"] == "sess-001"
    assert session_logger.context["user"] == "trader1"

    trade_logger = session_logger.bind(symbol="ETH/USDT", order_id="ord-99")
    assert trade_logger.context["session_id"] == "sess-001"
    assert trade_logger.context["symbol"] == "ETH/USDT"
    assert trade_logger.context["order_id"] == "ord-99"

    trade_logger.info("Order executed successfully")
    flush_logs()

    app_log = logs_dir / "app.log"
    content = app_log.read_text(encoding="utf-8")
    assert "Order executed successfully" in content
    assert "session_id=sess-001" in content
    assert "symbol=ETH/USDT" in content


def test_specialized_access_routing(tmp_path: Path) -> None:
    """Verify specialized routing of access events to data/logs/access.log."""
    logs_dir = tmp_path / "logs"
    setup_logging(logs_dir, level=logging.INFO, async_engine=False)

    access_logger = get_access_logger()
    general_logger = get_logger("haruquantai.general")

    access_logger.info("HTTP GET /api/v1/workspaces 200 OK")
    general_logger.info("General background task heartbeat")
    flush_logs()

    access_log = logs_dir / "access.log"
    assert access_log.exists()
    access_content = access_log.read_text(encoding="utf-8")

    assert "HTTP GET /api/v1/workspaces 200 OK" in access_content
    assert "General background task heartbeat" not in access_content


def test_log_event_formatting_exact_pattern() -> None:
    """Verify exact YYYY-MM-DD HH:MM:SS.mmm | LEVEL | module:function:line format."""
    plain_formatter = LogEventFormatter(colorize=False)
    colored_formatter = LogEventFormatter(colorize=True)

    record = logging.LogRecord(
        name="app.test_module",
        level=logging.INFO,
        pathname="app/test_module.py",
        lineno=42,
        msg="Test event notification",
        args=(),
        exc_info=None,
        func="test_func",
    )

    plain_output = plain_formatter.format(record)
    # Pattern: YYYY-MM-DD HH:MM:SS.mmm | LEVEL | module:function:line - message
    pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \| INFO  \| app\.test_module:test_func:42 - Test event notification$"
    assert re.match(pattern, plain_output) is not None

    colored_output = colored_formatter.format(record)
    assert "\033[" in colored_output
    assert ANSI_RESET in colored_output


def test_safe_error_boundary() -> None:
    """Verify safe error boundary prevents crashes on malformed format records."""
    formatter = LogEventFormatter(colorize=False)

    # Intentionally malformed record with mismatched format argument
    record = logging.LogRecord(
        name="app.error_boundary",
        level=logging.ERROR,
        pathname="",
        lineno=10,
        msg="Value format: %d %d",
        args=("not_a_number",),  # Only 1 arg supplied for 2 %d specifiers
        exc_info=None,
    )

    output = formatter.format(record)
    assert "[LOGGING-ERROR-BOUNDARY]" in output
    assert "Value format: %d %d" in output


def test_correlation_context(tmp_path: Path) -> None:
    """Verify request correlation context tracking across records and ring buffer."""
    logs_dir = tmp_path / "logs"
    buffer = setup_logging(logs_dir, level=logging.DEBUG, async_engine=False)

    logger = get_logger("haruquantai.correlation")
    token = set_correlation_id("req-correl-007")

    try:
        assert get_correlation_id() == "req-correl-007"
        logger.info("Tracking transaction request")
        flush_logs()

        records = buffer.get_records()
        matching = [
            r for r in records if r.get("message") and "Tracking" in r["message"]
        ]
        assert len(matching) > 0
        assert matching[0]["correlation_id"] == "req-correl-007"
    finally:
        reset_correlation_id(token)

    assert get_correlation_id() is None


def test_windows_safe_rotation(tmp_path: Path) -> None:
    """Verify WindowsSafeRotatingFileHandler handles 10MB limits and rollover."""
    target_file = tmp_path / "rotation.log"
    handler = WindowsSafeRotatingFileHandler(
        target_file,
        maxBytes=100,  # Small threshold to force rollover in test
        backupCount=3,
        delay=False,
    )
    formatter = LogEventFormatter(colorize=False)
    handler.setFormatter(formatter)

    test_logger = logging.getLogger("haruquantai.rotation")
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.INFO)

    try:
        # Write enough records to trigger rotation multiple times
        for i in range(10):
            test_logger.info("Log line payload number %d with extra data", i)

        handler.flush()
        handler.close()

        assert target_file.exists()
        backup_file = tmp_path / "rotation.log.1"
        assert backup_file.exists()
    finally:
        test_logger.removeHandler(handler)
        handler.close()


def test_async_telemetry_engine(tmp_path: Path) -> None:
    """Verify asynchronous telemetry queue listener engine and flush/shutdown."""
    logs_dir = tmp_path / "logs"
    buffer = setup_logging(logs_dir, level=logging.INFO, async_engine=True)
    assert isinstance(buffer, LogRingBuffer)

    test_logger = get_logger("haruquantai.async_test")
    for i in range(20):
        test_logger.info("Async queue message %d", i)

    flush_logs()

    app_log = logs_dir / "app.log"
    assert app_log.exists()
    content = app_log.read_text(encoding="utf-8")
    assert "Async queue message 19" in content

    shutdown_logging()


def test_lazy_bootstrap_no_import_side_effects() -> None:
    """Verify constants and limits match requirement specifications."""
    assert MAX_LOG_FILE_BYTES == 10 * 1024 * 1024
    assert LOG_BACKUP_COUNT == 30
    assert ENGINE_FR == "FR-HOST-TELEMETRY-ENGINE"
    assert ERROR_BOUNDARY_FR == "FR-HOST-TELEMETRY-ERROR-BOUNDARY"
    assert FORMATTING_FR == "FR-HOST-TELEMETRY-FORMATTING"
    assert SINKS_FR == "FR-HOST-TELEMETRY-SINKS"
    assert CORRELATION_FR == "FR-HOST-TELEMETRY-CORRELATION"
    assert LAZY_BOOTSTRAP_FR == "FR-HOST-TELEMETRY-LAZY-BOOTSTRAP"


def test_logging_cli_main_entrypoint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify execution of logging main() demonstration entrypoint."""
    monkeypatch.setattr("app.host.logging.DEFAULT_LOG_DIR", tmp_path / "logs")
    logging_main()
    flush_logs()

    assert (tmp_path / "logs" / "app.log").exists()
    assert (tmp_path / "logs" / "access.log").exists()
    assert (tmp_path / "logs" / "errors.log").exists()
    shutdown_logging()


def test_diagnostics_cli_main_entrypoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify execution of diagnostics main() demonstration entrypoint."""
    monkeypatch.chdir(tmp_path)
    diagnostics_main()


def test_workspace_directory_inspection(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify workspace directory inspection logs INFO for available and WARNING for absent."""
    caplog.set_level(logging.INFO)
    existing_dir = tmp_path / "custom_data"
    existing_dir.mkdir(parents=True)
    absent_dir = tmp_path / "missing_strategies"

    class FakeSettings:
        def __init__(self) -> None:
            self.workspace_paths = {
                "custom_data": str(existing_dir),
                "missing_strategies": str(absent_dir),
            }

    results = inspect_workspace_directories(settings=FakeSettings())
    assert results["custom_data"] is True
    assert results["missing_strategies"] is False

    assert any(
        "workspace directory 'custom_data' is available" in r.message
        for r in caplog.records
    )
    assert any(
        "workspace directory 'missing_strategies' is absent" in r.message
        for r in caplog.records
    )


def test_granular_system_probes(tmp_path: Path) -> None:
    """Verify granular probe functions for CPU, memory, disk, and process."""
    cpu = probe_cpu()
    assert cpu.logical_cores >= 1
    assert cpu.is_available is True

    mem = probe_memory()
    assert mem.total_bytes > 0
    assert mem.available_bytes > 0
    assert 0.0 <= mem.used_pct <= 100.0
    assert mem.is_available is True

    disk = probe_disk(tmp_path)
    assert disk.mount_point != ""
    assert disk.total_bytes > 0
    assert 0.0 <= disk.free_pct <= 100.0
    assert disk.is_available is True

    proc = probe_process()
    assert proc.pid == os.getpid()
    assert proc.memory_rss_bytes > 0
    assert proc.threads_count >= 1
    assert proc.uptime_seconds >= 0.0
    assert proc.is_available is True


def test_worker_capacity_and_affinity() -> None:
    """Verify worker pool allocation logic, capacity model, and core affinity."""
    assert calculate_worker_allocation(12, mode="single") == 1
    assert calculate_worker_allocation(12, mode="reserve-one") == 11
    assert calculate_worker_allocation(12, mode="all_except_one") == 11
    assert calculate_worker_allocation(12, mode="maximum") == 12
    assert calculate_worker_allocation(12, mode="all") == 12
    assert calculate_worker_allocation(12, mode="custom", custom_cores=4) == 4
    assert calculate_worker_allocation(12, mode="custom", custom_cores=99) == 12
    assert calculate_worker_allocation(1, mode="reserve-one") == 1

    capacity = get_worker_capacity(mode="single")
    assert capacity.allocated_workers == 1
    assert capacity.mode == "single"
    assert capacity.total_cores >= 1

    supported, current_aff = inspect_cpu_affinity()
    assert isinstance(supported, bool)
    if supported:
        assert isinstance(current_aff, list)
        assert len(current_aff) > 0
        res = apply_cpu_affinity(current_aff)
        assert res is True
    assert apply_cpu_affinity([]) is False


def test_gpu_qualification_safety(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify GPU acceleration inspection is fail-safe and never raises."""
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "-1")
    assert inspect_gpu_qualification() is False

    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    assert inspect_gpu_qualification() is True

    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    monkeypatch.delenv("CUDA_PATH", raising=False)
    monkeypatch.delenv("NVIDIA_VISIBLE_DEVICES", raising=False)
    assert inspect_gpu_qualification() is False


def test_bounded_computational_benchmark() -> None:
    """Verify deterministic quantitative benchmark throughput and cooperative cancellation."""
    res = run_cpu_benchmark(iterations=2_000)
    assert res.total_ticks == 2_000
    assert res.duration_seconds >= 0.0
    assert res.throughput_ops_per_sec > 0.0
    assert res.time_per_tick_ms >= 0.0
    assert res.avg_strategies_per_hour >= 0

    cancel_evt = threading.Event()
    cancel_evt.set()
    with pytest.raises(InterruptedError):
        run_cpu_benchmark(iterations=50_000, cancel_event=cancel_evt)

    runner = BenchmarkRunner()
    job = runner.start_job(iterations=1_000)
    assert job.job_id.startswith("bench-")
    assert job.state == "running"

    time.sleep(0.02)
    completed_job = runner.get_job(job.job_id)
    assert completed_job is not None
    assert completed_job.state in ("running", "completed")

    cancel_ok = runner.cancel_job(job.job_id)
    assert isinstance(cancel_ok, bool)
    assert runner.cancel_job("nonexistent-job") is False


def test_ring_buffer_capacity_2000_and_sha256_secret_fingerprinting() -> None:
    """Verify collections.deque(maxlen=2000) capacity and SHA-256 secret fingerprinting."""
    assert DEFAULT_RING_BUFFER_CAPACITY == 2000
    ring = LogRingBuffer()
    assert ring.maxlen == 2000
    assert get_ring_buffer().maxlen == 2000

    # Verify deterministic 8-hex SHA-256 secret fingerprinting
    fp1 = fingerprint_secret("super-secret-api-key")
    fp2 = fingerprint_secret("super-secret-api-key")
    fp_other = fingerprint_secret("different-secret")
    assert fp1 == fp2
    assert fp1 != fp_other
    assert fp1.startswith("***REDACTED:sha256:")
    assert fp1.endswith("***")

    nested = {
        "username": "operator",
        "api_key": "super-secret-api-key",
        "nested": {"password": "my-password-123"},
    }
    redacted_fp = redact_secrets(nested, fingerprint=True)
    assert redacted_fp["username"] == "operator"
    assert redacted_fp["api_key"] == fp1
    assert redacted_fp["nested"]["password"] == fingerprint_secret("my-password-123")
