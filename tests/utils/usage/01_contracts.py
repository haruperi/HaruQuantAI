"""Run real shared-contract construction examples."""

import sys
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError as PydanticValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import AuditEvent, AuthContext

_REQUEST_ID = "req-8be20911-572d-42f7-bc52-e6844f8d2125"
_WORKFLOW_ID = "wf-f4bccf77-6121-44e0-a480-17ae2043868d"
_CORRELATION_ID = "cor-0d5ab3cf-4003-47ec-a797-f70db66418a4"
_EVENT_ID = "evt-e3b98a03-9dc3-45fd-b4d7-f31aa8ae87a7"


def example_auth_context() -> AuthContext:
    """Construct an immutable authenticated-principal context."""
    context = AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="user-123",
        principal_type="USER",
        roles=("operator",),
        permissions=("backtest:run",),
        scopes=("portfolio:demo",),
        tenant_or_environment="dev",
        request_id=_REQUEST_ID,
        workflow_id=_WORKFLOW_ID,
        correlation_id=_CORRELATION_ID,
        issued_at=datetime.now(UTC),
    )
    print("AuthContext:", context.principal_id, context.request_id)
    return context


def example_audit_event() -> AuditEvent:
    """Construct a safe audit event ready for Data-owned persistence."""
    event = AuditEvent(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=_EVENT_ID,
        timestamp=datetime.now(UTC),
        domain="utils",
        action="USAGE_EXECUTED",
        request_id=_REQUEST_ID,
        correlation_id=_CORRELATION_ID,
        payload={"result": "success"},
    )
    print("AuditEvent:", event.action, event.payload)
    return event


def example_contract_validation() -> None:
    """Execute the fail-closed timestamp validation path."""
    try:
        AuthContext(
            contract_version="v1",
            schema_id="invalid",  # type: ignore[arg-type]
            principal_id="user-123",
            principal_type="USER",
            roles=(),
            permissions=(),
            scopes=(),
            tenant_or_environment="dev",
            request_id=_REQUEST_ID,
            workflow_id=_WORKFLOW_ID,
            correlation_id=_CORRELATION_ID,
            issued_at=datetime.now(UTC),
        )
    except PydanticValidationError as error:
        print("Rejected invalid contract:", error.title)
    else:
        raise AssertionError("invalid schema identity was accepted")


if __name__ == "__main__":
    example_auth_context()
    example_audit_event()
    example_contract_validation()
