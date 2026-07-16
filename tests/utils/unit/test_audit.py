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
        _event(timestamp=datetime.now(UTC).replace(tzinfo=None))


def test_audit_event_payload_is_deeply_immutable() -> None:
    event = _event(payload={"nested": {"state": "safe"}})
    with pytest.raises(TypeError):
        event.payload["new"] = "value"  # type: ignore[index]
    assert not isinstance(event.payload["nested"], dict)
