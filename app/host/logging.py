# ruff: noqa: INP001
"""Telemetry, multi-sink logging, secret redaction, and log ring buffer.

Description:
    Provides the central logging and telemetry infrastructure for the host
    platform, workspaces, and plugins. Implements an asynchronous queue-based
    telemetry worker engine decoupling log production from disk I/O, multi-sink
    queued file outputs (app.log, access.log, errors.log) with Windows-safe 10MB
    rotation and 30-day archiving, recursive secret and path redaction, a safe
    error boundary preventing logging failures from impacting callers, exact
    millisecond-precision log event formatting with console ANSI colorization,
    automatic SHA-256 secret fingerprints and a bounded log callback for SSE/WS,
    an in-memory live ring buffer projected to the DebugConsole, BoundLogger with
    context accumulation, request correlation context, and lazy bootstrapping
    with zero import-time side-effects.

Purpose:
    FEAT-HOST-TELEMETRY: Host platform telemetry, redacted logging and diagnostics.

Key Capabilities:
    - FR-HOST-TELEMETRY-ENGINE: Telemetry Worker & Engine.
      Associated: `TelemetryEngine`, `flush_logs()`, `shutdown_logging()`
      Logging: INFO on telemetry engine startup and shutdown.
    - FR-HOST-TELEMETRY-REDACTION: Secret & Path Redaction.
      Associated: `redact_secrets()`, `fingerprint_secret()`, `normalize_path()`
      Logging: DEBUG on redaction filter execution.
    - FR-HOST-TELEMETRY-ERROR-BOUNDARY: Safe Error Boundary.
      Associated: `SafeErrorBoundary`, `LogEventFormatter`
      Logging: Fallback error emission on formatting exceptions.
    - FR-HOST-TELEMETRY-FORMATTING: Log Event & Formatting.
      Associated: `LogEventFormatter`
      Logging: Structured event formatting with optional ANSI colors.
    - FR-HOST-TELEMETRY-SINKS: Sinks, Windows-Safe Rotation & Archiving.
      Associated: `WindowsSafeRotatingFileHandler`
      Logging: INFO on log file creation and rotation.
    - FR-HOST-TELEMETRY-RINGBUFFER: Log Ring Buffer & Debug Console Projection.
      Associated: `LogRingBuffer`, `RingBufferHandler`, `get_ring_buffer()`
      Logging: DEBUG on ring buffer query and capacity truncation.
    - FR-HOST-TELEMETRY-BOUND-LOGGER: Bound Logger & Facade.
      Associated: `BoundLogger`, `get_logger()`, `get_access_logger()`
      Logging: DEBUG on dynamic context binding.
    - FR-HOST-TELEMETRY-CORRELATION: Request Correlation Context.
      Associated: `set_correlation_id()`, `get_correlation_id()`
      Logging: Contextual request ID tracking across threads.
    - FR-HOST-TELEMETRY-LAZY-BOOTSTRAP: Public Module Exports & Lazy Bootstrap.
      Associated: `setup_logging()`, `__all__`
      Logging: Lazy initialization on first emission without import side-effects.

Python API Usage:
    ```python
    from app.host.logging import (
        get_access_logger,
        get_logger,
        set_correlation_id,
        setup_logging,
    )

    setup_logging("data/logs")
    logger = get_logger(__name__)
    set_correlation_id("req-12345")
    ctx_logger = logger.bind(session_id="sess-01")
    ctx_logger.info("Order submitted", extra={"fr_id": "FR-HOST-TELEMETRY-ENGINE"})

    access = get_access_logger()
    access.info("GET /health 200", extra={"fr_id": "FR-HOST-TELEMETRY-SINKS"})
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.logging
    ```
"""

from __future__ import annotations

import collections
import contextlib
import contextvars
import copy
import hashlib
import logging
import logging.handlers
import queue
import re
import sys
import threading
import time
from collections.abc import Callable, Mapping, MutableMapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

