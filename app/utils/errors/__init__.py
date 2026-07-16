"""Expose shared error types, safe mapping, metadata, and injected routing.

Domain packages extend the base hierarchy with their own symbolic codes while
raw provider exceptions remain behind the owning boundary.
"""

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

__all__ = (
    "ConfigurationError",
    "ErrorMetadata",
    "ErrorSink",
    "ExternalServiceError",
    "HaruQuantError",
    "SecurityError",
    "ValidationError",
    "get_error_metadata",
    "map_exception",
    "normalize_error_code",
    "route_error_event",
)
