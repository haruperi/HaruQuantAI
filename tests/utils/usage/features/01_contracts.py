"""Executable shared-contract examples."""

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    build_event_envelope,
    create_audit_event,
    create_auth_context,
    find_sequence_gap,
    generate_id,
    get_audit_event_type,
    get_auth_context_type,
    is_duplicate_event,
    parse_event_envelope,
    redact_mapping_value,
)
from pydantic import ValidationError as PydanticValidationError


def _feature_header(title: str) -> None:
    """Print feature title and module flow banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_utils_002_audit_event() -> None:
    """FR-UTL-002: Stage 1 & 3 — Redact untrusted payload and construct immutable AuditEvent."""
    _header(
        "Stage 1 & 3: AuditEvent Construction - Untrusted Mapping -> Immutable AuditEvent (FR-UTL-002)"
    )
    payload = redact_mapping_value({"status": "accepted", "token": "demo"}).value
    assert isinstance(payload, dict)
    event = create_audit_event(
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
    assert isinstance(event, get_audit_event_type())
    print(_format_result(event))
    print(
        f"Data -> domain='{event.domain}', action='{event.action}', token='{event.payload['token']}'"
    )


def fr_utils_003_contract_validation() -> None:
    """FR-UTL-003: Stage 2 — Demonstrate fail-closed strict contract-field validation."""
    _header("Stage 2: Strict Validation - Contract Field Validation (FR-UTL-003)")
    try:
        create_auth_context(
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
    except PydanticValidationError as exc:
        print(_format_result(exc))
        print(
            f"Data -> Contract validation: naive timestamp rejected ({exc.error_count()} validation error)"
        )


def fr_utils_001_auth_context() -> None:
    """FR-UTL-001: Stage 3 — Construct immutable AuthContext identity evidence."""
    _header("Stage 3: Immutable Context - AuthContext Construction (FR-UTL-001)")
    context = create_auth_context(
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
    assert isinstance(context, get_auth_context_type())
    print(_format_result(context))
    print(
        f"Data -> principal_id='{context.principal_id}', principal_type='{context.principal_type}', tenant='{context.tenant_or_environment}'"
    )


def main() -> None:
    """Run all shared-contract examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-UTIL-00 — contracts/ — Shared Context and Audit Contracts\n\n"
        "Purpose: Define the immutable authenticated principal, trace context,\n"
        "and redacted audit envelope shared across every domain.\n\n"
        "Module flow:\n"
        "-> untrusted trace/identity mapping\n"
        "-> strict contract-field validation\n"
        "-> immutable AuthContext / AuditEvent"
    )

    # Stage 1 & 3: Untrusted mapping and AuditEvent construction
    fr_utils_002_audit_event()

    # Stage 2: Strict contract-field validation fail-closed check
    fr_utils_003_contract_validation()

    # Stage 3: Immutable AuthContext output construction
    fr_utils_001_auth_context()

    envelope = build_event_envelope(
        event_id="evt-demo",
        source_id="usage",
        source_sequence=1,
        correlation_id="cor-demo",
        causation_id=None,
        deduplication_key="dedupe-demo",
        emitted_at=datetime(2026, 1, 1, tzinfo=UTC),
        payload={"status": "accepted"},
    )
    parsed = parse_event_envelope(envelope)
    assert not is_duplicate_event(parsed, set())
    assert find_sequence_gap(parsed, expected_sequence=1) is None


if __name__ == "__main__":
    main()
