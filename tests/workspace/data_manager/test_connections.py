"""Connection rotation and provider-test outcomes without real credentials/network."""

import asyncio
import json
import sqlite3
from contextlib import closing
from unittest.mock import AsyncMock, Mock, patch

from app.core.host.transport import ServletConnection
from app.host.persistence import HostPersistence
from app.workspace.data_manager.sources.connections import (
    test_provider_access as provider_access,
)


class MemoryVault:
    def __init__(self):
        self.values = {}

    def store(self, secret):
        reference = f"owned-{len(self.values)}"
        self.values[reference] = secret
        return reference

    def resolve(self, reference):
        return self.values[reference]

    def revoke(self, reference):
        self.values.pop(reference, None)


def test_credential_rotation_keeps_only_public_references(tmp_path):
    path = tmp_path / "connections.db"
    with closing(sqlite3.connect(path)) as database:
        database.execute(
            "CREATE TABLE host_entities (entity_id TEXT,entity_type TEXT,scope TEXT,payload TEXT,created_at_utc TEXT,updated_at_utc TEXT,PRIMARY KEY(entity_id,entity_type))"
        )
    gateway = HostPersistence(path)
    vault = MemoryVault()
    service = ServletConnection(gateway, vault=vault)
    first = service.save_connection(
        {
            "name": "Feed",
            "provider": "yahoo",
            "endpoint": "https://query1.finance.yahoo.com",
            "credentials": {"password": "first-test-secret"},
        }
    )
    old = first["vault_refs"]["password"]
    second = service.save_connection(
        {"name": "Updated", "credentials": {"password": "second-test-secret"}},
        connection_id=first["connection_id"],
    )
    assert old not in vault.values
    assert vault.resolve(second["vault_refs"]["password"]) == "second-test-secret"
    assert "test-secret" not in json.dumps(service.list_connections())
    saved = service.save_connection(
        {"name": "Updated again"}, connection_id=first["connection_id"]
    )
    assert saved["vault_refs"] == second["vault_refs"]


def test_endpoint_denial_does_not_report_authenticated():
    response = Mock(status_code=403)
    client = AsyncMock()
    client.get.return_value = response
    with patch(
        "app.workspace.data_manager.sources.connections.httpx.AsyncClient"
    ) as factory:
        factory.return_value.__aenter__.return_value = client
        result = asyncio.run(
            provider_access(
                {
                    "provider": "yahoo",
                    "endpoint": "https://example.test",
                    "credentials": {},
                }
            )
        )
    assert result["entitlement"] == "denied" and result["authenticated"] is None
