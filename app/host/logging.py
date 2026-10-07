"""Centralized application telemetry, multi-sink routing, and DebugConsole.

Description:
    This module provides the central telemetry engine, multi-sink router,
    credential/path redaction pipeline, in-memory ring buffer, and DebugConsole
    projections for the HaruQuantAI host process and runtime plugins. It guarantees
    that sensitive credentials, authentication tokens, private keys, and physical
    local filesystem paths are systematically fingerprinted or sanitized before
    emission, while delivering non-blocking asynchronous event delivery across four
    dedicated rotating ZIP file sinks, a bounded in-memory ring buffer, and a
    color-aware console sink. Applications obtain logger handles via
    `get_logger(__name__)` or the global `logger` instance. The engine lazily
    initializes on the first runtime log emission, keeping module import times
    completely inert and side-effect free. Internally, a dedicated background worker
    consumes a bounded queue to isolate latency-sensitive quantitative workflows
    from disk I/O, file rotation, and ZIP archiving under Windows file-locking
    semantics. It also provides the FastAPI router and projection models consumed
    by the browser-based DebugConsole workspace.

Purpose:
    FEAT-HOST-LOGGING: Centralized application telemetry, multi-sink routing,
    credential and path redaction, and DebugConsole projection.

Key Capabilities:
    - FR-HOST-LOG-RESOLVE-NAMESPACE: Resolve namespaces and bootstrap telemetry
      lazily on first runtime emission without import-time side-effects.
      Associated: `get_logger()`, `TelemetryEngine.get_or_create()`
      Logging: Emits DEBUG telemetry upon runtime initialization of new namespaces.
    - FR-HOST-LOG-BOUND-CONTEXT: Expose bound logger with immutable context.
      Associated: `BoundLogger`, `BoundLogger.bind()`
      Logging: Attaches immutable context key-value pairs to every emitted event.
    - FR-HOST-LOG-SECRET-REDACTION: Fingerprint detected credentials before emission.
      Associated: `redact_secrets()`, `sanitize_payload()`
      Logging: Replaces credentials with deterministic SHA-256 fingerprint digests.
    - FR-HOST-LOG-PATH-REDACTION: Sanitize physical host filesystem paths.
      Associated: `redact_paths()`, `sanitize_payload()`
      Logging: Replaces absolute host paths with logical basename references.
    - FR-HOST-LOG-STRUCTURED-FORMATTING: Serialize events to bounded JSON and text.
      Associated: `format_human_record()`, `format_json_record()`
      Logging: Formats records for terminal and disk with bounded sizes.
    - FR-HOST-LOG-MULTI-SINK-ROUTING: Demux events across app, access, debug,
      and error logs.
      Associated: `TelemetryEngine._dispatch_event()`, `SinkRouter`
      Logging: Routes events to app.log, access.log, debug.log, and errors.log.
    - FR-HOST-LOG-WINDOWS-ROTATING-ZIP: Enforce byte-limit ZIP rotation and retention.
      Associated: `RotatingZipSink._rotate_and_archive()`, `prune_expired_archives()`
      Logging: Rotates files at max_bytes, archives with deflated ZIP compression.
    - FR-HOST-LOG-RING-BUFFER: In-memory bounded ring buffer with cursor tracking.
      Associated: `LogRingBuffer.append()`, `LogRingBuffer.get_snapshot()`
      Logging: Buffers recent events, tracks monotonic cursors, and flags gaps.
    - FR-HOST-LOG-DEBUG-CONSOLE-PROJECTION: HTTP endpoints for DebugConsole UI.
      Associated: `create_debug_console_router()`, route handlers
      Logging: Emits INFO on log retrieval, category queries, and log clearance.
    - FR-HOST-LOG-REQUEST-CORRELATION: Scope request metadata via contextvars.
      Associated: `request_context()`
      Logging: Injects scoped correlation tokens into concurrent async event contexts.
    - FR-HOST-LOG-SAFE-ERROR-BOUNDARY: Log errors without sensitive tracebacks.
      Associated: `safe_error_boundary()`, `BoundLogger.exception()`
      Logging: Captures exception class, message, and bounded call-site frames.
    - FR-HOST-LOG-ASYNC-QUEUE: Non-blocking bounded queue worker with drop tracking.
      Associated: `TelemetryEngine.enqueue()`, `TelemetryWorker`
      Logging: Discards events non-blockingly on saturation and tracks drop metrics.
    - FR-HOST-LOG-LIBRARY-BRIDGE: Forward and sanitize standard-library loggers.
      Associated: `bridge_standard_logging()`, `HostBridgeHandler`
      Logging: Intercepts foreign logging records and routes through telemetry engine.
    - FR-HOST-LOG-LIFECYCLE-SYNC: Clean shutdown, atexit cleanup, and test isolation.
      Associated: `flush()`, `shutdown()`, `reset_logging()`
      Logging: Synchronizes queued events, releases file handles, and resets state.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.logging import (
        configure_host_logging,
        create_debug_console_router,
        get_logger,
        request_context,
        reset_logging,
    )

    # 1. Configure or rely on lazy bootstrap
    engine = configure_host_logging(Path("data/logs"))

    # 2. Bind context and scope requests
    log = get_logger("app.workspace").bind(worker_id="w-01")
    with request_context(request_id="req-999"):
        log.info("Processing job", extra={"task": "backtest"})

    # 3. Mount DebugConsole router in FastAPI
    router = create_debug_console_router(engine)

    # 4. Clean teardown at shutdown
    reset_logging()
    ```

CLI Usage:
    Run application and inspect rotating logs or live access lines via shell:
    ```bash
    # Inspect rotating JSON files
    tail -f data/logs/app.log

    # View live access logs
    tail -f data/logs/access.log
    ```
"""

