"""Public registry for the utilities domain.

This module exposes only approved public names. It is import-safe and
side-effect free: importing it does not configure logging, read
configuration files, open network connections, or load heavy optional
dependencies such as pydantic-settings (dotenv).

Lightweight modules are imported eagerly. ``app.utils.settings`` is
deferred via ``__getattr__`` because ``pydantic_settings`` triggers
dotenv scanning at class-body evaluation time.

Compatibility review (v8): all public names in ``__all__`` are stable.
Removals or renames require a new versioned specification and a registry
review before merging.

Export groups
-------------
Eager:
    auth, data_quality, dataframe_tools, errors, logger, normalization,
    notifications, security, standard, validations
Lazy:
    settings
"""

from __future__ import annotations

from importlib import import_module

# ── auth.py exports ──────────────────────────────────────────────────────
from app.utils.auth import (
    AuthContext,
    AuthorizationDecision,
    authorize_action,
    build_auth_context,
    require_authorization,
    validate_auth_context,
)

# ── logger.py exports ────────────────────────────────────────────────────
from app.utils.logger import logger

# ── normalization.py exports ─────────────────────────────────────────────
from app.utils.normalization import (
    DEFAULT_TIMEZONE,
    UTC,
    ClockDriftStatus,
    TimestampIssue,
    check_clock_drift,
    format_timestamp,
    format_utc_timestamp,
    is_stale,
    normalize_timestamp,
    normalize_timestamp_column,
    normalize_timestamp_sequence,
    parse_datetime,
    to_naive_utc,
    to_utc_datetime,
    utc_now,
    validate_timestamp_sequence,
)

# ── notifications.py exports ─────────────────────────────────────────────
from app.utils.notifications import (
    DesktopNotificationAdapter,
    EmailNotificationAdapter,
    FakeNotificationAdapter,
    NotificationMessage,
    NotificationResult,
    NotificationRouter,
    TelegramNotificationAdapter,
    broadcast_notification,
    render_notification,
    route_notification,
)

# ── security.py exports ──────────────────────────────────────────────────
from app.utils.security import (
    MAX_REDACTION_DEPTH,
    SECRET_VERSION_NOT_FOUND,
    SENSITIVE_KEY_PATTERN,
    RedactionDiagnostics,
    SecretVersion,
    classify_secret_key,
    decrypt_text,
    decrypt_value,
    encrypt_text,
    encrypt_value,
    generate_encryption_key,
    hash_password,
    load_encryption_key,
    redact_mapping,
    redact_mapping_with_diagnostics,
    redact_payload,
    redact_text,
    redact_value,
    select_active_secret_version,
    verify_password,
)

# ── errors.py exports ────────────────────────────────────────────────────
from app.utils.standard import (
    AlertDeduplicator,
    ConfigurationError,
    DataError,
    DataQualityIssue,
    Error,
    ErrorEvent,
    ErrorPayload,
    ExternalServiceError,
    SecurityError,
    StandardEnvelope,
    StandardResponse,
    ToolError,
    ToolMetadata,
    ValidationError,
    build_data_quality_issue,
    build_error_event,
    build_error_response,
    build_metadata,
    build_success_response,
    canonical_json,
    circuit_open_response,
    code_for_exception,
    error_response,
    exception_to_error_payload,
    get_execution_ms,
    is_official_tool_allowed,
    normalize_error_code,
    response_from_exception,
    route_error,
    stable_identifier,
    success_response,
    validate_error_payload,
    validate_metric_labels,
    validate_ohlcv_records,
    validate_standard_response,
)

# ── settings.py exports (lazy — avoids eager pydantic-settings / dotenv) ─
_LAZY_SETTINGS_EXPORTS: frozenset[str] = frozenset(
    {
        "CONFIGURATION_ERROR",
        "HARUQUANT_HOME",
        "HaruQuantConfigurationError",
        "Settings",
        "create_config",
        "load_config",
        "settings",
        "validate_config",
    }
)

__all__ = [
    "CONFIGURATION_ERROR",
    "DEFAULT_TIMEZONE",
    "HARUQUANT_HOME",
    "MAX_REDACTION_DEPTH",
    "SECRET_VERSION_NOT_FOUND",
    "SENSITIVE_KEY_PATTERN",
    "UTC",
    "AlertDeduplicator",
    "AuthContext",
    "AuthorizationDecision",
    "ClockDriftStatus",
    "ConfigurationError",
    "DataError",
    "DataQualityIssue",
    "DesktopNotificationAdapter",
    "EmailNotificationAdapter",
    "Error",
    "ErrorEvent",
    "ErrorPayload",
    "ExternalServiceError",
    "FakeNotificationAdapter",
    "HaruQuantConfigurationError",
    "NotificationMessage",
    "NotificationResult",
    "NotificationRouter",
    "RedactionDiagnostics",
    "SecretVersion",
    "SecurityError",
    "Settings",
    "StandardEnvelope",
    "StandardResponse",
    "TelegramNotificationAdapter",
    "TimestampIssue",
    "ToolError",
    "ToolMetadata",
    "ValidationError",
    "authorize_action",
    "broadcast_notification",
    "build_auth_context",
    "build_data_quality_issue",
    "build_error_event",
    "build_error_response",
    "build_metadata",
    "build_success_response",
    "canonical_json",
    "check_clock_drift",
    "circuit_open_response",
    "classify_secret_key",
    "clear_trace_context",
    "code_for_exception",
    "configure_logging",
    "create_config",
    "decrypt_text",
    "decrypt_value",
    "encrypt_text",
    "encrypt_value",
    "error_response",
    "exception_to_error_payload",
    "format_timestamp",
    "format_utc_timestamp",
    "generate_encryption_key",
    "get_execution_ms",
    "get_logger",
    "hash_password",
    "is_official_tool_allowed",
    "is_stale",
    "load_config",
    "load_encryption_key",
    "logger",
    "normalize_error_code",
    "normalize_timestamp",
    "normalize_timestamp_column",
    "normalize_timestamp_sequence",
    "parse_datetime",
    "redact_mapping",
    "redact_mapping_with_diagnostics",
    "redact_payload",
    "redact_text",
    "redact_value",
    "render_notification",
    "require_authorization",
    "response_from_exception",
    "route_error",
    "route_notification",
    "select_active_secret_version",
    "set_trace_context",
    "settings",
    "stable_identifier",
    "success_response",
    "to_naive_utc",
    "to_utc_datetime",
    "utc_now",
    "validate_auth_context",
    "validate_config",
    "validate_error_payload",
    "validate_metric_labels",
    "validate_ohlcv_records",
    "validate_standard_response",
    "validate_timestamp_sequence",
    "verify_password",
]


def __getattr__(name: str) -> object:
    """Lazily resolve settings exports to avoid eager dotenv loading.

    Resolved values are cached in the module's global namespace so that
    subsequent attribute accesses bypass this function entirely.

    Args:
        name: The attribute name being accessed on this package.

    Returns:
        The requested public symbol from ``app.utils.settings``.

    Raises:
        AttributeError: If ``name`` is not an approved public export.
    """
    if name in _LAZY_SETTINGS_EXPORTS:
        module = import_module("app.utils.settings")
        value: object = getattr(module, name)
        globals()[name] = value
        return value
    message = f"module 'app.utils' has no attribute {name!r}"
    raise AttributeError(message)
