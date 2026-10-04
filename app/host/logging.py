"""Centralized application telemetry, multi-sink routing, and credential redaction.

Description:
    This module provides the central telemetry and logging engine for the
    HaruQuantAI host process and runtime plugins. It guarantees that sensitive
    credentials, authentication tokens, and private keys are systematically
    fingerprinted and redacted before emission, while delivering non-blocking
    asynchronous event delivery across four dedicated file sinks and a color-aware
    console sink. Applications obtain logger handles via `get_logger(__name__)` or
    the root `logger` instance. The engine lazily initializes on the first runtime log
    emission, keeping module import times completely inert and side-effect free.
    Internally, a dedicated background worker consumes a bounded queue to isolate
    latency-sensitive trading operations from disk I/O, file rotation, and ZIP
    archiving under Windows file-locking semantics.

Purpose:
    FEAT-HOST-LOGGING: Centralized application telemetry, multi-sink routing, and
    credential redaction across host and plugin runtimes.

Key Capabilities:
    - FR-HOST-LOGGER-RESOLUTION: Resolve namespaces and bootstrap telemetry lazily
      on first runtime emission without import-time side-effects.
      Associated: `get_logger()`, `TelemetryEngine.get_or_create()`
      Logging: Emits DEBUG telemetry upon runtime initialization of new namespaces.
    - FR-HOST-BOUND-LOGGER: Expose global bound logger with immutable context.
      Associated: `BoundLogger`, `BoundLogger.bind()`
      Logging: Attaches immutable context key-value pairs to every emitted event.
    - FR-HOST-SECRET-REDACTION: Fingerprint detected credentials before emission.
      Associated: `redact_secrets()`, `sanitize_payload()`
      Logging: Replaces credentials with deterministic SHA-256 fingerprint digests.
    - FR-HOST-STRUCTURED-FORMATTING: Serialize events to bounded JSON and human text.
      Associated: `format_human_record()`, `format_json_record()`
      Logging: Formats records for terminal and disk with bounded sizes.
    - FR-HOST-MULTI-SINK-ROUTING: Demux events across app, access, debug,
      and error logs.
      Associated: `TelemetryEngine._dispatch_event()`, `SinkRouter`
      Logging: Routes events to app.log, access.log, debug.log, and errors.log.
    - FR-HOST-BOUNDED-TELEMETRY: Enforce 10 MB ZIP rotation and 10-day retention.
      Associated: `RotatingZipSink._rotate_and_archive()`, `prune_expired_archives()`
      Logging: Rotates files at 10 MB and archives with deflated ZIP compression.
    - FR-HOST-REQUEST-CORRELATION: Scope request metadata via contextvars.
      Associated: `request_context()`
      Logging: Injects scoped correlation tokens into concurrent async event contexts.
    - FR-HOST-SAFE-ERROR-BOUNDARY: Log errors without sensitive tracebacks.
      Associated: `safe_error_boundary()`, `BoundLogger.exception()`
      Logging: Captures exception class, message, and bounded call-site frames.
    - FR-HOST-LIFECYCLE-SYNC: Provide clean shutdown, atexit cleanup, and queue sync.
      Associated: `flush()`, `shutdown()`, `reset_logging()`
      Logging: Synchronizes queued events and releases file descriptors cleanly.
    - FR-HOST-ASYNC-QUEUE: Non-blocking bounded queue worker with backpressure drops.
      Associated: `TelemetryEngine.enqueue()`, `TelemetryWorker`
      Logging: Discards events non-blockingly on saturation and tracks drop metrics.
    - FR-HOST-WINDOWS-ROTATION: Windows file-locking-safe stream closure and archiving.
      Associated: `RotatingZipSink._rotate_and_archive()`
      Logging: Closes open file handles before renaming and compressing on Windows.
    - FR-HOST-LIBRARY-BRIDGE: Forward and sanitize third-party standard-library loggers.
      Associated: `bridge_standard_logging()`, `HostBridgeHandler`
      Logging: Intercepts foreign logging records and routes through telemetry engine.
    - FR-HOST-TEST-ISOLATION: Explicit configuration and teardown reset for test suites.
      Associated: `configure_host_logging()`, `reset_logging()`
      Logging: Reinitializes sinks in temporary directories and resets global state.
    - FR-HOST-STRICT-TYPING: Python 3.14 strict typing with zero runtime warnings.
      Associated: `request_context()`, `BoundLogger`
      Logging: Adheres to Generator[None] context typing and PEP 695/strict mypy rules.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.logging import (
        configure_host_logging,
        get_logger,
        request_context,
        reset_logging,
    )

    # 1. Configure or rely on lazy bootstrap
    configure_host_logging(Path("data/logs"))

    # 2. Bind context and scope requests
    log = get_logger("app.workspace").bind(worker_id="w-01")
    with request_context(request_id="req-999"):
        log.info("Processing job", extra={"task": "backtest"})

    # 3. Clean teardown at shutdown
    reset_logging()
    ```

CLI Usage:
    Run the application or check log output via shell:
    ```bash
    # Inspect rotating JSON files
    tail -f data/logs/app.log

    # View live access logs
    tail -f data/logs/access.log
    ```
"""

