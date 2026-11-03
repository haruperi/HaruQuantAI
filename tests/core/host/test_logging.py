import io
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from unittest.mock import patch

from app.core.host.logging import (
    CLILogger,
    DuplicateLogFilter,
    SafeRotatingFileHandler,
    SensitiveDataFilter,
    activate_debug_logging,
    configure_logging_from_settings,
    emit_startup_diagnostics,
    get_logger,
    redact_sensitive_text,
    redirect_cli_output,
    setup_logging,
    shutdown_logging,
)


def test_get_logger_initializes_once_under_concurrent_access(tmp_path: Path) -> None:
    path = tmp_path / "app.log"
    shutdown_logging()
    original_setup = setup_logging

    def configure() -> None:
        original_setup(log_path=path, console=io.StringIO())

    try:
        with patch(
            "app.core.host.logging.setup_logging", side_effect=configure
        ) as setup:
            with ThreadPoolExecutor(max_workers=8) as executor:
                loggers = list(executor.map(get_logger, ["automatic"] * 32))
            assert setup.call_count == 1
        assert all(logger is loggers[0] for logger in loggers)
        loggers[0].info("automatic setup")
    finally:
        shutdown_logging()
    assert path.read_text().count("automatic setup") == 1


def test_get_logger_preserves_explicit_configuration(tmp_path: Path) -> None:
    path = tmp_path / "custom.log"
    setup_logging(logging.DEBUG, log_path=path, console=io.StringIO())
    try:
        with patch("app.core.host.logging.setup_logging") as setup:
            get_logger(__name__).debug("custom configuration")
            setup.assert_not_called()
    finally:
        shutdown_logging()
    assert "custom configuration" in path.read_text()


def test_format_colors_traceback_and_drain(tmp_path: Path) -> None:
    output = io.StringIO()
    path = tmp_path / "app.log"
    setup_logging(log_path=path, console=output, color=True)
    try:
        logging.getLogger(__name__).info("hello %s", "world")
        try:
            raise ValueError("failure")
        except ValueError:
            logging.getLogger(__name__).exception("caught")
    finally:
        shutdown_logging()
    content = path.read_text(encoding="utf-8")
    assert re.search(
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \| INFO \| "
        r"test_logging:test_format_colors_traceback_and_drain:\d+ - hello world",
        content,
    )
    assert "ValueError: failure" in content
    assert "\x1b[" not in content
    assert "\x1b[32mINFO\x1b[0m" in output.getvalue()
    assert "\x1b[32mhello world\x1b[0m" in output.getvalue()


def test_slow_output_does_not_block_producer(tmp_path: Path) -> None:
    entered = threading.Event()
    release = threading.Event()

    class SlowStream(io.StringIO):
        def write(self, text: str) -> int:
            entered.set()
            assert release.wait(5)
            return super().write(text)

    setup_logging(log_path=tmp_path / "app.log", console=SlowStream())
    try:
        logging.getLogger(__name__).info("first")
        assert entered.wait(5)
        logging.getLogger(__name__).info("second")
    finally:
        release.set()
        shutdown_logging()
    assert "second" in (tmp_path / "app.log").read_text()


def test_rotation_retention_and_windows_lock_recovery(tmp_path: Path) -> None:
    path = tmp_path / "app.log"
    old = tmp_path / "app.log.old.log"
    old.write_text("old")
    expired = time.time() - 31 * 86400
    os.utime(old, (expired, expired))
    handler = SafeRotatingFileHandler(path)
    handler.maxBytes = 10
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "message", (), None)
    try:
        assert not old.exists()
        handler.emit(record)
        with (
            patch.object(Path, "rename", side_effect=PermissionError),
            patch("app.core.host.logging.time.sleep") as sleep,
        ):
            handler.emit(record)
            assert sleep.call_count == 4
        assert path.read_text().count("message") == 2
        handler.emit(record)
        archives = list(tmp_path.glob("app.log.*.log"))
        assert len(archives) == 1
        assert archives[0].read_text().count("message") == 2
        assert path.read_text().count("message") == 1
    finally:
        handler.close()


def test_redact_sensitive_text_and_filter() -> None:
    assert redact_sensitive_text("") == ""
    bearer = "Authorization: Bearer super-secret-token-xyz123"
    assert redact_sensitive_text(bearer) == "Authorization: Bearer [REDACTED]"

    basic = "Authorization: Basic dXNlcjpwYXNz"
    assert redact_sensitive_text(basic) == "Authorization: Basic [REDACTED]"

    pass_kv = "User password=super_secret_value123 logged in"
    assert redact_sensitive_text(pass_kv) == "User password=[REDACTED] logged in"

    json_kv = '{"api_key": "abc12345", "auth_token": "tok789"}'
    redacted_json = redact_sensitive_text(json_kv)
    assert "abc12345" not in redacted_json
    assert "tok789" not in redacted_json

    url = "https://admin:secret123@api.broker.com/v1"
    assert redact_sensitive_text(url) == "https://admin:[REDACTED]@api.broker.com/v1"

    flt = SensitiveDataFilter()
    rec = logging.LogRecord(
        "test",
        logging.INFO,
        __file__,
        1,
        "token=secret_val",
        (),
        None,
    )
    assert flt.filter(rec)
    assert rec.msg == "token=[REDACTED]"

    rec_args = logging.LogRecord(
        "test",
        logging.INFO,
        __file__,
        1,
        "Key: %s",
        ("api_key=secret99",),
        None,
    )
    assert flt.filter(rec_args)
    assert rec_args.args == ("api_key=[REDACTED]",)

    rec_dict_args = logging.LogRecord(
        "test",
        logging.INFO,
        __file__,
        1,
        "payload",
        {"secret": "xyz123", "num": 42},
        None,
    )
    assert flt.filter(rec_dict_args)
    assert rec_dict_args.args == {"secret": "[REDACTED]", "num": 42}


