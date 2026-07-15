import json
import logging
import os
import subprocess
import sys
import time
import zipfile
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.utils import (
    BoundLogger,
    ConfigurationError,
    LoggingSettings,
    RedactingFilter,
    StructuredFormatter,
    configure_logging,
    flush_logging,
    get_logger,
    shutdown_logging,
)
from app.utils import (
    logger as global_logger,
)


@pytest.fixture(autouse=True)
def _reset_logging() -> Iterator[None]:
    """Stop queue threads and close file sinks after every test."""
    yield
    shutdown_logging()


def test_get_logger_configures_no_handlers() -> None:
    logger = get_logger("unit.no_handlers")
    assert logger.handlers == []


def test_default_configuration_creates_all_sinks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    configure_logging()
    root = logging.getLogger("haruquant")
    owned = [
        handler
        for handler in root.handlers
        if handler.__class__.__module__ == "app.utils.logging.logger"
    ]
    assert len(owned) == 1
    global_logger.info("default profile")
    shutdown_logging()
    log_directory = tmp_path / "data" / "logs"
    assert {path.name for path in log_directory.iterdir()} == {
        "access.log",
        "app.log",
        "debug.log",
        "errors.log",
    }
    console_output = capsys.readouterr().out
    assert not console_output.startswith("\033[")
    assert "| \033[32mINFO    \033[0m |" in console_output
    assert " - \033[32mdefault profile\033[0m" in console_output


def test_first_bound_log_activates_default_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    global_logger.info("lazy default profile")
    shutdown_logging()

    assert "lazy default profile" in capsys.readouterr().out
    assert {path.name for path in (tmp_path / "data" / "logs").iterdir()} == {
        "access.log",
        "app.log",
        "debug.log",
        "errors.log",
    }


def test_first_bound_log_is_thread_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(global_logger.info, (f"record-{index}" for index in range(8)))
        )
    flush_logging()

    owned = [
        handler
        for handler in logging.getLogger("haruquant").handlers
        if handler.__class__.__module__ == "app.utils.logging.logger"
    ]
    assert len(owned) == 1
    app_log = (tmp_path / "data" / "logs" / "app.log").read_text(encoding="utf-8")
    assert all(f"record-{index}" in app_log for index in range(8))


def test_explicit_configuration_is_not_replaced_by_lazy_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    configure_logging(
        LoggingSettings(
            level="ERROR",
            log_directory=None,
            enqueue=False,
        )
    )

    global_logger.info("suppressed by explicit profile")

    assert logging.getLogger("haruquant").level == logging.ERROR
    assert not (tmp_path / "data" / "logs").exists()


def test_redacting_filter_runs_before_formatting() -> None:
    record = logging.LogRecord(
        "haruquant.test",
        logging.INFO,
        __file__,
        1,
        "token=abc123",
        (),
        None,
    )
    assert RedactingFilter().filter(record)
    assert "abc123" not in record.getMessage()


def test_structured_formatter_includes_trace_ids() -> None:
    record = logging.makeLogRecord(
        {
            "name": "haruquant.test",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": "ready",
            "request_id": "req-example",
        }
    )
    RedactingFilter().filter(record)
    output = json.loads(StructuredFormatter("json").format(record))
    assert output["request_id"] == "req-example"


def test_human_formatter_uses_source_aware_layout() -> None:
    record = logging.LogRecord(
        "haruquant",
        logging.INFO,
        "usage.py",
        8,
        "General system status updates.",
        (),
        None,
        func="<module>",
    )
    record.created = datetime(2026, 7, 14, 17, 47, 2, 123_000, tzinfo=UTC).timestamp()
    record._source_module = "__main__"
    RedactingFilter().filter(record)

    assert StructuredFormatter().format(record) == (
        "2026-07-14 17:47:02.123 | INFO     | "
        "__main__:<module>:8 - General system status updates."
    )


def test_human_formatter_colors_only_level_and_message() -> None:
    record = logging.LogRecord(
        "haruquant",
        logging.INFO,
        "usage.py",
        8,
        "General system status updates.",
        (),
        None,
        func="<module>",
    )
    record.created = datetime(2026, 7, 14, 17, 47, 2, 123_000, tzinfo=UTC).timestamp()
    record._source_module = "__main__"
    record.request_id = "REQ-1002"
    RedactingFilter().filter(record)

    assert StructuredFormatter(colorize=True).format(record) == (
        "2026-07-14 17:47:02.123 | \033[32mINFO    \033[0m | "
        "__main__:<module>:8 - \033[32mGeneral system status updates. | "
        "request_id=REQ-1002\033[0m"
    )


def test_sink_failure_uses_safe_fallback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_parent = tmp_path / "missing" / "app.log"
    with pytest.raises(ConfigurationError):
        configure_logging(LoggingSettings(file_path=missing_parent))
    assert "logging_configuration_failed" in capsys.readouterr().err


def test_configure_logging_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    configure_logging()
    configure_logging()
    owned = [
        handler
        for handler in logging.getLogger("haruquant").handlers
        if handler.__class__.__module__ == "app.utils.logging.logger"
    ]
    assert len(owned) == 1


