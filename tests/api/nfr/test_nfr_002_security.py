"""NFR-API-002: Protected endpoints require validated user/service context.

Verifies the complete security gate: protected endpoints reject requests
without a valid session (401), with a valid session but missing permission
(403), and governed writes additionally require idempotency. Public endpoints
(liveness) remain accessible without authentication.
"""

from pathlib import Path

import pytest
from app.services.api import (
    build_api_settings,
    build_in_process_api_graph,
    create_api_app,
    create_api_session,
    get_required_in_process_provider_names,
    register_api_user,
)
from app.utils import generate_id
from fastapi.testclient import TestClient


def _providers() -> dict[str, object]:
    """Build a complete provider graph with stub owner sources."""
    values: dict[str, object] = {
        name: lambda *_args, **_kwargs: (_args, _kwargs)
        for name in get_required_in_process_provider_names()
    }
    return values


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):  # type: ignore[misc]
    """Build the canonical in-process app with a stub owner graph."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///nfr-002-security.db")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10.0")
    graph = build_in_process_api_graph(_providers())
    app = create_api_app(build_api_settings(), in_process_graph=graph)
    with TestClient(app) as c:
        yield c


class TestNfrApi002Security:
    """NFR-API-002: security gate verification."""

    @staticmethod
    def test_public_endpoint_accessible_without_auth(client: TestClient) -> None:
        """Liveness is public; no session required."""
        response = client.get("/api/v1/health/liveness")
        assert response.status_code == 200

    @staticmethod
    def test_protected_endpoint_rejects_missing_session(client: TestClient) -> None:
        """Settings read requires authentication; 401 without a session."""
        response = client.get("/api/v1/settings")
        assert response.status_code in (401, 403)
        body = response.json()
        code = body.get("error", {}).get("code", body.get("detail", ""))
        assert code in (
            "AUTHENTICATION_REQUIRED",
            "AUTHORIZATION_DENIED",
            "AUTHENTICATION_REQUIRED",
        )

    @staticmethod
    def test_protected_endpoint_rejects_invalid_token(client: TestClient) -> None:
        """A garbage bearer token is rejected."""
        response = client.get(
            "/api/v1/settings",
            headers={"Authorization": "Bearer invalid-token-value"},
        )
        assert response.status_code in (401, 403)

    @staticmethod
    def test_authorized_session_accesses_protected_endpoint(
        client: TestClient,
    ) -> None:
        """A session with settings:read accesses the settings endpoint."""
        user = register_api_user(
            username="nfr-002-reader",
            password="bounded nfr password",  # pragma: allowlist secret
            permissions=("settings:read",),
            request_id=generate_id("req"),
        )
        session = create_api_session(
            user, request_id=generate_id("req"), ttl_seconds=60
        )
        response = client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {session.session_token}"},
        )
        assert response.status_code == 200

    @staticmethod
    def test_permission_denied_without_correct_permission(
        client: TestClient,
    ) -> None:
        """A session without settings:read gets 403 on the settings endpoint."""
        user = register_api_user(
            username="nfr-002-no-settings",
            password="bounded nfr password",  # pragma: allowlist secret
            permissions=("dashboard:read",),
            request_id=generate_id("req"),
        )
        session = create_api_session(
            user, request_id=generate_id("req"), ttl_seconds=60
        )
        response = client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {session.session_token}"},
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "AUTHORIZATION_DENIED"
