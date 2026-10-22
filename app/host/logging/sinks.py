"""Console, rotating-file, and in-memory telemetry sinks."""

from __future__ import annotations

import collections
import contextlib
import copy
import logging
import logging.handlers
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

from .formatting import LogEventFormatter
from .security import _boundary_diagnostic, normalize_path, redact_value

SINKS_FR = "FR-HOST-LOGGING-SINKS"
RING_BUFFER_FR = "FR-HOST-LOGGING-RING-BUFFER"
DEFAULT_RING_BUFFER_CAPACITY = 2000
MAX_LOG_FILE_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 30
_MAX_RENAME_RETRIES = 5
_RENAME_RETRY_DELAY_SEC = 0.05
_WS_SINKS: list[Callable[[dict[str, Any]], None]] = []
_WS_SINKS_LOCK = threading.Lock()


def register_ws_sink(sink: Callable[[dict[str, Any]], None]) -> None:
    """Register a live log receiver without duplicates."""
    with _WS_SINKS_LOCK:
        if sink not in _WS_SINKS:
            _WS_SINKS.append(sink)


def clear_ws_sinks() -> None:
    """Release subscriptions at host shutdown."""
    with _WS_SINKS_LOCK:
        _WS_SINKS.clear()


class _SafeStreamHandler(logging.StreamHandler[Any]):
    """Keep console failures from echoing unsanitized records."""

    @override
    def handleError(self, record: logging.LogRecord) -> None:
        _boundary_diagnostic()


class WindowsSafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """RotatingFileHandler with Windows-safe retry logic for locked files."""

    def __init__(
        self,
        filename: str | Path,
        *,
        mode: str = "a",
        maxBytes: int = MAX_LOG_FILE_BYTES,  # noqa: N803
        backupCount: int = LOG_BACKUP_COUNT,  # noqa: N803
        encoding: str = "utf-8",
        delay: bool = True,
        errors: str | None = None,
    ) -> None:
        """Initialize WindowsSafeRotatingFileHandler with 10MB limit and 30 backups."""
        super().__init__(
            str(filename),
            mode=mode,
            maxBytes=maxBytes,
            backupCount=backupCount,
            encoding=encoding,
            delay=delay,
            errors=errors,
        )

    @override
    def handleError(self, record: logging.LogRecord) -> None:
        """Report sink failure without echoing unsanitized records."""
        _boundary_diagnostic()

    @override
    def doRollover(self) -> None:
        """Perform rollover with explicit stream closure and Windows lock retry."""
        if self.stream is not None:
            self.stream.flush()
            self.stream.close()
            self.stream = None

        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(f"{self.baseFilename}.{i}")
                dfn = self.rotation_filename(f"{self.baseFilename}.{i + 1}")
                if Path(sfn).exists():
                    self._safe_rename(sfn, dfn)
            dfn = self.rotation_filename(f"{self.baseFilename}.1")
            if Path(self.baseFilename).exists():
                self._safe_rename(self.baseFilename, dfn)

        if not self.delay:
            self.stream = self._open()

    def _safe_rename(self, source: str, destination: str) -> None:
        """Rename source to destination with retries on Windows PermissionError."""
        if Path(destination).exists():
            with contextlib.suppress(OSError):
                Path(destination).unlink()

        for attempt in range(_MAX_RENAME_RETRIES):
            try:
                Path(source).rename(destination)
                return
            except (PermissionError, FileExistsError):
                if attempt < _MAX_RENAME_RETRIES - 1:
                    time.sleep(_RENAME_RETRY_DELAY_SEC)
                else:
                    raise  # Report a failed rotation; do not pretend it succeeded.


