"""Unit tests for tools.utils.result."""

from __future__ import annotations

import pytest

from tools.utils.result import ERROR_APPROVAL_REQUIRED
from tools.utils.result import ERROR_MISSING_INPUT
from tools.utils.result import ERROR_POLICY_BLOCKED
from tools.utils.result import STATUS_BLOCKED
from tools.utils.result import STATUS_ERROR
from tools.utils.result import STATUS_NEEDS_APPROVAL
from tools.utils.result import STATUS_NEEDS_CLARIFICATION
from tools.utils.result import STATUS_SUCCESS
from tools.utils.result import VALID_RESULT_STATUSES
from tools.utils.result import blocked_result
from tools.utils.result import error_result
from tools.utils.result import needs_approval_result
from tools.utils.result import needs_clarification_result
from tools.utils.result import success_result


def _assert_base_schema(result: dict) -> None:
    assert set(result) == {"status", "message", "data", "error", "metadata"}
    assert isinstance(result["message"], str)
    assert isinstance(result["metadata"], dict)
    assert "request_id" in result["metadata"]
    assert "workflow_id" in result["metadata"]
    assert "source" in result["metadata"]
    assert "created_at" in result["metadata"]
    assert "extra" in result["metadata"]


def test_success_result_returns_standard_schema() -> None:
    result = success_result(
        "Completed.",
        data={"value": 10},
        request_id="req-001",
        workflow_id="wf-001",
        metadata={"component": "unit-test"},
    )

    _assert_base_schema(result)
    assert result["status"] == STATUS_SUCCESS
    assert result["data"] == {"value": 10}
    assert result["error"] is None
    assert result["metadata"]["request_id"] == "req-001"
    assert result["metadata"]["workflow_id"] == "wf-001"
    assert result["metadata"]["extra"] == {"component": "unit-test"}


def test_error_result_returns_standard_error_schema() -> None:
    result = error_result(
        "Validation failed.",
        code="VALIDATION_FAILED",
        details="symbol is required.",
        request_id="req-002",
    )

    _assert_base_schema(result)
    assert result["status"] == STATUS_ERROR
    assert result["data"] is None
    assert result["error"] == {
        "code": "VALIDATION_FAILED",
        "details": "symbol is required.",
    }
    assert result["metadata"]["request_id"] == "req-002"


def test_blocked_result_uses_policy_blocked_default_code() -> None:
    result = blocked_result("Blocked by risk policy.")

    _assert_base_schema(result)
    assert result["status"] == STATUS_BLOCKED
    assert result["error"]["code"] == ERROR_POLICY_BLOCKED


def test_needs_approval_result_uses_approval_required_code() -> None:
    result = needs_approval_result("Approval needed.")

    _assert_base_schema(result)
    assert result["status"] == STATUS_NEEDS_APPROVAL
    assert result["error"]["code"] == ERROR_APPROVAL_REQUIRED


def test_needs_clarification_result_uses_missing_input_code() -> None:
    result = needs_clarification_result("Need symbol.")

    _assert_base_schema(result)
    assert result["status"] == STATUS_NEEDS_CLARIFICATION
    assert result["error"]["code"] == ERROR_MISSING_INPUT


@pytest.mark.parametrize(
    "builder,args",
    [
        (success_result, ("",)),
        (error_result, ("", "INVALID_INPUT", "details")),
        (blocked_result, ("",)),
        (needs_approval_result, ("",)),
        (needs_clarification_result, ("",)),
    ],
)
def test_result_builders_reject_empty_message(builder, args: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="message cannot be empty"):
        builder(*args)


@pytest.mark.parametrize(
    "builder,args",
    [
        (error_result, ("Invalid.", "", "details")),
        (error_result, ("Invalid.", "INVALID_INPUT", "")),
        (blocked_result, ("Blocked.", "")),
        (blocked_result, ("Blocked.", "POLICY_BLOCKED", "")),
        (needs_approval_result, ("Approval.", "")),
        (needs_clarification_result, ("Clarification.", "")),
    ],
)
def test_error_like_builders_reject_empty_code_or_details(
    builder,
    args: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError):
        builder(*args)


def test_metadata_cannot_overwrite_reserved_trace_fields() -> None:
    with pytest.raises(ValueError, match="reserved key"):
        success_result("Completed.", metadata={"created_at": "fake-time"})

    with pytest.raises(ValueError, match="reserved key"):
        success_result("Completed.", metadata={"request_id": "fake-request"})


def test_metadata_must_be_dictionary() -> None:
    with pytest.raises(TypeError, match="metadata must be a dictionary"):
        success_result("Completed.", metadata=["not", "a", "dict"])  # type: ignore[arg-type]


def test_source_must_be_non_empty_string() -> None:
    with pytest.raises(ValueError, match="source cannot be empty"):
        success_result("Completed.", source="")


def test_all_public_statuses_are_valid() -> None:
    expected_statuses = {
        STATUS_SUCCESS,
        STATUS_ERROR,
        STATUS_BLOCKED,
        STATUS_NEEDS_APPROVAL,
        STATUS_NEEDS_CLARIFICATION,
    }
    assert VALID_RESULT_STATUSES == expected_statuses
