"""Executable shared-contract examples."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import AuditEvent, AuthContext, generate_id, redact_mapping_value
from pydantic import ValidationError as PydanticValidationError


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_utils_001_auth_context() -> None:
    """FR-UTL-001: Construct and display bounded AuthContext identity evidence."""
    _header("Example 1: AuthContext Construction")
    context = AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="service-demo",
        principal_type="SERVICE_ACCOUNT",
        roles=("operator",),
        permissions=("data:read",),
        scopes=("demo",),
        tenant_or_environment="test",
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    print("AuthContext:", context.principal_type, context.tenant_or_environment)


def fr_utils_002_audit_event() -> None:
    """FR-UTL-002: Construct and display redacted AuditEvent metadata."""
    _header("Example 2: AuditEvent Construction")
    payload = redact_mapping_value({"status": "accepted", "token": "demo"}).value
    assert isinstance(payload, dict)
    event = AuditEvent(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=generate_id("evt"),
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        domain="usage",
        action="constructed",
        request_id=generate_id("req"),
        correlation_id=generate_id("cor"),
        payload=payload,
    )
    print("AuditEvent:", event.domain, event.action, event.payload["token"])


def fr_utils_003_contract_validation() -> None:
    """FR-UTL-003: Demonstrate fail-closed contract timestamp validation."""
    _header("Example 3: Contract Validation")
    try:
        AuthContext(
            contract_version="v1",
            schema_id="utils.auth_context.v1",
            principal_id="service-demo",
            principal_type="SERVICE_ACCOUNT",
            roles=(),
            permissions=(),
            scopes=(),
            tenant_or_environment="test",
            request_id=generate_id("req"),
            workflow_id=generate_id("wf"),
            correlation_id=generate_id("cor"),
            issued_at=datetime(2026, 1, 1, tzinfo=UTC).replace(tzinfo=None),
        )
    except PydanticValidationError:
        print("Contract validation: naive timestamp rejected")


def main() -> None:
    """Run all shared-contract examples."""
    fr_utils_001_auth_context()
    fr_utils_002_audit_event()
    fr_utils_003_contract_validation()


if __name__ == "__main__":
    main()
