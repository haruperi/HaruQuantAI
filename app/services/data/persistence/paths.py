"""Validate Data-owned persistence paths before filesystem access."""

from __future__ import annotations

from pathlib import Path

from app.services.data._settings import get_data_settings
from app.services.data.contracts import DataError

APPROVED_STORAGE_ROOTS_SETTING = "APPROVED_STORAGE_ROOTS"


def resolve_approved_storage_path(path: Path, request_id: str | None = None) -> Path:
    """Resolve a destination beneath an active approved storage root.

    Args:
        path: Caller-selected destination to validate without creating it.
        request_id: Optional request identifier for the safe public error.

    Returns:
        The absolute normalized destination path.

    Raises:
        DataError: If the path is invalid or lies outside every approved root.
    """
    if not isinstance(path, Path):
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "path"},
            request_id=request_id,
        )
    try:
        resolved_path = path.expanduser().resolve()
        approved_roots = tuple(
            root.expanduser().resolve()
            for root in get_data_settings().approved_storage_roots
        )
    except OSError:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "path"},
            request_id=request_id,
        ) from None
    if not approved_roots or not any(
        resolved_path.is_relative_to(root) for root in approved_roots
    ):
        raise DataError(
            "PERMISSION_DENIED",
            safe_details={"field": "path", "reason": "outside_approved_roots"},
            request_id=request_id,
        )
    return resolved_path


__all__ = ["APPROVED_STORAGE_ROOTS_SETTING", "resolve_approved_storage_path"]
