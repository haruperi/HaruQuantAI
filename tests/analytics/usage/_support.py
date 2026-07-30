"""Shared response handling for executable Analytics usage examples."""

from typing import cast


def unwrap[T](response: object) -> T:
    """Return successful public-port data.

    Args:
        response: Standard Analytics response.

    Returns:
        Raw value carried in ``data``.

    Raises:
        AssertionError: If the public operation failed.
    """
    if getattr(response, "status", None) != "success":
        raise AssertionError(getattr(response, "error", None))
    return cast("T", response.data)
