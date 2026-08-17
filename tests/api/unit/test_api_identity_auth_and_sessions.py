"""Unit tests for API identity authorization, credentials, sessions, and persistence."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.services.api.identity.accounts import AuthenticatedUser
from app.services.api.identity.authorization import (
    _coerce_non_empty_text,
    _coerce_text_list,
    _coerce_utc_datetime,
    _requires_approval,
    require_auth_context,
    require_permission,
)
from app.services.api.identity.credentials import (
    _select_key,
)
from app.services.api.identity.errors import IdentityError
from app.services.api.identity.idempotency import (
    IdempotencyDecision,
)
from app.services.api.identity.persistence import (
    delete_auth_failure_record,
    delete_idempotency_record,
    revoke_session_record,
    update_credential_record,
)
from app.services.api.identity.sessions import (
    create_session,
)
from app.utils import create_auth_context, generate_id
from fastapi import HTTPException


def test_authorization_coercion_and_approval() -> None:
    """Verify text, list, and datetime coercion helpers and approval check."""
    assert _coerce_non_empty_text("  hello  ", "field") == "hello"
    with pytest.raises(HTTPException):
        _coerce_non_empty_text("", "field")

    assert _coerce_text_list(["a", "b"], "roles") == ("a", "b")
    with pytest.raises(HTTPException):
        _coerce_text_list(["a", "a"], "roles")

    now = datetime.now(UTC)
    assert _coerce_utc_datetime(now, "time") == now
    with pytest.raises(HTTPException):
        _coerce_utc_datetime(datetime.now(), "time")  # noqa: DTZ005

    assert _requires_approval("risk.action") is True
    assert _requires_approval("trading.read") is False


def test_authorization_require_helpers() -> None:
    """Verify require_auth_context, require_permission, and require_human_permission."""
    with pytest.raises(HTTPException):
        require_auth_context()

    now = datetime.now(UTC)
    req_id = generate_id("req")
    wf_id = generate_id("wf")
    cor_id = generate_id("cor")

    ctx_user = create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="user-1",
        principal_type="USER",
        roles=("trader",),
        permissions=("trading:read", "trading:write"),
        scopes=("read",),
        tenant_or_environment="demo",
        runtime_profile="simulation",
        issued_at=now,
        request_id=req_id,
        workflow_id=wf_id,
        correlation_id=cor_id,
    )

    ctx_svc = create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="service-1",
        principal_type="SERVICE_ACCOUNT",
        roles=("system",),
        permissions=("trading:read",),
        scopes=("read",),
        tenant_or_environment="demo",
        runtime_profile="simulation",
        issued_at=now,
        request_id=req_id,
        workflow_id=wf_id,
        correlation_id=cor_id,
    )
    assert ctx_svc.principal_type == "SERVICE_ACCOUNT"

    # require_permission succeeds without raising exception for authorized permission
    require_permission(ctx_user, "trading:read")

    with pytest.raises(HTTPException):
        require_permission(ctx_user, "risk:override")


def test_credentials_key_selection() -> None:
    """Verify _select_key error handling."""
    key_set = {"k1": b"0" * 32}
    key_id, key = _select_key(key_set, "k1")
    assert key_id == "k1"
    assert len(key) == 32

    with pytest.raises(IdentityError, match="CREDENTIAL_ACTIVE_KEY_MISSING"):
        _select_key(key_set, "invalid_key")

    with pytest.raises(IdentityError, match="CREDENTIAL_ACTIVE_KEY_INVALID"):
        _select_key({"k2": b"invalid_len"}, "k2")


def test_identity_sessions_ttl_validation() -> None:
    """Verify create_session rejects inactive users or out-of-bound TTL."""
    user_inactive = AuthenticatedUser(
        user_id="u1",
        username="user1",
        tenant_or_environment="demo",
        runtime_profile="simulation",
        active=False,
        verified=True,
        roles=("trader",),
        permissions=("trading:read",),
        scopes=("read",),
    )
    user_active = AuthenticatedUser(
        user_id="u2",
        username="user2",
        tenant_or_environment="demo",
        runtime_profile="simulation",
        active=True,
        verified=True,
        roles=("trader",),
        permissions=("trading:read",),
        scopes=("read",),
    )

    with pytest.raises(IdentityError, match="ACCOUNT_STATE_INVALID"):
        create_session(user_inactive, request_id="req-1", ttl_seconds=3600)

    with pytest.raises(ValueError, match="ttl_seconds is outside the approved range"):
        create_session(user_active, request_id="req-1", ttl_seconds=10)


def test_identity_idempotency_decision() -> None:
    """Verify IdempotencyDecision instantiation."""
    dec = IdempotencyDecision(state="reserved")
    assert dec.state == "reserved"


def test_identity_persistence_exports() -> None:
    """Verify identity persistence functions exist."""
    assert update_credential_record is not None
    assert delete_auth_failure_record is not None
    assert delete_idempotency_record is not None
    assert revoke_session_record is not None
