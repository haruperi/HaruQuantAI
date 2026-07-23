"""Producer-side compatibility evidence for the Utils-owned `AuthContext v1`.

Utils owns the contract definition; UI/API is the documented producer and every
governed domain is a consumer. This module proves the producer-side compatibility
surface that consumers bind to: the fixed compatibility keys, the exact required
field set, immutability, and lossless round-trip reconstruction. Consumer-side
acceptance is proven inside each consuming domain's own test suite, so this module
deliberately imports nothing from `app.services`.
"""

from datetime import UTC, datetime

import pytest
from app.utils import AuthContext, generate_id
from pydantic import ValidationError

_CONTRACT_VERSION = "v1"
_SCHEMA_ID = "utils.auth_context.v1"
_REQUIRED_FIELDS = frozenset(
    {
        "contract_version",
        "schema_id",
        "principal_id",
        "principal_type",
        "roles",
        "permissions",
        "scopes",
        "tenant_or_environment",
        "request_id",
        "workflow_id",
        "correlation_id",
        "issued_at",
    }
)


def _canonical_context() -> AuthContext:
    return AuthContext(
        contract_version=_CONTRACT_VERSION,
        schema_id=_SCHEMA_ID,
        principal_id="user-123",
        principal_type="USER",
        roles=("operator", "manager"),
        permissions=("backtest:run", "promote_source"),
        scopes=("portfolio:demo",),
        tenant_or_environment="test",
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=datetime.now(UTC),
    )


def test_auth_context_exposes_stable_compatibility_keys() -> None:
    """Pin the version and schema identity every consumer dispatches on."""
    context = _canonical_context()
    assert context.contract_version == _CONTRACT_VERSION
    assert context.schema_id == _SCHEMA_ID


def test_auth_context_exposes_exactly_the_required_consumer_fields() -> None:
    """Prove the consumed field set is complete and carries no extra field."""
    context = _canonical_context()
    assert set(type(context).model_fields) == _REQUIRED_FIELDS
    for field in _REQUIRED_FIELDS:
        assert getattr(context, field) is not None


def test_auth_context_round_trips_without_loss() -> None:
    """Reconstruct a producer-serialized context exactly, as a consumer would."""
    context = _canonical_context()
    rebuilt = AuthContext(**context.model_dump())
    assert rebuilt == context
    assert rebuilt.request_id == context.request_id
    assert rebuilt.roles == context.roles
    assert rebuilt.issued_at == context.issued_at


def test_auth_context_is_immutable_across_the_boundary() -> None:
    """Reject consumer-side mutation of a delivered context."""
    context = _canonical_context()
    with pytest.raises(ValidationError):
        context.principal_id = "changed"
    with pytest.raises(ValidationError):
        context.roles = ("admin",)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("contract_version", "v2"),
        ("schema_id", "utils.auth_context.v2"),
        ("principal_type", "ADMIN"),
    ],
)
def test_auth_context_rejects_incompatible_identity(field: str, value: str) -> None:
    """Fail closed on version, schema, or principal-type drift."""
    values = _canonical_context().model_dump()
    values[field] = value
    with pytest.raises(ValidationError):
        AuthContext(**values)


def test_auth_context_rejects_unknown_field() -> None:
    """Reject producer-side field additions that consumers cannot interpret."""
    values = _canonical_context().model_dump()
    values["impersonated_by"] = "user-999"
    with pytest.raises(ValidationError):
        AuthContext(**values)