__all__ = [
    "DEFAULT_RING_BUFFER_CAPACITY",
    "fingerprint_secret",
    "flush_logs",
    "get_access_logger",
    "get_logger",
    "get_ring_buffer",
    "normalize_path",
    "redact_secrets",
    "set_correlation_id",
    "setup_logging",
    "shutdown_logging",
]

ENGINE_FR = "FR-HOST-TELEMETRY-ENGINE"
REDACTION_FR = "FR-HOST-TELEMETRY-REDACTION"
ERROR_BOUNDARY_FR = "FR-HOST-TELEMETRY-ERROR-BOUNDARY"
FORMATTING_FR = "FR-HOST-TELEMETRY-FORMATTING"
SINKS_FR = "FR-HOST-TELEMETRY-SINKS"
RINGBUFFER_FR = "FR-HOST-TELEMETRY-RINGBUFFER"
BOUND_LOGGER_FR = "FR-HOST-TELEMETRY-BOUND-LOGGER"
CORRELATION_FR = "FR-HOST-TELEMETRY-CORRELATION"
LAZY_BOOTSTRAP_FR = "FR-HOST-TELEMETRY-LAZY-BOOTSTRAP"

DEFAULT_LOG_DIR: Path = Path("data/logs")
DEFAULT_RING_BUFFER_CAPACITY: int = 2000
MAX_LOG_FILE_BYTES: int = 10 * 1024 * 1024  # 10 MiB
LOG_BACKUP_COUNT: int = 30  # 30 days/generations retention
_MAX_RENAME_RETRIES: int = 5
_RENAME_RETRY_DELAY_SEC: float = 0.05
REDACTED_STR: str = "***REDACTED***"

ANSI_RESET: str = "\033[0m"
ANSI_LEVEL_COLORS: dict[str, str] = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[1;35m",  # Bold Magenta
}

SENSITIVE_KEY_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)(password|token|secret|key|api_?key|auth|authorization|credential|hash|bearer)"
)
SENSITIVE_VALUE_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)(bearer\s+[^\s,'\";]+)|"
    r"((?:token|secret|password|api_?key|key)['\"]?\s*[:=]\s*"
    r"(?:\"[^\"]*\"|'[^']*'|[^\s,;}\]]+))"
)

_CORRELATION_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)

_GLOBAL_RING_BUFFER: LogRingBuffer | None = None
_GLOBAL_ENGINE: TelemetryEngine | None = None
_LOGGING_LOCK: threading.RLock = threading.RLock()
_BOOTSTRAPPED: bool = False


# ============================================================================
# Capability 8: Request Correlation Context
# ============================================================================


def set_correlation_id(correlation_id: str) -> contextvars.Token[str | None]:
    """Set current request correlation ID in task context.

    Args:
        correlation_id: Unique correlation or trace ID string.

    Returns:
        ContextVar token for resetting.
    """
    return _CORRELATION_ID.set(correlation_id)


def reset_correlation_id(token: contextvars.Token[str | None]) -> None:
    """Reset request correlation ID using context token.

    Args:
        token: ContextVar token returned by set_correlation_id.
    """
    _CORRELATION_ID.reset(token)


def get_correlation_id() -> str | None:
    """Return current request correlation ID if set, or None.

    Returns:
        Active correlation ID string or None.
    """
    return _CORRELATION_ID.get()


# ============================================================================
# Capability 2: Secret & Path Redaction
# ============================================================================


def normalize_path(path_str: str, root_dir: Path | None = None) -> str:
    """Normalize absolute paths to relative tokens to prevent environment leaks.

    Args:
        path_str: Path string to normalize.
        root_dir: Optional root directory to normalize against (defaults to cwd).

    Returns:
        Path string with repository or home directory prefixes masked.
    """
    root = (root_dir or Path.cwd()).resolve()
    resolved_str = str(root)
    normalized = path_str.replace(resolved_str, "[WORKSPACE]")
    try:
        home_str = str(Path.home().resolve())
        normalized = normalized.replace(home_str, "~")
    except RuntimeError:
        pass
    return normalized.replace("\\", "/")


