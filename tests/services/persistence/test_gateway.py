"""Tests for transactional gateway persistence (FEAT-PERSISTENCE-GATEWAY)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.contracts.gateway import GATEWAY_PERSISTENCE
from app.kernel.bootstrapper import Runtime
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
    DatabaseServiceImpl,
)
from app.services.persistence.gateway import (
    GatewayPersistenceConfig,
    GatewayPersistenceFeature,
    GatewayPersistenceService,
)


def _setup_service(tmp_path: Path) -> GatewayPersistenceService:
    """Set up an isolated in-memory or temporary database persistence service."""
    db_file = tmp_path / "test_gateway.db"
    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    service = GatewayPersistenceService(db)
    service.initialize_schema()
    return service


def test_gateway_persistence_config_validation() -> None:
    """Verify configuration validation bounds."""
    valid = GatewayPersistenceConfig(schema_version=1, default_idempotency_ttl_s=3600)
    assert valid.schema_version == 1
    assert valid.default_idempotency_ttl_s == 3600

    with pytest.raises(ValueError, match="schema_version must be >= 1"):
        GatewayPersistenceConfig(schema_version=0)

    with pytest.raises(ValueError, match="default_idempotency_ttl_s must be > 0"):
        GatewayPersistenceConfig(default_idempotency_ttl_s=0)


def test_gateway_settings_crud(tmp_path: Path) -> None:
    """Test getting and setting durable gateway settings."""
    service = _setup_service(tmp_path)

    # Initial state is None
    assert service.get_setting("remote_access") is None

    # Set value
    service.set_setting("remote_access", "true")
    assert service.get_setting("remote_access") == "true"

    # Upsert value
    service.set_setting("remote_access", "false")
    assert service.get_setting("remote_access") == "false"


def test_gateway_tokens(tmp_path: Path) -> None:
    """Test storing and verifying hashed API tokens."""
    service = _setup_service(tmp_path)

    token = "secret-token-12345"
    assert not service.verify_token(token)

    service.store_token(token, "test-client")
    assert service.verify_token(token)
    assert not service.verify_token("invalid-token")


def test_gateway_idempotency(tmp_path: Path) -> None:
    """Test idempotency key recording and retrieval."""
    service = _setup_service(tmp_path)

    key = "idem-key-abc-123"
    response_body = '{"success": true, "job_id": "job-1"}'

    # Initial lookup returns None
    assert service.get_idempotency_response(key) is None

    # First record succeeds
    recorded = service.record_idempotency_key(
        key, 202, response_body, expire_seconds=60
    )
    assert recorded is True

    # Duplicate record returns False
    recorded_again = service.record_idempotency_key(
        key, 202, response_body, expire_seconds=60
    )
    assert recorded_again is False

    # Lookup returns stored status and body
    cached = service.get_idempotency_response(key)
    assert cached is not None
    status, body = cached
    assert status == 202
    assert body == response_body


def test_gateway_idempotency_purge(tmp_path: Path) -> None:
    """Test purging expired idempotency records."""
    service = _setup_service(tmp_path)

    # Insert an expired record (negative TTL)
    service.record_idempotency_key("expired-key", 200, "{}", expire_seconds=-10)
    # Insert an active record
    service.record_idempotency_key("active-key", 200, "{}", expire_seconds=3600)

    # Purge expired keys
    deleted_count = service.purge_expired_idempotency()
    assert deleted_count == 1

    # Verify expired key is gone, active remains
    assert service.get_idempotency_response("expired-key") is None
    assert service.get_idempotency_response("active-key") is not None


def test_gateway_persistence_lifecycle(tmp_path: Path) -> None:
    """Test feature composition lifecycle."""
    db_file = tmp_path / "lifecycle.db"

    def db_factory() -> DatabaseFeature:
        return DatabaseFeature(DatabaseConfig(database_path=db_file))

    def gw_factory() -> GatewayPersistenceFeature:
        return GatewayPersistenceFeature()

    async def _run() -> None:
        async with Runtime((db_factory, gw_factory)) as runtime:
            pers = runtime.require(GATEWAY_PERSISTENCE)
            pers.set_setting("test_key", "test_val")
            assert pers.get_setting("test_key") == "test_val"

    asyncio.run(_run())
