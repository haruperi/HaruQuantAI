"""Public shared-error exports."""

from app.utils.errors.catalog import get_common_error_catalog
from app.utils.errors.mapping import map_exception
from app.utils.errors.metadata import get_error_metadata, normalize_error_code
from app.utils.errors.routing import route_error_event
from app.utils.errors.validation import (
    require_error_definition,
    validate_error_catalog,
)

__all__ = [
    "get_common_error_catalog",
    "get_error_metadata",
    "map_exception",
    "normalize_error_code",
    "require_error_definition",
    "route_error_event",
    "validate_error_catalog",
]
