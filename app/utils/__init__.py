"""Business-neutral shared infrastructure for HaruQuantAI domains."""

from app.utils.contracts import create_audit_event, create_auth_context
from app.utils.errors import (
    get_common_error_catalog,
    get_error_metadata,
    map_exception,
    normalize_error_code,
    require_error_definition,
    route_error_event,
    validate_error_catalog,
)
from app.utils.identity import derive_stable_id, generate_id, validate_id
from app.utils.logging import (
    configure_logging,
    flush_logging,
    get_logger,
    shutdown_logging,
)
from app.utils.responses import (
    build_response_metadata,
    error_response,
    exception_response,
    get_execution_ms,
    success_response,
)
from app.utils.security import (
    get_default_redaction_policy,
    is_sensitive_key,
    redact_mapping_value,
    redact_text_value,
)
from app.utils.serialization import canonical_digest, canonical_json, to_json_safe
from app.utils.settings import load_settings
from app.utils.time import (
    age_seconds,
    format_utc_timestamp,
    is_fresh,
    parse_utc_timestamp,
    utc_now,
)

__all__ = (
    "age_seconds",
    "build_response_metadata",
    "canonical_digest",
    "canonical_json",
    "configure_logging",
    "create_audit_event",
    "create_auth_context",
    "derive_stable_id",
    "error_response",
    "exception_response",
    "flush_logging",
    "format_utc_timestamp",
    "generate_id",
    "get_common_error_catalog",
    "get_default_redaction_policy",
    "get_error_metadata",
    "get_execution_ms",
    "get_logger",
    "is_fresh",
    "is_sensitive_key",
    "load_settings",
    "map_exception",
    "normalize_error_code",
    "parse_utc_timestamp",
    "redact_mapping_value",
    "redact_text_value",
    "require_error_definition",
    "route_error_event",
    "shutdown_logging",
    "success_response",
    "to_json_safe",
    "utc_now",
    "validate_error_catalog",
    "validate_id",
)
