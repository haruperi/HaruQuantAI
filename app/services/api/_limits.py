"""Validated package-wide UI/API limits."""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

API_DEFAULT_PAGE_SIZE: Final = 50
API_MAX_PAGE_SIZE: Final = 200
API_ENDPOINT_TIMEOUT_SECONDS: Final = 30.0
PREFLIGHT_WARNING_TTL_SECONDS: Final = 30.0
HTTP_IDEMPOTENCY_RETENTION_SECONDS: Final = 86_400
MAX_ERROR_DETAILS: Final = 16
MAX_ERROR_TEXT_LENGTH: Final = 256
MAX_VISIBLE_ENTITY_IDS: Final = 200

_DEFAULT_RATE_LIMITS = MappingProxyType(
    {
        "authentication": (5, 60.0),
        "read": (120, 60.0),
        "compute": (10, 60.0),
        "governed_write": (10, 60.0),
        "stream": (10, 60.0),
    }
)


def get_default_rate_limits() -> MappingProxyType[str, tuple[int, float]]:
    """Return immutable conservative development rate-limit classes.

    Returns:
        Mapping from route class to request count and window seconds.
    """
    return _DEFAULT_RATE_LIMITS


__all__ = ("get_default_rate_limits",)
