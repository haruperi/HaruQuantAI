"""Contracts for loading an approved local CSV or Parquet dataset."""

from pathlib import Path
from typing import Literal

from pydantic import field_validator

from app.services.data.contracts._base import TracedOpenContract


def _relative_path(value: Path) -> Path:
    """Validate an approved-root-relative, traversal-free artifact path."""
    if value.is_absolute() or not value.parts or ".." in value.parts:
        raise ValueError("path must be relative and traversal-free")
    if any(part.startswith(".") for part in value.parts):
        raise ValueError("hidden path segments are not allowed")
    return value


class DatasetLoadRequest(TracedOpenContract):
    """Approved-root-relative local dataset load request."""

    relative_path: Path
    format: Literal["csv", "parquet"]
    request_id: str

    @field_validator("relative_path")
    @classmethod
    def _validate_path(cls, value: Path) -> Path:
        """Validate the requested relative artifact path."""
        return _relative_path(value)


__all__ = ["DatasetLoadRequest"]
