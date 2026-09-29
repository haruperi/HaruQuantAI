"""Structured JSON Logging, ANSI Color Console, and Credential Redaction.

Description:
    This module provides the central telemetry and logging engine for the
    HaruQuantAI host process. It exists to guarantee that sensitive credentials,
    bearer tokens, and authorization parameters are systematically redacted before
    emission, while delivering structured JSON-lines telemetry for machine analysis
    and colored console logs for developer diagnostics. Externally, it participates
    in three key workflows: (1) `app.main` calls `configure_boot_logging()` at the
    earliest phase of process boot to capture startup events in memory before
    storage is initialized; (2) `BootstrapCoordinator` calls `configure_host_logging()`
    to open the rotating file sink, replay buffered early boot events, and attach
    Uvicorn server log forwarding, subsequently calling `close_host_logging()` on
    shutdown; and (3) Host, workspace, and plugin modules obtain logger handles via
    `get_logger(__name__)` and attach structured context fields without configuring
    handlers. Internally, `SensitiveDataFilter` scrubs sensitive patterns via regex;
    `bind_correlation()` manages request tracing contexts; and `JsonLinesFormatter`
    and `ColorFormatter` serialize records for disk and terminal output.

Purpose:
    FEAT-HOST-LOGGING: Structured Logging, Credential Redaction, and Early Boot Replay.
    Provides structured JSON and color console logging, automated credential
    masking, request correlation context, and early boot buffer replay.

Key Capabilities:
    - FR-HOST-LOGGING-CREDENTIAL-REDACTION: Automatic Secret Masking & Redaction
      Associated: `SensitiveDataFilter`, `redact_sensitive()`,
      `secret_fingerprint()`
      Logging: Replaces detected passwords, tokens, and authorization
      headers with deterministic hash fingerprints in all emitted records.
    - FR-HOST-LOGGING-BOOT-BUFFER: Early Startup Memory Buffer & Replay
      Associated: `BootBuffer`, `configure_boot_logging()`
      Logging: Captures log events in memory prior to disk readiness and
      replays them into the rotating file handler upon initialization.
    - FR-HOST-LOGGING-ROTATING-SINK: Bounded Rotating File Telemetry
      Associated: `configure_host_logging()`, `close_host_logging()`
      Logging: Binds rotating JSON log file, enforces size limits, and
      replays early buffered boot records to disk.
    - FR-HOST-LOGGING-CORRELATION-TRACING: Request Context Correlation
      Associated: `bind_correlation()`
      Logging: Injects contextual correlation IDs into structured record
      metadata for end-to-end request tracing.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.logging import (
        bind_correlation,
        close_host_logging,
        configure_host_logging,
        get_logger,
    )

    # 1. Configure rotating log sink
    logger = configure_host_logging(Path("data/logs"))

    # 2. Log with structured metadata and request correlation
    app_logger = get_logger("app.workspace")
    with bind_correlation("req-123"):
        app_logger.info("Processing task", extra={"fields": {"task_id": "t1"}})

    # 3. Release handlers at shutdown
    close_host_logging()
    ```

CLI Usage:
    Logging behavior and output sinks are controlled via entrypoint CLI flags:
    ```bash
    # Run host with custom log directory
    uv run python -m app.main --data-dir ./data

    # Inspect rotating JSON log lines
    tail -f data/logs/haruquantai.log
    ```
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import sys
from collections import deque
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TextIO, override

LOGGER_NAME = "app"
LOG_FILENAME = "haruquantai.log"
DEFAULT_LOG_DIR = Path("data/logs")
DEFAULT_MAX_BYTES = 10 * 1024 * 1024
DEFAULT_BACKUP_COUNT = 5
DEFAULT_LOG_LEVEL = logging.DEBUG

_CORRELATION: ContextVar[str | None] = ContextVar("host_correlation", default=None)
_MARKER = re.compile(r"\[REDACTED:[0-9a-f]{12}\]")
_SENSITIVE_KEY = re.compile(
    r"(?i)^(?:password|passwd|pwd|api[_-]?key|(?:access|refresh|auth)?[_-]?token|"
    r"session[_-]?id|sessionid|db[_-]?password|database[_-]?password|"
    r"authorization)$"
)
_QUOTED_ASSIGNMENT = re.compile(
    r"(?i)(?P<prefix>\b(?:password|passwd|pwd|api[_-]?key|"
    r"(?:access|refresh|auth)?[_-]?token|session[_-]?id|sessionid|"
    r"db[_-]?password|database[_-]?password|authorization)\b"
    r"[\"']?\s*[:=]\s*)(?P<quote>[\"'])(?P<secret>.*?)(?P=quote)"
)
_BARE_ASSIGNMENT = re.compile(
    r"(?i)(?P<prefix>\b(?:password|passwd|pwd|api[_-]?key|"
    r"(?:access|refresh|auth)?[_-]?token|session[_-]?id|sessionid|"
    r"db[_-]?password|database[_-]?password|authorization)\b"
    r"[\"']?\s*[:=]\s*)(?P<secret>\[REDACTED:[0-9a-f]{12}\]|[^\s,;&}\]\"']+)"
)
_BEARER = re.compile(r"(?i)(?P<prefix>\bBearer\s+)(?P<secret>[A-Za-z0-9._~+/-]+)")
_AUTH_SCHEME = re.compile(
    r"(?i)(?P<prefix>\bAuthorization\b[\"']?\s*[:=]\s*[\"']?"
    r"(?:Bearer|Basic)\s+)(?P<secret>[A-Za-z0-9._~+/-]+)"
)
_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_COLORS = {
    logging.DEBUG: "\x1b[36m",
    logging.INFO: "\x1b[32m",
    logging.WARNING: "\x1b[33m",
    logging.ERROR: "\x1b[31m",
    logging.CRITICAL: "\x1b[35m",
}


def secret_fingerprint(secret: str) -> str:
    """Return a stable 12-character SHA-256 fingerprint for a secret."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:12]