def fingerprint_secret(value: Any) -> str:
    """Compute a non-reversible SHA-256 redaction fingerprint for a secret value."""
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:8]
    return f"***REDACTED:sha256:{digest}***"


def redact_secrets(data: Any, *, fingerprint: bool = False) -> Any:
    """Recursively mask sensitive values in strings, mappings, and sequences.

    Args:
        data: Arbitrary data structure to scrub.
        fingerprint: When True, emit SHA-256 fingerprint token
            ``***REDACTED:sha256:<8-hex>***`` instead of ``***REDACTED***``.

    Returns:
        Scrubbed data structure with sensitive fields masked.
    """
    if isinstance(data, str):
        if fingerprint:
            return SENSITIVE_VALUE_PATTERN.sub(
                lambda m: fingerprint_secret(m.group(0)), data
            )
        return SENSITIVE_VALUE_PATTERN.sub(REDACTED_STR, data)
    if isinstance(data, Mapping):
        scrubbed_dict: dict[str, Any] = {}
        for k, v in data.items():
            key_str = str(k)
            if SENSITIVE_KEY_PATTERN.search(key_str):
                scrubbed_dict[key_str] = (
                    fingerprint_secret(v) if fingerprint else REDACTED_STR
                )
            else:
                scrubbed_dict[key_str] = redact_secrets(v, fingerprint=fingerprint)
        return scrubbed_dict
    if isinstance(data, list):
        return [redact_secrets(item, fingerprint=fingerprint) for item in data]
    if isinstance(data, tuple):
        return tuple(redact_secrets(item, fingerprint=fingerprint) for item in data)
    return data


# ============================================================================
# Capability 4: Log Event & Formatting & Capability 3: Safe Error Boundary
# ============================================================================


class LogEventFormatter(logging.Formatter):
    """Structured formatter with timestamp, ANSI styling, and safe error boundary."""

    def __init__(
        self,
        *,
        colorize: bool = False,
        root_dir: Path | None = None,
    ) -> None:
        """Initialize formatter with optional colorization and path normalization.

        Args:
            colorize: True to apply ANSI color codes to level and message.
            root_dir: Optional root path for machine path normalization.
        """
        super().__init__()
        self.colorize = colorize
        self.root_dir = root_dir

    @override
    def format(self, record: logging.LogRecord) -> str:
        """Format: YYYY-MM-DD HH:MM:SS.mmm | LEVEL | module:function:line - message.

        Args:
            record: Logging log record instance to format.

        Returns:
            Formatted log event string.
        """
        original_msg = record.msg
        original_args = record.args

        try:
            # 1. Exact millisecond-precision timestamp
            record_dt = datetime.fromtimestamp(record.created, tz=UTC)
            time_str = (
                record_dt.strftime("%Y-%m-%d %H:%M:%S") + f".{int(record.msecs):03d}"
            )

            # 2. Mask secrets in args
            if isinstance(record.args, dict):
                record.args = redact_secrets(record.args, fingerprint=True)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_secrets(arg, fingerprint=True)
                    if not isinstance(arg, str)
                    else arg
                    for arg in record.args
                )

            # 3. Safe formatting boundary
            try:
                raw_msg = record.getMessage()
            except Exception as format_exc:  # noqa: BLE001
                raw_msg = (
                    f"[LOGGING-ERROR-BOUNDARY] Failed to format message "
                    f"({type(format_exc).__name__}: {format_exc}) | Raw: {record.msg}"
                )

            # 4. Redact secrets and normalize machine paths
            clean_msg = normalize_path(
                str(redact_secrets(raw_msg, fingerprint=True)), self.root_dir
            )

            # 5. Build caller location: module:function:line
            caller = f"{record.name}:{record.funcName}:{record.lineno}"

            # 6. Apply ANSI colors if requested
            level_name = record.levelname
            if (self.colorize and sys.stderr.isatty()) or self.colorize:
                color = ANSI_LEVEL_COLORS.get(level_name, "")
                formatted_level = f"{color}{level_name:<5}{ANSI_RESET}"
                formatted_msg = f"{color}{clean_msg}{ANSI_RESET}"
            else:
                formatted_level = f"{level_name:<5}"
                formatted_msg = clean_msg

            formatted = f"{time_str} | {formatted_level} | {caller} - {formatted_msg}"

            # 7. Append scrubbed exception traceback if present
            if record.exc_info and not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
            if record.exc_text:
                scrubbed_exc = normalize_path(
                    str(redact_secrets(record.exc_text, fingerprint=True)),
                    self.root_dir,
                )
                formatted = f"{formatted}\n{scrubbed_exc}"

            if record.stack_info:
                scrubbed_stack = normalize_path(
                    str(
                        redact_secrets(
                            self.formatStack(record.stack_info), fingerprint=True
                        )
                    ),
                    self.root_dir,
                )
                formatted = f"{formatted}\n{scrubbed_stack}"

            return formatted

        except Exception as boundary_exc:  # noqa: BLE001
            # Fallback error boundary to ensure application never crashes
            return (
                f"[LOGGING-ERROR-BOUNDARY-CRITICAL] {type(boundary_exc).__name__}: "
                f"{boundary_exc} | Record: {getattr(record, 'name', 'unknown')}"
            )
        finally:
            record.msg = original_msg
            record.args = original_args


