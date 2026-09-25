"""Explicit host logging with redacted text, JSON, and bounded diagnostics."""

# ruff: noqa: INP001 -- the reset host package has no initializer yet.

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


class HostLogger(logging.Logger):
    """Host logger ensuring centralized telemetry is configured before emission."""

    def _ensure_configured(self) -> None:
        root_logger = logging.getLogger(LOGGER_NAME)
        if not any(
            getattr(handler, "_host_telemetry_owned", False)
            for handler in root_logger.handlers
        ):
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(ColorFormatter(sys.stderr))
            console_handler.addFilter(SensitiveDataFilter())
            console_handler.__dict__["_host_telemetry_owned"] = True
            root_logger.addHandler(console_handler)
            root_logger.setLevel(logging.INFO)
            root_logger.propagate = False

    @override
    def isEnabledFor(self, level: int) -> bool:
        self._ensure_configured()
        return super().isEnabledFor(level)

    @override
    def handle(self, record: logging.LogRecord) -> None:
        self._ensure_configured()
        super().handle(record)


def host_log_path(log_dir: Path) -> Path:
    """Return the fixed rotating host log path without filesystem access."""
    return log_dir / LOG_FILENAME


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger bound to the host logging hierarchy with full module path."""
    logging.setLoggerClass(HostLogger)
    if not name or name == LOGGER_NAME:
        return logging.getLogger(LOGGER_NAME)
    if name == "__main__":
        return logging.getLogger(f"{LOGGER_NAME}.main")
    if name.startswith(f"{LOGGER_NAME}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


def configure_host_logging(
    log_dir: Path | None = None,
    *,
    level: int = logging.INFO,
    console_stream: TextIO | None = None,
    include_console: bool = True,
    console_format: str = "text",
    file_format: str = "json",
    use_color: bool | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> logging.Logger:
    """Explicitly configure the host logger and its bounded local file sink."""
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
    return logger
