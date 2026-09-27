"""Password, peer, runtime-key, expiry and revocation boundaries."""

import pytest
from app.host.config import HostSettings
from app.host.security import hash_password, is_loopback, verify_password
from app.host.sessions import SessionError, SessionManager
from app.persistence.host import prepare_boot_database
from pydantic import SecretStr


def manager(config: HostSettings) -> SessionManager:
    prepare_boot_database(config.database_path)
    return SessionManager(config)


def test_local_operator_and_durable_revocation(host_config):
    authority = manager(host_config)
    token = authority.login("operator", None, peer="127.0.0.1")
    verified = authority.verify(token)
    assert verified is not None and verified.username == "operator"
    assert authority.verify("bad") is None
    assert authority.verify(token + "x") is None
    authority.revoke(token)
    assert authority.verify(token) is None


def test_password_and_retry_limits(host_config):
    authority = manager(
        host_config.model_copy(update={"password": SecretStr("example-password")})
    )
    with pytest.raises(SessionError):
        authority.login("operator", "bad", peer="127.0.0.1")
    token = authority.login("operator", "example-password", peer="127.0.0.1")
    assert authority.verify(token)
    for _ in range(6):
        with pytest.raises(SessionError):
            authority.login("operator", "bad", peer="127.0.0.2")
    with pytest.raises(SessionError, match="Retry"):
        authority.login("operator", "example-password", peer="127.0.0.2")


def test_remote_peer_cannot_auto_login(host_config):
    authority = manager(host_config)
    for username, peer in (("operator", "198.51.100.1"), ("unknown", "127.0.0.1")):
        with pytest.raises(SessionError):
            authority.login(username, None, peer=peer)


def test_expiry_and_restart_invalidate_tokens(host_config, monkeypatch):
    authority = manager(host_config)
    token = authority.login("operator", None, peer="127.0.0.1")
    assert SessionManager(host_config).verify(token) is None
    monkeypatch.setattr("app.host.sessions.time.time", lambda: 10**12)
    assert authority.verify(token) is None


def test_existing_credentials_cannot_be_silently_replaced(host_config):
    manager(host_config)
    with pytest.raises(SessionError):
        SessionManager(
            host_config.model_copy(update={"password": SecretStr("new-password")})
        )


def test_hash_round_trip_and_malformed_hash():
    stored = hash_password("test-pass")
    assert stored != hash_password("test-pass")
    assert verify_password("test-pass", stored)
    assert not verify_password("bad", stored)
    assert not verify_password("bad", "invalid")
    assert is_loopback("::1")
    assert not is_loopback("localhost")


def test_auth_endpoints_and_redaction(client, auth_headers):
    assert client.get("/api/v1/settings").status_code == 401
    assert client.get("/api/v1/settings", headers=auth_headers).status_code == 200
    assert client.post("/api/v1/auth/login", json={"username": []}).status_code == 401
    assert (
        client.post("/api/v1/auth/login", json={"username": "unknown"}).status_code
        == 401
    )


def test_haruquantai_and_operator_alias_login(host_config):
    authority = manager(host_config)
    token1 = authority.login("haruquantai", None, peer="127.0.0.1")
    verified1 = authority.verify(token1)
    assert verified1 is not None and verified1.username == "haruquantai"

    token2 = authority.login("operator", None, peer="127.0.0.1")
    verified2 = authority.verify(token2)
    assert verified2 is not None and verified2.username == "operator"


def test_credentials_primitives_and_auth_store(tmp_path):
    from app.host.security import hash_credentials, verify_credentials
    from app.persistence.host import AuthStore

    path = tmp_path / "auth_test.db"
    prepare_boot_database(path)
    store = AuthStore(path)

    hash_val, salt_val = hash_credentials("mypassword")
    assert verify_credentials("mypassword", hash_val, salt_val)
    assert not verify_credentials("wrongpassword", hash_val, salt_val)
    assert not verify_credentials("mypassword", hash_val, "invalid-hex")

    store.provision("custom_user", f"{salt_val}:{hash_val}")
    store.provision("custom_user", "different_hash")
    exists, stored = store.credential("custom_user")
    assert exists is True
    assert stored == f"{salt_val}:{hash_val}"
