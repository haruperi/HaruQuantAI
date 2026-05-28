"""Unit tests for tools.utils.logger."""

from __future__ import annotations

import queue
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

from tools.utils.security import REDACTED_VALUE
from tools.utils.security import _redact_mapping
from tools.utils.security import _redact_text
from tools.utils.logger import CompatRecord
from tools.utils.logger import StructlogAdapter
from tools.utils.logger import configure_default_file_sinks
from tools.utils.logger import configure_multiprocess_listener
from tools.utils.logger import init_worker_logger

REQUIRED_RESPONSE_KEYS = {"status", "message", "data", "error", "metadata"}
REQUIRED_METADATA_KEYS = {
    "tool_name",
    "tool_version",
    "tool_category",
    "tool_risk_level",
    "request_id",
    "execution_ms",
    "read_only",
    "writes_file",
    "modifies_database",
    "places_trade",
    "requires_network",
}
logger_module: Any = import_module("tools.utils.logger")


@pytest.fixture(autouse=True)
def reset_logger_process_state() -> Generator[None, None, None]:
    """Reset module-level logger state between tests."""
    logger_module._WORKER_LOG_QUEUE = None
    logger_module._QUEUE_LISTENER_RUNNING = False
    logger_module._DEFAULT_FILE_SINKS_CONFIGURED = False
    yield
    logger_module._WORKER_LOG_QUEUE = None
    logger_module._QUEUE_LISTENER_RUNNING = False
    logger_module._DEFAULT_FILE_SINKS_CONFIGURED = False


def assert_standard_response(result: Dict[str, Any]) -> None:
    """Assert that a tool response follows the HaruQuantAI schema."""
    assert set(result) == REQUIRED_RESPONSE_KEYS
    assert result["status"] in {"success", "error"}
    assert isinstance(result["message"], str)
    assert result["metadata"].keys() >= REQUIRED_METADATA_KEYS
    assert isinstance(result["metadata"]["execution_ms"], float)
    if result["status"] == "success":
        assert result["error"] is None
    else:
        assert result["error"] is not None
        assert "code" in result["error"]
        assert "details" in result["error"]


class BadQueue:
    """Queue-like object missing required methods."""


class ListSink:
    """Collects log output for assertions."""

    def __init__(self) -> None:
        self.records: list[str] = []

    def write(self, value: str) -> None:
        self.records.append(value)

    def flush(self) -> None:
        return None


class BrokenSink:
    """Sink that raises for write and flush operations."""

    def write(self, value: str) -> None:
        raise OSError(f"broken sink: {value}")

    def flush(self) -> None:
        raise OSError("flush failed")


class RaisingCallableSink:
    """Callable sink that raises when invoked."""

    def __call__(self, record: CompatRecord) -> None:
        raise RuntimeError(f"cannot write {record.message}")


class BadPutQueue:
    """Queue-like object whose put method fails."""

    def put_nowait(self, item: Any) -> None:
        raise RuntimeError(f"cannot queue {item!r}")


def make_record(message: str = "record") -> CompatRecord:
    """Build a minimal compatible log record for sink tests."""
    return CompatRecord(
        time=datetime.now(timezone.utc),
        level=logger_module._CompatLevel(name="INFO", no=20),
        message=message,
        name="test",
        file="test_file",
        function="test_function",
        line=1,
        correlation_id="corr",
        run_id="run",
        trace_id="trace",
        extra={},
    )


def test_redact_mapping_hides_sensitive_keys() -> None:
    result = _redact_mapping({"api_key": "abc", "safe": "value"})

    assert result["api_key"] == REDACTED_VALUE
    assert result["safe"] == "value"


def test_redact_text_hides_sensitive_values() -> None:
    result = _redact_text("token=abc password:secret visible=yes")

    assert "abc" not in result
    assert "secret" not in result
    assert result.count(REDACTED_VALUE) == 2
    assert "visible=yes" in result


