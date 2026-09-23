"""Tests for the shared host envelope."""

from app.host.envelope import (
    API_VERSION,
    ValidationIssue,
    error_payload,
    new_request_id,
    success_payload,
)


def test_success_payload_carries_data_and_envelope_fields() -> None:
    payload = success_payload("req-1", {"ready": True})

    assert payload["api_version"] == API_VERSION
    assert payload["request_id"] == "req-1"
    assert payload["status"] == "success"
    assert payload["data"] == {"ready": True}
    assert "error" not in payload


def test_error_payload_serializes_structured_issues() -> None:
    issue = ValidationIssue(path="$.nodes", code="required", message="missing nodes")

    payload = error_payload("req-2", "SCHEMA_INVALID", "rejected", [issue])

    assert payload["status"] == "error"
    assert "data" not in payload
    assert payload["error"]["code"] == "SCHEMA_INVALID"
    assert payload["error"]["message"] == "rejected"
    assert payload["error"]["issues"] == [
        {"path": "$.nodes", "code": "required", "message": "missing nodes"}
    ]


def test_request_ids_are_fresh_and_prefixed() -> None:
    first = new_request_id()
    second = new_request_id()

    assert first.startswith("req-")
    assert second.startswith("req-")
    assert first != second
