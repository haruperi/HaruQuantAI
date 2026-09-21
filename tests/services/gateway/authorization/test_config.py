"""Tests for gateway authorization configuration."""

from __future__ import annotations

import pytest
from app.services.gateway.authorization import AuthorizationConfig


def test_authorization_config_defaults() -> None:
    """Verify default authorization configuration values."""
    config = AuthorizationConfig()
    assert not config.token_auth_enabled
    assert not config.remote_access_allowed
    assert config.static_tokens == ()
    assert config.auth_header_name == "X-API-Key"
    assert config.loopback_hosts == frozenset({"127.0.0.1", "::1", "localhost"})


def test_authorization_config_validation() -> None:
    """Verify authorization config validation on empty header name or hosts."""
    with pytest.raises(ValueError, match="auth_header_name cannot be empty"):
        AuthorizationConfig(auth_header_name="")

    with pytest.raises(ValueError, match="loopback_hosts cannot be empty"):
        AuthorizationConfig(loopback_hosts=frozenset())