def test_safe_redaction_falls_back_when_helper_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_mapping(value: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError(f"bad mapping {value}")

    def fail_text(value: str) -> str:
        raise RuntimeError(f"bad text {value}")

    monkeypatch.setattr(logger_module, "_redact_mapping", fail_mapping)
    monkeypatch.setattr(logger_module, "_redact_text", fail_text)

    assert logger_module._safe_redact_mapping({"token": "abc"}) == {"token": "abc"}
    assert logger_module._safe_redact_text("token=abc") == "token=abc"


def test_file_sink_validates_limits(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="max_bytes"):
        logger_module._SizeAndTimeRotatingFileSink(
            tmp_path / "app.log",
            max_bytes=0,
            backup_count=1,
        )
    with pytest.raises(ValueError, match="backup_count"):
        logger_module._SizeAndTimeRotatingFileSink(
            tmp_path / "app.log",
            max_bytes=10,
            backup_count=0,
        )


def test_file_sink_rotates_and_prunes_backups(tmp_path: Path) -> None:
    sink = logger_module._SizeAndTimeRotatingFileSink(
        tmp_path / "app.log",
        max_bytes=10,
        backup_count=1,
    )
    try:
        sink.write("first line\n")
        sink.write("second line\n")
        backups = list(tmp_path.glob("app.log.*"))
        assert len(backups) <= 1
        assert (tmp_path / "app.log").exists()
    finally:
        sink.close()


def test_init_worker_logger_success() -> None:
    log_queue: queue.Queue[Any] = queue.Queue()

    result = init_worker_logger(log_queue, request_id="req-001")

    assert_standard_response(result)
    assert result["status"] == "success"
    assert result["data"] is True
    assert result["metadata"]["tool_name"] == "init_worker_logger"
    assert result["metadata"]["request_id"] == "req-001"
    assert result["metadata"]["writes_file"] is True


def test_init_worker_logger_rejects_missing_queue() -> None:
    result = init_worker_logger(None, request_id="req-002")

    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_init_worker_logger_rejects_queue_without_put_nowait() -> None:
    result = init_worker_logger(BadQueue(), request_id="req-003")

    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_configure_multiprocess_listener_success() -> None:
    log_queue: queue.Queue[Any] = queue.Queue()

    result = configure_multiprocess_listener(log_queue, request_id="req-004")

    assert_standard_response(result)
    assert result["status"] == "success"
    assert result["data"] is True
    assert result["metadata"]["tool_name"] == "configure_multiprocess_listener"
    assert result["metadata"]["request_id"] == "req-004"
    log_queue.put(None)


def test_configure_multiprocess_listener_rejects_missing_queue() -> None:
    result = configure_multiprocess_listener(None, request_id="req-005")

    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_configure_multiprocess_listener_rejects_invalid_logger() -> None:
    log_queue: queue.Queue[Any] = queue.Queue()

    result = configure_multiprocess_listener(
        log_queue,
        log_instance=object(),
        request_id="req-006",
    )

    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_init_worker_logger_returns_error_when_internal_setup_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_init(queue_value: Any) -> None:
        raise RuntimeError(f"cannot initialize {queue_value!r}")

    monkeypatch.setattr(logger_module, "_init_worker_logger", fail_init)

    result = init_worker_logger(queue.Queue(), request_id="req-error-worker")

    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "TOOL_EXECUTION_FAILED"


def test_configure_listener_returns_error_when_internal_setup_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_listener(queue_value: Any, log_instance: Any = None) -> None:
        raise RuntimeError(f"cannot listen {queue_value!r} {log_instance!r}")

    monkeypatch.setattr(
        logger_module, "_configure_multiprocess_listener", fail_listener
    )

    result = configure_multiprocess_listener(
        queue.Queue(), request_id="req-error-listener"
    )

    assert_standard_response(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "TOOL_EXECUTION_FAILED"


def test_structlog_adapter_dispatches_to_sink() -> None:
    sink = ListSink()
    log = StructlogAdapter(name="test")
    log.remove()
    log.add(sink, level="INFO")

    log.info("hello %s", "world", extra={"request_id": "req-007"})

    assert any("hello world" in item for item in sink.records)


def test_structlog_adapter_filters_by_level() -> None:
    sink = ListSink()
    log = StructlogAdapter(name="test")
    log.remove()
    log.add(sink, level="ERROR")

    log.info("ignored")
    log.error("captured")

    assert not any("ignored" in item for item in sink.records)
    assert any("captured" in item for item in sink.records)


def test_context_ids_are_added() -> None:
    sink = ListSink()
    log = StructlogAdapter(name="test")
    log.remove()
    log.add(sink, level="INFO", format="{correlation_id}|{run_id}|{trace_id}|{message}")

    log.info("context test")

    assert any("||" in item and "context test" in item for item in sink.records)


def test_structlog_adapter_level_and_context_controls() -> None:
    sink = ListSink()
    log = StructlogAdapter(name="test")
    log.add(sink, level="TRACE")

    log.set_min_level("ERROR")
    assert log.get_min_level() == "ERROR"
    log.warning("ignored warning")
    log.error("captured error")

    log.set_component_level("quiet", "CRITICAL")
    log.bind(component="quiet").error("quiet component")
    log.clear_component_level("quiet")
    log.bind(component="quiet").error("loud component")
    log.clear_all_component_levels()

    with log.contextualize(component="ctx") as contextual_logger:
        contextual_logger.critical("context critical")

    assert not any("ignored warning" in item for item in sink.records)
    assert any("captured error" in item for item in sink.records)
    assert not any("quiet component" in item for item in sink.records)
    assert any("loud component" in item for item in sink.records)
    assert any("context critical" in item for item in sink.records)


def test_structlog_adapter_emits_common_levels() -> None:
    sink = ListSink()
    log = StructlogAdapter(name="test")
    log.add(sink, level="TRACE")

    log.debug("debug message")
    log.success("success message")
    log.warning("warning message")
    log.critical("critical message")
    log.exception("exception message")
    log.log(20, "numeric info")
    log.log(99, "numeric critical")
    log.log("unknown", "default info")

    assert any("debug message" in item for item in sink.records)
    assert any("success message" in item for item in sink.records)
    assert any("warning message" in item for item in sink.records)
    assert any("critical message" in item for item in sink.records)
    assert any("exception message" in item for item in sink.records)
    assert any("numeric info" in item for item in sink.records)
    assert any("numeric critical" in item for item in sink.records)
    assert any("default info" in item for item in sink.records)


def test_structlog_adapter_path_sink_and_remove_handler(tmp_path: Path) -> None:
    log = StructlogAdapter(name="test")
    path = tmp_path / "custom.log"
    handler_id = log.add(path, level="INFO")

    log.info("path sink")
    log.remove(handler_id)

    assert "path sink" in path.read_text(encoding="utf-8")


def test_structlog_adapter_handles_sink_failures() -> None:
    log = StructlogAdapter(name="test")
    log.add(BrokenSink(), level="INFO")
    log.add(RaisingCallableSink(), level="INFO", raw=True)
    log.flush()

    log.info("should not raise")


def test_structlog_adapter_dispatch_filter_and_raw_callable() -> None:
    captured: list[CompatRecord] = []
    log = StructlogAdapter(name="test")
    log.add(captured.append, level="INFO", raw=True)
    log.add(captured.append, level="INFO", raw=True, filter=lambda record: False)
    log.add(captured.append, level="INFO", raw=True, filter=lambda record: 1 / 0)

    log.dispatch_record(make_record("raw record"))

    assert [record.message for record in captured] == ["raw record"]


def test_format_record_falls_back_for_bad_template() -> None:
    log = StructlogAdapter(name="test")
    formatted = log._format_record(make_record("fallback"), "{missing")

    assert "fallback" in formatted


def test_colorize_level_and_caller_unknown_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(logger_module.inspect, "currentframe", lambda: None)

    assert "\033[" in StructlogAdapter._colorize_level("ERROR")
    assert StructlogAdapter._colorize_level("CUSTOM") == "CUSTOM"
    assert StructlogAdapter._caller_meta() == {
        "file": "<unknown>",
        "function": "<unknown>",
        "line": 0,
    }


def test_emit_to_stdlib_when_structlog_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(logger_module, "_HAS_STRUCTLOG", False)
    sink = ListSink()
    log = StructlogAdapter(name="test")
    log.add(sink, level="TRACE")

    log.debug("stdlib debug")
    log.warning("stdlib warning")
    log.error("stdlib error")

    assert any("stdlib debug" in item for item in sink.records)
    assert any("stdlib warning" in item for item in sink.records)
    assert any("stdlib error" in item for item in sink.records)


def test_worker_queue_failure_is_recoverable() -> None:
    logger_module._WORKER_LOG_QUEUE = BadPutQueue()
    log = StructlogAdapter(name="test")

    log.info("queue failure should not raise")


def test_configure_default_file_sinks_validates_and_is_idempotent(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="max_bytes"):
        configure_default_file_sinks(tmp_path, max_bytes=0)
    with pytest.raises(ValueError, match="backup_count"):
        configure_default_file_sinks(tmp_path, backup_count=0)

    log = StructlogAdapter(name="test")
    configure_default_file_sinks(tmp_path, log_instance=log)
    configure_default_file_sinks(tmp_path, log_instance=log)
    log.remove()


def test_multiprocess_listener_drains_records_and_ignores_bad_items() -> None:
    sink = ListSink()
    log = StructlogAdapter(name="test")
    log.add(sink, level="INFO")
    log_queue: queue.Queue[Any] = queue.Queue()

    configure_multiprocess_listener(log_queue, log_instance=log, request_id="req-drain")
    log_queue.put("bad-item")
    log_queue.put(make_record("from queue"))
    log_queue.put(None)
    log_queue.join if hasattr(log_queue, "join") else None

    import time

    deadline = time.time() + 2
    while time.time() < deadline and not any(
        "from queue" in item for item in sink.records
    ):
        time.sleep(0.01)

    assert any("from queue" in item for item in sink.records)


def test_configure_default_file_sinks_creates_log_files(tmp_path: Path) -> None:
    log = StructlogAdapter(name="test")
    log.remove()

    configure_default_file_sinks(
        tmp_path, log_instance=log, max_bytes=1024, backup_count=2
    )
    try:
        log.info("file sink test")
        log.flush()

        assert (tmp_path / "app.log").exists()
    finally:
        log.remove()
