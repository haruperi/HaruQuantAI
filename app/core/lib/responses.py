"""Canonical StandardResponse envelope and host response builders.

Combines the canonical StandardResponse[T] frozen dataclass envelope for structured
JSON payloads with host operation error categories, metadata, and dictionary builders.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from pydantic import TypeAdapter

from app.core.lib.errors import JSONValue, copy_json

_MAX_MESSAGE_LENGTH = 1024
_JSON_ADAPTER: TypeAdapter[Any] = TypeAdapter(Any)


class ErrorCode(StrEnum):
    """Stable operation error categories, independent of transport status codes."""

    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"
    INTERNAL = "internal"


def _check_message(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("message must be a non-empty string")
    if len(value) > _MAX_MESSAGE_LENGTH:
        raise ValueError(f"message must not exceed {_MAX_MESSAGE_LENGTH} characters")


def _freeze(value: Any) -> Any:
    """Copy and freeze JSON values, rejecting unsupported or non-finite values."""
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("JSON object keys must be strings")
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise ValueError("details and extensions must contain finite JSON values")


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _freeze_effects(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError("side_effects must be a list or tuple of strings")
    for effect in value:
        _check_message(effect)
    return tuple(value)


@dataclass(frozen=True, slots=True, kw_only=True)
class StandardError:
    """Structured failure with a stable category and safe public details.

    Messages and details must be suitable for public consumption; do not include
    secrets or internal tracebacks. Retryability is explicit, not inferred.
    """

    code: ErrorCode
    message: str
    retryable: bool = False
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and defensively freeze failure details."""
        object.__setattr__(self, "code", ErrorCode(self.code))
        _check_message(self.message)
        if not isinstance(self.retryable, bool):
            raise TypeError("retryable must be a bool")
        if not isinstance(self.details, Mapping):
            raise TypeError("details must be a mapping")
        object.__setattr__(self, "details", _freeze(self.details))


@dataclass(frozen=True, slots=True, kw_only=True)
class ResponseMetadata:
    """Required execution context, reported side effects, and JSON extensions.

    duration_ms is elapsed wall time measured by the operation, preferably with a
    monotonic clock. side_effects describes effects that actually occurred, even
    when an operation failed. An empty tuple means no reported side effects.
    """

    operation: str
    duration_ms: float
    side_effects: tuple[str, ...] = ()
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate execution context and freeze caller-owned metadata."""
        _check_message(self.operation)
        if (
            isinstance(self.duration_ms, bool)
            or not isinstance(self.duration_ms, (int, float))
            or not math.isfinite(self.duration_ms)
            or self.duration_ms < 0
        ):
            raise ValueError("duration_ms must be finite and non-negative")
        object.__setattr__(self, "side_effects", _freeze_effects(self.side_effects))
        if not isinstance(self.extensions, Mapping):
            raise TypeError("extensions must be a mapping")
        object.__setattr__(self, "extensions", _freeze(self.extensions))


@dataclass(frozen=True, slots=True, kw_only=True)
class StandardResponse[T]:
    """Standard response envelope for API, host, and workspace operations.

    Supports both canonical generic envelope instances (request_id, data, revision)
    and static builder methods (StandardResponse.success, StandardResponse.failure)
    for bounded host operation responses.
    """

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

    @staticmethod
    def success(
        *, message: str, metadata: ResponseMetadata, data: Any = None
    ) -> dict[str, Any]:
        """Build a successful result; None is a valid successful value.

        Common result types such as models, dataclasses, datetimes, UUIDs, and
        enums are serialized to JSON values. Unsupported data raises an error.
        """
        return _build_response(
            success=True, message=message, metadata=metadata, data=data, error=None
        )

    @staticmethod
    def failure(
        *, message: str, metadata: ResponseMetadata, error: StandardError
    ) -> dict[str, Any]:
        """Build a failed result with a required structured error and no data."""
        if not isinstance(error, StandardError):
            raise TypeError("failure requires StandardError")
        return _build_response(
            success=False, message=message, metadata=metadata, data=None, error=error
        )


def _build_response(
    *,
    success: bool,
    message: str,
    metadata: ResponseMetadata,
    data: Any,
    error: StandardError | None,
) -> dict[str, Any]:
    _check_message(message)
    if not isinstance(metadata, ResponseMetadata):
        raise TypeError("metadata must be ResponseMetadata")
    return {
        "success": success,
        "message": message,
        "data": _JSON_ADAPTER.dump_python(data, mode="json"),
        "error": (
            {
                "code": error.code.value,
                "message": error.message,
                "retryable": error.retryable,
                "details": _thaw(error.details),
            }
            if error is not None
            else None
        ),
        "metadata": {
            "operation": metadata.operation,
            "duration_ms": metadata.duration_ms,
            "side_effects": list(metadata.side_effects),
            "extensions": _thaw(metadata.extensions),
        },
    }
