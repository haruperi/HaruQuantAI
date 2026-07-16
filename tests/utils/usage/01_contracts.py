"""Executable shared-contract examples."""

from datetime import UTC, datetime

from app.utils import AuditEvent, AuthContext, generate_id
from pydantic import ValidationError


def example_auth_context() -> AuthContext:
    """Construct a valid immutable authentication context."""
    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="user-example",
        principal_type="USER",
        roles=("operator",),
        permissions=("read",),
        scopes=("demo",),
        tenant_or_environment="test",
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=datetime.now(UTC),
    )


def example_audit_event() -> AuditEvent:
    """Construct a bounded safe audit event."""
    return AuditEvent(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=generate_id("evt"),
        timestamp=datetime.now(UTC),
        domain="strategy",
        action="evaluated",
        request_id=generate_id("req"),
        correlation_id=generate_id("cor"),
        payload={"status": "complete"},
    )


def example_contract_validation() -> None:
    """Demonstrate fail-closed schema validation."""
    try:
        AuthContext.model_validate(
            {**example_auth_context().model_dump(), "schema_id": "invalid"}
        )
    except ValidationError:
        return
    raise AssertionError("malformed schema was accepted")


def main() -> None:
    """Run all contract examples."""
    auth_context = example_auth_context()
    audit_event = example_audit_event()
    assert auth_context.principal_type == "USER"
    assert audit_event.domain == "strategy"
    example_contract_validation()
    print(
        "AuthContext:",
        {
            "principal_id": auth_context.principal_id,
            "principal_type": auth_context.principal_type,
            "request_id": auth_context.request_id,
        },
    )
    print(
        "AuditEvent:",
        {
            "event_id": audit_event.event_id,
            "domain": audit_event.domain,
            "action": audit_event.action,
            "payload": dict(audit_event.payload),
        },
    )
    print("Contract validation: malformed schema rejected")


if __name__ == "__main__":
    main()