from __future__ import annotations

import atexit
import contextlib
import hashlib
import json
import logging
import queue
import re
import sys
import threading
import time
import traceback
import zipfile
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Final, TextIO, override

if TYPE_CHECKING:
    from collections.abc import Generator

__all__ = [
    "BoundLogger",
    "LoggingConfig",
    "TelemetryEngine",
    "bridge_standard_logging",
    "configure_host_logging",
    "flush",
    "get_logger",
    "logger",
    "redact_secrets",
    "request_context",
    "reset_logging",
    "safe_error_boundary",
    "shutdown",
]

# ============================================================================
# Constants & Defaults
# ============================================================================

DEFAULT_LOG_DIR: Final[Path] = Path("data/logs")
DEFAULT_MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB
DEFAULT_RETENTION_DAYS: Final[int] = 10
DEFAULT_QUEUE_SIZE: Final[int] = 1024
MAX_EVENT_BYTES: Final[int] = 16 * 1024  # 16 KB max serialized event size
MAX_STACK_FRAMES: Final[int] = 8
MAX_RECURSION_DEPTH: Final[int] = 8

# ANSI Color Codes
ANSI_RESET: Final[str] = "\033[0m"
ANSI_CYAN: Final[str] = "\033[36m"
ANSI_GREEN: Final[str] = "\033[32m"
ANSI_YELLOW: Final[str] = "\033[33m"
ANSI_RED: Final[str] = "\033[31m"
ANSI_BOLD_RED: Final[str] = "\033[1;31m"

LEVEL_COLORS: Final[dict[str, str]] = {
    "DEBUG": ANSI_CYAN,
    "INFO": ANSI_GREEN,
    "WARNING": ANSI_YELLOW,
    "ERROR": ANSI_RED,
    "CRITICAL": ANSI_BOLD_RED,
}

LEVEL_NUMBERS: Final[dict[str, int]] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def parse_log_level(level: int | str) -> int:
    """Normalize integer or string log level representation to standard integer."""
    if isinstance(level, str):
        return LEVEL_NUMBERS.get(level.strip().upper(), logging.INFO)
    return int(level)


# ============================================================================
# Secret Redaction Patterns
# ============================================================================

# Matches sensitive keys in dictionary/json representations
_SENSITIVE_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?i)^(?:password|passwd|pwd|key|api[_-]?key|(?:access|refresh|auth)?[_-]?token|"
    r"session[_-]?id|sessionid|db[_-]?password|database[_-]?password|"
    r"authorization|bearer|secret|cookie|private[_-]?key)$"
)

# Matches key-value assignments in strings (e.g. password="xyz", api_key: "abc")
_ASSIGNMENT_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?i)(?P<prefix>\b(?:password|passwd|pwd|key|api[_-]?key|"
    r"(?:access|refresh|auth)?[_-]?token|session[_-]?id|sessionid|"
    r"db[_-]?password|database[_-]?password|authorization|bearer|secret|cookie)\b"
    r"[\"']?\s*[:=]\s*)(?P<quote>[\"'])(?P<secret>[^\"']+)(?P=quote)"
)

# Matches bearer tokens directly (e.g. Bearer eyJhbGci...)
_BEARER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?i)\bBearer\s+(?P<token>[A-Za-z0-9_\-\.]{16,})"
)