# ============================================================================
# Capability 5: Sinks, Windows-Safe Rotation & Archiving
# ============================================================================


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
            except PermissionError, FileExistsError:
                if attempt < _MAX_RENAME_RETRIES - 1:
                    time.sleep(_RENAME_RETRY_DELAY_SEC)
                else:
                    break


# ============================================================================
# Capability 6: Log Ring Buffer & Debug Console Projection
# ============================================================================


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

    def get_records(
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
    ) -> None:
        """Initialize with target LogRingBuffer."""
        super().__init__()
        self.ring_buffer = ring_buffer
        self.publish_log = publish_log

    @override
    def emit(self, record: logging.LogRecord) -> None:
        """Emit structured dictionary entry into the ring buffer."""
        try:
            record_dt = datetime.fromtimestamp(record.created, tz=UTC)
            time_str = (
                record_dt.strftime("%Y-%m-%d %H:%M:%S") + f".{int(record.msecs):03d}"
            )
            safe_record = copy.copy(record)
            safe_record.args = redact_secrets(record.args, fingerprint=True)
            raw_msg = safe_record.getMessage()
            clean_msg = normalize_path(str(redact_secrets(raw_msg, fingerprint=True)))
            caller = f"{record.name}:{record.funcName}:{record.lineno}"

            entry = {
                "timestamp": time_str,
                "name": record.name,
                "level": record.levelname,
                "caller": caller,
                "message": clean_msg,
                "fr_id": getattr(record, "fr_id", None),
                "correlation_id": getattr(record, "correlation_id", None)
                or get_correlation_id(),
            }
            self.ring_buffer.append(entry)
            if (
                self.publish_log is not None
                and getattr(record, "fr_id", None) != "FR-HOST-TRANSPORT-EVENT-BUS"
            ):
                self.publish_log(entry)
        except Exception:  # noqa: BLE001
            sys.stderr.write(
                "FR-HOST-TELEMETRY-ERROR-BOUNDARY: live log delivery failed\n"
            )


def get_ring_buffer() -> LogRingBuffer:
    """Return the global log ring buffer, initializing if needed."""
    global _GLOBAL_RING_BUFFER  # noqa: PLW0603
    if _GLOBAL_RING_BUFFER is None:
        with _LOGGING_LOCK:
            if _GLOBAL_RING_BUFFER is None:
                _GLOBAL_RING_BUFFER = LogRingBuffer()
    return _GLOBAL_RING_BUFFER


# ============================================================================
# Capability 7: Bound Logger & Facade
# ============================================================================


