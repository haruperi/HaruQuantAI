"""Tests for bearer-token sessions and auth enforcement."""

import logging
import time
from dataclasses import replace
from pathlib import Path

import pytest
from app.host.bootstrapper import build_services
from app.host.sessions import SessionError, SessionManager
from app.host.webserver import create_app
from starlette.testclient import TestClient

from tests.host.conftest import make_config


def test_login_and_verify_roundtrip() -> None:
    manager = SessionManager(None)

    token = manager.login("researcher", None)
    session = manager.verify(token)

    assert session is not None
    assert session.username == "researcher"
    assert session.expires_at > session.issued_at


def test_unknown_token_fails_verification() -> None:
    assert SessionManager(None).verify("no-such-token") is None


def test_required_password_rejects_wrong_and_missing() -> None:
    manager = SessionManager("s3cret")

    with pytest.raises(SessionError):
        manager.login("researcher", "wrong")
    with pytest.raises(SessionError):
        manager.login("researcher", None)
    assert manager.login("researcher", "s3cret")


def test_research_mode_issues_without_password() -> None:
    token = SessionManager(None).login("researcher", None)

    assert token


def test_expired_session_is_dropped() -> None:
    manager = SessionManager(None, ttl_seconds=0)
    token = manager.login("researcher", None)
    time.sleep(0.01)

    assert manager.verify(token) is None


def test_revoke_removes_session() -> None:
    manager = SessionManager(None)
    token = manager.login("researcher", None)

    manager.revoke(token)

    assert manager.verify(token) is None


def test_empty_username_is_rejected() -> None:
    with pytest.raises(SessionError):
        SessionManager(None).login("   ", None)


def test_api_requires_authorization(client: TestClient) -> None:
    response = client.get("/api/v1/settings")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_api_accepts_valid_token(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/settings", headers=auth_headers)

    assert response.status_code == 200


def test_login_rejects_bad_credentials_when_password_set(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    locked = replace(config, password="s3cret")  # pragma: allowlist secret
    app = create_app(build_services(locked), logging.getLogger("tests.host"))
    strict_client = TestClient(app)

    bad = strict_client.post(
        "/api/v1/auth/login", json={"username": "u", "password": "no"}
    )
    good = strict_client.post(
        "/api/v1/auth/login",
        json={"username": "u", "password": "s3cret"},  # pragma: allowlist secret
    )

    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "UNAUTHORIZED"
    assert good.status_code == 200
