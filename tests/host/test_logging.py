import io
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from app.host.logging import (
    SafeRotatingFileHandler,
    get_logger,
    setup_logging,
    shutdown_logging,
)


def test_get_logger_initializes_once_under_concurrent_access(tmp_path):
    path = tmp_path / "app.log"
    shutdown_logging()
    original_setup = setup_logging

    def configure():
        original_setup(log_path=path, console=io.StringIO())

    try:
        with patch("app.host.logging.setup_logging", side_effect=configure) as setup:
            with ThreadPoolExecutor(max_workers=8) as executor:
                loggers = list(executor.map(get_logger, ["automatic"] * 32))
            assert setup.call_count == 1
        assert all(logger is loggers[0] for logger in loggers)
        loggers[0].info("automatic setup")
    finally:
        shutdown_logging()
    assert path.read_text().count("automatic setup") == 1


def test_get_logger_preserves_explicit_configuration(tmp_path):
    path = tmp_path / "custom.log"
    setup_logging(logging.DEBUG, log_path=path, console=io.StringIO())
    try:
        with patch("app.host.logging.setup_logging") as setup:
            get_logger(__name__).debug("custom configuration")
            setup.assert_not_called()
    finally:
        shutdown_logging()
    assert "custom configuration" in path.read_text()


def test_format_colors_traceback_and_drain(tmp_path):
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


def test_slow_output_does_not_block_producer(tmp_path):
    entered = threading.Event()
    release = threading.Event()

    class SlowStream(io.StringIO):
        def write(self, text):
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


def test_rotation_retention_and_windows_lock_recovery(tmp_path):
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
            patch("app.host.logging.time.sleep") as sleep,
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
