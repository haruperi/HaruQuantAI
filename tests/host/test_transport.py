"""Host gateway authorization, metadata safety, and network diagnostics."""

import asyncio
import json
import socket
import sqlite3
from contextlib import closing
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from app.host.persistence import HostPersistence
from app.host.session import SessionManager
from app.host.transport import ServletConnection, TransportError
from app.main import create_app
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


@pytest.fixture
def gateway(tmp_path):
    path = tmp_path / "transport.db"
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript("""
            CREATE TABLE host_settings (
                scope TEXT NOT NULL, key TEXT NOT NULL, value_json TEXT NOT NULL,
                schema_version INTEGER NOT NULL DEFAULT 1, updated_at_utc TEXT NOT NULL,
                PRIMARY KEY(scope,key));
            CREATE TABLE host_session (
                session_id TEXT PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL, peer_id TEXT NOT NULL,
                created_at_utc TEXT NOT NULL, expires_at_utc TEXT NOT NULL,
                revoked_at_utc TEXT, status TEXT NOT NULL);
            CREATE TABLE host_entities (
                entity_id TEXT NOT NULL, entity_type TEXT NOT NULL, scope TEXT NOT NULL,
                payload TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1,
                created_at_utc TEXT NOT NULL, updated_at_utc TEXT NOT NULL,
                PRIMARY KEY(entity_id,entity_type));
        """)
    gateway = HostPersistence(path)
    response = gateway.create_records(
        "host_settings",
        [
            {
                "scope": "application",
                "key": "user_access",
                "value_json": json.dumps(
                    {
                        "username": "tester",
                        "password_hash": SessionManager.hash_password("password"),
                    }
                ),
                "updated_at_utc": "unchanged",
            },
            {
                "scope": "application",
                "key": "app_general",
                "value_json": json.dumps(
                    {
                        "theme": "dark",
                        "password": "private-setting",
                        "nested": {"api_key": "private-key"},
                    }
                ),
                "updated_at_utc": "unchanged",
            },
            {
                "scope": "_system",
                "key": "revision",
                "value_json": "1",
                "updated_at_utc": "unchanged",
            },
        ],
    )
    assert response["success"]
    return gateway


@pytest.fixture
def client(gateway):
    with TestClient(create_app(gateway)) as client:
        yield client


def sign_in(client):
    response = client.post("/api/v1/auth/login", json={"password": "password"})
    assert response.status_code == 200, response.text
    return response.json()["data"]["token"]


def metadata(**overrides):
    return {
        "name": "Test",
        "provider": "test",
        "endpoint": "https://example.test/",
        **overrides,
    }


def test_routes_are_installed(client):
    schema = client.get("/openapi.json").json()
    for path in (
        "auth",
        "auth/login",
        "sessions/me",
        "status",
        "readiness",
        "app-loaded",
        "about",
        "constants",
        "specs",
        "settings",
        "settings/catalogue",
        "settings/secrets",
        "auth/account",
        "connections",
        "connections/test",
        "connections/{connection_id}",
        "connections/{connection_id}/test",
    ):
        assert f"/api/v1/{path}" in schema["paths"]
    assert client.get("/api/v1/status").status_code == 200
    assert client.get("/api/v1/readiness").json()["data"]["ready"]
    assert client.get("/api/v1/settings").status_code == 401


