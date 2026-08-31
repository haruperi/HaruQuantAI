# pylint: disable=too-many-lines,broad-exception-caught
"""Composition-owned structured logging infrastructure and lifecycle management."""

from __future__ import annotations

import collections
import contextlib
import contextvars
import hashlib
import itertools
import json
import logging
import logging.handlers
import math
import re
import sys
import time
import zipfile
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Self, cast, override

_OWNED_HANDLER_ATTR: Final[str] = "_haruquantai_owned"
_HANDLER_GENERATION_ATTR: Final[str] = "_haruquantai_generation"
_BASELINE_LEVEL_ATTR: Final[str] = "_haruquantai_baseline_level"
_CORRELATION_RECORD_ATTR: Final[str] = "_haruquantai_correlation_snapshot"
_LOG_SCHEMA_VERSION: Final[int] = 1

_MAX_TEXT_CHARS: Final[int] = 4096
_MAX_MAPPING_ITEMS: Final[int] = 64
_MAX_COLLECTION_ITEMS: Final[int] = 64
_MAX_NESTING_DEPTH: Final[int] = 8
_MAX_RECORD_BYTES: Final[int] = 32768
_MAX_CLEANUP_DIAGNOSTICS: Final[int] = 16

_VALID_LEVELS: Final[dict[str, int]] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
_GENERATION_COUNTER = itertools.count(1)

_SENSITIVE_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?i)(password|secret|token|key|api_key|apikey|jwt|credential|"
    r"auth|private|passphrase|signature|bearer)"
)
_SENSITIVE_TEXT_PATTERNS: Final[Sequence[re.Pattern[str]]] = (
    re.compile(r"(?i)\bBearer\s+([A-Za-z0-9._~+/=-]+)"),
    re.compile(
        r"(?i)(?:api[_-]?key|token|secret|password|credential|passphrase)"
        r"\s*[:=]\s*['\"]?([A-Za-z0-9_~+/%-]{4,})['\"]?"
    ),
    re.compile(r"\b(?:sk|pk)_(?:live|test)_[0-9a-zA-Z]{16,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9._-]+\b"),
)

_CORRELATION_CONTEXT: Final[contextvars.ContextVar[dict[str, object] | None]] = (
    contextvars.ContextVar("_haruquantai_correlation_context", default=None)
)

_STANDARD_LOG_RECORD_ATTRS: Final[frozenset[str]] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)
_RESERVED_LOG_ATTRS: Final[frozenset[str]] = frozenset(
    _STANDARD_LOG_RECORD_ATTRS | {"event", "fields", _CORRELATION_RECORD_ATTR}
)


def compute_secret_fingerprint(secret: str) -> str:
    """Compute a truncated SHA-256 diagnostic fingerprint.

    Args:
        secret: Raw secret text.

    Returns:
        Deterministic redaction marker with an eight-character digest.
    """
    digest = hashlib.sha256(secret.encode("utf-8", errors="replace")).hexdigest()[:8]
    return f"[REDACTED:sha256:{digest}]"


def _safe_type_name(value: object) -> str:
    """Return a bounded type name without invoking an object representation."""
    value_type = type(value)
    return f"{value_type.__module__}.{value_type.__qualname__}"[:_MAX_TEXT_CHARS]


def _truncate_text(text: str) -> str:
    """Bound sanitized text while retaining a deterministic omission marker."

    Returns:
        Original or deterministically truncated text.
    """
    if len(text) <= _MAX_TEXT_CHARS:
        return text
    marker = f"…[TRUNCATED:{compute_secret_fingerprint(text)}]"
    return f"{text[: _MAX_TEXT_CHARS - len(marker)]}{marker}"


def redact_text(text: str) -> str:
    """Redact recognized secret patterns before bounding free-form text.

    Returns:
        Bounded string with recognized secrets replaced by fingerprints.
    """
    redacted = text
    for pattern in _SENSITIVE_TEXT_PATTERNS:

        def _replace_match(match: re.Match[str]) -> str:
            if match.lastindex and match.lastindex >= 1:
                secret_value = match.group(1)
                return match.group(0).replace(
                    secret_value,
                    compute_secret_fingerprint(secret_value),
                )
            return compute_secret_fingerprint(match.group(0))

        redacted = pattern.sub(_replace_match, redacted)
    return _truncate_text(redacted)


