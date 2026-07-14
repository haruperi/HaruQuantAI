"""Deterministic secret-safe exception boundary mapping."""

from __future__ import annotations

from app.utils.errors.exceptions import HaruQuantError


def map_exception(exception: BaseException) -> dict[str, str]:
    """Map an exception to deterministic boundary-safe evidence.

    Args:
        exception: Caught exception. It is never returned or retained.

    Returns:
        A two-field mapping containing symbolic ``code`` and ``detail``.
    """
    if isinstance(exception, HaruQuantError):
        return {"code": exception.code, "detail": exception.detail}
    return {"code": "INTERNAL_ERROR", "detail": "UNEXPECTED_EXCEPTION"}
