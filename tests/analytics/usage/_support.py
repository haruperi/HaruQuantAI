"""Shared response handling for executable Analytics usage examples."""

from typing import cast

from app.utils import StandardResponse


def unwrap[T](response: StandardResponse[T]) -> T:
    """Return successful public-port data.

    Args:
        response: Standard Analytics response.

    Returns:
        Raw value carried in ``data``.

    Raises:
        AssertionError: If the public operation failed.
    """
    if response.status != "success":
        raise AssertionError(response.error)
    return cast("T", response.data)