def _canonical_secret_value(  # noqa: PLR0911
    value: object,
    *,
    depth: int = 0,
    seen: set[int] | None = None,
) -> object:
    """Build a deterministic private representation used only for hashing.

    Returns:
        Canonical JSON-safe value for private fingerprint input.
    """
    type_name = _safe_type_name(value)
    active: set[int] = set(seen) if seen is not None else set()
    if depth >= _MAX_NESTING_DEPTH:
        return {"bounded_type": type_name}
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else {"float": str(value)}
    if isinstance(value, bytes):
        return {"bytes_sha256": hashlib.sha256(value).hexdigest()}

    identity = id(value)
    if isinstance(value, (Mapping, list, tuple, set, frozenset)):
        if identity in active:
            return {"cycle_type": type_name}
        active.add(identity)
        try:
            if isinstance(value, Mapping):
                mapping_val = cast("Mapping[object, object]", value)
                pairs = [
                    (
                        _canonical_mapping_key(key),
                        _canonical_secret_value(
                            item,
                            depth=depth + 1,
                            seen=active,
                        ),
                    )
                    for key, item in mapping_val.items()
                ]
                pairs.sort(
                    key=lambda pair: json.dumps(
                        pair[0],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
                return dict(pairs)
            items = [
                _canonical_secret_value(item, depth=depth + 1, seen=active)
                for item in cast(
                    "Sequence[object] | set[object] | frozenset[object]", value
                )
            ]
            if isinstance(value, (set, frozenset)):
                items.sort(
                    key=lambda item: json.dumps(
                        item,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
            return items
        finally:
            active.remove(identity)
    return {"unsupported_type": type_name}


def _canonical_mapping_key(key: object) -> str:
    """Return a deterministic mapping key without unsafe object conversion."""
    if isinstance(key, str):
        return key
    if key is None or isinstance(key, (bool, int)):
        return json.dumps(key, sort_keys=True)
    if isinstance(key, float) and math.isfinite(key):
        return json.dumps(key, sort_keys=True)
    return f"<key:{_safe_type_name(key)}>"


def _fingerprint_sensitive_value(value: object) -> str:
    """Fingerprint a scalar or canonical compound sensitive value.

    Returns:
        Stable truncated SHA-256 marker.
    """
    if isinstance(value, str):
        return compute_secret_fingerprint(value)
    canonical = json.dumps(
        _canonical_secret_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return compute_secret_fingerprint(canonical)


def _safe_mapping_key(key: object) -> str:
    """Return a redacted, bounded, JSON-safe mapping key."""
    return redact_text(_canonical_mapping_key(key))


def _sanitize_data(  # noqa: PLR0911
    data: object,
    *,
    depth: int,
    seen: set[int],
) -> object:
    """Normalize one object into a bounded, redacted JSON-safe value.

    Returns:
        Sanitized JSON-safe value.
    """
    type_name = _safe_type_name(data)
    if depth >= _MAX_NESTING_DEPTH:
        return f"<MAX_DEPTH:{type_name}>"
    if data is None or isinstance(data, (bool, int)):
        return data
    if isinstance(data, float):
        return data if math.isfinite(data) else f"<NON_FINITE:{data}>"
    if isinstance(data, str):
        return redact_text(data)
    if isinstance(data, bytes):
        return {
            "binary_type": "bytes",
            "content_fingerprint": compute_secret_fingerprint(data.hex()),
        }

    identity = id(data)
    if isinstance(data, (Mapping, list, tuple, set, frozenset)):
        if identity in seen:
            return f"<CYCLE:{type_name}>"
        seen.add(identity)
        try:
            if isinstance(data, Mapping):
                mapping_data = cast("Mapping[object, object]", data)
                pairs: list[tuple[str, object]] = []
                for key, value in mapping_data.items():
                    safe_key = _safe_mapping_key(key)
                    if isinstance(key, str) and _SENSITIVE_KEY_PATTERN.search(key):
                        safe_value: object = _fingerprint_sensitive_value(value)
                    else:
                        safe_value = _sanitize_data(
                            value,
                            depth=depth + 1,
                            seen=seen,
                        )
                    pairs.append((safe_key, safe_value))
                pairs.sort(key=lambda pair: pair[0])
                truncated_count = max(0, len(pairs) - _MAX_MAPPING_ITEMS)
                result = dict(pairs[:_MAX_MAPPING_ITEMS])
                if truncated_count:
                    result["_haruquantai_truncated_items"] = truncated_count
                return result

            items = [
                _sanitize_data(item, depth=depth + 1, seen=seen)
                for item in cast(
                    "Sequence[object] | set[object] | frozenset[object]", data
                )
            ]
            if isinstance(data, (set, frozenset)):
                items.sort(
                    key=lambda item: json.dumps(
                        item,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
            truncated_count = max(0, len(items) - _MAX_COLLECTION_ITEMS)
            bounded = items[:_MAX_COLLECTION_ITEMS]
            if truncated_count:
                bounded.append({"_haruquantai_truncated_items": truncated_count})
            return bounded
        finally:
            seen.remove(identity)
    return {"unsupported_type": type_name}


def redact_data(data: object) -> object:
    """Return a bounded, deterministic, redacted JSON-safe object.

    Returns:
        Sanitized JSON-safe value.
    """
    return _sanitize_data(data, depth=0, seen=set())


def get_correlation_context() -> dict[str, object]:
    """Return a copy of the current correlation context."""
    context = _CORRELATION_CONTEXT.get()
    return dict(context) if context is not None else {}


@contextmanager
def bind_correlation(**kwargs: object) -> Generator[dict[str, object]]:
    """Bind correlation dimensions to the current context.

    Args:
        **kwargs: Correlation dimensions to set or remove when `None`.

    Yields:
        Updated active correlation context.
    """
    updated = get_correlation_context()
    for key, value in kwargs.items():
        if value is None:
            updated.pop(key, None)
        else:
            updated[key] = value
    token = _CORRELATION_CONTEXT.set(updated)
    try:
        yield dict(updated)
    finally:
        _CORRELATION_CONTEXT.reset(token)


def _record_correlation(record: logging.LogRecord) -> dict[str, object]:
    """Attach and return one immutable-in-practice correlation snapshot.

    Returns:
        Correlation snapshot fixed to the supplied record.
    """
    existing = getattr(record, _CORRELATION_RECORD_ATTR, None)
    if isinstance(existing, Mapping):
        return {str(k): v for k, v in cast("Mapping[object, object]", existing).items()}
    snapshot = get_correlation_context()
    setattr(record, _CORRELATION_RECORD_ATTR, snapshot)
    return dict(snapshot)


def _record_timestamp(record: logging.LogRecord) -> str:
    """Return the record creation timestamp as UTC ISO text."""
    return datetime.fromtimestamp(record.created, tz=UTC).isoformat()


def _build_payload(
    record: logging.LogRecord,
    schema_version: int,
    formatter: logging.Formatter,
) -> dict[str, object]:
    """Build one sanitized structured payload from a log record.

    Returns:
        Structured schema payload.
    """
    raw_event = getattr(record, "event", "LOG_RECORD")
    event = redact_text(raw_event if isinstance(raw_event, str) else "LOG_RECORD")
    message = redact_text(record.getMessage())

    correlation_value = redact_data(_record_correlation(record))
    correlation: dict[str, object] = (
        {
            str(k): v
            for k, v in cast("Mapping[object, object]", correlation_value).items()
        }
        if isinstance(correlation_value, Mapping)
        else {}
    )

    raw_fields: dict[str, object] = {
        key: value
        for key, value in record.__dict__.items()
        if key not in _RESERVED_LOG_ATTRS
    }
    explicit_fields = getattr(record, "fields", None)
    if isinstance(explicit_fields, Mapping):
        raw_fields.update(cast("Mapping[str, object]", explicit_fields))
    fields_value = redact_data(raw_fields)
    fields: dict[str, object] = (
        {str(k): v for k, v in cast("Mapping[object, object]", fields_value).items()}
        if isinstance(fields_value, Mapping)
        else {}
    )

    payload: dict[str, object] = {
        "v": schema_version,
        "timestamp": _record_timestamp(record),
        "level": redact_text(record.levelname),
        "logger": redact_text(record.name),
        "event": event,
        "message": message,
    }
    if correlation:
        payload["correlation"] = correlation
    if fields:
        payload["fields"] = fields

    if record.exc_info and record.exc_info[1] is not None:
        error = record.exc_info[1]
        payload["error"] = {
            "type": redact_text(type(error).__name__),
            "message": redact_text(str(error)),
            "traceback": redact_text(formatter.formatException(record.exc_info)),
        }
    return payload


def _encode_json(payload: Mapping[str, object]) -> str:
    """Encode one payload as deterministic strict JSON.

    Returns:
        Compact, key-sorted JSON text.
    """
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _bounded_payload(
    record: logging.LogRecord,
    schema_version: int,
    formatter: logging.Formatter,
) -> tuple[dict[str, object], str]:
    """Build a payload and replace oversized output with a bounded summary.

    Returns:
        Final payload and its encoded JSON representation.
    """
    payload = _build_payload(record, schema_version, formatter)
    encoded = _encode_json(payload)
    if len(encoded.encode("utf-8")) <= _MAX_RECORD_BYTES:
        return payload, encoded

    summary: dict[str, object] = {
        "v": schema_version,
        "timestamp": _record_timestamp(record),
        "level": redact_text(record.levelname),
        "logger": redact_text(record.name),
        "event": "LOG_RECORD_TRUNCATED",
        "message": "Structured log record exceeded the configured safety bound",
        "fields": {
            "record_truncated": True,
            "content_fingerprint": compute_secret_fingerprint(encoded),
        },
    }
    summary_encoded = _encode_json(summary)
    return summary, summary_encoded


@dataclass(frozen=True, slots=True)
class LogRecordSnapshot:
    """Immutable structured record captured for diagnostic inspection."""

    schema_version: int
    timestamp: str
    level: str
    logger: str
    event: str
    message: str
    correlation: dict[str, object]
    fields: dict[str, object]
    error: dict[str, object] | None
    diagnostic_id: str


class DiagnosticCaptureHandler(logging.Handler):
    """In-memory bounded handler storing sanitized structured records."""

    def __init__(self, capacity: int = 1000) -> None:
        """Initialize the capture handler.

        Args:
            capacity: Maximum active and recent-expired reference count.
        """
        super().__init__()
        self.capacity = max(1, capacity)
        self._records: collections.deque[LogRecordSnapshot] = collections.deque(
            maxlen=self.capacity
        )
        self._active_ids: set[str] = set()
        self._expired_order: collections.deque[str] = collections.deque(
            maxlen=self.capacity
        )
        self._expired_ids: set[str] = set()
        self._counter = 0

    def _mark_expired(self, diagnostic_id: str) -> None:
        """Move one issued ID into bounded recent-expiry history."""
        if diagnostic_id in self._expired_ids:
            return
        if len(self._expired_order) == self.capacity:
            forgotten = self._expired_order.popleft()
            self._expired_ids.discard(forgotten)
        self._expired_order.append(diagnostic_id)
        self._expired_ids.add(diagnostic_id)

    @override
    def emit(self, record: logging.LogRecord) -> None:
        """Sanitize and retain one log record."""
        try:
            snapshot = self._to_snapshot(record)
            if len(self._records) == self.capacity and self._records:
                evicted = self._records[0]
                self._active_ids.discard(evicted.diagnostic_id)
                self._mark_expired(evicted.diagnostic_id)
            self._records.append(snapshot)
            self._active_ids.add(snapshot.diagnostic_id)
        except Exception:  # pylint: disable=broad-exception-caught
            self.handleError(record)

    def _to_snapshot(self, record: logging.LogRecord) -> LogRecordSnapshot:
        """Convert one record into a schema-aligned snapshot.

        Returns:
            Immutable capture snapshot.
        """
        self._counter += 1
        diagnostic_id = f"diag-{self._counter:08x}"
        formatter = self.formatter or StructuredJsonFormatter()
        payload, _encoded = _bounded_payload(record, _LOG_SCHEMA_VERSION, formatter)

        correlation_value = payload.get("correlation", {})
        fields_value = payload.get("fields", {})
        error_value = payload.get("error")
        return LogRecordSnapshot(
            schema_version=_LOG_SCHEMA_VERSION,
            timestamp=str(payload["timestamp"]),
            level=str(payload["level"]),
            logger=str(payload["logger"]),
            event=str(payload["event"]),
            message=str(payload["message"]),
            correlation=(
                {
                    str(k): str(v)
                    for k, v in cast(
                        "Mapping[object, object]", correlation_value
                    ).items()
                }
                if isinstance(correlation_value, Mapping)
                else {}
            ),
            fields=(
                {
                    str(k): v
                    for k, v in cast("Mapping[object, object]", fields_value).items()
                }
                if isinstance(fields_value, Mapping)
                else {}
            ),
            error=(
                {
                    str(k): v
                    for k, v in cast("Mapping[object, object]", error_value).items()
                }
                if isinstance(error_value, Mapping)
                else None
            ),
            diagnostic_id=diagnostic_id,
        )

    def get_records(self) -> tuple[LogRecordSnapshot, ...]:
        """Return active snapshots in chronological order."""
        return tuple(self._records)

    def get_by_id(self, diagnostic_id: str) -> LogRecordSnapshot | None:
        """Return an active snapshot by diagnostic ID, if present."""
        return next(
            (
                record
                for record in self._records
                if record.diagnostic_id == diagnostic_id
            ),
            None,
        )

    def is_expired(self, diagnostic_id: str) -> bool:
        """Return whether an issued ID is in recent bounded expiry history."""
        return diagnostic_id in self._expired_ids

    def clear(self) -> None:
        """Expire and remove all active captured records."""
        for record in self._records:
            self._mark_expired(record.diagnostic_id)
        self._records.clear()
        self._active_ids.clear()


_VALID_FORMATS: Final[frozenset[str]] = frozenset({"text", "json"})
_LEVEL_COLORS: Final[dict[str, str]] = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[1;31m",
}
_COLOR_RESET: Final[str] = "\033[0m"


class StandardTextFormatter(logging.Formatter):
    """Deterministic, bounded, secret-safe human-readable text formatter."""

    def __init__(self, *, colorize: bool = True) -> None:
        """Initialize the text formatter.

        Args:
            colorize: Whether to apply ANSI color codes to level and message.
        """
        super().__init__()
        self.colorize = colorize

    def _apply_color(self, text: str, level_name: str) -> str:
        """Apply level-specific ANSI color if colorization is enabled.

        Returns:
            Colorized string or original text when colorization is inactive.
        """
        if not self.colorize:
            return text
        color = _LEVEL_COLORS.get(level_name, "")
        if not color:
            return text
        return f"{color}{text}{_COLOR_RESET}"

    @override
    def format(self, record: logging.LogRecord) -> str:
        """Format one log record as human-readable text.

        Returns:
            Formatted log message text with timestamp, level, and location.
        """
        created_at = datetime.fromtimestamp(record.created, tz=UTC)
        human_timestamp = created_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level_padded = f"{record.levelname:<8}"
        level_text = self._apply_color(level_padded, record.levelname)

        source_module = getattr(record, "_source_module", record.module)
        source_function = getattr(record, "_source_function", record.funcName)
        source_line = getattr(record, "_source_line", record.lineno)

        raw_message = record.getMessage()
        message_text = redact_text(raw_message)

        correlation = _record_correlation(record)
        context_parts: list[str] = []
        if correlation:
            context_parts.extend(
                f"{key}={value}" for key, value in sorted(correlation.items())
            )
        raw_fields = getattr(record, "fields", None)
        if isinstance(raw_fields, Mapping):
            raw_fields_mapping = cast("Mapping[object, object]", raw_fields)
            field_items = sorted((str(k), v) for k, v in raw_fields_mapping.items())
            context_parts.extend(f"{k}={v}" for k, v in field_items)

        suffix = f" | {' '.join(context_parts)}" if context_parts else ""
        full_message = f"{message_text}{suffix}"

        if record.exc_info and record.exc_info[1] is not None:
            exc_text = self.formatException(record.exc_info)
            if exc_text:
                full_message = f"{full_message}\n{redact_text(exc_text)}"

        colored_message = self._apply_color(full_message, record.levelname)

        return (
            f"{human_timestamp} | {level_text} | "
            f"{source_module}:{source_function}:{source_line} - "
            f"{colored_message}"
        )


class StructuredJsonFormatter(logging.Formatter):
    """Deterministic, bounded, secret-safe JSON Lines formatter."""

    def __init__(self, schema_version: int = _LOG_SCHEMA_VERSION) -> None:
        """Initialize the formatter.

        Args:
            schema_version: Structured logging schema version.
        """
        super().__init__()
        self.schema_version = schema_version

    @override
    def format(self, record: logging.LogRecord) -> str:
        """Return one deterministic bounded JSON record."""
        _payload, encoded = _bounded_payload(record, self.schema_version, self)
        return encoded


_VALID_COMPRESSION: Final[frozenset[str]] = frozenset({"zip", "none"})


def _zip_rotated_name(default_name: str) -> str:
    """Format the rotated file name with a zip extension.

    Returns:
        Formatted zipped log name.
    """
    return f"{default_name}.zip"


def _zip_rotator(source: str, destination: str) -> None:
    """Compress the source file to destination in ZIP format, then remove source."""
    source_path = Path(source)
    with zipfile.ZipFile(
        destination,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.write(source_path, arcname=source_path.name)
    source_path.unlink(missing_ok=True)


class _RouteFilter(logging.Filter):
    """Filter records for specialized destination logs."""

    def __init__(self, route: str) -> None:
        """Initialize route filter.

        Args:
            route: Route name ('access', 'debug', or 'error').
        """
        super().__init__()
        self._route = route

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        """Return whether record matches the route criteria.

        Returns:
            True if record matches route criteria, False otherwise.
        """
        if self._route == "access":
            if getattr(record, "log_type", None) == "access":
                return True
            event = getattr(record, "event", "")
            if isinstance(event, str) and event.upper() in {
                "ACCESS",
                "HTTP_REQUEST",
                "API_REQUEST",
            }:
                return True
            fields = getattr(record, "fields", None)
            return bool(
                isinstance(fields, Mapping)
                and cast("Mapping[str, object]", fields).get("log_type") == "access"
            )
        if self._route == "debug":
            return record.levelno == logging.DEBUG
        if self._route == "error":
            return record.levelno >= logging.ERROR
        return True


class CompressingRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Rotating file handler with optional ZIP compression and age retention."""

    def __init__(
        self,
        filename: Path | str,
        *,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
        retention_days: int = 30,
        compression: str = "zip",
    ) -> None:
        """Initialize rotating handler with retention and compression.

        Args:
            filename: Active file path for the log.
            max_bytes: Bounded maximum size in bytes before rollover.
            backup_count: Maximum number of backup files to keep.
            retention_days: Days of historical logs to retain.
            compression: Compression mode ('zip' or 'none').
        """
        super().__init__(
            str(filename),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        self.retention_days = retention_days
        self.compression = compression
        if compression == "zip":
            self.namer = _zip_rotated_name
            self.rotator = _zip_rotator

    @override
    def doRollover(self) -> None:
        """Rotate the active file and remove expired rotated files."""
        super().doRollover()
        if self.retention_days > 0:
            cutoff = time.time() - (self.retention_days * 86_400)
            base_path = Path(self.baseFilename)
            for candidate in base_path.parent.glob(f"{base_path.name}.*"):
                if candidate.is_file() and candidate.stat().st_mtime < cutoff:
                    candidate.unlink(missing_ok=True)


@dataclass(frozen=True, slots=True)
class CleanupDiagnostic:
    """Bounded, non-sensitive handler cleanup failure evidence."""

    stage: str
    handler_type: str
    error_type: str


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Configuration options for application structured logging."""

    level: str = "INFO"
    console: bool = True
    file_path: Path | str | None = None
    log_directory: Path | str | None = Path("data/logs")
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5
    capture_capacity: int = 1000
    format: str = "text"
    colorize: bool = True
    retention_days: int = 30
    compression: str = "zip"

    def normalized_level(self) -> str:
        """Return a validated canonical level name."""
        self.validate()
        return self.level.strip().upper()

    def normalized_format(self) -> str:
        """Return a validated canonical format name."""
        self.validate()
        return self.format.strip().lower()

    def normalized_compression(self) -> str:
        """Return a validated canonical compression mode."""
        self.validate()
        return self.compression.strip().lower()

    def validate(self) -> None:
        """Validate level and positive retention bounds.

        Raises:
            ValueError: If any logging option is outside its safe bounds.
        """
        level = self.level.strip().upper()
        if level not in _VALID_LEVELS:
            msg = f"Unsupported logging level: {self.level!r}"
            raise ValueError(msg)
        format_name = self.format.strip().lower()
        if format_name not in _VALID_FORMATS:
            msg = f"Unsupported logging format: {self.format!r}"
            raise ValueError(msg)
        compression_mode = self.compression.strip().lower()
        if compression_mode not in _VALID_COMPRESSION:
            msg = f"Unsupported logging compression: {self.compression!r}"
            raise ValueError(msg)
        if self.max_bytes <= 0:
            msg = f"max_bytes must be strictly positive, got {self.max_bytes}"
            raise ValueError(msg)
        if self.backup_count <= 0:
            msg = f"backup_count must be strictly positive, got {self.backup_count}"
            raise ValueError(msg)
        if self.capture_capacity <= 0:
            msg = (
                "capture_capacity must be strictly positive, "
                f"got {self.capture_capacity}"
            )
            raise ValueError(msg)
        if self.retention_days <= 0:
            msg = f"retention_days must be strictly positive, got {self.retention_days}"
            raise ValueError(msg)


class LoggingHandle:
    """Generation-aware lifecycle handle for Composition-owned handlers."""

    def __init__(
        self,
        handlers: Sequence[logging.Handler],
        *,
        capture_handler: DiagnosticCaptureHandler | None,
        target_logger: logging.Logger,
        previous_level: int,
        generation: int,
        cleanup_diagnostics: Sequence[CleanupDiagnostic] = (),
    ) -> None:
        """Initialize the owned lifecycle handle."""
        self._handlers = tuple(handlers)
        self._capture_handler = capture_handler
        self._target_logger = target_logger
        self._previous_level = previous_level
        self._generation = generation
        self._cleanup_diagnostics = list(cleanup_diagnostics[:_MAX_CLEANUP_DIAGNOSTICS])
        self._closed = False

    @property
    def handlers(self) -> tuple[logging.Handler, ...]:
        """Return this generation's owned handlers."""
        return self._handlers

    @property
    def capture_handler(self) -> DiagnosticCaptureHandler | None:
        """Return the diagnostic capture handler, if configured."""
        return self._capture_handler

    @property
    def cleanup_diagnostics(self) -> tuple[CleanupDiagnostic, ...]:
        """Return bounded cleanup failure evidence."""
        return tuple(self._cleanup_diagnostics)

    @property
    def is_closed(self) -> bool:
        """Return whether close has already run."""
        return self._closed

    def _record_cleanup_error(
        self,
        stage: str,
        target: object,
        error: BaseException,
    ) -> None:
        """Append one non-sensitive cleanup diagnostic within its bound."""
        if len(self._cleanup_diagnostics) >= _MAX_CLEANUP_DIAGNOSTICS:
            return
        self._cleanup_diagnostics.append(
            CleanupDiagnostic(
                stage=stage,
                handler_type=type(target).__name__[:_MAX_TEXT_CHARS],
                error_type=type(error).__name__[:_MAX_TEXT_CHARS],
            )
        )

    def close(self) -> tuple[CleanupDiagnostic, ...]:
        """Remove and close this generation without touching foreign handlers.

        Returns:
            Bounded cleanup failure diagnostics.
        """
        if self._closed:
            return self.cleanup_diagnostics
        self._closed = True
        was_active = any(
            handler in self._target_logger.handlers for handler in self._handlers
        )

        for handler in self._handlers:
            if handler in self._target_logger.handlers:
                try:
                    self._target_logger.removeHandler(handler)
                except Exception as error:  # pylint: disable=broad-exception-caught
                    self._record_cleanup_error("remove", handler, error)
            try:
                handler.flush()
            except Exception as error:  # pylint: disable=broad-exception-caught
                self._record_cleanup_error("flush", handler, error)
            try:
                handler.close()
            except Exception as error:  # pylint: disable=broad-exception-caught
                self._record_cleanup_error("close", handler, error)

        remaining_owned = any(
            getattr(handler, _OWNED_HANDLER_ATTR, False)
            for handler in self._target_logger.handlers
        )
        if was_active and not remaining_owned:
            try:
                self._target_logger.setLevel(self._previous_level)
            except Exception as error:  # pylint: disable=broad-exception-caught
                self._record_cleanup_error("restore_level", self._target_logger, error)
        return self.cleanup_diagnostics

    def __enter__(self) -> Self:
        """Return this handle for context-manager use."""
        return self

    def __exit__(self, *args: object) -> None:
        """Close the owned generation on context exit."""
        self.close()


def emit_cleanup_diagnostics(
    diagnostics: Sequence[CleanupDiagnostic],
) -> None:
    """Emit bounded cleanup evidence through an unattached one-shot handler.

    Args:
        diagnostics: Stage/type-only cleanup diagnostics to report.
    """
    bounded = tuple(diagnostics[:_MAX_CLEANUP_DIAGNOSTICS])
    if not bounded:
        return
    record = logging.LogRecord(
        name=__name__,
        level=logging.ERROR,
        pathname=__file__,
        lineno=0,
        msg="Composition logging handler cleanup incomplete",
        args=(),
        exc_info=None,
    )
    record.event = "LOGGING_CLEANUP_FAILED"
    record.fields = {
        "cleanup_errors": [
            {
                "stage": item.stage,
                "handler_type": item.handler_type,
                "error_type": item.error_type,
            }
            for item in bounded
        ]
    }
    fallback = logging.StreamHandler(sys.stderr)
    fallback.setFormatter(StructuredJsonFormatter())
    try:
        fallback.handle(record)
    finally:
        fallback.close()


def _cleanup_new_handlers(handlers: Sequence[logging.Handler]) -> None:
    """Best-effort flush and close handlers from an uncommitted configuration."""
    for handler in handlers:
        with contextlib.suppress(Exception):
            handler.flush()
        with contextlib.suppress(Exception):
            handler.close()


def _cleanup_stale_handlers(
    target_logger: logging.Logger,
    handlers: Sequence[logging.Handler],
) -> tuple[CleanupDiagnostic, ...]:
    """Detach an old owned generation and retain bounded safe failures.

    Returns:
        Bounded stage/type-only cleanup diagnostics.
    """
    diagnostics: list[CleanupDiagnostic] = []
    for handler in handlers:
        for stage, operation in (
            ("remove_stale", lambda item=handler: target_logger.removeHandler(item)),
            ("flush_stale", handler.flush),
            ("close_stale", handler.close),
        ):
            try:
                operation()
            except Exception as error:  # pylint: disable=broad-exception-caught
                if len(diagnostics) < _MAX_CLEANUP_DIAGNOSTICS:
                    diagnostics.append(
                        CleanupDiagnostic(
                            stage=stage,
                            handler_type=type(handler).__name__,
                            error_type=type(error).__name__,
                        )
                    )
    return tuple(diagnostics)


def _create_handlers(
    cfg: LoggingConfig,
    numeric_level: int,
) -> tuple[list[logging.Handler], DiagnosticCaptureHandler]:
    """Instantiate and configure owned handlers according to LoggingConfig.

    Returns:
        Tuple of new handlers list and the diagnostic capture handler.
    """
    if cfg.normalized_format() == "json":
        console_formatter: logging.Formatter = StructuredJsonFormatter()
        file_formatter: logging.Formatter = StructuredJsonFormatter()
    else:
        console_formatter = StandardTextFormatter(colorize=cfg.colorize)
        file_formatter = StandardTextFormatter(colorize=False)
    handlers: list[logging.Handler] = []

    if cfg.console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)

    if cfg.file_path is not None:
        file_path = Path(cfg.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        custom_handler = CompressingRotatingFileHandler(
            filename=file_path,
            max_bytes=cfg.max_bytes,
            backup_count=cfg.backup_count,
            retention_days=cfg.retention_days,
            compression=cfg.normalized_compression(),
        )
        custom_handler.setLevel(numeric_level)
        custom_handler.setFormatter(file_formatter)
        handlers.append(custom_handler)

    if cfg.log_directory is not None:
        directory = Path(cfg.log_directory)
        directory.mkdir(parents=True, exist_ok=True)

        app_handler = CompressingRotatingFileHandler(
            filename=directory / "app.log",
            max_bytes=cfg.max_bytes,
            backup_count=cfg.backup_count,
            retention_days=cfg.retention_days,
            compression=cfg.normalized_compression(),
        )
        app_handler.setLevel(numeric_level)
        app_handler.setFormatter(file_formatter)
        handlers.append(app_handler)

        access_handler = CompressingRotatingFileHandler(
            filename=directory / "access.log",
            max_bytes=cfg.max_bytes,
            backup_count=cfg.backup_count,
            retention_days=cfg.retention_days,
            compression=cfg.normalized_compression(),
        )
        access_handler.setLevel(numeric_level)
        access_handler.setFormatter(file_formatter)
        access_handler.addFilter(_RouteFilter("access"))
        handlers.append(access_handler)

        debug_handler = CompressingRotatingFileHandler(
            filename=directory / "debug.log",
            max_bytes=cfg.max_bytes,
            backup_count=cfg.backup_count,
            retention_days=cfg.retention_days,
            compression=cfg.normalized_compression(),
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(file_formatter)
        debug_handler.addFilter(_RouteFilter("debug"))
        handlers.append(debug_handler)

        error_handler = CompressingRotatingFileHandler(
            filename=directory / "error.log",
            max_bytes=cfg.max_bytes,
            backup_count=cfg.backup_count,
            retention_days=cfg.retention_days,
            compression=cfg.normalized_compression(),
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        error_handler.addFilter(_RouteFilter("error"))
        handlers.append(error_handler)

    capture_handler = DiagnosticCaptureHandler(capacity=cfg.capture_capacity)
    capture_handler.setLevel(numeric_level)
    capture_handler.setFormatter(StructuredJsonFormatter())
    handlers.append(capture_handler)
    return handlers, capture_handler


def configure_logging(
    config: LoggingConfig | None = None,
    target_logger: logging.Logger | None = None,
) -> LoggingHandle:
    """Transactionally configure and return one owned handler generation.

    Args:
        config: Logging configuration, or safe defaults when omitted.
        target_logger: Logger receiving owned handlers; defaults to root.

    Returns:
        Lifecycle handle for the committed owned generation.

    Raises:
        ValueError: If configuration is invalid.
        OSError: If a requested file handler cannot be constructed.
    """
    cfg = config or LoggingConfig()
    level_name = cfg.normalized_level()
    numeric_level = _VALID_LEVELS[level_name]
    logger_target = target_logger or logging.getLogger()
    current_level = logger_target.level
    existing_owned = tuple(
        handler
        for handler in logger_target.handlers
        if getattr(handler, _OWNED_HANDLER_ATTR, False)
    )
    previous_level = (
        int(getattr(existing_owned[0], _BASELINE_LEVEL_ATTR, current_level))
        if existing_owned
        else current_level
    )
    generation = next(_GENERATION_COUNTER)
    new_handlers: list[logging.Handler] = []
    capture_handler: DiagnosticCaptureHandler | None = None

    try:
        new_handlers, capture_handler = _create_handlers(cfg, numeric_level)
        for handler in new_handlers:
            setattr(handler, _OWNED_HANDLER_ATTR, True)
            setattr(handler, _HANDLER_GENERATION_ATTR, generation)
            setattr(handler, _BASELINE_LEVEL_ATTR, previous_level)
    except Exception:
        _cleanup_new_handlers(new_handlers)
        raise

    try:
        for handler in new_handlers:
            logger_target.addHandler(handler)
        logger_target.setLevel(numeric_level)
    except Exception:
        for handler in tuple(logger_target.handlers):
            if handler in new_handlers:
                with contextlib.suppress(Exception):
                    logger_target.removeHandler(handler)
        _cleanup_new_handlers(new_handlers)
        with contextlib.suppress(Exception):
            logger_target.setLevel(current_level)
        raise

    stale_diagnostics = _cleanup_stale_handlers(logger_target, existing_owned)
    return LoggingHandle(
        new_handlers,
        capture_handler=capture_handler,
        target_logger=logger_target,
        previous_level=previous_level,
        generation=generation,
        cleanup_diagnostics=stale_diagnostics,
    )


def _run_scenario_1(config: LoggingConfig) -> bool:
    """Verify deterministic schema formatting and bounded output.

    Args:
        config: Logging configuration to use for the scenario.

    Returns:
        Whether the scenario passed.
    """
    with configure_logging(config) as handle:
        harness_logger = logging.getLogger("haruquantai.harness")
        harness_logger.debug(
            "Debug event",
            extra={"event": "DEBUG_INIT", "fields": {"step": 1}},
        )
        capture = handle.capture_handler
        if capture is None or len(capture.get_records()) != 1:
            print("[FAIL] Structured record capture failed")
            return False
        record = capture.get_records()[0]
        if record.event != "DEBUG_INIT" or record.fields.get("step") != 1:
            print("[FAIL] Structured field mismatch")
            return False
    return True


def _run_scenario_2(config: LoggingConfig) -> bool:
    """Verify nested correlation propagation and reset.

    Args:
        config: Logging configuration to use for the scenario.

    Returns:
        Whether the scenario passed.
    """
    with configure_logging(config) as handle:
        harness_logger = logging.getLogger("haruquantai.harness")
        with bind_correlation(request_id="req-123", job_id="job-abc"):
            harness_logger.info("Processing job", extra={"event": "JOB_START"})
        capture = handle.capture_handler
        if capture is None or len(capture.get_records()) != 1:
            print("[FAIL] Correlation capture missing")
            return False
        record = capture.get_records()[0]
        if record.correlation != {"job_id": "job-abc", "request_id": "req-123"}:
            print("[FAIL] Correlation propagation failed")
            return False
    return not get_correlation_context()


def _run_scenario_3(config: LoggingConfig) -> bool:
    """Verify scalar and compound sensitive-value fingerprinting.

    Args:
        config: Logging configuration to use for the scenario.

    Returns:
        Whether the scenario passed.
    """
    with configure_logging(config) as handle:
        harness_logger = logging.getLogger("haruquantai.harness")
        canary = "super_secret_token_value_xyz"
        harness_logger.info(
            "Auth test",
            extra={
                "event": "AUTH_CHECK",
                "fields": {"api_key": canary, "tokens": [canary]},
            },
        )
        capture = handle.capture_handler
        if capture is None or len(capture.get_records()) != 1:
            print("[FAIL] Redaction capture missing")
            return False
        rendered = str(capture.get_records()[0].fields)
        if canary in rendered or compute_secret_fingerprint(canary) not in rendered:
            print("[FAIL] Secret redaction failed")
            return False
    return True


def _run_scenario_4() -> bool:
    """Verify bounded active and expired diagnostic references.

    Returns:
        Whether the scenario passed.
    """
    config = LoggingConfig(
        level="INFO",
        console=False,
        log_directory=None,
        capture_capacity=2,
    )
    with configure_logging(config) as handle:
        harness_logger = logging.getLogger("haruquantai.harness")
        harness_logger.info("First", extra={"event": "E1"})
        capture = handle.capture_handler
        if capture is None:
            print("[FAIL] Diagnostic capture missing")
            return False
        first_id = capture.get_records()[0].diagnostic_id
        harness_logger.info("Second", extra={"event": "E2"})
        harness_logger.info("Third", extra={"event": "E3"})
        if len(
            capture.get_records()
        ) != config.capture_capacity or not capture.is_expired(first_id):
            print("[FAIL] Diagnostic expiry failed")
            return False
        if capture.is_expired("never-issued"):
            print("[FAIL] Unknown diagnostic was marked expired")
            return False
    return True


def _run_scenario_5(config: LoggingConfig) -> bool:
    """Verify exact handler cleanup and logger-level restoration.

    Args:
        config: Logging configuration to use for the scenario.

    Returns:
        Whether the scenario passed.
    """
    root = logging.getLogger()
    baseline_level = root.level
    handle = configure_logging(config)
    if not any(
        getattr(handler, _OWNED_HANDLER_ATTR, False) for handler in root.handlers
    ):
        print("[FAIL] Handler attachment failed")
        return False
    handle.close()
    if any(getattr(handler, _OWNED_HANDLER_ATTR, False) for handler in root.handlers):
        print("[FAIL] Handler detachment failed")
        return False
    if root.level != baseline_level:
        print("[FAIL] Logger state restoration failed")
        return False
    return not handle.cleanup_diagnostics


def _harness_main() -> int:
    """Run bounded executable logging verification scenarios.

    Returns:
        Zero when all scenarios pass; otherwise one.
    """
    print("Running app.composition.logging verification harness...")
    config = LoggingConfig(
        level="DEBUG",
        console=False,
        log_directory=None,
        capture_capacity=10,
    )
    if not all(
        (
            _run_scenario_1(config),
            _run_scenario_2(config),
            _run_scenario_3(config),
            _run_scenario_4(),
            _run_scenario_5(config),
        )
    ):
        return 1
    print("All logging harness scenarios passed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(_harness_main())