from __future__ import annotations

import atexit
import collections
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

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from collections.abc import Generator

__all__ = [
    "BoundLogger",
    "ClearResponse",
    "DebugConsoleSnapshot",
    "DebugLogEntry",
    "LogEvent",
    "LogQuery",
    "LogRingBuffer",
    "LoggingConfig",
    "RotatingZipSink",
    "TelemetryEngine",
    "bridge_standard_logging",
    "configure_host_logging",
    "create_debug_console_router",
    "fingerprint_secret",
    "flush",
    "format_human_record",
    "format_json_record",
    "get_logger",
    "logger",
    "parse_log_level",
    "redact_paths",
    "redact_secrets",
    "request_context",
    "reset_logging",
    "safe_error_boundary",
    "sanitize_payload",
    "shutdown",
]

# ============================================================================
# Constants & Defaults
# ============================================================================

DEFAULT_LOG_DIR: Final[Path] = Path("data/logs")
DEFAULT_MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB
DEFAULT_RETENTION_DAYS: Final[int] = 10
DEFAULT_QUEUE_SIZE: Final[int] = 1024
DEFAULT_RING_BUFFER_CAPACITY: Final[int] = 1000
MAX_EVENT_BYTES: Final[int] = 16 * 1024  # 16 KB max serialized event size
MAX_STACK_FRAMES: Final[int] = 8
MAX_RECURSION_DEPTH: Final[int] = 8
MAX_DEBUG_CONSOLE_CHARS: Final[int] = 10_000

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
    return level


# ============================================================================
# Secret & Path Redaction Patterns
# ============================================================================

# Matches sensitive keys in dictionary/json representations
_SENSITIVE_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?i)^(?:password|passwd|pwd|key|api[_-]?key|(?:access|refresh|auth)?[_-]?token|"
    r"session[_-]?id|sessionid|db[_-]?password|database[_-]?password|"
    r"authorization|bearer|secret|cookie|private[_-]?key|license[_-]?key)$"
)

# Matches key-value assignments in strings (e.g. password="xyz", api_key: "abc")
_ASSIGNMENT_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?i)(?P<prefix>\b(?:password|passwd|pwd|key|api[_-]?key|"
    r"(?:access|refresh|auth)?[_-]?token|session[_-]?id|sessionid|"
    r"db[_-]?password|database[_-]?password|authorization|bearer|secret|cookie|"
    r"license[_-]?key)\b[\"']?\s*[:=]\s*)(?P<quote>[\"'])(?P<secret>[^\"']+)(?P=quote)"
)

# Matches bearer tokens directly (e.g. Bearer eyJhbGci...)
_BEARER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?i)\bBearer\s+(?P<token>[A-Za-z0-9_\-\.]{16,})"
)

# Matches already redacted markers to ensure idempotency
_ALREADY_REDACTED_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\[REDACTED:[0-9a-f]{12}\]$"
)

# Matches physical absolute filesystem paths (Windows drive and POSIX user homes)
_WINDOWS_PATH_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[a-zA-Z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)+[^\\/:*?\"<>|\r\n]+"
)
_POSIX_PATH_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?:/(?:Users|home)/[^/\s\"'<>|:*?]+(?:/[^/\s\"'<>|:*?]+)+)"
)

