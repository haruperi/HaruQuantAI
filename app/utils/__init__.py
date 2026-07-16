"""Expose the stable business-neutral Utils API.

Consumers import shared contracts, errors, identifiers, UTC helpers,
serialization, settings models, redaction policy, and logging only from this
package root or their documented feature package. Importing this module has no
configuration, environment, filesystem, network, or provider side effects.
"""

from app.utils.contracts import AuditEvent, AuthContext
from app.utils.errors import (
    ConfigurationError,
    ErrorMetadata,
    ErrorSink,
    ExternalServiceError,
    HaruQuantError,
    SecurityError,
    ValidationError,
    get_error_metadata,
    map_exception,
    normalize_error_code,
    route_error_event,
)
from app.utils.identity import derive_stable_id, generate_id, validate_id
from app.utils.logging import (
    BoundLogger,
    RedactingFilter,
    StructuredFormatter,
    configure_logging,
    flush_logging,
    get_logger,
    logger,
    shutdown_logging,
)
from app.utils.security import RedactionPolicy
from app.utils.serialization import canonical_json, to_json_safe
from app.utils.settings import AppSettings, LoggingSettings, RuntimeSettings
from app.utils.time import (
    Clock,
    SystemClock,
    age_seconds,
    format_utc_timestamp,
    is_fresh,
    parse_utc_timestamp,
    utc_now,
)

__all__ = (
    "AppSettings",
    "AuditEvent",
    "AuthContext",
    "BoundLogger",
    "Clock",
    "ConfigurationError",
    "ErrorMetadata",
    "ErrorSink",
    "ExternalServiceError",
    "HaruQuantError",
    "LoggingSettings",
    "RedactingFilter",
    "RedactionPolicy",
    "RuntimeSettings",
    "SecurityError",
    "StructuredFormatter",
    "SystemClock",
    "ValidationError",
    "age_seconds",
    "canonical_json",
    "configure_logging",
    "derive_stable_id",
    "flush_logging",
    "format_utc_timestamp",
    "generate_id",
    "get_error_metadata",
    "get_logger",
    "is_fresh",
    "logger",
    "map_exception",
    "normalize_error_code",
    "parse_utc_timestamp",
    "route_error_event",
    "shutdown_logging",
    "to_json_safe",
    "utc_now",
    "validate_id",
)
