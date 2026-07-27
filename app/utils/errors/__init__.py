"""Public shared-error exports."""

from app.utils.errors.catalog import COMMON_ERROR_CATALOG
from app.utils.errors.contracts import ErrorDefinition, ErrorSeverity
from app.utils.errors.exceptions import (
    ConfigurationError,
    ExternalServiceError,
    HaruQuantError,
    SecurityError,
    ValidationError,
)
from app.utils.errors.mapping import map_exception
from app.utils.errors.metadata import (
    ErrorMetadata,
    get_error_metadata,
    normalize_error_code,
)
from app.utils.errors.routing import ErrorSink, route_error_event
from app.utils.errors.validation import (
    require_error_definition,
    validate_error_catalog,
)

__all__ = [
    "COMMON_ERROR_CATALOG",
    "ConfigurationError",
    "ErrorDefinition",
    "ErrorMetadata",
    "ErrorSeverity",
    "ErrorSink",
    "ExternalServiceError",
    "HaruQuantError",
    "SecurityError",
    "ValidationError",
    "get_error_metadata",
    "map_exception",
    "normalize_error_code",
    "require_error_definition",
    "route_error_event",
    "validate_error_catalog",
]