# ContextVar for request correlation across tasks
_CORRELATION_CONTEXT: Final[ContextVar[dict[str, object] | None]] = ContextVar(
    "host_logging_correlation_context", default=None
)

# Thread-local reentrancy guard
_LOCAL_STATE = threading.local()


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


def redact_paths(text: str) -> str:
    """Redact physical filesystem paths, replacing them with logical basenames.

    Args:
        text: Input string that may contain physical host paths.

    Returns:
        String with physical paths replaced by `[PATH:<basename>]`.
    """
    if not text:
        return text

    def _replace_win_path(match: re.Match[str]) -> str:
        full_path = match.group(0)
        basename = full_path.rstrip("\\").split("\\")[-1]
        return f"[PATH:{basename}]"

    def _replace_posix_path(match: re.Match[str]) -> str:
        full_path = match.group(0)
        basename = full_path.rstrip("/").split("/")[-1]
        return f"[PATH:{basename}]"

    result = _WINDOWS_PATH_PATTERN.sub(_replace_win_path, text)
    return _POSIX_PATH_PATTERN.sub(_replace_posix_path, result)


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
    redacted = _BEARER_PATTERN.sub(_replace_bearer, redacted)
    return redact_paths(redacted)


def sanitize_payload(obj: object, depth: int = 0) -> object:
    """Recursively sanitize data structures, masking secrets and physical paths.

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
    cursor: int = 0


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
        "cursor": event.cursor,
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
    """Thread-safe rotating file sink with ZIP archiving and retention pruning.

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
# Log Ring Buffer & Debug Console Projection
# ============================================================================


class DebugLogEntry(BaseModel):
    """Debug console log item projection schema."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(description="Unique entry identifier")
    time: str = Field(description="Formatted timestamp HH:MM:SS")
    category: str = Field(description="Log category name")
    message: str = Field(description="Sanitized log message")
    level: str = Field(description="Log level name")
    cursor: int = Field(description="Monotonic cursor identifier")
    timestamp: str = Field(description="Full ISO 8601 timestamp string")


class DebugConsoleSnapshot(BaseModel):
    """Snapshot of debug console logs with pagination and gap metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    entries: list[DebugLogEntry] = Field(description="Filtered log entries")
    oldest_cursor: int = Field(description="Oldest available cursor in ring buffer")
    newest_cursor: int = Field(description="Newest available cursor in ring buffer")
    total_retained: int = Field(description="Total retained entries in ring buffer")
    has_gap: bool = Field(
        description="True if requested cursor is older than ring buffer"
    )


class ClearResponse(BaseModel):
    """Result of clearing the debug console ring buffer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cleared: bool = Field(description="True if ring buffer was cleared")
    cleared_at_cursor: int = Field(description="Cursor high-water mark at clearance")


class LogQuery(BaseModel):
    """Query parameters for querying debug console logs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    after_cursor: int | None = Field(default=None, description="Cursor offset query")
    category: str = Field(default="All", description="Category filter query")
    query: str | None = Field(default=None, description="Case-insensitive search query")
    limit: int = Field(default=100, ge=1, le=1000, description="Max entries to return")