class BoundLogger(logging.LoggerAdapter[logging.Logger]):
    """Logger adapter providing dynamic context binding and structured tags."""

    def __init__(
        self,
        logger: logging.Logger,
        extra: Mapping[str, Any] | None = None,
    ) -> None:
        """Initialize BoundLogger with underlying logger and contextual extra dict."""
        super().__init__(logger, dict(extra) if extra is not None else {})

    @property
    def context(self) -> dict[str, Any]:
        """Return a copy of the bound context attributes."""
        return dict(self.extra) if self.extra is not None else {}

    def bind(self, **kwargs: Any) -> BoundLogger:
        """Return a new BoundLogger instance with merged contextual attributes."""
        merged: dict[str, Any] = {**self.context, **kwargs}
        return BoundLogger(self.logger, merged)

    @override
    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> tuple[Any, MutableMapping[str, Any]]:
        """Process log message and keyword arguments to merge bound context."""
        extra_dict = dict(self.context)
        if "extra" in kwargs and isinstance(kwargs["extra"], Mapping):
            extra_dict.update(kwargs["extra"])

        cid = get_correlation_id()
        if cid is not None and "correlation_id" not in extra_dict:
            extra_dict["correlation_id"] = cid

        kwargs["extra"] = extra_dict
        if extra_dict:
            context_str = " ".join(f"{k}={v}" for k, v in extra_dict.items())
            msg = f"{msg} [{context_str}]"
        return msg, kwargs


def get_logger(name: str) -> BoundLogger:
    """Return standard BoundLogger for module with dynamic context binding support."""
    _ensure_bootstrapped()
    return BoundLogger(logging.getLogger(name))


def get_access_logger() -> BoundLogger:
    """Return specialized BoundLogger routing events to data/logs/access.log."""
    _ensure_bootstrapped()
    return get_logger("haruquantai.access")


# ============================================================================
# Capability 1: Telemetry Worker & Engine & Capability 9: Lazy Bootstrap
# ============================================================================


class _RedactingQueueHandler(logging.handlers.QueueHandler):
    """Scrub structured arguments before the queue flattens them to text."""

    @override
    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        prepared = copy.copy(record)
        prepared.args = redact_secrets(record.args, fingerprint=True)
        queued: logging.LogRecord = super().prepare(prepared)
        queued.msg = normalize_path(str(redact_secrets(queued.msg, fingerprint=True)))
        return queued

    @override
    def handleError(self, record: logging.LogRecord) -> None:
        """Report queue/format failures without echoing the unsanitized record."""
        sys.stderr.write("FR-HOST-TELEMETRY-ERROR-BOUNDARY: telemetry record dropped\n")


class TelemetryEngine:
    """Asynchronous queue listener engine decoupling log emission from disk I/O."""

    def __init__(
        self,
        downstream_handlers: list[logging.Handler],
        queue_size: int = 10000,
    ) -> None:
        """Initialize telemetry engine with non-blocking queue and listener thread."""
        self._queue: queue.Queue[logging.LogRecord | None] = queue.Queue(
            maxsize=queue_size
        )
        self.downstream_handlers = downstream_handlers
        self._queue_handler = _RedactingQueueHandler(self._queue)
        self._listener = logging.handlers.QueueListener(
            self._queue,
            *self.downstream_handlers,
            respect_handler_level=True,
        )
        self._listener.start()

    @property
    def queue_handler(self) -> logging.handlers.QueueHandler:
        """Return the queue handler attached to the root logger."""
        return self._queue_handler

    def flush(self) -> None:
        """Flush all pending records synchronously through the listener."""
        self._queue.join()
        for h in self.downstream_handlers:
            with contextlib.suppress(Exception):
                h.flush()

    def stop(self) -> None:
        """Stop the background listener thread and close downstream handlers."""
        self.flush()
        with contextlib.suppress(Exception):
            self._listener.stop()
        for h in self.downstream_handlers:
            with contextlib.suppress(Exception):
                h.close()


