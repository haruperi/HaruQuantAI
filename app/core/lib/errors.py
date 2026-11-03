"""Domain errors and finite JSON value handling matching donor SQException.

Description:
    Defines canonical domain exceptions and recursive JSON value detachment
    utilities. Rejects non-finite floats, reference cycles, and non-string keys,
    preserving immutability and diagnostic safety across host and workspaces.

Purpose:
    FEAT-CORE-LIB-ERRORS: Provide verified domain exception and JSON isolation
    primitives.

Key Capabilities:
    - FR-core-lib-json-copy: Recursively validate and detach finite JSON values,
      rejecting non-finite numbers and reference cycles.
    - FR-core-lib-domain-error: Represent typed operational or contract failures with
      structured, safe JSON details.

Python API Usage:
    ```python
    from app.core.lib.errors import DomainError, SQException, copy_json

    raise DomainError(code="INVALID_STATE", message="State invalid", details={"k": "v"})
    ```

CLI Usage:
    ```bash
    uv run pytest tests/core/lib/test_errors.py -q
    ```
"""

from __future__ import annotations

import math
from typing import Any

type JSONValue = (
    bool | int | float | str | list[JSONValue] | dict[str, JSONValue] | None
)

__all__ = ["DomainError", "JSONValue", "SQException", "copy_json"]


def _copy_list(items: list[Any], path_ids: set[int]) -> list[JSONValue]:
    val_id = id(items)
    if val_id in path_ids:
        raise ValueError("value must not contain cycles")
    path_ids.add(val_id)
    try:
        return [_copy_json_internal(item, path_ids) for item in items]
    finally:
        path_ids.remove(val_id)


def _copy_dict(mapping: dict[str, Any], path_ids: set[int]) -> dict[str, JSONValue]:
    val_id = id(mapping)
    if val_id in path_ids:
        raise ValueError("value must not contain cycles")
    path_ids.add(val_id)
    try:
        detached: dict[str, JSONValue] = {}
        for k, v in mapping.items():
            if not isinstance(k, str):
                raise ValueError("value must contain finite JSON values")  # noqa: TRY004
            detached[k] = _copy_json_internal(v, path_ids)
        return detached
    finally:
        path_ids.remove(val_id)


def _copy_json_internal(value: Any, path_ids: set[int]) -> JSONValue:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("value must contain finite JSON values")
        return value
    if isinstance(value, list):
        return _copy_list(value, path_ids)
    if isinstance(value, dict):
        return _copy_dict(value, path_ids)
    raise ValueError("value must contain finite JSON values")


def copy_json(value: JSONValue) -> JSONValue:
    """Recursively validate and create a detached copy of a finite JSON value.

    Args:
        value: The candidate JSON value to detach and validate.

    Returns:
        A detached copy of the JSON value.

    Raises:
        ValueError: If value contains non-finite numbers, unsupported types,
            non-string dictionary keys, or reference cycles.
    """
    return _copy_json_internal(value, set())


class DomainError(Exception):
    """Domain exception representing an operational or contract failure."""

    code: str
    message: str
    details: dict[str, JSONValue]

    def __init__(
        self,
        *,
        code: str,
        message: str,
        details: dict[str, JSONValue] | None = None,
    ) -> None:
        """Initialize domain error with explicit code, message, and details.

        Args:
            code: Non-empty machine-readable error code.
            message: Non-empty human-readable error description.
            details: Optional dictionary containing additional structured JSON details.

        Raises:
            ValueError: If code or message are not non-empty strings, or details
                is not a dictionary/None, or details contains non-finite JSON/cycles.
        """
        if not isinstance(code, str) or not code:
            raise ValueError("code must be non-empty")
        if not isinstance(message, str) or not message:
            raise ValueError("message must be non-empty")
        if details is not None and not isinstance(details, dict):
            raise ValueError("details must be an object or None")

        super().__init__(message)
        self.code = code
        self.message = message
        if details is not None:
            copied = copy_json(details)
            if not isinstance(copied, dict):
                raise ValueError("details must be an object or None")
            self.details = copied
        else:
            self.details = {}

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize domain error into a detached dictionary representation.

        Returns:
            Dictionary matching {'code': ..., 'message': ..., 'details': ...}.
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": copy_json(self.details),
        }


SQException = DomainError
