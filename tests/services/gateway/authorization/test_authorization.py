"""Functional tests for transport authorization service."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.contracts.gateway import AuthenticationError, GatewayError
from app.services.gateway.authorization import (
    AuthorizationConfig,
    AuthorizationService,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseServiceImpl,
)
from app.services.persistence.gateway import (
    GatewayPersistenceService,
)


def test_loopback_access_permitted_by_default() -> None:
    """Verify loopback addresses are allowed when remote access is disabled."""
    service = AuthorizationService(AuthorizationConfig())

    # 127.0.0.1
    ctx1 = service.authenticate_request({}, "127.0.0.1")
    assert ctx1.authenticated
    assert ctx1.is_loopback
    assert "write" in ctx1.scopes

    # localhost
    ctx2 = service.authenticate_request({}, "localhost")
    assert ctx2.authenticated
    assert ctx2.is_loopback

    # ::1
    ctx3 = service.authenticate_request({}, "::1")
    assert ctx3.authenticated
    assert ctx3.is_loopback

    # testclient is NOT loopback by default
    with pytest.raises(AuthenticationError, match="Remote access is disabled"):
        service.authenticate_request({}, "testclient")


def test_custom_loopback_hosts_permitted() -> None:
    """Verify custom loopback hosts can be explicitly configured."""
    config = AuthorizationConfig(loopback_hosts=frozenset({"127.0.0.1", "testclient"}))
    service = AuthorizationService(config)
    ctx = service.authenticate_request({}, "testclient")
    assert ctx.authenticated
    assert ctx.is_loopback


def test_remote_access_rejected_when_disabled() -> None:
    """Verify non-loopback clients are rejected if remote access is false."""
    service = AuthorizationService(AuthorizationConfig(remote_access_allowed=False))

    with pytest.raises(AuthenticationError, match="Remote access is disabled"):
        service.authenticate_request({}, "192.168.1.50")


def test_remote_access_permitted_when_enabled() -> None:
    """Verify non-loopback clients are accepted when remote access is true."""
    service = AuthorizationService(AuthorizationConfig(remote_access_allowed=True))

    ctx = service.authenticate_request({}, "192.168.1.50")
    assert ctx.authenticated
    assert not ctx.is_loopback
    assert ctx.scopes == ("read",)


def test_token_authentication_headers() -> None:
    """Verify token validation against static tokens and multiple header schemes."""
    config = AuthorizationConfig(
        token_auth_enabled=True,
        static_tokens=("valid-secret-key",),
    )
    service = AuthorizationService(config)

    # Missing token fails
    with pytest.raises(
        AuthenticationError, match="Missing required authentication credentials"
    ):
        service.authenticate_request({}, "127.0.0.1")

    # Invalid token fails
    with pytest.raises(AuthenticationError, match="Invalid authentication token"):
        service.authenticate_request({"X-API-Key": "wrong-key"}, "127.0.0.1")

    # Custom header (X-API-Key)
    ctx1 = service.authenticate_request({"X-API-Key": "valid-secret-key"}, "127.0.0.1")
    assert ctx1.authenticated

    # SQX reference header (sq-auth-token)
    ctx2 = service.authenticate_request(
        {"sq-auth-token": "valid-secret-key"}, "127.0.0.1"
    )
    assert ctx2.authenticated

    # Bearer header
    ctx3 = service.authenticate_request(
        {"Authorization": "Bearer valid-secret-key"}, "127.0.0.1"
    )
    assert ctx3.authenticated


def test_remote_access_toggle() -> None:
    """Verify set_remote_access dynamically toggles permission."""
    service = AuthorizationService(AuthorizationConfig(remote_access_allowed=False))
    assert not service.is_remote_access_enabled()

    service.set_remote_access(True)
    assert service.is_remote_access_enabled()
    ctx = service.authenticate_request({}, "10.0.0.1")
    assert ctx.authenticated

    service.set_remote_access(False)
    assert not service.is_remote_access_enabled()
    with pytest.raises(AuthenticationError, match="Remote access is disabled"):
        service.authenticate_request({}, "10.0.0.1")


def test_issue_token(tmp_path: Path) -> None:
    """Verify issue_token generates and persists verifiable tokens."""
    # Test without persistence raises GatewayError
    service_no_pers = AuthorizationService(AuthorizationConfig())
    with pytest.raises(GatewayError, match="Cannot issue token"):
        service_no_pers.issue_token("test-key")

    # Test with persistence
    db = DatabaseServiceImpl(DatabaseConfig(database_path=tmp_path / "auth_test.db"))
    pers = GatewayPersistenceService(db)
    pers.initialize_schema()

    config = AuthorizationConfig(token_auth_enabled=True)
    service = AuthorizationService(config, persistence=pers)

    token = service.issue_token("admin-key", scopes=("read", "write"))
    assert isinstance(token, str)
    assert len(token) > 20

    # Request with this issued token from loopback should authenticate
    ctx_loopback = service.authenticate_request({"X-API-Key": token}, "127.0.0.1")
    assert ctx_loopback.authenticated
    assert ctx_loopback.client_id.startswith("token-client-")

    # Non-loopback fails if remote access is disabled
    with pytest.raises(AuthenticationError, match="Remote access is disabled"):
        service.authenticate_request({"X-API-Key": token}, "192.168.1.100")

    # Non-loopback succeeds when remote access is enabled
    service.set_remote_access(True)
    ctx_remote = service.authenticate_request({"X-API-Key": token}, "192.168.1.100")
    assert ctx_remote.authenticated
