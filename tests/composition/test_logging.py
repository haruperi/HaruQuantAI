"""Focused tests for Composition-owned structured logging infrastructure."""

import asyncio
import io
import json
import logging
import zipfile
from pathlib import Path
from typing import Any, override

import pytest
from app.composition.logging import (
    _OWNED_HANDLER_ATTR,
    DiagnosticCaptureHandler,
    LoggingConfig,
    LoggingHandle,
    StructuredJsonFormatter,
    bind_correlation,
    compute_secret_fingerprint,
    configure_logging,
    get_correlation_context,
    redact_data,
)


def _record(message: str = "Sample operational event") -> logging.LogRecord:
    """Build one fixed structured log record for formatter tests."""
    record = logging.LogRecord(
        name="test.schema.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )
    record.created = 1_700_000_000.125
    record.event = "OP_STARTED"
    record.fields = {"step": 1, "target": "workspace"}
    return record


def test_structured_json_schema_levels_and_fixed_record_determinism() -> None:
    """Schema output is level-filtered and fixed-record formatting is byte-identical."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    formatter = StructuredJsonFormatter()
    handler.setFormatter(formatter)
    test_logger = logging.getLogger("test.schema.levels")
    previous_level = test_logger.level
    previous_propagate = test_logger.propagate
    test_logger.setLevel(logging.INFO)
    test_logger.propagate = False
    test_logger.addHandler(handler)
    try:
        test_logger.debug("Omitted debug message")
        assert stream.getvalue() == ""
        test_logger.info(
            "Sample operational event",
            extra={
                "event": "OP_STARTED",
                "fields": {"step": 1, "target": "workspace"},
            },
        )
        payload = json.loads(stream.getvalue())
        assert payload["v"] == 1
        assert payload["level"] == "INFO"
        assert payload["logger"] == "test.schema.levels"
        assert payload["event"] == "OP_STARTED"
        assert payload["fields"] == {"step": 1, "target": "workspace"}
    finally:
        test_logger.removeHandler(handler)
        test_logger.setLevel(previous_level)
        test_logger.propagate = previous_propagate
        handler.close()

    fixed = _record()
    with bind_correlation(request_id="REQ-A"):
        first = formatter.format(fixed)
    with bind_correlation(request_id="REQ-B"):
        second = formatter.format(fixed)
    assert first == second
    fixed_payload = json.loads(first)
    assert fixed_payload["timestamp"] == "2023-11-14T22:13:20.125000+00:00"
    assert fixed_payload["correlation"] == {"request_id": "REQ-A"}


@pytest.mark.asyncio
async def test_correlation_context_nesting_and_async_propagation() -> None:
    """Correlation dimensions propagate across tasks and nested contexts cleanly."""
    config = LoggingConfig(level="INFO", console=False, capture_capacity=50)
    with configure_logging(config) as handle:
        test_logger = logging.getLogger("test.correlation.logger")
        capture = handle.capture_handler
        assert capture is not None

        async def worker(task_id: str, correlation_id: str) -> None:
            with bind_correlation(task_id=task_id, correlation_id=correlation_id):
                test_logger.info("Step 1", extra={"event": "WORKER_STEP_1"})
                await asyncio.sleep(0)
                with bind_correlation(operation_id="OP-NESTED"):
                    test_logger.info("Step 2", extra={"event": "WORKER_STEP_2"})
                test_logger.info("Step 3", extra={"event": "WORKER_STEP_3"})

        with bind_correlation(request_id="REQ-ROOT", workspace_id="WS-1"):
            await asyncio.gather(
                worker("TASK-A", "CORR-A"),
                worker("TASK-B", "CORR-B"),
            )

        records = capture.get_records()
        assert len(records) == 6
        records_a = [
            record
            for record in records
            if record.correlation.get("task_id") == "TASK-A"
        ]
        assert len(records_a) == 3
        assert records_a[0].correlation["request_id"] == "REQ-ROOT"
        assert records_a[0].correlation["correlation_id"] == "CORR-A"
        assert records_a[1].correlation["operation_id"] == "OP-NESTED"
        assert "operation_id" not in records_a[2].correlation
    assert get_correlation_context() == {}


def test_redaction_handles_compounds_unordered_cycles_and_unsupported() -> None:
    """Sanitization is secret-safe, deterministic, bounded, and JSON-compatible."""
    canary = "raw_nested_secret_value_91f2"

    class UnsafeRepresentation:
        @override
        def __repr__(self) -> str:
            return f"UnsafeRepresentation({canary})"

    cyclic: list[object] = []
    cyclic.append(cyclic)
    source: dict[str, Any] = {
        "tokens": [canary, {"password": canary}],
        "safe_set": {"z", "a", "m"},
        "cycle": cyclic,
        "unsupported": UnsafeRepresentation(),
        "oversized": "x" * 10_000,
    }
    first = redact_data(source)
    second = redact_data(source)
    assert isinstance(first, dict)
    assert first == second
    encoded = json.dumps(first, sort_keys=True)
    assert canary not in encoded
    assert "[REDACTED:sha256:" in encoded
    assert '"safe_set": ["a", "m", "z"]' in encoded
    assert "<CYCLE:" in encoded
    assert "UnsafeRepresentation" in encoded
    assert len(first["oversized"]) <= 4096

    sensitive_collection = redact_data({"tokens": [canary]})
    assert isinstance(sensitive_collection, dict)
    assert isinstance(sensitive_collection["tokens"], str)
    assert canary not in sensitive_collection["tokens"]


def test_formatter_bounds_record_and_redacts_exception() -> None:
    """Oversized records become bounded JSON and exception canaries never emit."""
    formatter = StructuredJsonFormatter()
    oversized = _record("x" * 100_000)
    oversized.fields = {f"field-{index}": "y" * 5000 for index in range(100)}
    encoded = formatter.format(oversized)
    assert len(encoded.encode("utf-8")) <= 32768
    payload = json.loads(encoded)
    assert payload["event"] == "LOG_RECORD_TRUNCATED"
    assert payload["fields"]["record_truncated"] is True

    canary = "exception_secret=canary_8743"

    def raise_canary_error() -> None:
        raise RuntimeError(canary)

    try:
        raise_canary_error()
    except RuntimeError as error:
        error_record = _record("Failure")
        error_record.exc_info = (RuntimeError, error, error.__traceback__)
    rendered = formatter.format(error_record)
    assert canary not in rendered
    assert compute_secret_fingerprint("canary_8743") in rendered


def test_bounded_diagnostic_capture_active_expired_unknown_and_clear() -> None:
    """Capture distinguishes active, recently expired, forgotten, and unknown IDs."""
    handler = DiagnosticCaptureHandler(capacity=2)
    test_logger = logging.getLogger("test.capture.expiry")
    previous_level = test_logger.level
    previous_propagate = test_logger.propagate
    test_logger.setLevel(logging.INFO)
    test_logger.propagate = False
    test_logger.addHandler(handler)
    try:
        test_logger.info("Event 1", extra={"event": "E1"})
        first_id = handler.get_records()[0].diagnostic_id
        assert handler.get_by_id(first_id) is not None
        assert not handler.is_expired(first_id)
        assert not handler.is_expired("never-issued")

        test_logger.info("Event 2", extra={"event": "E2"})
        second_id = handler.get_records()[1].diagnostic_id
        test_logger.info("Event 3", extra={"event": "E3"})
        assert handler.get_by_id(first_id) is None
        assert handler.is_expired(first_id)

        handler.clear()
        assert not handler.get_records()
        assert handler.is_expired(second_id)

        test_logger.info("Event 4", extra={"event": "E4"})
        test_logger.info("Event 5", extra={"event": "E5"})
        handler.clear()
        assert not handler.is_expired(first_id)
        assert not handler.is_expired("never-issued")
    finally:
        test_logger.removeHandler(handler)
        test_logger.setLevel(previous_level)
        test_logger.propagate = previous_propagate
        handler.close()


def test_rotating_file_handler_bounds_and_secret_safety(tmp_path: Path) -> None:
    """File rotation honors positive bounds and stores no cleartext canary in logs or zip archives."""
    log_file = tmp_path / "app_rotating.log"
    canary = "file_secret=canary_5091"
    config = LoggingConfig(
        level="INFO",
        console=False,
        file_path=log_file,
        log_directory=None,
        max_bytes=500,
        backup_count=2,
        capture_capacity=50,
        compression="zip",
    )
    with configure_logging(config):
        test_logger = logging.getLogger("test.rotation.logger")
        for index in range(15):
            test_logger.info(
                "%s entry %03d",
                canary,
                index,
                extra={"event": "ROTATING_EVENT", "fields": {"index": index}},
            )

    files = list(tmp_path.glob("app_rotating.log*"))
    assert 2 <= len(files) <= 3
    contents: list[str] = []
    for path in files:
        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as z:
                contents.extend(z.read(name).decode("utf-8") for name in z.namelist())
        else:
            contents.append(path.read_text(encoding="utf-8"))
    combined = "".join(contents)
    assert canary not in combined
    assert compute_secret_fingerprint("canary_5091") in combined


def test_reconfiguration_preserves_foreign_handler_and_restores_level() -> None:
    """Replacement carries the original level and stale handles cannot alter it."""
    target = logging.getLogger("test.lifecycle.reconfigure")
    baseline_level = logging.ERROR
    previous_level = target.level
    previous_propagate = target.propagate
    target.setLevel(baseline_level)
    target.propagate = False
    foreign_handler = logging.StreamHandler(io.StringIO())
    target.addHandler(foreign_handler)
    first: LoggingHandle | None = None
    second: LoggingHandle | None = None
    try:
        config = LoggingConfig(
            level="INFO", console=False, log_directory=None, capture_capacity=10
        )
        first = configure_logging(config, target)
        second = configure_logging(config, target)
        assert foreign_handler in target.handlers
        assert target.level == logging.INFO
        assert (
            len(
                [
                    handler
                    for handler in target.handlers
                    if getattr(handler, _OWNED_HANDLER_ATTR, False)
                ]
            )
            == 1
        )

        first.close()
        assert target.level == logging.INFO
        assert foreign_handler in target.handlers
        second.close()
        assert target.level == baseline_level
        assert foreign_handler in target.handlers
        assert second.close() == ()
    finally:
        if first is not None:
            first.close()
        if second is not None:
            second.close()
        target.removeHandler(foreign_handler)
        foreign_handler.close()
        target.setLevel(previous_level)
        target.propagate = previous_propagate


def test_configuration_failure_rolls_back_to_active_generation(tmp_path: Path) -> None:
    """Failed handler construction leaves the prior generation usable and unchanged."""
    target = logging.getLogger("test.lifecycle.transaction")
    previous_level = target.level
    previous_propagate = target.propagate
    target.setLevel(logging.ERROR)
    target.propagate = False
    handle = configure_logging(
        LoggingConfig(
            level="INFO", console=False, log_directory=None, capture_capacity=10
        ),
        target,
    )
    try:
        capture = handle.capture_handler
        assert capture is not None
        with pytest.raises(
            PermissionError,
            match=r"Permission denied|Access is denied",
        ):
            configure_logging(
                LoggingConfig(
                    level="DEBUG",
                    console=True,
                    file_path=tmp_path,
                    log_directory=None,
                    capture_capacity=10,
                ),
                target,
            )
        assert target.level == logging.INFO
        assert handle.handlers[0] in target.handlers
        target.info("Still active", extra={"event": "ACTIVE_AFTER_ROLLBACK"})
        assert capture.get_records()[-1].event == "ACTIVE_AFTER_ROLLBACK"
    finally:
        handle.close()
        target.setLevel(previous_level)
        target.propagate = previous_propagate


def test_cleanup_failure_is_bounded_safe_and_does_not_skip_restoration() -> None:
    """Raising cleanup operations produce stage/type evidence and continue cleanup."""

    class RaisingHandler(logging.Handler):
        @override
        def emit(self, record: logging.LogRecord) -> None:
            del record

        @override
        def flush(self) -> None:
            raise RuntimeError("cleanup_secret=never_emit_this")

        @override
        def close(self) -> None:
            raise ValueError("cleanup_secret=never_emit_this")

    target = logging.getLogger("test.lifecycle.cleanup_failure")
    previous_level = target.level
    target.setLevel(logging.INFO)
    handler = RaisingHandler()
    setattr(handler, _OWNED_HANDLER_ATTR, True)
    target.addHandler(handler)
    handle = LoggingHandle(
        [handler],
        capture_handler=None,
        target_logger=target,
        previous_level=logging.ERROR,
        generation=999,
    )
    diagnostics = handle.close()
    assert handler not in target.handlers
    assert target.level == logging.ERROR
    assert [(item.stage, item.error_type) for item in diagnostics] == [
        ("flush", "RuntimeError"),
        ("close", "ValueError"),
    ]
    assert "never_emit_this" not in str(diagnostics)
    target.setLevel(previous_level)


@pytest.mark.parametrize("level", ["TRACE", "", "NOTSET", "INFOO"])
def test_logging_config_rejects_invalid_levels(level: str) -> None:
    """Programmatic configuration fails closed for unsupported levels."""
    with pytest.raises(ValueError, match="Unsupported logging level"):
        LoggingConfig(level=level).validate()


def test_logging_config_validation_and_case_normalization() -> None:
    """Positive bounds are mandatory and supported levels normalize safely."""
    assert LoggingConfig(level=" warning ").normalized_level() == "WARNING"
    assert LoggingConfig(compression=" ZIP ").normalized_compression() == "zip"
    with pytest.raises(ValueError, match="max_bytes must be strictly positive"):
        LoggingConfig(max_bytes=0).validate()
    with pytest.raises(ValueError, match="backup_count must be strictly positive"):
        LoggingConfig(backup_count=0).validate()
    with pytest.raises(ValueError, match="capture_capacity must be strictly positive"):
        LoggingConfig(capture_capacity=0).validate()
    with pytest.raises(ValueError, match="retention_days must be strictly positive"):
        LoggingConfig(retention_days=0).validate()
    with pytest.raises(ValueError, match="Unsupported logging compression"):
        LoggingConfig(compression="invalid").validate()


def test_configuration_rollback_on_partial_attachment_failure() -> None:
    """When addHandler attaches to target logger and then raises, rollback cleans attached handlers."""

    class PartialAttachLogger(logging.Logger):
        def __init__(self, name: str) -> None:
            super().__init__(name)
            self._fail_on_call = 2
            self._call_count = 0

        @override
        def addHandler(self, hdlr: logging.Handler) -> None:
            super().addHandler(hdlr)
            self._call_count += 1
            if self._call_count >= self._fail_on_call:
                raise RuntimeError("attachment mutation failure")

    target = PartialAttachLogger("test.lifecycle.partial_attach")
    previous_level = target.level
    target.setLevel(logging.ERROR)
    foreign_handler = logging.NullHandler()
    target.addHandler(foreign_handler)

    target._call_count = 0
    target._fail_on_call = 999
    first_handle = configure_logging(
        LoggingConfig(
            level="INFO", console=False, log_directory=None, capture_capacity=5
        ),
        target,
    )
    assert first_handle.handlers[0] in target.handlers
    assert target.level == logging.INFO

    target._call_count = 0
    target._fail_on_call = 2
    with pytest.raises(RuntimeError, match="attachment mutation failure"):
        configure_logging(
            LoggingConfig(
                level="DEBUG", console=True, log_directory=None, capture_capacity=10
            ),
            target,
        )

    assert first_handle.handlers[0] in target.handlers
    assert foreign_handler in target.handlers
    assert len(target.handlers) == 2
    assert target.level == logging.INFO

    first_handle.close()
    assert foreign_handler in target.handlers
    assert len(target.handlers) == 1
    assert target.level == logging.ERROR
    target.removeHandler(foreign_handler)
    target.setLevel(previous_level)


def test_specialized_four_file_routing_with_zip_compression_and_retention(
    tmp_path: Path,
) -> None:
    """Verify app.log, access.log, debug.log, and error.log routing and zip rollover."""
    log_dir = tmp_path / "data" / "logs"
    config = LoggingConfig(
        level="DEBUG",
        console=False,
        log_directory=log_dir,
        max_bytes=1000,
        backup_count=3,
        retention_days=30,
        compression="zip",
    )
    with configure_logging(config):
        test_logger = logging.getLogger("test.four_files.logger")
        # 1. Normal INFO -> should appear in app.log
        test_logger.info("General application info event")

        # 2. Access record -> should appear in app.log AND access.log
        test_logger.info(
            "HTTP GET /api/v1/health 200",
            extra={"log_type": "access", "event": "ACCESS"},
        )

        # 3. DEBUG record -> should appear in app.log AND debug.log
        test_logger.debug("Low-level debugging calculation details")

        # 4. ERROR record -> should appear in app.log AND error.log
        test_logger.error("Database connection failure detected")

    app_log = (log_dir / "app.log").read_text(encoding="utf-8")
    access_log = (log_dir / "access.log").read_text(encoding="utf-8")
    debug_log = (log_dir / "debug.log").read_text(encoding="utf-8")
    error_log = (log_dir / "error.log").read_text(encoding="utf-8")

    # Verify app.log has all 4 events
    assert "General application info event" in app_log
    assert "HTTP GET /api/v1/health 200" in app_log
    assert "Low-level debugging calculation details" in app_log
    assert "Database connection failure detected" in app_log

    # Verify access.log only has access records
    assert "HTTP GET /api/v1/health 200" in access_log
    assert "General application info event" not in access_log
    assert "Low-level debugging calculation details" not in access_log
    assert "Database connection failure detected" not in access_log

    # Verify debug.log has debug records
    assert "Low-level debugging calculation details" in debug_log
    assert "General application info event" not in debug_log
    assert "HTTP GET /api/v1/health 200" not in debug_log

    # Verify error.log has error records
    assert "Database connection failure detected" in error_log
    assert "General application info event" not in error_log
    assert "Low-level debugging calculation details" not in error_log


def test_standard_text_formatter_output_format() -> None:
    """Standard text formatting matches YYYY-MM-DD HH:MM:SS.mmm | LEVEL | module:func:line - message."""
    from app.composition.logging import StandardTextFormatter

    # Test with colorize=False
    plain_formatter = StandardTextFormatter(colorize=False)
    record = _record("Sample text message")
    record.module = "__main__"
    record.funcName = "example_01_logger_example"
    record.lineno = 28
    plain_rendered = plain_formatter.format(record)
    assert (
        " | INFO     | __main__:example_01_logger_example:28 - Sample text message"
        in plain_rendered
    )

    # Test with colorize=True
    color_formatter = StandardTextFormatter(colorize=True)
    color_rendered = color_formatter.format(record)
    assert "\033[32mINFO    \033[0m" in color_rendered
    assert "\033[32mSample text message" in color_rendered
    assert color_rendered.endswith("\033[0m")


def test_logging_usage_scenarios() -> None:
    """Verify the __main__ usage demonstration scenarios run cleanly."""
    from app.composition.logging import _harness_main

    assert _harness_main() == 0