def _replace_secret(match: re.Match[str]) -> str:
    """Replace one detected credential with a stable redaction marker."""
    secret = match.group("secret")
    if _MARKER.fullmatch(secret):
        return match.group(0)
    quote = match.groupdict().get("quote", "")
    marker = f"[REDACTED:{secret_fingerprint(secret)}]"
    return f"{match.group('prefix')}{quote}{marker}{quote}"


def redact_sensitive(text: str) -> str:
    """Mask common credential forms while preserving deterministic fingerprints.

    Pattern matching cannot guarantee removal of unknown secret formats. Callers
    must avoid putting raw credentials in log messages in the first place.
    """
    redacted = _AUTH_SCHEME.sub(_replace_secret, text)
    redacted = _QUOTED_ASSIGNMENT.sub(_replace_secret, redacted)
    redacted = _BARE_ASSIGNMENT.sub(_replace_secret, redacted)
    return _BEARER.sub(_replace_secret, redacted)


def _sanitize_fields(value: object) -> object:
    """Recursively sanitize supported structured log fields."""
    if isinstance(value, Mapping):
        return {
            str(key): (
                (
                    str(item)
                    if _MARKER.fullmatch(str(item))
                    else f"[REDACTED:{secret_fingerprint(str(item))}]"
                )
                if _SENSITIVE_KEY.fullmatch(str(key)) and item is not None
                else _sanitize_fields(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_sanitize_fields(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive(value)
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return redact_sensitive(str(value))


@contextmanager
def bind_correlation(correlation_id: str) -> Generator[None]:
    """Bind a sanitized correlation identifier for this context and child tasks."""
    if not correlation_id:
        raise ValueError("correlation_id must not be empty")
    token = _CORRELATION.set(redact_sensitive(correlation_id))
    try:
        yield
    finally:
        _CORRELATION.reset(token)


class SensitiveDataFilter(logging.Filter):
    """Sanitize messages and typed telemetry fields before handler formatting."""

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        """Prepare one record without changing logging admission."""
        record.msg = redact_sensitive(record.getMessage())
        record.args = ()
        correlation = getattr(record, "correlation_id", _CORRELATION.get())
        record.correlation_id = (
            redact_sensitive(str(correlation)) if correlation is not None else None
        )
        if hasattr(record, "fields"):
            record.fields = _sanitize_fields(record.fields)
        return True


class TextFormatter(logging.Formatter):
    """Render redacted host diagnostics in the specified operator format."""

    def _format_parts(self, record: logging.LogRecord) -> tuple[str, str, str, str]:
        """Return (header, level, target, message) components."""
        stamp = (
            datetime.fromtimestamp(record.created, UTC)
            .astimezone()
            .strftime("%Y-%m-%d %H:%M:%S")
        )
        header = (
            f"{stamp},{int(record.msecs):03d} "
            f"[{redact_sensitive(record.threadName or '')}] "
        )
        level = redact_sensitive(record.levelname)
        target = f"  {redact_sensitive(record.name)}:{record.lineno} - "
        message = redact_sensitive(record.getMessage())
        correlation = getattr(record, "correlation_id", _CORRELATION.get())
        if correlation is not None:
            message = f"{message} [correlation_id={redact_sensitive(str(correlation))}]"
        fields = getattr(record, "fields", None)
        if fields is not None:
            encoded = json.dumps(_sanitize_fields(fields), separators=(",", ":"))
            message = f"{message} fields={encoded}"
        if record.exc_info:
            exception = redact_sensitive(self.formatException(record.exc_info))
            message = f"{message}\n{exception}"
        if record.stack_info:
            message = f"{message}\n{redact_sensitive(record.stack_info)}"
        return header, level, target, message

    @override
    def format(self, record: logging.LogRecord) -> str:
        """Return one timestamped line, plus redacted exception details."""
        header, level, target, message = self._format_parts(record)
        return f"{header}{level}{target}{message}"


class JsonLinesFormatter(logging.Formatter):
    """Render compact, sanitized JSON Lines for telemetry ingestion."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        """Return one JSON object with stable host fields."""
        correlation = getattr(record, "correlation_id", _CORRELATION.get())
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(
                timespec="milliseconds"
            ),
            "level": redact_sensitive(record.levelname),
            "logger": redact_sensitive(record.name),
            "line": record.lineno,
            "thread": redact_sensitive(record.threadName or ""),
            "correlation_id": (
                redact_sensitive(str(correlation)) if correlation is not None else None
            ),
            "message": redact_sensitive(record.getMessage()),
        }
        if hasattr(record, "fields"):
            payload["fields"] = _sanitize_fields(record.fields)
        if record.exc_info:
            exception = self.formatException(record.exc_info)
            payload["exception"] = redact_sensitive(exception)
        if record.stack_info:
            payload["stack"] = redact_sensitive(record.stack_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class ColorFormatter(TextFormatter):
    """Colorize log level and message when the stream is interactive."""

    def __init__(self, stream: TextIO, *, use_color: bool | None = None) -> None:
        """Select color from a TTY unless the caller explicitly overrides it."""
        super().__init__()
        self.use_color = stream.isatty() if use_color is None else use_color

    @override
    def format(self, record: logging.LogRecord) -> str:
        """Return a colored or plain sanitized line."""
        header, level, target, message = self._format_parts(record)
        if not self.use_color:
            return f"{header}{level}{target}{message}"
        color = _COLORS.get(record.levelno, "")
        if not color:
            return f"{header}{level}{target}{message}"
        return f"{header}{color}{level}\x1b[0m{target}{color}{message}\x1b[0m"


class DiagnosticCaptureHandler(logging.Handler):
    """Keep a thread-safe bounded FIFO of sanitized diagnostics for a UI."""

    def __init__(
        self, capacity: int, *, formatter: logging.Formatter | None = None
    ) -> None:
        """Create a capture with positive capacity and no external effects."""
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        super().__init__()
        self._entries: deque[str] = deque(maxlen=capacity)
        self.addFilter(SensitiveDataFilter())
        self.setFormatter(formatter or TextFormatter())

    @override
    def emit(self, record: logging.LogRecord) -> None:
        """Append a sanitized formatted entry."""
        self._entries.append(_ANSI.sub("", redact_sensitive(self.format(record))))

    def snapshot(self) -> tuple[str, ...]:
        """Return an immutable copy in oldest-to-newest order."""
        self.acquire()
        try:
            return tuple(self._entries)
        finally:
            self.release()


def host_log_path(log_dir: Path) -> Path:
    """Return the fixed rotating host log path without filesystem access."""
    return log_dir / LOG_FILENAME


def get_logger(name: str | None = None) -> logging.Logger:
    """Resolve a module logger beneath the app hierarchy without configuring sinks.

    Does not install handlers, set a global logger class, or create files. The
    entrypoint must explicitly configure logging before expecting host output.

    Args:
        name: Module __name__, or None for the app root; __main__ maps to app.main.

    Returns:
        Standard-library logger with the normalized host-qualified name.
    """
    if not name or name == LOGGER_NAME:
        return logging.getLogger(LOGGER_NAME)
    if name == "__main__":
        return logging.getLogger(f"{LOGGER_NAME}.main")
    if name.startswith(f"{LOGGER_NAME}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


class BootBuffer(logging.Handler):
    """Retain up to 256 early records for transfer to the host file sink.

    The standard handler filter sanitizes records before emit. Oldest records are
    evicted at capacity. configure_host_logging replays retained records to the file
    only, avoiding duplicate early console output.
    """

    def __init__(self) -> None:
        """Create an empty 256-record ring with the sensitive-data filter.

        No logger is modified and no sink is opened until the caller attaches it.
        """
        super().__init__()
        self.records: deque[logging.LogRecord] = deque(maxlen=256)
        self.addFilter(SensitiveDataFilter())

    @override
    def emit(self, record: logging.LogRecord) -> None:
        """Append a filtered record, evicting the oldest when full.

        Retains the record object rather than copying it; use standard Handler.handle
        for filtering and lock ownership.

        Args:
            record: LogRecord already passed through handler filtering.
        """
        self.records.append(record)


class HostForwardHandler(logging.Handler):
    """Forward Uvicorn diagnostics through the explicitly configured host sinks."""

    @override
    def emit(self, record: logging.LogRecord) -> None:
        """Forward a server record through the configured app handlers.

        Does not create sinks or recursively forward through the Uvicorn hierarchy.

        Args:
            record: Uvicorn diagnostic record; app sinks apply their own
                formatting/redaction.
        """
        logging.getLogger(LOGGER_NAME).handle(record)


def configure_boot_logging() -> None:
    """Install early stderr and bounded buffering before settings are loaded.

    Returns unchanged when the app logger already has handlers. Otherwise installs
    DEBUG-level console and BootBuffer handlers owned by the host and disables
    propagation. Creates no log directory or file.
    """
    root = logging.getLogger(LOGGER_NAME)
    if root.handlers:
        return
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(ColorFormatter(sys.stderr))
    console.addFilter(SensitiveDataFilter())
    for handler in (console, BootBuffer()):
        handler.__dict__["_host_telemetry_owned"] = True
        root.addHandler(handler)
    root.setLevel(DEFAULT_LOG_LEVEL)
    root.propagate = False
    root.__dict__.pop("_host_telemetry_config", None)


def close_host_logging() -> None:
    """Detach and close only handlers marked as host-owned.

    Visits app and uvicorn logger hierarchies. Repeated calls are harmless and
    foreign handlers are preserved; logger levels and propagation are not reset.
    """
    for name in (LOGGER_NAME, "uvicorn"):
        root = logging.getLogger(name)
        for handler in tuple(root.handlers):
            if getattr(handler, "_host_telemetry_owned", False):
                root.removeHandler(handler)
                handler.close()


def configure_host_logging(
    log_dir: Path | None = None,
    *,
    level: int = DEFAULT_LOG_LEVEL,
    console_stream: TextIO | None = None,
    include_console: bool = True,
    console_format: str = "text",
    file_format: str = "json",
    use_color: bool | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> logging.Logger:
    """Configure rotating file output and optional console diagnostics.

    Repeated identical configuration reuses owned handlers. Reconfiguration replaces
    owned sinks only, copies buffered early records into the file, and attaches one
    Uvicorn forwarder. The caller owns eventual close_host_logging.

    Args:
        log_dir: Destination directory; None selects DEFAULT_LOG_DIR.
        level: Standard-library logging threshold.
        console_stream: Console stream; None selects stderr.
        include_console: Whether to attach a console sink.
        console_format: Console representation: text or json.
        file_format: File representation: text or json.
        use_color: Explicit console color policy, or None for terminal detection.
        max_bytes: Positive file rotation threshold in bytes.
        backup_count: Nonnegative count of rotated files to retain.

    Returns:
        The configured app logger.

    Raises:
        ValueError: Rotation limits or format choices are invalid.
        OSError: Log directory or file creation fails.
    """
    target_dir = DEFAULT_LOG_DIR if log_dir is None else log_dir
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    if backup_count < 0:
        raise ValueError("backup_count must not be negative")
    if console_format not in {"text", "json"} or file_format not in {"text", "json"}:
        raise ValueError("formats must be 'text' or 'json'")
    stream = console_stream if console_stream is not None else sys.stderr
    config = (
        target_dir.resolve(),
        level,
        id(stream) if include_console else None,
        console_format,
        file_format,
        use_color,
        max_bytes,
        backup_count,
    )
    logger = logging.getLogger(LOGGER_NAME)
    if getattr(logger, "_host_telemetry_config", None) == config and any(
        getattr(handler, "_host_telemetry_owned", False) for handler in logger.handlers
    ):
        return logger
    target_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        host_log_path(target_dir),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_formatter = JsonLinesFormatter() if file_format == "json" else TextFormatter()
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(SensitiveDataFilter())
    new_handlers: list[logging.Handler] = [file_handler]
    if include_console:
        console_handler = logging.StreamHandler(stream)
        formatter: logging.Formatter = (
            JsonLinesFormatter()
            if console_format == "json"
            else ColorFormatter(stream, use_color=use_color)
        )
        console_handler.setFormatter(formatter)
        console_handler.addFilter(SensitiveDataFilter())
        new_handlers.append(console_handler)
    early = [
        record
        for handler in logger.handlers
        if isinstance(handler, BootBuffer)
        for record in handler.records
    ]
    for handler in tuple(logger.handlers):
        if getattr(handler, "_host_telemetry_owned", False):
            logger.removeHandler(handler)
            handler.close()
    for handler in new_handlers:
        handler.__dict__["_host_telemetry_owned"] = True
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    logger.__dict__["_host_telemetry_config"] = config
    for record in early:
        file_handler.handle(record)
    _forward_server_logging(level)
    return logger


def _forward_server_logging(level: int) -> None:
    """Attach one owned Uvicorn-to-app diagnostic forwarding handler.

    An existing HostForwardHandler is retained; this helper does not add a second
    formatter stack or update that existing handler configuration.

    Args:
        level: Logging threshold set when a new forwarding handler is attached.
    """
    server_logger = logging.getLogger("uvicorn")
    if not any(
        isinstance(handler, HostForwardHandler) for handler in server_logger.handlers
    ):
        forward = HostForwardHandler()
        forward.__dict__["_host_telemetry_owned"] = True
        server_logger.addHandler(forward)
        server_logger.setLevel(level)
        server_logger.propagate = False
