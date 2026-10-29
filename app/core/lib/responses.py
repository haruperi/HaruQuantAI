"""Canonical StandardResponse envelope for structured JSON payloads."""

import json
from dataclasses import dataclass

from app.core.lib.errors import JSONValue, copy_json


@dataclass(frozen=True, slots=True, kw_only=True)
class StandardResponse[T]:
    """Standard success response envelope for API and workspace operations."""

    request_id: str
    data: T
    revision: int | None = None

    def __post_init__(self) -> None:
        """Validate fields and store a detached copy of data."""
        if not isinstance(self.request_id, str) or not self.request_id:
            raise ValueError("request_id must be non-empty")
        if self.revision is not None and (
            isinstance(self.revision, bool)
            or not isinstance(self.revision, int)
            or self.revision < 0
        ):
            raise ValueError("revision must be a non-negative integer or None")
        object.__setattr__(self, "data", copy_json(self.data))  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, JSONValue]:
        """Convert response envelope into a detached dictionary representation.

        Returns:
            Dictionary with request_id, data, and revision.
        """
        return {
            "request_id": self.request_id,
            "data": copy_json(self.data),  # type: ignore[arg-type]
            "revision": self.revision,
        }

    def to_json(self) -> bytes:
        """Encode response envelope into canonical UTF-8 JSON bytes.

        Returns:
            JSON bytes formatted with ensure_ascii and compact separators.
        """
        return json.dumps(
            self.to_dict(),
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