def test_import_registers_no_handlers() -> None:
    command = (
        "import logging; import app.utils; "
        "print(len(logging.getLogger('haruquant').handlers))"
    )
    completed = subprocess.run(  # noqa: S603 - fixed interpreter and source.
        [sys.executable, "-c", command],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "0"


def test_import_time_bound_log_does_not_activate_defaults(tmp_path: Path) -> None:
    probe = tmp_path / "lazy_logging_probe.py"
    probe.write_text(
        "from app.utils import logger\nlogger.info('import-time record')\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(tmp_path), environment.get("PYTHONPATH", "")))
    )
    command = (
        "import logging; import lazy_logging_probe; "
        "print(len(logging.getLogger('haruquant').handlers))"
    )

    completed = subprocess.run(  # noqa: S603 - fixed interpreter and source.
        [sys.executable, "-c", command],
        check=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[3],
        env=environment,
    )

    assert completed.stdout.strip() == "0"
    assert not (tmp_path / "data" / "logs").exists()


def test_configure_logging_applies_log_level() -> None:
    configure_logging(LoggingSettings(level="ERROR", log_directory=None, enqueue=False))
    assert logging.getLogger("haruquant").level == logging.ERROR


def test_bound_logger_preserves_context(tmp_path: Path) -> None:
    configure_logging(
        LoggingSettings(
            level="DEBUG",
            file_path=tmp_path / "app.log",
            log_directory=None,
            enqueue=False,
            render="json",
        )
    )
    first = global_logger.bind(request_id="REQ-1002")
    second = first.bind(user_id="USER-A")
    assert isinstance(second, BoundLogger)
    first.info("first")
    second.info("second")
    records = [
        json.loads(line)
        for line in (tmp_path / "app.log").read_text(encoding="utf-8").splitlines()
    ]
    assert "user_id" not in records[0]
    assert records[1]["request_id"] == "REQ-1002"
    assert records[1]["user_id"] == "USER-A"


def test_specialized_log_routing(tmp_path: Path) -> None:
    configure_logging(
        LoggingSettings(level="DEBUG", log_directory=tmp_path, render="json")
    )
    global_logger.bind(log_type="access").info("access event")
    global_logger.bind(log_type="debug").info("developer event")
    global_logger.debug("debug-level event")
    global_logger.error("error event")
    global_logger.critical("critical event")
    global_logger.info("general event")
    shutdown_logging()
    access_log = (tmp_path / "access.log").read_text(encoding="utf-8")
    debug_log = (tmp_path / "debug.log").read_text(encoding="utf-8")
    app_log = (tmp_path / "app.log").read_text(encoding="utf-8")
    error_log = (tmp_path / "errors.log").read_text(encoding="utf-8")
    assert "access event" in access_log
    assert "general event" not in access_log
    assert "developer event" not in debug_log
    assert "debug-level event" in debug_log
    assert "general event" in app_log
    assert "error event" in error_log
    assert "critical event" in error_log
    assert "general event" not in error_log


def test_exception_logging_includes_traceback(tmp_path: Path) -> None:
    configure_logging(
        LoggingSettings(
            file_path=tmp_path / "app.log",
            log_directory=None,
            render="json",
        )
    )
    try:
        _ = 1 / 0
    except ZeroDivisionError:
        global_logger.exception("captured")
    shutdown_logging()
    record = json.loads((tmp_path / "app.log").read_text(encoding="utf-8"))
    assert "ZeroDivisionError" in record["exception"]


def test_flush_logging_synchronizes_delivery_without_shutdown(tmp_path: Path) -> None:
    log_path = tmp_path / "app.log"
    configure_logging(
        LoggingSettings(
            file_path=log_path,
            log_directory=None,
            colorize=False,
        )
    )

    global_logger.info("first queued record")
    flush_logging()
    assert "first queued record" in log_path.read_text(encoding="utf-8")

    global_logger.info("second queued record")
    flush_logging()
    assert "second queued record" in log_path.read_text(encoding="utf-8")


def test_zip_rollover_and_shutdown(tmp_path: Path) -> None:
    configure_logging(
        LoggingSettings(
            log_directory=tmp_path,
            max_bytes=1_024,
            backup_count=10,
            retention_days=10,
            compression="zip",
            enqueue=True,
            colorize=False,
        )
    )
    expired = tmp_path / "app.log.9.zip"
    expired.write_text("expired", encoding="utf-8")
    old_timestamp = time.time() - (11 * 86_400)
    os.utime(expired, (old_timestamp, old_timestamp))
    for index in range(30):
        global_logger.debug("rollover %s %s", index, "x" * 200)
    shutdown_logging()

    archives = sorted(tmp_path.glob("app.log.*.zip"))
    assert archives
    assert all(zipfile.is_zipfile(archive) for archive in archives)
    cutoff = time.time() - (10 * 86_400)
    assert all(archive.stat().st_mtime >= cutoff for archive in archives)
