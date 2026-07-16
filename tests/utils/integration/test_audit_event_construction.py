from datetime import UTC, datetime

from app.utils import (
    AuditEvent,
    canonical_json,
    generate_id,
    redact_mapping_value,
)


def test_redacted_canonical_audit_event_is_ready_for_data_persistence() -> None:
    safe_payload = redact_mapping_value({"account": "demo", "token": "abc123"}).value
    assert isinstance(safe_payload, dict)
    event = AuditEvent(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=generate_id("evt"),
        timestamp=datetime.now(UTC),
        domain="trading",
        action="request_received",
        request_id=generate_id("req"),
        correlation_id=generate_id("cor"),
        payload=safe_payload,
    )
    serialized = canonical_json(event.payload)
    assert "abc123" not in serialized
    assert "[REDACTED]" in serialized
