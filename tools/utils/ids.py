"""Trace identifier generation and validation helpers.

Generates and validates prefixed identifiers used for request, workflow, run,
and tool-call traceability across HaruQuant workflows.

This module is a utility helper, not an official AI tool file. It does not
return AI-tool response dictionaries and should be used internally by agents,
tools, workflows, runtime layers, audit writers, and tests when trace IDs are
required.

Exported AI Tools:
    None.

Public Helpers:
    - new_request_id: Create a request identifier.
    - new_workflow_id: Create a workflow identifier.
    - new_run_id: Create a run identifier.
    - new_tool_call_id: Create a tool-call identifier.
    - is_valid_prefixed_id: Validate an identifier against a prefix.
    - is_request_id: Validate a request identifier.
    - is_workflow_id: Validate a workflow identifier.
    - is_run_id: Validate a run identifier.
    - is_tool_call_id: Validate a tool-call identifier.

Internal Helpers:
    - _require_valid_prefix: Validate an approved ID prefix.
    - _new_prefixed_id: Create a prefixed UUID-based identifier.

Classes:
    None.
"""

from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from tools.utils.logger import logger

ID_SEPARATOR = "_"
UUID_HEX_LENGTH = 32

REQUEST_ID_PREFIX = "req"
WORKFLOW_ID_PREFIX = "wf"
RUN_ID_PREFIX = "run"
TOOL_CALL_ID_PREFIX = "toolcall"

VALID_ID_PREFIXES = frozenset(
    {
        REQUEST_ID_PREFIX,
        WORKFLOW_ID_PREFIX,
        RUN_ID_PREFIX,
        TOOL_CALL_ID_PREFIX,
    }
)

_UUID_HEX_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def _require_valid_prefix(prefix: Any) -> str:
    """
    Validate that a prefix is an approved HaruQuant trace ID prefix.

    Args:
        prefix (str): Candidate prefix.

    Returns:
        str: Validated prefix.

    Raises:
        TypeError: If ``prefix`` is not a string.
        ValueError: If ``prefix`` is empty or not approved.
    """
    if not isinstance(prefix, str):
        logger.warning("Invalid ID prefix type | prefix_type=%s", type(prefix).__name__)
        raise TypeError("prefix must be a string.")

    if not prefix:
        logger.warning("Invalid ID prefix | reason=empty")
        raise ValueError("prefix cannot be empty.")

    if prefix != prefix.strip():
        logger.warning("Invalid ID prefix | reason=surrounding_whitespace")
        raise ValueError("prefix cannot contain surrounding whitespace.")

    if prefix not in VALID_ID_PREFIXES:
        logger.warning("Invalid ID prefix | prefix=%s", prefix)
        allowed = ", ".join(sorted(VALID_ID_PREFIXES))
        raise ValueError(f"prefix must be one of: {allowed}.")

    return prefix


def _new_prefixed_id(prefix: str) -> str:
    """
    Create a unique identifier with an approved stable prefix.

    Args:
        prefix (str): Approved prefix identifying the ID category.

    Returns:
        str: Prefixed unique identifier in ``{prefix}_{uuid_hex}`` format.

    Raises:
        TypeError: If ``prefix`` is not a string.
        ValueError: If ``prefix`` is empty or not approved.
    """
    safe_prefix = _require_valid_prefix(prefix)
    return f"{safe_prefix}{ID_SEPARATOR}{uuid4().hex}"


def is_valid_prefixed_id(value: Any, prefix: Any) -> bool:
    """
    Validate that a value matches the standard HaruQuant prefixed ID format.

    The expected format is ``{prefix}_{32_hex_chars}``.

    Args:
        value (str): Candidate identifier.
        prefix (str): Expected approved ID prefix.

    Returns:
        bool: True when the value matches the expected format, otherwise False.

    Raises:
        TypeError: If ``prefix`` is not a string.
        ValueError: If ``prefix`` is empty or not approved.
    """
    safe_prefix = _require_valid_prefix(prefix)

    if not isinstance(value, str):
        return False

    expected_start = f"{safe_prefix}{ID_SEPARATOR}"
    if not value.startswith(expected_start):
        return False

    suffix = value[len(expected_start) :]
    return bool(_UUID_HEX_PATTERN.fullmatch(suffix))


def is_request_id(value: str) -> bool:
    """
    Validate whether a value is a standard request identifier.

    Args:
        value (str): Candidate request ID.

    Returns:
        bool: True when the value is a valid request ID.
    """
    return is_valid_prefixed_id(value, REQUEST_ID_PREFIX)


def is_workflow_id(value: str) -> bool:
    """
    Validate whether a value is a standard workflow identifier.

    Args:
        value (str): Candidate workflow ID.

    Returns:
        bool: True when the value is a valid workflow ID.
    """
    return is_valid_prefixed_id(value, WORKFLOW_ID_PREFIX)


def is_run_id(value: str) -> bool:
    """
    Validate whether a value is a standard run identifier.

    Args:
        value (str): Candidate run ID.

    Returns:
        bool: True when the value is a valid run ID.
    """
    return is_valid_prefixed_id(value, RUN_ID_PREFIX)


def is_tool_call_id(value: str) -> bool:
    """
    Validate whether a value is a standard tool-call identifier.

    Args:
        value (str): Candidate tool-call ID.

    Returns:
        bool: True when the value is a valid tool-call ID.
    """
    return is_valid_prefixed_id(value, TOOL_CALL_ID_PREFIX)


def new_request_id() -> str:
    """
    Create a unique request identifier.

    Returns:
        str: Identifier prefixed with ``req_``.
    """
    return _new_prefixed_id(REQUEST_ID_PREFIX)


def new_workflow_id() -> str:
    """
    Create a unique workflow identifier.

    Returns:
        str: Identifier prefixed with ``wf_``.
    """
    return _new_prefixed_id(WORKFLOW_ID_PREFIX)


def new_run_id() -> str:
    """
    Create a unique run identifier.

    Returns:
        str: Identifier prefixed with ``run_``.
    """
    return _new_prefixed_id(RUN_ID_PREFIX)


def new_tool_call_id() -> str:
    """
    Create a unique tool-call identifier.

    Returns:
        str: Identifier prefixed with ``toolcall_``.
    """
    return _new_prefixed_id(TOOL_CALL_ID_PREFIX)


__all__ = [
    "ID_SEPARATOR",
    "UUID_HEX_LENGTH",
    "REQUEST_ID_PREFIX",
    "WORKFLOW_ID_PREFIX",
    "RUN_ID_PREFIX",
    "TOOL_CALL_ID_PREFIX",
    "VALID_ID_PREFIXES",
    "is_request_id",
    "is_run_id",
    "is_tool_call_id",
    "is_valid_prefixed_id",
    "is_workflow_id",
    "new_request_id",
    "new_run_id",
    "new_tool_call_id",
    "new_workflow_id",
]