class LogRingBuffer:
    """Thread-safe bounded in-memory ring buffer with cursor and gap tracking."""

    def __init__(self, capacity: int = DEFAULT_RING_BUFFER_CAPACITY) -> None:
        """Initialize ring buffer.

        Args:
            capacity: Maximum events to retain in memory (default 1000).
        """
        self.capacity = capacity
        self._lock = threading.Lock()
        self._entries: collections.deque[LogEvent] = collections.deque(maxlen=capacity)
        self._next_cursor: int = 1
        self._oldest_cursor: int = 1
        self._low_watermark: int = 0
        self._categories: set[str] = {"All", "System", "Application"}

    def append(self, event: LogEvent) -> LogEvent:
        """Assign monotonic cursor, record category, and buffer event in ring.

        Args:
            event: The LogEvent to buffer.

        Returns:
            LogEvent updated with assigned cursor.
        """
        with self._lock:
            cursor = self._next_cursor
            self._next_cursor += 1

            category = event.category or "Application"
            self._categories.add(category)

            stamped_event = LogEvent(
                timestamp=event.timestamp,
                level=event.level,
                namespace=event.namespace,
                module=event.module,
                function=event.function,
                line=event.line,
                message=event.message,
                context=event.context,
                error=event.error,
                category=category,
                cursor=cursor,
            )

            # Check if ring buffer is full and oldest cursor will advance
            if len(self._entries) == self.capacity:
                dropped = self._entries[0]
                self._oldest_cursor = dropped.cursor + 1

            self._entries.append(stamped_event)
            return stamped_event

    def get_snapshot(
        self,
        after_cursor: int | None = None,
        category: str = "All",
        query: str | None = None,
        limit: int = 100,
    ) -> DebugConsoleSnapshot:
        """Retrieve bounded snapshot of logs with cursor pagination and filtering.

        Args:
            after_cursor: Retrieve logs with cursor strictly greater than this value.
            category: Filter by specific category or 'All'.
            query: Case-insensitive text query to filter messages.
            limit: Maximum entries to return.

        Returns:
            DebugConsoleSnapshot with filtered entries and cursor metadata.
        """
        with self._lock:
            oldest = self._oldest_cursor
            newest = self._next_cursor - 1
            has_gap = False

            if after_cursor is not None and after_cursor < (oldest - 1):
                has_gap = True

            min_cursor = max(
                after_cursor + 1 if after_cursor is not None else oldest,
                self._low_watermark + 1,
            )

            filtered_entries: list[DebugLogEntry] = []
            search_query = query.strip().lower() if query else None

            # Iterate entries
            for event in self._entries:
                if event.cursor < min_cursor:
                    continue

                event_cat = event.category or "Application"
                if category not in ("All", event_cat):
                    continue

                if search_query and search_query not in event.message.lower():
                    continue

                ts_time = event.timestamp.strftime("%H:%M:%S")
                entry = DebugLogEntry(
                    id=f"log-{event.cursor}",
                    time=ts_time,
                    category=event_cat,
                    message=event.message,
                    level=event.level,
                    cursor=event.cursor,
                    timestamp=event.timestamp.isoformat(),
                )
                filtered_entries.append(entry)
                if len(filtered_entries) >= limit:
                    break

            return DebugConsoleSnapshot(
                entries=filtered_entries,
                oldest_cursor=oldest,
                newest_cursor=newest,
                total_retained=len(self._entries),
                has_gap=has_gap,
            )

    def get_categories(self) -> list[str]:
        """Return sorted list of active log categories starting with 'All'."""
        with self._lock:
            categories = sorted(self._categories - {"All"})
            return ["All", *categories]

    def clear(self) -> int:
        """Clear the ring buffer and advance low-watermark.

        Returns:
            The cursor high-water mark at clearance.
        """
        with self._lock:
            high_watermark = self._next_cursor - 1
            self._low_watermark = high_watermark
            self._entries.clear()
            self._oldest_cursor = self._next_cursor
            return high_watermark


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
    ring_buffer_capacity: int = DEFAULT_RING_BUFFER_CAPACITY
    include_console: bool = True
    use_color: bool | None = None


class TelemetryEngine:
    """Telemetry coordinator, multi-sink router, ring buffer, and async worker."""

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

        # Ring buffer sink for DebugConsole
        self.ring_buffer = LogRingBuffer(capacity=config.ring_buffer_capacity)

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
        """Dispatch a single event to console, ring buffer, and file sinks.

        Args:
            event: The event to dispatch.
        """
        # Reentrancy check
        if getattr(_LOCAL_STATE, "is_dispatching", False):
            return

        _LOCAL_STATE.is_dispatching = True
        try:
            # 1. Ring buffer sink receives event and assigns monotonic cursor
            stamped_event = self.ring_buffer.append(event)

            # 2. Console emission
            event_level_no = LEVEL_NUMBERS.get(stamped_event.level, logging.INFO)
            if self.config.include_console and event_level_no >= self.config.level:
                human_line = format_human_record(
                    stamped_event, use_color=self._use_color
                )
                try:
                    self._console_stream.write(human_line + "\n")
                    self._console_stream.flush()
                except OSError:
                    pass

            # 3. JSON Line for file sinks
            json_line = format_json_record(stamped_event)

            # app.log receives all runtime logs
            self.sink_app.write(json_line)

            # debug.log receives DEBUG level logs
            if stamped_event.level == "DEBUG":
                self.sink_debug.write(json_line)

            # errors.log receives ERROR and CRITICAL logs
            if stamped_event.level in ("ERROR", "CRITICAL"):
                self.sink_errors.write(json_line)

            # access.log receives access-categorized logs
            if (
                stamped_event.category == "access"
                or stamped_event.namespace.startswith("uvicorn.access")
                or stamped_event.namespace.endswith(".access")
            ):
                self.sink_access.write(json_line)
        finally:
            _LOCAL_STATE.is_dispatching = False

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
        if getattr(_LOCAL_STATE, "is_logging", False):
            return

        _LOCAL_STATE.is_logging = True
        try:
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

            chosen_category = category or self._category or "Application"

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
            _bridge_event_to_stdlib(event)
        finally:
            _LOCAL_STATE.is_logging = False

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


