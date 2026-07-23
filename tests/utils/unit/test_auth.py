from datetime import UTC, datetime

import pytest
from app.utils import AuthContext, generate_id
from pydantic import ValidationError


def test_auth_context_rejects_naive_time() -> None:
    with pytest.raises(ValidationError):
        AuthContext(
            contract_version="v1",
            schema_id="utils.auth_context.v1",
            principal_id="user-1",
            principal_type="USER",
            roles=("operator",),
            permissions=("read",),
            scopes=("demo",),
            tenant_or_environment="test",
            request_id=generate_id("req"),
            workflow_id=generate_id("wf"),
            correlation_id=generate_id("cor"),
            issued_at=datetime.now(UTC).replace(tzinfo=None),
        )


def test_auth_context_rejects_stable_trace_identifier() -> None:
    """Reject deterministic hashes where the contract requires UUID4 traces."""
    with pytest.raises(ValidationError):
        AuthContext(
            contract_version="v1",
            schema_id="utils.auth_context.v1",
            principal_id="user-1",
            principal_type="USER",
            roles=("operator",),
            permissions=("read",),
            scopes=("demo",),
            tenant_or_environment="test",
            request_id="req-" + "a" * 64,
            workflow_id=generate_id("wf"),
            correlation_id=generate_id("cor"),
            issued_at=datetime.now(UTC),
        )


def test_auth_context_is_immutable_and_complete() -> None:
    context = AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="service-1",
        principal_type="SERVICE_ACCOUNT",
        roles=(),
        permissions=("read",),
        scopes=("demo",),
        tenant_or_environment="test",
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=datetime.now(UTC),
    )
    with pytest.raises(ValidationError):
        context.principal_id = "changed"
