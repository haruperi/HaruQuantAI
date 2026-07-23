"""Utils-owned construction portion of `WF-UTL-003`.

Steps 1-4 of the workflow are owned by Utils: domain-supplied action facts and
trace context, ID and UTC validation, redaction plus canonicalization, and bounded
`AuditEvent v1` construction. Step 5, persistence, is owned by Data and is proven by
`tests/data/integration/test_audit_event_handoff.py`, which keeps this module free of
any `app.services` dependency.
"""

from datetime import UTC, datetime

import pytest
from app.utils import (
    AuditEvent,
    canonical_json,
    generate_id,
    redact_mapping_value,
)
from pydantic import ValidationError


def test_redacted_canonical_audit_event_is_constructed() -> None:
    """Build one genuinely redacted, canonicalized Utils audit envelope."""
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
    assert event.payload["account"] == "demo"


def test_audit_event_construction_fails_closed_on_protected_key() -> None:
    """Reject a payload carrying a protected credential key before persistence."""
    with pytest.raises(ValidationError):
        AuditEvent(
            contract_version="v1",
            schema_id="utils.audit_event.v1",
            event_id=generate_id("evt"),
            timestamp=datetime.now(UTC),
            domain="trading",
            action="request_received",
            request_id=generate_id("req"),
            correlation_id=generate_id("cor"),
            payload={"api_key": "abc123"},
        )
