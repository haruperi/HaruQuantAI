"""Focused tests for explicit host logging and sanitized diagnostic sinks."""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import logging
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from app.host.logging import (
    ColorFormatter,
    DiagnosticCaptureHandler,
    JsonLinesFormatter,
    SensitiveDataFilter,
    TextFormatter,
    bind_correlation,
    configure_host_logging,
    get_logger,
    host_log_path,
    redact_sensitive,
    secret_fingerprint,
)


@pytest.fixture(autouse=True)
def clean_host_logger() -> Iterator[None]:
    """Isolate the process-global standard-library logger between tests."""
    yield
    for name in ("app", "haruquantai"):
        logger = logging.getLogger(name)
        for handler in tuple(logger.handlers):
            logger.removeHandler(handler)
            handler.close()
        logger.__dict__.pop("_host_telemetry_config", None)
        logger.propagate = True
        logger.setLevel(logging.NOTSET)


def test_fingerprint_and_common_credential_redaction_are_stable() -> None:
    secret = "synthetic-value-42"  # pragma: allowlist secret
    expected = hashlib.sha256(secret.encode()).hexdigest()[:12]
    assert secret_fingerprint(secret) == expected
    marker = f"[REDACTED:{expected}]"
    for source in (
        f"password={secret}",
        f"API_KEY: {secret}",
        f'{{"token":"{secret}"}}',
        f"session_id={secret}",
        f"database_password='{secret}'",
        f"Bearer {secret}",
    ):
        cleaned = redact_sensitive(source)
        assert secret not in cleaned
        assert marker in cleaned
        assert redact_sensitive(cleaned) == cleaned
    for scheme in ("Bearer", "Basic"):
        cleaned = redact_sensitive(f"Authorization: {scheme} {secret}")
        assert secret not in cleaned
        assert redact_sensitive(cleaned) == cleaned


def test_text_and_json_formatters_scrub_messages_fields_and_exceptions() -> None:
    logger = logging.getLogger("test.telemetry.formats")
    logger.propagate = False
    logger.setLevel(logging.INFO)
    text_capture = DiagnosticCaptureHandler(3, formatter=TextFormatter())
    json_capture = DiagnosticCaptureHandler(3, formatter=JsonLinesFormatter())
    logger.addHandler(text_capture)
    logger.addHandler(json_capture)
    try:
        with bind_correlation("run-17"):
            try:
                raise ValueError("password=synthetic-exception")
            except ValueError:
                logger.exception(
                    "Bearer synthetic-message",
                    extra={
                        "fields": {
                            "api_key": "synthetic-field",  # pragma: allowlist secret
                            "count": 2,
                        }
                    },
                )
        line = text_capture.snapshot()[0]
        assert re.match(
            r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3} "
            r"\[MainThread\] ERROR  test\.telemetry\.formats:\d+ - ",
            line,
        )
        assert "run-17" in line
        parsed = json.loads(json_capture.snapshot()[0])
        assert parsed["correlation_id"] == "run-17"
        assert parsed["fields"]["count"] == 2
        assert parsed["fields"]["api_key"].startswith("[REDACTED:")
        assert parsed["level"] == "ERROR"
        assert parsed["logger"] == "test.telemetry.formats"
        assert parsed["line"] > 0
        assert "exception" in parsed
        for raw in (
            "synthetic-message",
            "synthetic-field",
            "synthetic-exception",
        ):
            assert raw not in line
            assert raw not in json_capture.snapshot()[0]
    finally:
        logger.removeHandler(text_capture)
        logger.removeHandler(json_capture)
        text_capture.close()
        json_capture.close()


def test_color_is_tty_aware_and_capture_strips_ansi() -> None:
    class TtyStream(io.StringIO):
        def isatty(self) -> bool:
            return True

    record = logging.makeLogRecord(
        {
            "name": "test",
            "levelno": logging.WARNING,
            "levelname": "WARNING",
            "msg": "ok",
        }
    )
    formatted = ColorFormatter(TtyStream()).format(record)
    assert "\x1b[" in formatted
    assert "\x1b[33mWARNING\x1b[0m" in formatted
    assert "\x1b[33mok\x1b[0m" in formatted
    prefix_before_level = formatted.split("\x1b[33mWARNING\x1b[0m")[0]
    assert "\x1b[" not in prefix_before_level
    between = formatted.split("\x1b[33mWARNING\x1b[0m")[1].split("\x1b[33mok\x1b[0m")[0]
    assert "\x1b[" not in between
    assert "\x1b[" not in ColorFormatter(io.StringIO()).format(record)
    capture = DiagnosticCaptureHandler(1, formatter=ColorFormatter(TtyStream()))
    capture.handle(record)
    assert "\x1b[" not in capture.snapshot()[0]


def test_formatter_metadata_is_sanitized() -> None:
    record = logging.makeLogRecord(
        {
            "name": "api_key=synthetic-name",
            "threadName": "password=synthetic-thread",
            "msg": "safe",
        }
    )
    for line in (TextFormatter().format(record), JsonLinesFormatter().format(record)):
        assert "synthetic-name" not in line
        assert "synthetic-thread" not in line


