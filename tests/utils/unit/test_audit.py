from datetime import UTC, datetime

import pytest
from app.utils import AuditEvent, generate_id
from pydantic import ValidationError


def _event(**overrides: object) -> AuditEvent:
    values: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "utils.audit_event.v1",
        "event_id": generate_id("evt"),
        "timestamp": datetime.now(UTC),
        "domain": "risk",
        "action": "decision",
        "request_id": generate_id("req"),
        "correlation_id": generate_id("cor"),
        "payload": {"status": "approved"},
    }
    values.update(overrides)
    return AuditEvent.model_validate(values)


def test_audit_event_requires_json_safe_payload() -> None:
    with pytest.raises(ValidationError):
        _event(payload={"unsafe": object()})
    with pytest.raises(ValidationError):
        _event(payload={"api_key": "secret"})  # pragma: allowlist secret


def test_contract_field_validation_rejects_malformed_schema() -> None:
    with pytest.raises(ValidationError):
        _event(schema_id="audit.v1")
    with pytest.raises(ValidationError):
        _event(event_id=f"evt-{'a' * 64}")


def test_audit_event_payload_is_deeply_immutable() -> None:
    event = _event(
        causation_id=generate_id("cau"),
        payload={"nested": {"state": "safe", "values": [None, True, 1, 1.5]}},
    )
    with pytest.raises(TypeError):
        event.payload["new"] = "value"  # type: ignore[index]
    nested = event.payload["nested"]
    assert isinstance(nested, dict) is False


@pytest.mark.parametrize(
    "payload",
    [
        {"number": float("inf")},
        {1: "invalid-key"},
        {"items": list(range(1_001))},
        {"text": "x" * 65_537},
    ],
)
def test_audit_event_rejects_payload_boundaries(payload: object) -> None:
    """Reject non-JSON, unbounded, or non-finite audit evidence."""
    with pytest.raises((TypeError, ValidationError)):
        _event(payload=payload)


def test_audit_event_rejects_non_mapping_and_excessive_depth() -> None:
    """Reject non-mapping payloads and nesting beyond the contract ceiling."""
    with pytest.raises((TypeError, ValidationError)):
        _event(payload=["not-a-mapping"])
    nested: dict[str, object] = {"value": "leaf"}
    for _ in range(17):
        nested = {"nested": nested}
    with pytest.raises(ValidationError):
        _event(payload=nested)