def _bridge_event_to_stdlib(event: LogEvent) -> None:
    """Forward sanitized record to active standard library handlers."""
    with contextlib.suppress(Exception):
        stdlib_logger = logging.getLogger(event.namespace)
        root_logger = logging.getLogger()
        active = list(stdlib_logger.handlers) + list(root_logger.handlers)
        if not active:
            return
        lvl_no = getattr(logging, event.level, logging.INFO)
        record = stdlib_logger.makeRecord(
            event.namespace,
            lvl_no,
            event.module,
            event.line,
            event.message,
            args=(),
            exc_info=None,
            func=event.function,
            extra=event.context,
        )
        for handler in active:
            if not isinstance(handler, HostBridgeHandler):
                handler.handle(record)


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
        stdlib_logger.setLevel(logging.DEBUG)
        # Avoid duplicate bridge handlers
        if not any(isinstance(h, HostBridgeHandler) for h in stdlib_logger.handlers):
            category = "access" if "access" in name else None
            handler = HostBridgeHandler(category=category)
            stdlib_logger.addHandler(handler)
            stdlib_logger.propagate = False


# ============================================================================
# Debug Console FastAPI Router
# ============================================================================


def create_debug_console_router(
    engine: TelemetryEngine | None = None,
) -> APIRouter:
    """Create FastAPI router for the browser DebugConsole workspace.

    Provides endpoints matching the UI projection contract and legacy SQX
    plugin path `/debugconsole`.

    Args:
        engine: Optional TelemetryEngine instance. Defaults to active singleton.

    Returns:
        APIRouter configured with DebugConsole projection endpoints.
    """
    router = APIRouter(tags=["debugconsole"])

    def _get_engine() -> TelemetryEngine:
        return engine if engine is not None else TelemetryEngine.get_or_create()

    @router.get(
        "/api/v1/debugconsole/logs",
        response_model=DebugConsoleSnapshot,
        summary="Query DebugConsole logs",
    )
    @router.get(
        "/debugconsole/logs",
        response_model=DebugConsoleSnapshot,
        include_in_schema=False,
    )
    async def get_logs(
        after_cursor: int | None = Query(default=None, description="Cursor offset"),
        category: str = Query(default="All", description="Category filter"),
        query: str | None = Query(default=None, description="Message filter search"),
        limit: int = Query(default=100, ge=1, le=1000, description="Page limit"),
    ) -> DebugConsoleSnapshot:
        eng = _get_engine()
        return eng.ring_buffer.get_snapshot(
            after_cursor=after_cursor,
            category=category,
            query=query,
            limit=limit,
        )

    @router.get(
        "/api/v1/debugconsole/categories",
        response_model=list[str],
        summary="List active DebugConsole categories",
    )
    @router.get(
        "/debugconsole/categories",
        response_model=list[str],
        include_in_schema=False,
    )
    async def get_categories() -> list[str]:
        eng = _get_engine()
        return eng.ring_buffer.get_categories()

    @router.post(
        "/api/v1/debugconsole/clear",
        response_model=ClearResponse,
        status_code=status.HTTP_200_OK,
        summary="Clear DebugConsole log buffer",
    )
    @router.post(
        "/debugconsole/clear",
        response_model=ClearResponse,
        status_code=status.HTTP_200_OK,
        include_in_schema=False,
    )
    async def clear_logs() -> ClearResponse:
        eng = _get_engine()
        cleared_cursor = eng.ring_buffer.clear()
        return ClearResponse(cleared=True, cleared_at_cursor=cleared_cursor)

    return router


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
    ring_buffer_capacity: int = DEFAULT_RING_BUFFER_CAPACITY,
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
        ring_buffer_capacity: Number of entries retained in memory for DebugConsole.
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
        ring_buffer_capacity=ring_buffer_capacity,
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