def test_ui_login_restart_and_logout(gateway, client):
    assert (
        client.post("/api/v1/auth/login", json={"password": "wrong"}).status_code == 401
    )
    token = sign_in(client)
    assert client.get("/api/v1/sessions/me").json()["data"]["peer_id"].startswith("ui:")
    with TestClient(create_app(gateway)) as restarted:
        restarted.cookies.update(client.cookies)
        assert restarted.get("/api/v1/sessions/me").status_code == 200
        assert (
            restarted.post("/api/v1/auth", json={"action": "logout"}).status_code == 200
        )
    assert (
        client.get(
            "/api/v1/sessions/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 401
    )


def test_cli_token_cannot_access_ui_gateway(client, gateway):
    sign_in(client)
    token = SessionManager(gateway).create_session("tester", "cli")
    response = client.get(
        "/api/v1/settings", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_bearer_token_without_cookie_authenticates_ui(gateway):
    with TestClient(create_app(gateway)) as client:
        token = SessionManager(gateway).create_session("tester", "ui:testbrowser")
        res = client.get(
            "/api/v1/sessions/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        assert res.json()["data"]["peer_id"] == "ui:testbrowser"
        # Also verify that CLI tokens without cookies are denied
        cli_token = SessionManager(gateway).create_session("tester", "cli")
        res_cli = client.get(
            "/api/v1/settings", headers={"Authorization": f"Bearer {cli_token}"}
        )
        assert res_cli.status_code == 401


def test_settings_projection_and_revision_guard(client):
    sign_in(client)
    for path in ("settings", "settings/catalogue", "auth/account"):
        response = client.get(f"/api/v1/{path}")
        assert response.status_code == 200
        assert "private-setting" not in response.text
        assert "private-key" not in response.text
        assert "pbkdf2_sha256" not in response.text
    response = client.put(
        "/api/v1/settings",
        json={"expected_revision": 1, "changes": {"app.general": {"theme": "light"}}},
    )
    assert response.status_code == 200, response.text
    assert (
        response.json()["data"]["values"]["application"]["app_general"]["theme"]
        == "light"
    )
    assert (
        client.put(
            "/api/v1/settings",
            json={
                "expected_revision": 1,
                "changes": {"app.general": {"theme": "dark"}},
            },
        ).status_code
        == 409
    )
    assert (
        client.put(
            "/api/v1/settings",
            json={
                "expected_revision": 2,
                "changes": {"user_access": {"username": "attacker"}},
            },
        ).status_code
        == 422
    )


def test_connections_routes_and_inline_secrets_rejected(client):
    sign_in(client)
    response = client.post("/api/v1/connections", json=metadata())
    assert response.status_code == 200
    connection_id = response.json()["data"]["connection_id"]
    assert len(client.get("/api/v1/connections").json()["data"]) == 1
    assert (
        client.post(
            "/api/v1/connections", json=metadata(password="private")
        ).status_code
        == 422
    )
    assert client.post(f"/api/v1/connections/{connection_id}/test").status_code == 503
    assert client.delete(f"/api/v1/connections/{connection_id}").status_code == 200
    assert client.delete(f"/api/v1/connections/{connection_id}").status_code == 404


def test_vault_reference_ownership_and_revocation(gateway):
    vault = Mock()
    vault.resolve.return_value = "private-secret"
    service = ServletConnection(gateway, vault=vault)
    record = service.save(metadata(vault_refs={"api_key": "vault:one"}))
    with pytest.raises(TransportError, match="already owned"):
        service.save(metadata(vault_refs={"api_key": "vault:one"}))
    vault.revoke.side_effect = RuntimeError("vault offline")
    with pytest.raises(RuntimeError, match="vault offline"):
        service.delete(record["connection_id"])
    assert len(service.list()) == 1
    vault.revoke.side_effect = None
    assert service.delete(record["connection_id"])["deleted"]
    assert service.list() == []


def test_provider_tester_receives_secrets_but_result_does_not(gateway):
    vault = Mock()
    vault.resolve.return_value = "private-secret"
    tester = AsyncMock(return_value=True)
    service = ServletConnection(gateway, vault=vault, testers={"test": tester})
    record = service.save(metadata(vault_refs={"api_key": "vault:one"}))
    response = asyncio.run(
        service.test_connection(connection_id=record["connection_id"])
    )
    assert response["authenticated"]
    assert response["latency_ms"] >= 0
    assert tester.call_args.args[0]["credentials"]["api_key"] == "private-secret"
    assert "private-secret" not in json.dumps(response)


def test_http_probe_reachability_and_loss():
    def respond(request):
        if request.url.host == "offline.test":
            raise httpx.ConnectError("offline")
        return httpx.Response(401)

    service = ServletConnection(http_transport=httpx.MockTransport(respond))
    result = asyncio.run(service.ping_endpoint("http://localhost/"))
    assert result["reachable"] and not result["healthy"]
    loss = asyncio.run(service.check_latency("https://offline.test/", probes=2))
    assert loss["lost"] == 2
    assert loss["packet_loss_percent"] == 100
    assert loss["mean_ms"] is None
    with pytest.raises(ValueError, match="endpoint"):
        asyncio.run(service.ping_endpoint("https://user:password@example.test/"))
    with pytest.raises(ValueError, match="probes"):
        asyncio.run(service.check_latency("http://localhost/", probes=0))


def test_dns_and_socket_diagnosis(monkeypatch):
    async def run():
        loop = asyncio.get_running_loop()
        monkeypatch.setattr(
            loop, "getaddrinfo", AsyncMock(side_effect=socket.gaierror())
        )
        service = ServletConnection()
        assert (await service.diagnose_network("https://example.test/"))[
            "dns"
        ] == "failed"
        monkeypatch.setattr(
            loop,
            "getaddrinfo",
            AsyncMock(
                return_value=[
                    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
                ]
            ),
        )
        monkeypatch.setattr(
            asyncio, "open_connection", AsyncMock(side_effect=ConnectionRefusedError())
        )
        assert (await service.diagnose_network("https://example.test/")) == {
            "dns": "ok",
            "socket": "failed",
        }

    asyncio.run(run())


def test_websocket_auth_and_revocation(client):
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/api/v1/ws"):
        pytest.fail("Unauthenticated socket was accepted")
    sign_in(client)
    with client.websocket_connect("/api/v1/ws") as websocket:
        websocket.send_text("ping")
        assert websocket.receive_json()["data"]["type"] == "pong"
        client.post("/api/v1/auth", json={"action": "logout"})
        websocket.send_text("ping")
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_json()


def test_capability_denial_and_secret_settings_write(client, gateway):
    sign_in(client)
    response = client.put(
        "/api/v1/settings/secrets",
        json={
            "expected_revision": 1,
            "changes": {
                "app.general": {"password": "new-private-setting", "theme": "light"}
            },
        },
    )
    assert response.status_code == 200
    assert "new-private-setting" not in response.text
    client.app.state.sessions = SessionManager(
        gateway, scope_resolver=lambda _: ("settings:read",)
    )
    assert client.get("/api/v1/settings").status_code == 200
    assert client.post("/api/v1/connections", json=metadata()).status_code == 403


def test_account_password_change_requires_current_password(client):
    sign_in(client)
    body = {
        "expected_revision": 1,
        "current_password": "wrong",
        "new_password": "replacement",
    }
    assert client.put("/api/v1/auth/account", json=body).status_code == 401
    body["current_password"] = "password"
    assert client.put("/api/v1/auth/account", json=body).status_code == 200
    assert (
        client.post("/api/v1/auth/login", json={"password": "password"}).status_code
        == 401
    )
    assert (
        client.post("/api/v1/auth/login", json={"password": "replacement"}).status_code
        == 200
    )


def test_diagnostics_and_resources_endpoints(client):
    sign_in(client)
    for path in ("diagnostics", "resources"):
        response = client.get(f"/api/v1/{path}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert "status" in data
        assert "hardware" in data
        assert "memory_watchdog" in data


def test_events_and_sse_endpoints(client):
    sign_in(client)
    resp = client.get("/api/v1/events/channels")
    assert resp.status_code == 200
    assert "core_channels" in resp.json()["data"]

    pub = client.post(
        "/api/v1/events/publish",
        json={"channel": "system", "event_type": "notice", "payload": {"k": "v"}},
    )
    assert pub.status_code == 200

    snap = client.get("/api/v1/events/snapshot?channel=system")
    assert snap.status_code == 200

    with client.stream(
        "GET", "/api/v1/events?channels=system&since_cursor=0&limit=1"
    ) as sse:
        assert sse.status_code == 200
        assert "text/event-stream" in sse.headers.get("content-type", "")


def test_connection_test_and_constants_classes():
    from app.host.transport import ConnectionTest, ServletConstants, TransportCLI

    parsed = ConnectionTest._parse("https://example.com:8443/path")
    assert parsed[1] == "example.com"
    assert parsed[2] == 8443

    consts = ServletConstants().get_constants()
    assert consts["application"] == "HaruQuantAI"
    specs = ServletConstants().get_system_specs()
    assert "cpu_cores" in specs

    assert TransportCLI.run(["--test-bus"]) == 0
