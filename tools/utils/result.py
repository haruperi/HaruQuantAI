"""Result helpers for HaruQuantAI utilities.

Builds standard structured result dictionaries for HaruQuant utilities,
workflows, tools, and runtime layers.

This module is a small utility helper, not an official AI tool file. It does
not expose agent-callable tools. It provides deterministic dictionary builders
that other HaruQuant modules can use when returning structured outcomes.

Exported AI Tools:
    None.

Public Helpers:
    - success_result: Build a standard success result.
    - error_result: Build a standard error result.
    - blocked_result: Build a standard policy-blocked result.
    - needs_approval_result: Build a standard approval-required result.
    - needs_clarification_result: Build a standard clarification-required result.

Internal Helpers:
    - _metadata: Build protected trace metadata.
    - _result: Build and validate the final result dictionary.
    - _require_non_empty_string: Validate required string fields.
    - _validate_status: Validate result status values.
    - _validate_extra_metadata: Validate optional caller metadata.

Classes:
    None.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypeAlias

from tools.utils.logger import logger

ResultDict: TypeAlias = dict[str, Any]
MetadataDict: TypeAlias = dict[str, Any]
ErrorDict: TypeAlias = dict[str, str]

STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
STATUS_BLOCKED = "blocked"
STATUS_NEEDS_APPROVAL = "needs_approval"
STATUS_NEEDS_CLARIFICATION = "needs_clarification"

VALID_RESULT_STATUSES = frozenset(
    {
        STATUS_SUCCESS,
        STATUS_ERROR,
        STATUS_BLOCKED,
        STATUS_NEEDS_APPROVAL,
        STATUS_NEEDS_CLARIFICATION,
    }
)

ERROR_INVALID_INPUT = "INVALID_INPUT"
ERROR_MISSING_INPUT = "MISSING_INPUT"
ERROR_POLICY_BLOCKED = "POLICY_BLOCKED"
ERROR_APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
ERROR_VALIDATION_FAILED = "VALIDATION_FAILED"
ERROR_UNKNOWN = "UNKNOWN_ERROR"

RESERVED_METADATA_KEYS = frozenset(
    {
        "request_id",
        "workflow_id",
        "source",
        "created_at",
        "extra",
    }
)

DEFAULT_SOURCE = "tools.utils.result"


def _utc_timestamp() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _require_non_empty_string(value: str, field_name: str) -> str:
    """
    Validate and normalize a required string field.

    Args:
        value (str): Candidate string value.
        field_name (str): Field name used in validation errors.

    Returns:
        str: Trimmed non-empty string.

    Raises:
        TypeError: If the value is not a string.
        ValueError: If the value is empty after trimming whitespace.
    """
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty.")

    return normalized


def _validate_status(status: str) -> str:
    """
    Validate a standard HaruQuant result status.

    Args:
        status (str): Candidate result status.

    Returns:
        str: Validated status.

    Raises:
        TypeError: If status is not a string.
        ValueError: If status is not one of the supported result statuses.
    """
    normalized = _require_non_empty_string(status, "status")
    if normalized not in VALID_RESULT_STATUSES:
        allowed = ", ".join(sorted(VALID_RESULT_STATUSES))
        raise ValueError(f"status must be one of: {allowed}.")

    return normalized


def _validate_extra_metadata(extra: MetadataDict | None) -> MetadataDict | None:
    """
    Validate optional caller-provided metadata.

    Args:
        extra (MetadataDict | None): Optional extra metadata to include under
            the result metadata ``extra`` key.

    Returns:
        MetadataDict | None: A shallow copy of validated metadata, or ``None``.

    Raises:
        TypeError: If extra metadata is not a dictionary.
        ValueError: If extra metadata tries to overwrite reserved trace fields.
    """
    if extra is None:
        return None

    if not isinstance(extra, dict):
        raise TypeError("metadata must be a dictionary when provided.")

    reserved = RESERVED_METADATA_KEYS.intersection(extra)
    if reserved:
        blocked = ", ".join(sorted(reserved))
        raise ValueError(f"metadata cannot contain reserved key(s): {blocked}.")

    return dict(extra)


def _metadata(
    *,
    request_id: str | None = None,
    workflow_id: str | None = None,
    source: str = DEFAULT_SOURCE,
    extra: MetadataDict | None = None,
) -> MetadataDict:
    """
    Build protected metadata shared by standard result dictionaries.

    Caller-provided metadata is stored under ``extra`` so it cannot overwrite
    trace fields such as ``request_id``, ``workflow_id``, ``source``, or
    ``created_at``.

    Args:
        request_id (str | None, optional): Request trace ID.
        workflow_id (str | None, optional): Workflow trace ID.
        source (str, optional): Component creating the result.
        extra (MetadataDict | None, optional): Additional non-reserved metadata.

    Returns:
        MetadataDict: Result metadata with protected trace fields.

    Raises:
        TypeError: If ``source`` or ``extra`` has an invalid type.
        ValueError: If ``source`` is empty or ``extra`` contains reserved keys.
    """
    safe_source = _require_non_empty_string(source, "source")
    safe_extra = _validate_extra_metadata(extra)

    metadata: MetadataDict = {
        "request_id": request_id,
        "workflow_id": workflow_id,
        "source": safe_source,
        "created_at": _utc_timestamp(),
        "extra": safe_extra or {},
    }

    return metadata


def _result(
    *,
    status: str,
    message: str,
    data: Any = None,
    error: ErrorDict | None = None,
    request_id: str | None = None,
    workflow_id: str | None = None,
    source: str = DEFAULT_SOURCE,
    metadata: MetadataDict | None = None,
) -> ResultDict:
    """
    Build the standard HaruQuant result dictionary.

    Args:
        status (str): Standard result status.
        message (str): Human-readable result message.
        data (Any, optional): Result payload.
        error (ErrorDict | None, optional): Structured error details.
        request_id (str | None, optional): Request trace ID.
        workflow_id (str | None, optional): Workflow trace ID.
        source (str, optional): Component creating the result.
        metadata (MetadataDict | None, optional): Additional non-reserved
            metadata stored under ``metadata["extra"]``.

    Returns:
        ResultDict: Standard structured result.

    Raises:
        TypeError: If required string or metadata inputs have invalid types.
        ValueError: If status, message, source, or metadata is invalid.
    """
    safe_status = _validate_status(status)
    safe_message = _require_non_empty_string(message, "message")

    if error is not None and not isinstance(error, dict):
        raise TypeError("error must be a dictionary or None.")

    return {
        "status": safe_status,
        "message": safe_message,
        "data": data,
        "error": error,
        "metadata": _metadata(
            request_id=request_id,
            workflow_id=workflow_id,
            source=source,
            extra=metadata,
        ),
    }


def success_result(
    message: str,
    data: Any = None,
    *,
    request_id: str | None = None,
    workflow_id: str | None = None,
    source: str = DEFAULT_SOURCE,
    metadata: MetadataDict | None = None,
) -> ResultDict:
    """
    Build a standard success result.

    Use this helper when a utility, workflow, or runtime step completes
    successfully and needs to return a consistent HaruQuant result shape.

    Args:
        message (str): Human-readable success message.
        data (Any, optional): Success payload.
        request_id (str | None, optional): Request trace ID.
        workflow_id (str | None, optional): Workflow trace ID.
        source (str, optional): Component creating the result.
        metadata (MetadataDict | None, optional): Additional non-reserved
            metadata stored under ``metadata["extra"]``.

    Returns:
        ResultDict: Standard success result.

    Raises:
        TypeError: If required string or metadata inputs have invalid types.
        ValueError: If message, source, or metadata is invalid.
    """
    logger.debug("Building success result | request_id=%s", request_id)
    return _result(
        status=STATUS_SUCCESS,
        message=message,
        data=data,
        error=None,
        request_id=request_id,
        workflow_id=workflow_id,
        source=source,
        metadata=metadata,
    )


def error_result(
    message: str,
    code: str,
    details: str,
    *,
    request_id: str | None = None,
    workflow_id: str | None = None,
    source: str = DEFAULT_SOURCE,
    metadata: MetadataDict | None = None,
) -> ResultDict:
    """
    Build a standard error result.

    Use this helper when a utility, workflow, or runtime step fails and the
    caller needs a deterministic error code and explanation.

    Args:
        message (str): Human-readable failure message.
        code (str): Deterministic error code.
        details (str): Specific failure details.
        request_id (str | None, optional): Request trace ID.
        workflow_id (str | None, optional): Workflow trace ID.
        source (str, optional): Component creating the result.
        metadata (MetadataDict | None, optional): Additional non-reserved
            metadata stored under ``metadata["extra"]``.

    Returns:
        ResultDict: Standard error result.

    Raises:
        TypeError: If required string or metadata inputs have invalid types.
        ValueError: If message, code, details, source, or metadata is invalid.
    """
    safe_code = _require_non_empty_string(code, "code")
    safe_details = _require_non_empty_string(details, "details")

    logger.debug(
        "Building error result | request_id=%s | code=%s",
        request_id,
        safe_code,
    )
    return _result(
        status=STATUS_ERROR,
        message=message,
        data=None,
        error={"code": safe_code, "details": safe_details},
        request_id=request_id,
        workflow_id=workflow_id,
        source=source,
        metadata=metadata,
    )


def blocked_result(
    message: str,
    code: str = ERROR_POLICY_BLOCKED,
    details: str = "The requested operation was blocked.",
    *,
    request_id: str | None = None,
    workflow_id: str | None = None,
    source: str = DEFAULT_SOURCE,
    metadata: MetadataDict | None = None,
) -> ResultDict:
    """
    Build a standard policy-blocked result.

    Use this helper when deterministic policy, permissions, risk controls, or
    workflow rules prevent an operation from continuing.

    Args:
        message (str): Human-readable blocked message.
        code (str, optional): Deterministic error code.
        details (str, optional): Specific blocked details.
        request_id (str | None, optional): Request trace ID.
        workflow_id (str | None, optional): Workflow trace ID.
        source (str, optional): Component creating the result.
        metadata (MetadataDict | None, optional): Additional non-reserved
            metadata stored under ``metadata["extra"]``.

    Returns:
        ResultDict: Standard blocked result.

    Raises:
        TypeError: If required string or metadata inputs have invalid types.
        ValueError: If message, code, details, source, or metadata is invalid.
    """
    safe_code = _require_non_empty_string(code, "code")
    safe_details = _require_non_empty_string(details, "details")

    logger.debug(
        "Building blocked result | request_id=%s | code=%s",
        request_id,
        safe_code,
    )
    return _result(
        status=STATUS_BLOCKED,
        message=message,
        data=None,
        error={"code": safe_code, "details": safe_details},
        request_id=request_id,
        workflow_id=workflow_id,
        source=source,
        metadata=metadata,
    )


def needs_approval_result(
    message: str,
    details: str = "Approval is required before this operation can continue.",
    *,
    request_id: str | None = None,
    workflow_id: str | None = None,
    source: str = DEFAULT_SOURCE,
    metadata: MetadataDict | None = None,
) -> ResultDict:
    """
    Build a standard approval-required result.

    Use this helper when a workflow step is valid but cannot continue until a
    human or deterministic approval gate grants permission.

    Args:
        message (str): Human-readable approval message.
        details (str, optional): Specific approval details.
        request_id (str | None, optional): Request trace ID.
        workflow_id (str | None, optional): Workflow trace ID.
        source (str, optional): Component creating the result.
        metadata (MetadataDict | None, optional): Additional non-reserved
            metadata stored under ``metadata["extra"]``.

    Returns:
        ResultDict: Standard approval-required result.

    Raises:
        TypeError: If required string or metadata inputs have invalid types.
        ValueError: If message, details, source, or metadata is invalid.
    """
    safe_details = _require_non_empty_string(details, "details")

    logger.debug("Building approval-required result | request_id=%s", request_id)
    return _result(
        status=STATUS_NEEDS_APPROVAL,
        message=message,
        data=None,
        error={"code": ERROR_APPROVAL_REQUIRED, "details": safe_details},
        request_id=request_id,
        workflow_id=workflow_id,
        source=source,
        metadata=metadata,
    )


def needs_clarification_result(
    message: str,
    details: str = "More information is required before this operation can continue.",
    *,
    request_id: str | None = None,
    workflow_id: str | None = None,
    source: str = DEFAULT_SOURCE,
    metadata: MetadataDict | None = None,
) -> ResultDict:
    """
    Build a standard clarification-required result.

    Use this helper when a request is incomplete and the workflow needs more
    input before it can safely continue.

    Args:
        message (str): Human-readable clarification message.
        details (str, optional): Specific clarification details.
        request_id (str | None, optional): Request trace ID.
        workflow_id (str | None, optional): Workflow trace ID.
        source (str, optional): Component creating the result.
        metadata (MetadataDict | None, optional): Additional non-reserved
            metadata stored under ``metadata["extra"]``.

    Returns:
        ResultDict: Standard clarification-required result.

    Raises:
        TypeError: If required string or metadata inputs have invalid types.
        ValueError: If message, details, source, or metadata is invalid.
    """
    safe_details = _require_non_empty_string(details, "details")

    logger.debug("Building clarification-required result | request_id=%s", request_id)
    return _result(
        status=STATUS_NEEDS_CLARIFICATION,
        message=message,
        data=None,
        error={"code": ERROR_MISSING_INPUT, "details": safe_details},
        request_id=request_id,
        workflow_id=workflow_id,
        source=source,
        metadata=metadata,
    )


__all__ = [
    "ResultDict",
    "MetadataDict",
    "ErrorDict",
    "STATUS_SUCCESS",
    "STATUS_ERROR",
    "STATUS_BLOCKED",
    "STATUS_NEEDS_APPROVAL",
    "STATUS_NEEDS_CLARIFICATION",
    "VALID_RESULT_STATUSES",
    "ERROR_INVALID_INPUT",
    "ERROR_MISSING_INPUT",
    "ERROR_POLICY_BLOCKED",
    "ERROR_APPROVAL_REQUIRED",
    "ERROR_VALIDATION_FAILED",
    "ERROR_UNKNOWN",
    "success_result",
    "error_result",
    "blocked_result",
    "needs_approval_result",
    "needs_clarification_result",
]