def test_duplicate_log_filter() -> None:
    flt = DuplicateLogFilter(
        allowed_repetitions=3, expire_seconds=5.0, max_cache_size=4
    )
    empty_rec = logging.LogRecord("test", logging.INFO, __file__, 1, "", (), None)
    assert flt.filter(empty_rec)

    rep_rec = logging.LogRecord(
        "test", logging.INFO, __file__, 1, "repeated message", (), None
    )
    assert flt.filter(rep_rec) is True
    assert flt.filter(rep_rec) is True
    assert flt.filter(rep_rec) is True
    # Exceeded repetition limit of 3
    assert flt.filter(rep_rec) is False

    # Simulate TTL expiration
    with patch("app.core.host.logging.time.time", return_value=time.time() + 10.0):
        assert flt.filter(rep_rec) is True

    # Simulate cache overflow to trigger prune
    for i in range(10):
        r = logging.LogRecord("test", logging.INFO, __file__, 1, f"msg_{i}", (), None)
        flt.filter(r)
    assert len(flt._cache) <= 4


def test_activate_debug_logging_and_settings() -> None:
    class MockTroubleView:
        debug_level_active = True

    class MockSettings:
        config_troubleshooting = MockTroubleView()

    settings = MockSettings()
    assert configure_logging_from_settings(settings) is True
    assert logging.getLogger().level == logging.DEBUG

    MockTroubleView.debug_level_active = False
    assert configure_logging_from_settings(settings) is False
    assert logging.getLogger().level == logging.INFO

    # Test get_bool fallback
    class MockGetBoolSettings:
        def get_bool(self, scope: str, key: str, default: bool = False) -> bool:
            return scope == "config_troubleshooting" and key == "debug_level_active"

    assert configure_logging_from_settings(MockGetBoolSettings()) is True

    # Test get fallback
    class MockGetSettings:
        def get(self, scope: str, key: str, default: Any = None) -> Any:
            return True if scope == "config_troubleshooting" else False

    assert configure_logging_from_settings(MockGetSettings()) is True

    # Test invalid settings object
    assert configure_logging_from_settings(None) is False
    assert configure_logging_from_settings(12345) is False

    # Programmatic toggle
    assert activate_debug_logging(True) is True
    assert logging.getLogger().level == logging.DEBUG
    assert activate_debug_logging(False) is False
    assert logging.getLogger().level == logging.INFO


def test_emit_startup_diagnostics(tmp_path: Path) -> None:
    res = emit_startup_diagnostics(app_version="2.1.0", root_path=tmp_path)
    assert res["app_version"] == "2.1.0"
    assert "computer_name" in res
    assert "user_name" in res
    assert "timezone" in res
    assert "python_version" in res
    assert "platform" in res
    assert res["hardware"]["logical_cores"] >= 1
    assert str(tmp_path) in res["writable_directories"]

    # Test hardware fallback when probe raises
    with patch(
        "app.core.host.resources.probe_hardware",
        side_effect=RuntimeError("probe failure"),
    ):
        fallback_res = emit_startup_diagnostics(app_version="1.0.0", root_path=tmp_path)
        assert fallback_res["hardware"]["logical_cores"] >= 1

    # Test non-writable directory detection
    with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
        ro_res = emit_startup_diagnostics(
            app_version="1.0.0", root_path=tmp_path / "ro"
        )
        assert any(not v for v in ro_res["writable_directories"].values())


def test_cli_logger(tmp_path: Path) -> None:
    logger = CLILogger.get_instance()
    assert logger is CLILogger.get_instance()

    # Empty or whitespace message is no-op
    logger.log("   ")
    logger.log("{}")

    # Logging without file redirection
    logger.log("terminal output<br>line2", add_separator=True)

    # Redirection to file
    out_file = tmp_path / "cli_output.txt"
    redirect_cli_output(out_file)
    logger.log("first task log")
    logger.log("second task log", add_separator=True)
    redirect_cli_output(None)

    content = out_file.read_text(encoding="utf-8")
    assert "first task log" in content
    assert "second task log" in content
    assert "--------------------------------------------------" in content


def test_setup_logging_parameters(tmp_path: Path) -> None:
    path = tmp_path / "app_custom.log"
    setup_logging(
        level="DEBUG",
        log_path=path,
        filter_duplicates=False,
        redact_secrets=False,
    )
    try:
        rec = logging.getLogger("test_custom")
        rec.debug("custom debug message")
    finally:
        shutdown_logging()
    assert "custom debug message" in path.read_text(encoding="utf-8")
