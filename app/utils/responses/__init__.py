"""Public standard-response exports."""

from app.utils.responses.factories import (
    build_response_metadata,
    error_response,
    exception_response,
    success_response,
)
from app.utils.responses.models import StandardResponse
from app.utils.responses.timing import get_execution_ms


def get_standard_response_type() -> type[object]:
    """Return the internal canonical response runtime type.

    Returns:
        The internal generic response class for runtime contract introspection.
    """
    return StandardResponse


__all__ = [
    "build_response_metadata",
    "error_response",
    "exception_response",
    "get_execution_ms",
    "get_standard_response_type",
    "success_response",
]