class LogRingBuffer:
    """Thread-safe in-memory ring buffer holding recent structured log records."""

    def __init__(self, maxlen: int = DEFAULT_RING_BUFFER_CAPACITY) -> None:
        """Initialize ring buffer with bounded capacity."""
        self._buffer: collections.deque[dict[str, Any]] = collections.deque(
            maxlen=maxlen
        )
        self._lock: threading.Lock = threading.Lock()

    @property
    def maxlen(self) -> int:
        """Return maximum ring buffer capacity."""
        return self._buffer.maxlen or DEFAULT_RING_BUFFER_CAPACITY

    def append(self, entry: dict[str, Any]) -> None:
        """Append a structured log entry into the buffer."""
        with self._lock:
            self._buffer.append(entry)

    def query(
        self,
        *,
        limit: int | None = None,
        min_level: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve snapshot of recent records with optional level filtering."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        threshold = level_map.get(min_level.upper(), 0) if min_level else 0

        with self._lock:
            records = list(self._buffer)

        if threshold > 0:
            records = [
                r
                for r in records
                if level_map.get(str(r.get("level", "")).upper(), 0) >= threshold
            ]
        if limit is not None and limit > 0:
            records = records[-limit:]
        return records

    def clear(self) -> None:
        """Clear all records from ring buffer."""
        with self._lock:
            self._buffer.clear()

    def __len__(self) -> int:
        """Return number of entries currently stored."""
        with self._lock:
            return len(self._buffer)


class RingBufferHandler(logging.Handler):
    """Logging handler routing structured records into the in-memory ring buffer."""

    def __init__(
        self,
        ring_buffer: LogRingBuffer,
        publish_log: Callable[[dict[str, Any]], None] | None = None,
        *,
        correlation_id_getter: Callable[[], str | None] | None = None,
    ) -> None:
        """Initialize with target LogRingBuffer."""
        super().__init__()
        self.ring_buffer = ring_buffer
        self.publish_log = publish_log
        self._correlation_id_getter = correlation_id_getter

    @override
    def emit(self, record: logging.LogRecord) -> None:
        """Emit structured dictionary entry into the ring buffer and WS sinks."""
        try:
            record_dt = datetime.fromtimestamp(record.created, tz=UTC)
            time_str = (
                record_dt.strftime("%Y-%m-%d %H:%M:%S") + f".{int(record.msecs):03d}"
            )
            safe_record = copy.copy(record)
            safe_record.args = redact_value(
                record.args, fingerprint=True
            )
            raw_msg = safe_record.getMessage()
            clean_msg = normalize_path(str(redact_value(raw_msg, fingerprint=True)))
            caller = f"{record.name}:{record.funcName}:{record.lineno}"

            entry = {
                "timestamp": time_str,
                "name": record.name,
                "level": record.levelname,
                "caller": caller,
                "message": clean_msg,
                "fr_id": getattr(record, "fr_id", None),
                "correlation_id": getattr(record, "correlation_id", None)
                or (
                    self._correlation_id_getter()
                    if self._correlation_id_getter is not None
                    else None
                ),
            }
            self.ring_buffer.append(entry)
            if getattr(record, "fr_id", None) != "FR-HOST-TRANSPORT-EVENT-BUS":
                if self.publish_log is not None:
                    try:
                        self.publish_log(entry)
                    except Exception:  # noqa: BLE001
                        _boundary_diagnostic()
                with _WS_SINKS_LOCK:
                    ws_sinks = list(_WS_SINKS)
                for ws_sink in ws_sinks:
                    try:
                        ws_sink(entry)
                    except Exception:  # noqa: BLE001
                        _boundary_diagnostic()
        except Exception:  # noqa: BLE001
            _boundary_diagnostic()


def _build_sinks(
    target_dir: Path,
    level: int,
    ring_buffer: LogRingBuffer,
    publish_log: Callable[[dict[str, Any]], None] | None = None,
    correlation_id_getter: Callable[[], str | None] | None = None,
) -> list[logging.Handler]:
    """Construct console, rotating file, and ring buffer downstream sinks."""
    console_formatter = LogEventFormatter(colorize=True)
    file_formatter = LogEventFormatter(colorize=False)

    console_handler = _SafeStreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)

    app_file_handler = WindowsSafeRotatingFileHandler(
        target_dir / "app.log",
        maxBytes=MAX_LOG_FILE_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
        delay=True,
    )
    app_file_handler.setLevel(logging.DEBUG)
    app_file_handler.setFormatter(file_formatter)

    errors_file_handler = WindowsSafeRotatingFileHandler(
        target_dir / "errors.log",
        maxBytes=MAX_LOG_FILE_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
        delay=True,
    )
    errors_file_handler.setLevel(logging.WARNING)
    errors_file_handler.setFormatter(file_formatter)

    ring_handler = RingBufferHandler(
        ring_buffer,
        publish_log,
        correlation_id_getter=correlation_id_getter,
    )
    ring_handler.setLevel(level)

    return [console_handler, app_file_handler, errors_file_handler, ring_handler]


def _setup_access_logger(target_dir: Path) -> logging.Handler:
    """Configure specialized access log handler with 10MB rotation and retention."""
    access_logger = logging.getLogger("haruquantai.access")
    # Do not delete handlers owned by an embedding application.

    access_file_handler = WindowsSafeRotatingFileHandler(
        target_dir / "access.log",
        maxBytes=MAX_LOG_FILE_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
        delay=True,
    )
    access_file_handler.setLevel(logging.INFO)
    access_file_handler.setFormatter(LogEventFormatter(colorize=False))
    access_file_handler.addFilter(_AccessFilter())
    access_logger.propagate = True
    access_logger.setLevel(logging.INFO)
    return access_file_handler


class _AccessFilter(logging.Filter):
    """Keep the access sink restricted to explicitly routed access records."""

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name == "haruquantai.access"


