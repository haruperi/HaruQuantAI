"""Function-only constructors for shared error values."""

from app.utils.errors.exceptions import ValidationError


def create_validation_error(code: str, detail: str = "UNSPECIFIED") -> Exception:
    """Construct a shared validation error behind the function-only boundary.

    Args:
        code: Uppercase symbolic error code.
        detail: Uppercase symbolic safe detail.

    Returns:
        Shared validation exception instance.
    """
    return ValidationError(code, detail)


__all__ = ("create_validation_error",)