def flush_logs() -> None:
    """Flush pending log records across all telemetry queues and sinks."""
    if _GLOBAL_ENGINE is not None:
        _GLOBAL_ENGINE.flush()
    for h in logging.getLogger().handlers:
        with contextlib.suppress(Exception):
            h.flush()


def shutdown_logging() -> None:
    """Shut down asynchronous telemetry engine and close all log file handles."""
    global _GLOBAL_ENGINE, _BOOTSTRAPPED  # noqa: PLW0603
    with _LOGGING_LOCK:
        if _GLOBAL_ENGINE is not None:
            _GLOBAL_ENGINE.stop()
            _GLOBAL_ENGINE = None
        root = logging.getLogger()
        for h in list(root.handlers):
            with contextlib.suppress(Exception):
                h.close()
        root.handlers.clear()
        access_logger = logging.getLogger("haruquantai.access")
        for h in list(access_logger.handlers):
            with contextlib.suppress(Exception):
                h.close()
        access_logger.handlers.clear()
        _BOOTSTRAPPED = False


def _ensure_bootstrapped() -> None:
    """Lazily bootstrap telemetry engine if not already configured."""
    if not _BOOTSTRAPPED:
        with _LOGGING_LOCK:
            if not _BOOTSTRAPPED:
                setup_logging(DEFAULT_LOG_DIR, async_engine=False)


def _build_sinks(
    target_dir: Path,
    level: int,
    ring_buffer: LogRingBuffer,
    publish_log: Callable[[dict[str, Any]], None] | None = None,
) -> list[logging.Handler]:
    """Construct console, rotating file, and ring buffer downstream sinks."""
    console_formatter = LogEventFormatter(colorize=True)
    file_formatter = LogEventFormatter(colorize=False)

    console_handler = logging.StreamHandler()
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

    ring_handler = RingBufferHandler(ring_buffer, publish_log)
    ring_handler.setLevel(level)

    return [console_handler, app_file_handler, errors_file_handler, ring_handler]


def _setup_access_logger(target_dir: Path) -> logging.Handler:
    """Configure specialized access log handler with 10MB rotation and retention."""
    access_logger = logging.getLogger("haruquantai.access")
    for h in list(access_logger.handlers):
        with contextlib.suppress(Exception):
            h.close()
    access_logger.handlers.clear()

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


def setup_logging(
    log_dir: Path | str | None = None,
    *,
    level: int = logging.INFO,
    ring_buffer_size: int = DEFAULT_RING_BUFFER_CAPACITY,
    async_engine: bool = True,
    publish_log: Callable[[dict[str, Any]], None] | None = None,
) -> LogRingBuffer:
    """Configure multi-sink logging, secret redaction, and telemetry ring buffer.

    Args:
        log_dir: Target directory for log files (defaults to data/logs).
        level: Root logger severity threshold.
        ring_buffer_size: Capacity of in-memory live telemetry buffer.
        async_engine: True to run non-blocking asynchronous queue listener.
        publish_log: Optional lifecycle-owned callback receiving scrubbed entries.

    Returns:
        The configured global LogRingBuffer.
    """
    global _GLOBAL_RING_BUFFER, _GLOBAL_ENGINE, _BOOTSTRAPPED  # noqa: PLW0603
    target_dir = Path(log_dir) if log_dir is not None else DEFAULT_LOG_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    with _LOGGING_LOCK:
        if _GLOBAL_ENGINE is not None:
            _GLOBAL_ENGINE.stop()
            _GLOBAL_ENGINE = None

        _GLOBAL_RING_BUFFER = LogRingBuffer(maxlen=ring_buffer_size)
        root = logging.getLogger()
        root.setLevel(level)

        capture_handlers = [
            h for h in root.handlers if "pytest" in getattr(type(h), "__module__", "")
        ]
        for h in root.handlers:
            if h not in capture_handlers:
                with contextlib.suppress(Exception):
                    h.close()
        root.handlers.clear()
        for ch in capture_handlers:
            root.addHandler(ch)

        downstream_handlers = _build_sinks(
            target_dir, level, _GLOBAL_RING_BUFFER, publish_log
        )
        downstream_handlers.append(_setup_access_logger(target_dir))

        if async_engine:
            _GLOBAL_ENGINE = TelemetryEngine(downstream_handlers)
            root.addHandler(_GLOBAL_ENGINE.queue_handler)
        else:
            for dh in downstream_handlers:
                root.addHandler(dh)

        _BOOTSTRAPPED = True

    logger = logging.getLogger(__name__)
    logger.info(
        "%s: logging engine initialized (target=%s, level=%s, async=%s)",
        ENGINE_FR,
        target_dir,
        logging.getLevelName(level),
        async_engine,
        extra={"fr_id": ENGINE_FR, "log_dir": str(target_dir)},
    )
    return _GLOBAL_RING_BUFFER