def test_nested_and_concurrent_task_correlation_is_isolated() -> None:
    capture = DiagnosticCaptureHandler(8, formatter=JsonLinesFormatter())
    logger = logging.getLogger("test.telemetry.correlation")
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(capture)

    async def child(name: str) -> None:
        with bind_correlation(name):
            await asyncio.sleep(0)
            logger.info("child")
            with bind_correlation(f"{name}-nested"):
                logger.info("nested")
            logger.info("restored")

    async def run_children() -> None:
        await asyncio.gather(child("left"), child("right"))

    try:
        asyncio.run(run_children())
        values = [json.loads(item)["correlation_id"] for item in capture.snapshot()]
        assert values.count("left") == 2
        assert values.count("right") == 2
        assert values.count("left-nested") == 1
        assert values.count("right-nested") == 1
        logger.info("outside")
        assert json.loads(capture.snapshot()[-1])["correlation_id"] is None
    finally:
        logger.removeHandler(capture)
        capture.close()


def test_bounded_capture_and_validation() -> None:
    with pytest.raises(ValueError, match="capacity"):
        DiagnosticCaptureHandler(0)
    capture = DiagnosticCaptureHandler(2)
    for message in ("one", "two", "three"):
        capture.handle(logging.makeLogRecord({"name": "test", "msg": message}))
    entries = capture.snapshot()
    assert len(entries) == 2
    assert "two" in entries[0]
    assert "three" in entries[1]


def test_explicit_configuration_rotates_and_is_idempotent(tmp_path: Path) -> None:
    stream = io.StringIO()
    logger = configure_host_logging(
        tmp_path,
        console_stream=stream,
        file_format="text",
        max_bytes=120,
        backup_count=2,
    )
    original_handlers = tuple(logger.handlers)
    assert (
        configure_host_logging(
            tmp_path,
            console_stream=stream,
            file_format="text",
            max_bytes=120,
            backup_count=2,
        )
        is logger
    )
    assert tuple(logger.handlers) == original_handlers
    for index in range(12):
        logger.info("event %02d", index)
    assert host_log_path(tmp_path).exists()
    assert len(list(tmp_path.glob("haruquantai.log*"))) == 3
    assert "event" in stream.getvalue()
    assert "\x1b[" not in stream.getvalue()
    logger = configure_host_logging(tmp_path, include_console=False)
    assert len(logger.handlers) == 1


def test_default_file_sink_emits_sanitized_json_lines(tmp_path: Path) -> None:
    logger = configure_host_logging(tmp_path, include_console=False)
    logger.warning(
        "token=synthetic-file-message",
        extra={"fields": {"password": "synthetic-file-field", "ratio": float("nan")}},
    )
    line = host_log_path(tmp_path).read_text(encoding="utf-8").strip()
    assert "synthetic-file-message" not in line
    assert "synthetic-file-field" not in line
    payload = json.loads(line, parse_constant=pytest.fail)
    assert payload["message"].startswith("token=[REDACTED:")
    assert payload["fields"]["password"].startswith("[REDACTED:")
    assert payload["fields"]["ratio"] == "nan"


def test_invalid_configuration_has_no_file_effect(tmp_path: Path) -> None:
    for kwargs in (
        {"max_bytes": 0},
        {"backup_count": -1},
        {"file_format": "invalid"},
    ):
        with pytest.raises(ValueError):
            configure_host_logging(tmp_path / "logs", **kwargs)
    assert not (tmp_path / "logs").exists()


def test_import_does_not_install_handlers_or_create_files(tmp_path: Path) -> None:
    code = (
        "import logging; import app.host.logging; "
        "assert not logging.getLogger('app').handlers; "
        "assert not logging.getLogger('haruquantai').handlers"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert not host_log_path(tmp_path).exists()


def test_filter_sanitizes_message_without_changing_admission() -> None:
    record = logging.makeLogRecord(
        {"name": "test", "msg": "password=%s", "args": ("synthetic-value",)}
    )
    assert SensitiveDataFilter().filter(record)
    assert "synthetic-value" not in record.getMessage()


def test_get_logger_resolves_host_hierarchy() -> None:
    assert get_logger().name == "app"
    assert get_logger(None).name == "app"
    assert get_logger("").name == "app"
    assert get_logger("app").name == "app"
    assert get_logger("__main__").name == "app.main"
    assert get_logger("app.host.settings").name == "app.host.settings"
    assert get_logger("app.host.hardware").name == "app.host.hardware"
    assert get_logger("app.workspace.data").name == "app.workspace.data"
    assert get_logger("host.settings").name == "app.host.settings"
    assert get_logger("hardware").name == "app.hardware"
    child = get_logger("app.host.settings")
    assert child.propagate is True


def test_get_logger_does_not_implicitly_configure_console(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stream)
    logger = get_logger("app.test.lazy")
    root = logging.getLogger("app")
    assert not root.handlers
    logger.info("lazy message")
    assert not root.handlers
    assert "lazy message" not in stream.getvalue()


def test_early_boot_records_and_uvicorn_are_forwarded(tmp_path: Path) -> None:
    from app.host.logging import close_host_logging, configure_boot_logging

    close_host_logging()
    configure_boot_logging()
    get_logger("app.main").info("B02 early configuration")
    configure_host_logging(tmp_path, include_console=False)
    logging.getLogger("uvicorn.error").warning("server diagnostic")
    close_host_logging()
    text = host_log_path(tmp_path).read_text()
    assert "B02 early configuration" in text
    assert "server diagnostic" in text
    assert not logging.getLogger("app").handlers
    assert not any(
        getattr(handler, "_host_telemetry_owned", False)
        for handler in logging.getLogger("uvicorn").handlers
    )