# Matches already redacted markers to ensure idempotency
_ALREADY_REDACTED_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\[REDACTED:[0-9a-f]{12}\]$"
)

# ContextVar for request correlation across tasks
_CORRELATION_CONTEXT: Final[ContextVar[dict[str, object] | None]] = ContextVar(
    "host_logging_correlation_context", default=None
)


def fingerprint_secret(secret: str) -> str:
    """Create a deterministic truncated SHA-256 fingerprint for a secret string.

    Args:
        secret: Raw secret text.

    Returns:
        Truncated redaction string formatted as `[REDACTED:<digest:12>]`.
    """
    if _ALREADY_REDACTED_PATTERN.match(secret):
        return secret
    digest = hashlib.sha256(secret.encode("utf-8"), usedforsecurity=False).hexdigest()[
        :12
    ]
    return f"[REDACTED:{digest}]"


def redact_secrets(text: str) -> str:
    """Redact known credential patterns from a plain string.

    Args:
        text: Input string that may contain passwords, tokens, or bearer headers.

    Returns:
        Sanitized string with fingerprints replacing secret values.
    """
    if not text:
        return text

    def _replace_assignment(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        quote = match.group("quote")
        secret = match.group("secret")
        return f"{prefix}{quote}{fingerprint_secret(secret)}{quote}"

    def _replace_bearer(match: re.Match[str]) -> str:
        token = match.group("token")
        return f"Bearer {fingerprint_secret(token)}"

    redacted = _ASSIGNMENT_PATTERN.sub(_replace_assignment, text)
    return _BEARER_PATTERN.sub(_replace_bearer, redacted)


def sanitize_payload(obj: object, depth: int = 0) -> object:
    """Recursively sanitize data structures and mask sensitive keys.

    Args:
        obj: Arbitrary Python object.
        depth: Current recursion depth.

    Returns:
        Sanitized dictionary, list, or primitive representation.
    """
    if depth > MAX_RECURSION_DEPTH:
        return "[TRUNCATED_DEPTH]"

    if isinstance(obj, str):
        return redact_secrets(obj)

    if isinstance(obj, (int, float, bool)) or obj is None:
        return obj

    if isinstance(obj, dict):
        sanitized_dict: dict[str, object] = {}
        for key, value in obj.items():
            str_key = str(key)
            if _SENSITIVE_KEY_PATTERN.match(str_key):
                if isinstance(value, str):
                    sanitized_dict[str_key] = fingerprint_secret(value)
                else:
                    sanitized_dict[str_key] = "[REDACTED]"
            else:
                sanitized_dict[str_key] = sanitize_payload(value, depth + 1)
        return sanitized_dict

    if isinstance(obj, (list, tuple, set)):
        return [sanitize_payload(item, depth + 1) for item in obj]

    return redact_secrets(str(obj))


# ============================================================================
# Safe Error Boundary
# ============================================================================


def safe_error_boundary(exc: BaseException) -> dict[str, object]:
    """Extract safe, redacted diagnostic information from an exception.

    Strips caller frame local variables, environment dumps, and sensitive tracebacks,
    while capturing the exception type, sanitized message, and bounded call-site frames.

    Args:
        exc: The exception instance to inspect.

    Returns:
        A dictionary with keys 'type', 'message', and 'frames'.
    """
    exc_type = exc.__class__.__name__
    exc_msg = redact_secrets(str(exc))
    frames: list[str] = []

    tb = exc.__traceback__
    if tb is not None:
        extracted = traceback.extract_tb(tb)
        # Retain only the trailing bounded frames
        for frame in extracted[-MAX_STACK_FRAMES:]:
            file_name = Path(frame.filename).name
            frames.append(f"{file_name}:{frame.lineno}:{frame.name}")

    return {
        "type": exc_type,
        "message": exc_msg,
        "frames": frames,
    }


# ============================================================================
# Log Event & Formatting
# ============================================================================


@dataclass(frozen=True, slots=True)
class LogEvent:
    """Immutable representation of a sanitized telemetry event."""

    timestamp: datetime
    level: str
    namespace: str
    module: str
    function: str
    line: int
    message: str
    context: dict[str, object]
    error: dict[str, object] | None
    category: str | None


def format_human_record(event: LogEvent, use_color: bool = False) -> str:
    """Format a LogEvent into a human-readable text line.

    Format: `YYYY-MM-DD HH:MM:SS.mmm | LEVEL | module:function:line - message`

    Args:
        event: The LogEvent to format.
        use_color: Whether to apply ANSI color codes to level and message.

    Returns:
        Formatted single line string.
    """
    ts_str = event.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    loc_str = f"{event.module}:{event.function}:{event.line}"

    if use_color:
        color = LEVEL_COLORS.get(event.level, "")
        level_colored = f"{color}{event.level:<8}{ANSI_RESET}"
        msg_colored = f"{color}{event.message}{ANSI_RESET}"
        line = f"{ts_str} | {level_colored} | {loc_str} - {msg_colored}"
    else:
        line = f"{ts_str} | {event.level:<8} | {loc_str} - {event.message}"

    if event.error is not None:
        err_type = event.error.get("type", "Error")
        err_msg = event.error.get("message", "")
        line += f" [{err_type}: {err_msg}]"

    return line


def format_json_record(event: LogEvent) -> str:
    """Serialize a LogEvent into a bounded JSON string.

    Args:
        event: The LogEvent to format.

    Returns:
        JSON string without trailing newline.
    """
    payload: dict[str, object] = {
        "timestamp": event.timestamp.isoformat(),
        "level": event.level,
        "namespace": event.namespace,
        "module": event.module,
        "function": event.function,
        "line": event.line,
        "message": event.message,
    }
    if event.category:
        payload["category"] = event.category
    if event.context:
        payload["context"] = event.context
    if event.error:
        payload["error"] = event.error

    try:
        serialized = json.dumps(payload, ensure_ascii=False)
        if len(serialized.encode("utf-8")) > MAX_EVENT_BYTES:
            # Bound oversized payload by dropping context details
            payload["context"] = {"_truncated": True}
            payload["message"] = event.message[:256] + "... [TRUNCATED]"
            serialized = json.dumps(payload, ensure_ascii=False)
        return serialized
    except Exception:  # noqa: BLE001
        fallback = {
            "timestamp": event.timestamp.isoformat(),
            "level": event.level,
            "namespace": event.namespace,
            "message": "[FAILED_TO_SERIALIZE_EVENT]",
        }
        return json.dumps(fallback)


# ============================================================================
# Sinks, Windows-Safe Rotation & Archiving
# ============================================================================


class RotatingZipSink:
    """Thread-safe rotating file sink with 10 MB ZIP rotation and retention pruning.

    Designed to handle Windows file-locking semantics by closing the open stream
    before moving the file and archiving it in the background.
    """

    def __init__(
        self,
        filepath: Path,
        max_bytes: int = DEFAULT_MAX_BYTES,
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ) -> None:
        """Initialize the rotating sink.

        Args:
            filepath: Destination log file path.
            max_bytes: Maximum size in bytes before rotation (default 10 MB).
            retention_days: Number of days to retain rotated ZIP archives.
        """
        self.filepath = filepath
        self.max_bytes = max_bytes
        self.retention_days = retention_days
        self._lock = threading.Lock()
        self._stream: TextIO | None = None
        self._ensure_parent_dir()

    def _ensure_parent_dir(self) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def _get_stream(self) -> TextIO:
        if self._stream is None or self._stream.closed:
            self._ensure_parent_dir()
            self._stream = self.filepath.open("a", encoding="utf-8")
        return self._stream

    def write(self, record_line: str) -> None:
        """Write a record line to the file, triggering rotation if limit is reached.

        Args:
            record_line: Single record line (JSON or text).
        """
        with self._lock:
            stream = self._get_stream()
            stream.write(record_line + "\n")
            stream.flush()

            try:
                current_size = self.filepath.stat().st_size
                if current_size >= self.max_bytes:
                    self._rotate_and_archive()
            except OSError:
                pass

    def _rotate_and_archive(self) -> None:
        """Close the stream, rotate the file, and create a ZIP archive."""
        # 1. Close active stream under Windows to release file descriptor locks
        if self._stream is not None and not self._stream.closed:
            self._stream.close()
            self._stream = None

        if not self.filepath.exists():
            return

        ts_str = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
        base_name = self.filepath.stem
        rotated_path = self.filepath.parent / f"{base_name}_{ts_str}.log"
        zip_path = self.filepath.parent / f"{base_name}_{ts_str}.zip"

        try:
            # Rename the full file
            self.filepath.rename(rotated_path)

            # Create deflated ZIP archive
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.write(rotated_path, arcname=rotated_path.name)

            # Remove uncompressed rotated file
            rotated_path.unlink(missing_ok=True)

            # Prune old archives
            self.prune_expired_archives()
        except OSError:
            pass

    def prune_expired_archives(self) -> None:
        """Prune zip archives older than the retention threshold."""
        cutoff = datetime.now(UTC) - timedelta(days=self.retention_days)
        base_name = self.filepath.stem
        pattern = f"{base_name}_*.zip"

        for zip_file in self.filepath.parent.glob(pattern):
            try:
                mtime = datetime.fromtimestamp(zip_file.stat().st_mtime, tz=UTC)
                if mtime < cutoff:
                    zip_file.unlink(missing_ok=True)
            except OSError:
                pass

    def close(self) -> None:
        """Flush and close the active file stream."""
        with self._lock:
            if self._stream is not None and not self._stream.closed:
                try:
                    self._stream.flush()
                    self._stream.close()
                except OSError:
                    pass
                finally:
                    self._stream = None


# ============================================================================
# Telemetry Worker & Engine
# ============================================================================


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Immutable configuration profile for host telemetry."""

    log_dir: Path = DEFAULT_LOG_DIR
    level: int = logging.INFO
    max_bytes: int = DEFAULT_MAX_BYTES
    retention_days: int = DEFAULT_RETENTION_DAYS
    include_console: bool = True
    use_color: bool | None = None


class TelemetryEngine:
    """Telemetry coordinator, multi-sink router, and async queue manager."""

    _instance: TelemetryEngine | None = None
    _configured: bool = False
    _init_lock: Final[threading.RLock] = threading.RLock()

    def __init__(self, config: LoggingConfig) -> None:
        """Initialize the telemetry engine.

        Args:
            config: Telemetry configuration profile.
        """
        self.config = config
        self.queue: queue.Queue[LogEvent | object] = queue.Queue(
            maxsize=DEFAULT_QUEUE_SIZE
        )
        self._sentinel = object()
        self.dropped_events: int = 0
        self.is_running: bool = False

        # Console sink setup
        self._console_stream = sys.stderr
        self._use_color = (
            config.use_color
            if config.use_color is not None
            else getattr(self._console_stream, "isatty", lambda: False)()
        )

        # File sinks for multi-sink routing
        log_dir = config.log_dir
        self.sink_app = RotatingZipSink(
            log_dir / "app.log", config.max_bytes, config.retention_days
        )
        self.sink_access = RotatingZipSink(
            log_dir / "access.log", config.max_bytes, config.retention_days
        )
        self.sink_debug = RotatingZipSink(
            log_dir / "debug.log", config.max_bytes, config.retention_days
        )
        self.sink_errors = RotatingZipSink(
            log_dir / "errors.log", config.max_bytes, config.retention_days
        )

        # Background worker thread
        self._worker_thread = threading.Thread(
            target=self._worker_loop, name="TelemetryWorker", daemon=True
        )
        self.is_running = True
        self._worker_thread.start()
        atexit.register(self.shutdown)

    @classmethod
    def get_or_create(cls, config: LoggingConfig | None = None) -> TelemetryEngine:
        """Get the active singleton engine or create it under a lock.

        Args:
            config: Optional config profile. If None, default profile is used.

        Returns:
            The active TelemetryEngine singleton.
        """
        with cls._init_lock:
            if cls._instance is None:
                cfg = config if config is not None else LoggingConfig()
                cls._instance = TelemetryEngine(cfg)
            return cls._instance

    @classmethod
    def is_active(cls) -> bool:
        """Return True if an active singleton engine is running."""
        with cls._init_lock:
            return cls._instance is not None and cls._instance.is_running

    @classmethod
    def is_configured(cls) -> bool:
        """Return True if an engine was explicitly configured."""
        with cls._init_lock:
            return (
                cls._configured
                and cls._instance is not None
                and cls._instance.is_running
            )

    @classmethod
    def mark_configured(cls) -> None:
        """Mark the engine as explicitly configured under lock."""
        with cls._init_lock:
            cls._configured = True

    @classmethod
    def reset(cls) -> None:
        """Shut down and reset the active singleton engine."""
        with cls._init_lock:
            cls._configured = False
            if cls._instance is not None:
                cls._instance.shutdown()
                cls._instance = None

    @classmethod
    def flush_active(cls, timeout: float = 5.0) -> bool:
        """Flush the active singleton engine if initialized."""
        with cls._init_lock:
            inst = cls._instance
        if inst is not None:
            return inst.flush(timeout=timeout)
        return True

    @classmethod
    def shutdown_active(cls, timeout: float = 5.0) -> bool:
        """Shutdown the active singleton engine if initialized."""
        with cls._init_lock:
            inst = cls._instance
        if inst is not None:
            return inst.shutdown(timeout=timeout)
        return True

    def enqueue(self, event: LogEvent) -> None:
        """Enqueue an event non-blockingly, incrementing drop counter on full.

        Args:
            event: The sanitized LogEvent to enqueue.
        """
        if not self.is_running:
            return
        try:
            self.queue.put_nowait(event)
        except queue.Full:
            self.dropped_events += 1

    def _worker_loop(self) -> None:
        """Background worker thread draining events and writing to sinks."""
        while self.is_running:
            try:
                item = self.queue.get(timeout=0.05)
            except queue.Empty:
                continue

            if item is self._sentinel:
                self.queue.task_done()
                break

            if isinstance(item, LogEvent):
                with contextlib.suppress(Exception):
                    self._dispatch_event(item)
                self.queue.task_done()

        # Drain any remaining items after loop exit
        while not self.queue.empty():
            try:
                item = self.queue.get_nowait()
                if item is not self._sentinel and isinstance(item, LogEvent):
                    with contextlib.suppress(Exception):
                        self._dispatch_event(item)
                self.queue.task_done()
            except queue.Empty, ValueError:
                break

    def _dispatch_event(self, event: LogEvent) -> None:
        """Dispatch a single event to console and appropriate file sinks.

        Args:
            event: The event to dispatch.
        """
        # 1. Console emission
        event_level_no = LEVEL_NUMBERS.get(event.level, logging.INFO)
        if self.config.include_console and event_level_no >= self.config.level:
            human_line = format_human_record(event, use_color=self._use_color)
            try:
                self._console_stream.write(human_line + "\n")
                self._console_stream.flush()
            except OSError:
                pass

        # 2. JSON Line for file sinks
        json_line = format_json_record(event)

        # app.log receives all runtime logs
        self.sink_app.write(json_line)

        # debug.log receives DEBUG level logs
        if event.level == "DEBUG":
            self.sink_debug.write(json_line)

        # errors.log receives ERROR and CRITICAL logs
        if event.level in ("ERROR", "CRITICAL"):
            self.sink_errors.write(json_line)

        # access.log receives access-categorized logs
        if (
            event.category == "access"
            or event.namespace.startswith("uvicorn.access")
            or event.namespace.endswith(".access")
        ):
            self.sink_access.write(json_line)

    def flush(self, timeout: float = 5.0) -> bool:
        """Wait until all queued events are processed.

        Args:
            timeout: Maximum seconds to wait.

        Returns:
            True if queue was drained, False if timed out.
        """
        deadline = time.monotonic() + timeout
        while self.queue.unfinished_tasks > 0:
            if time.monotonic() > deadline:
                return False
            time.sleep(0.002)
        return True

    def shutdown(self, timeout: float = 5.0) -> bool:
        """Gracefully drain the queue and close all sink resources.

        Args:
            timeout: Maximum seconds to wait.

        Returns:
            True if shutdown completed cleanly, False otherwise.
        """
        with self._init_lock:
            if not self.is_running:
                return True
            self.is_running = False

            # Signal worker to terminate
            with contextlib.suppress(queue.Full):
                self.queue.put_nowait(self._sentinel)

            if self._worker_thread.is_alive():
                self._worker_thread.join(timeout=timeout)

            # Close all sinks
            self.sink_app.close()
            self.sink_access.close()
            self.sink_debug.close()
            self.sink_errors.close()
            return True


# ============================================================================
# Bound Logger & Facade
# ============================================================================


class BoundLogger:
    """Bound logger wrapper providing contextual logging and safe boundaries."""

    def __init__(
        self,
        name: str,
        context: dict[str, object] | None = None,
        category: str | None = None,
    ) -> None:
        """Create a new BoundLogger.

        Args:
            name: Logger namespace name.
            context: Immutable contextual key-value mapping.
            category: Optional log category slug (e.g. 'access').
        """
        self.name = name
        self._context: dict[str, object] = dict(context) if context else {}
        self._category = category

    def bind(self, **kwargs: object) -> BoundLogger:
        """Return a new BoundLogger with merged contextual key-value pairs.

        Args:
            **kwargs: Metadata key-value pairs to bind to the logger.

        Returns:
            New BoundLogger instance with merged context.
        """
        new_ctx = dict(self._context)
        sanitized = sanitize_payload(kwargs)
        if isinstance(sanitized, dict):
            new_ctx.update(sanitized)
        return BoundLogger(self.name, context=new_ctx, category=self._category)

    def _log(
        self,
        level_name: str,
        msg: str,
        *args: object,
        category: str | None = None,
        error: dict[str, object] | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        """Internal emission handler."""
        engine = TelemetryEngine.get_or_create()

        # Format positional args if provided
        if args:
            try:
                formatted_msg = msg % args
            except Exception:  # noqa: BLE001
                formatted_msg = f"{msg} [ARGS_INTERPOLATION_FAILED: {args!r}]"
        else:
            formatted_msg = msg

        sanitized_msg = redact_secrets(formatted_msg)

        # Merge contexts: Bound context + Scoped Request context + extra fields
        merged_context: dict[str, object] = dict(self._context)
        scoped_ctx = _CORRELATION_CONTEXT.get()
        if scoped_ctx:
            merged_context.update(scoped_ctx)
        if extra:
            sanitized_extra = sanitize_payload(extra)
            if isinstance(sanitized_extra, dict):
                merged_context.update(sanitized_extra)

        # Extract caller location
        frame = sys._getframe(2)  # noqa: SLF001
        module_name = frame.f_globals.get("__name__", "unknown")
        func_name = frame.f_code.co_name
        line_no = frame.f_lineno

        chosen_category = category or self._category

        event = LogEvent(
            timestamp=datetime.now(UTC),
            level=level_name,
            namespace=self.name,
            module=module_name,
            function=func_name,
            line=line_no,
            message=sanitized_msg,
            context=merged_context,
            error=error,
            category=chosen_category,
        )
        engine.enqueue(event)

    def debug(
        self,
        msg: str,
        *args: object,
        category: str | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        """Emit a DEBUG level log event."""
        self._log("DEBUG", msg, *args, category=category, extra=extra)

    def info(
        self,
        msg: str,
        *args: object,
        category: str | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        """Emit an INFO level log event."""
        self._log("INFO", msg, *args, category=category, extra=extra)

    def warning(
        self,
        msg: str,
        *args: object,
        category: str | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        """Emit a WARNING level log event."""
        self._log("WARNING", msg, *args, category=category, extra=extra)

    def error(
        self,
        msg: str,
        *args: object,
        category: str | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        """Emit an ERROR level log event."""
        self._log("ERROR", msg, *args, category=category, extra=extra)

    def critical(
        self,
        msg: str,
        *args: object,
        category: str | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        """Emit a CRITICAL level log event."""
        self._log("CRITICAL", msg, *args, category=category, extra=extra)

    def exception(
        self,
        msg: str,
        *args: object,
        category: str | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        """Emit an ERROR level event with safe, redacted exception diagnostics."""
        exc_val = sys.exception()
        err_info = safe_error_boundary(exc_val) if exc_val is not None else None
        self._log("ERROR", msg, *args, category=category, error=err_info, extra=extra)


# ============================================================================
# Request Correlation Context
# ============================================================================


@contextlib.contextmanager
def request_context(**metadata: object) -> Generator[None]:
    """Scope sanitized request metadata to the current execution context.

    Uses `contextvars.ContextVar` to propagate correlation tokens across async tasks
    without cross-talk. Restores prior context upon scope exit.

    Args:
        **metadata: Key-value pairs describing request or execution context.

    Yields:
        None
    """
    raw_current = _CORRELATION_CONTEXT.get()
    current: dict[str, object] = dict(raw_current) if raw_current else {}
    sanitized = sanitize_payload(metadata)
    if isinstance(sanitized, dict):
        current.update(sanitized)

    token = _CORRELATION_CONTEXT.set(current)
    try:
        yield
    finally:
        _CORRELATION_CONTEXT.reset(token)


# ============================================================================
# Standard Library Handler Bridge
# ============================================================================


class HostBridgeHandler(logging.Handler):
    """Bridge standard library log records into the host telemetry engine."""

    def __init__(self, category: str | None = None) -> None:
        super().__init__()
        self.category = category

    @override
    def emit(self, record: logging.LogRecord) -> None:
        """Forward a standard library log record into TelemetryEngine."""
        msg = record.getMessage()
        sanitized_msg = redact_secrets(msg)
        engine = TelemetryEngine.get_or_create()

        err_info: dict[str, object] | None = None
        if record.exc_info and record.exc_info[1]:
            err_info = safe_error_boundary(record.exc_info[1])

        event = LogEvent(
            timestamp=datetime.fromtimestamp(record.created, tz=UTC),
            level=record.levelname,
            namespace=record.name,
            module=record.module,
            function=record.funcName,
            line=record.lineno,
            message=sanitized_msg,
            context={},
            error=err_info,
            category=self.category,
        )
        engine.enqueue(event)


def bridge_standard_logging(logger_names: tuple[str, ...]) -> None:
    """Attach host telemetry handlers to external standard-library loggers.

    Intercepts diagnostics from frameworks like Uvicorn, FastAPI, and HTTPX.

    Args:
        logger_names: Tuple of logger names to intercept.
    """
    for name in logger_names:
        stdlib_logger = logging.getLogger(name)
        # Avoid duplicate bridge handlers
        if not any(isinstance(h, HostBridgeHandler) for h in stdlib_logger.handlers):
            category = "access" if "access" in name else None
            handler = HostBridgeHandler(category=category)
            stdlib_logger.addHandler(handler)
            stdlib_logger.propagate = False


# ============================================================================
# Public Module Exports & Lifecycle Management
# ============================================================================


def get_logger(name: str | None = None) -> BoundLogger:
    """Resolve a namespace logger without configuring sinks or incurring I/O.

    Args:
        name: Logger namespace name (typically `__name__`).

    Returns:
        A BoundLogger instance configured for the specified namespace.
    """
    return BoundLogger(name or "app")


# Global pre-instantiated root logger
logger: BoundLogger = get_logger("app")


def configure_host_logging(
    log_dir: Path | None = None,
    *,
    level: int | str = "INFO",
    max_bytes: int = DEFAULT_MAX_BYTES,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    include_console: bool = True,
    use_color: bool | None = None,
) -> TelemetryEngine:
    """Explicitly configure and initialize the host telemetry engine.

    If an engine is already running, it is shut down and replaced with the new
    configuration. Useful for test suites and production entrypoints.

    Args:
        log_dir: Target directory for log files and archives (default: 'data/logs').
        level: Minimum threshold log level (integer or string representation).
        max_bytes: Byte limit per file before ZIP rotation (default: 10 MB).
        retention_days: Days of rotated archives to retain (default: 10).
        include_console: Whether to emit human-readable lines to stderr.
        use_color: Whether to use ANSI terminal colors (None for auto-detection).

    Returns:
        The newly configured TelemetryEngine instance.
    """
    log_level = parse_log_level(level)
    reset_logging()
    cfg = LoggingConfig(
        log_dir=log_dir or DEFAULT_LOG_DIR,
        level=log_level,
        max_bytes=max_bytes,
        retention_days=retention_days,
        include_console=include_console,
        use_color=use_color,
    )
    TelemetryEngine.mark_configured()
    return TelemetryEngine.get_or_create(cfg)


def flush(timeout: float = 5.0) -> bool:
    """Flush pending events across all sinks."""
    return TelemetryEngine.flush_active(timeout=timeout)


def shutdown(timeout: float = 5.0) -> bool:
    """Shutdown the active telemetry engine and release resources."""
    return TelemetryEngine.shutdown_active(timeout=timeout)


def reset_logging() -> None:
    """Shut down and reset the telemetry singleton for test isolation."""
    TelemetryEngine.reset()