def main() -> None:
    """Demonstrate all 9 Key Capabilities of the telemetry and logging subsystem."""
    setup_logging(DEFAULT_LOG_DIR, level=logging.DEBUG, async_engine=False)
    logger = get_logger("haruquantai.demo")

    # 1. Telemetry Worker & Engine
    logger.info(
        "1. Telemetry Worker & Engine initialized",
        extra={"fr_id": ENGINE_FR},
    )

    # 2. Secret & Path Redaction
    secret_logger = logger.bind(
        token="super_secret_token_12345",  # noqa: S106
        password="my_admin_password",  # noqa: S106
    )
    secret_logger.info(
        "2. Secret & Path Redaction applied (path=%s)",
        str(Path.cwd() / "data" / "database"),
        extra={"fr_id": REDACTION_FR},
    )

    # 3. Safe Error Boundary
    logger.info(
        "3. Safe Error Boundary test: malformed format argument",
        extra={"fr_id": ERROR_BOUNDARY_FR},
    )

    def _simulate_failure() -> None:
        raise RuntimeError("Simulated transaction connection timeout")

    try:
        _simulate_failure()
    except RuntimeError:
        logger.exception(
            "3. Caught simulated exception safely handled by error boundary",
            extra={"fr_id": ERROR_BOUNDARY_FR},
        )

    # 4. Log Event & Formatting (exact format with ANSI colors on console)
    logger.debug(
        "4. Debug message demonstrating millisecond timestamp formatting",
        extra={"fr_id": FORMATTING_FR},
    )
    logger.warning(
        "4. Warning message demonstrating yellow ANSI color formatting",
        extra={"fr_id": FORMATTING_FR},
    )
    logger.error(
        "4. Error message demonstrating red ANSI color formatting",
        extra={"fr_id": FORMATTING_FR},
    )

    # 5. Sinks, Windows-Safe Rotation & Archiving
    logger.info(
        "5. Sinks configured with 10MB limit and 30-backup retention",
        extra={"fr_id": SINKS_FR},
    )

    # 6. Log Ring Buffer & Debug Console Projection
    ring_buf = get_ring_buffer()
    logger.info(
        "6. Log Ring Buffer active with %d entries recorded",
        len(ring_buf),
        extra={"fr_id": RINGBUFFER_FR},
    )

    # 7. Bound Logger & Facade
    bound_logger = logger.bind(
        session_id="sess-8899",
        account_id="ACC-QUANT-01",
        symbol="BTC/USDT",
    )
    bound_logger.info(
        "7. Bound Logger & Facade accumulating contextual tags",
        extra={"fr_id": BOUND_LOGGER_FR},
    )

    # 8. Request Correlation Context
    token = set_correlation_id("req-uuid-990011")
    try:
        logger.info(
            "8. Request Correlation Context propagated to records",
            extra={"fr_id": CORRELATION_FR},
        )
    finally:
        reset_correlation_id(token)

    # 9. Public Module Exports & Specialized routing
    access_logger = get_access_logger()
    access_logger.info(
        "9. Public Module Exports: routed to data/logs/access.log",
        extra={"fr_id": LAZY_BOOTSTRAP_FR},
    )

    flush_logs()


if __name__ == "__main__":
    main()
