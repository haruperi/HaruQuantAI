"""Map exceptions to deterministic, secret-safe boundary payloads."""

from app.utils.errors.exceptions import HaruQuantError


def map_exception(exception: BaseException) -> dict[str, str]:
    """Map an exception to deterministic boundary-safe evidence.

    Args:
        exception: Exception to sanitize for a shared boundary.

    Returns:
        A new mapping containing exactly ``code`` and ``detail``. Shared
        exceptions preserve their symbolic tokens; every unknown exception
        maps to a fixed internal-error payload.
    """
    if isinstance(exception, HaruQuantError):
        return {"code": exception.code, "detail": exception.detail}
    return {"code": "INTERNAL_ERROR", "detail": "UNEXPECTED_EXCEPTION"}
