"""Queued application logging with automatic setup on first get_logger() call.

Use get_logger(__name__) in application modules. Call shutdown_logging()
after producers stop to drain pending records (also registered with atexit).
File rotation supports one host process per log path.
"""

from __future__ import annotations

import atexit
import copy
import logging
import logging.handlers
import queue
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import TextIO, override

_FORMAT = (
    "%(asctime)s.%(msecs)03d | %(levelname)s | "
    "%(module)s:%(funcName)s:%(lineno)d - %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 10 * 1024 * 1024
_RETENTION_SECONDS = 30 * 24 * 60 * 60
_RETRY_ATTEMPTS = 5
_LOCK = threading.RLock()
_listener: logging.handlers.QueueListener | None = None
_queue_handler: logging.Handler | None = None
_previous_level = logging.WARNING


class _ConsoleFormatter(logging.Formatter):
    """Color the level and message while leaving source information readable."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        record = copy.copy(record)
        color = {
            logging.DEBUG: "\x1b[36m",
            logging.INFO: "\x1b[32m",
            logging.WARNING: "\x1b[33m",
            logging.ERROR: "\x1b[31m",
            logging.CRITICAL: "\x1b[35m",
        }.get(record.levelno, "\x1b[37m")
        record.levelname = f"{color}{record.levelname}\x1b[0m"
        record.msg = f"{color}{record.getMessage()}\x1b[0m"
        record.args = None
        return super().format(record)


class _QueueHandler(logging.handlers.QueueHandler):
    """Defer message interpolation and traceback formatting to the worker."""

    @override
    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        return copy.copy(record)


class SafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Rotate to unique archives and tolerate transient Windows sharing locks.

    Exhausted lock retries leave the current file in place; the record is still
    written and rotation is attempted again on the next record. Retention is
    checked at startup and on rotation, using archive modification times.
    """

    def __init__(self, filename: Path) -> None:
        filename.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename, maxBytes=_MAX_BYTES, encoding="utf-8")
        self._prune_archives()

    def _prune_archives(self) -> None:
        path = Path(self.baseFilename)
        cutoff = time.time() - _RETENTION_SECONDS
        for archive in path.parent.glob(f"{path.name}.*.log"):
            try:
                if archive.stat().st_mtime < cutoff:
                    archive.unlink()
            except OSError:
                # Locked archives are retried during the next retention sweep.
                continue

    @override
    def doRollover(self) -> None:
        if self.stream is not None:
            self.stream.close()
            self.stream = None
        path = Path(self.baseFilename)
        archive = path.with_name(f"{path.name}.{time.time_ns()}.{uuid.uuid4().hex}.log")
        try:
            for attempt in range(_RETRY_ATTEMPTS):
                try:
                    path.rename(archive)
                    break
                except PermissionError:
                    if attempt < _RETRY_ATTEMPTS - 1:
                        time.sleep(0.05 * 2**attempt)
                except FileNotFoundError:
                    break
        finally:
            self.stream = self._open()
        self._prune_archives()


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a standard logger, initializing default logging once on first use.

    Explicit setup_logging() settings are preserved by subsequent calls. Setup is
    serialized so concurrent module imports do not install duplicate handlers.
    """
    with _LOCK:
        if _listener is None:
            setup_logging()
        return logging.getLogger(name)


def setup_logging(
    level: int | str = logging.INFO,
    *,
    log_path: str | Path | None = None,
    console: TextIO | None = None,
    color: bool | None = None,
) -> None:
    """Install queued root logging, replacing any previous setup from this module.

    Existing external handlers are preserved. Colors default to terminal detection.
    The unbounded in-process queue avoids waiting for file or console I/O; callers
    should not mutate message arguments after enqueueing. Default paths are rooted
    at the repository, independent of the current working directory.
    """
    global _listener, _queue_handler, _previous_level  # noqa: PLW0603
    with _LOCK:
        shutdown_logging()
        root = logging.getLogger()
        resolved_level = (
            logging.getLevelNamesMapping()[level.upper()]
            if isinstance(level, str)
            else level
        )
        path = (
            Path(log_path)
            if log_path is not None
            else Path(__file__).resolve().parents[2] / "data" / "logs" / "app.log"
        )
        file_handler = SafeRotatingFileHandler(path)
        file_handler.setFormatter(logging.Formatter(_FORMAT, _DATE_FORMAT))
        stream = console if console is not None else sys.stderr
        console_handler = logging.StreamHandler(stream)
        use_color = stream.isatty() if color is None else color
        formatter = _ConsoleFormatter if use_color else logging.Formatter
        console_handler.setFormatter(formatter(_FORMAT, _DATE_FORMAT))
        records: queue.Queue[logging.LogRecord] = queue.Queue()
        handler = _QueueHandler(records)
        listener = logging.handlers.QueueListener(
            records, console_handler, file_handler, respect_handler_level=True
        )
        listener.start()
        _previous_level = root.level
        root.setLevel(resolved_level)
        root.addHandler(handler)
        _queue_handler = handler
        _listener = listener


def shutdown_logging() -> None:
    """Detach the queue, drain pending records, and close owned handlers."""
    global _listener, _queue_handler  # noqa: PLW0603
    with _LOCK:
        if _listener is None:
            return
        root = logging.getLogger()
        if _queue_handler is not None:
            root.removeHandler(_queue_handler)
            _queue_handler.close()
        _listener.stop()
        for handler in _listener.handlers:
            handler.close()
        root.setLevel(_previous_level)
        _listener = None
        _queue_handler = None


atexit.register(shutdown_logging)


if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
