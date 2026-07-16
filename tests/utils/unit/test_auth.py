from datetime import UTC, datetime

import pytest
from app.utils import AuthContext, generate_id
from pydantic import ValidationError


def _context(**overrides: object) -> AuthContext:
    values: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "utils.auth_context.v1",
        "principal_id": "user-1",
        "principal_type": "USER",
        "roles": ("operator",),
        "permissions": ("read",),
        "scopes": ("demo",),
        "tenant_or_environment": "test",
        "request_id": generate_id("req"),
        "workflow_id": generate_id("wf"),
        "correlation_id": generate_id("cor"),
        "issued_at": datetime.now(UTC),
    }
    values.update(overrides)
    return AuthContext.model_validate(values)


def test_auth_context_rejects_naive_time() -> None:
    with pytest.raises(ValidationError):
        _context(issued_at=datetime.now(UTC).replace(tzinfo=None))


def test_auth_context_is_immutable_and_complete() -> None:
    context = _context(principal_type="SERVICE_ACCOUNT", roles=())
    with pytest.raises(ValidationError):
        context.principal_id = "changed"
    with pytest.raises(ValidationError):
        _context(principal_type="ROBOT")
    with pytest.raises(ValidationError):
        _context(roles=("operator", "operator"))
