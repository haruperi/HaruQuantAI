"""NFR-API-005: No secrets in logs, errors, traces, telemetry, or examples.

Verifies that canary secret values never appear in HTTP error envelopes,
response metadata, or the Prometheus metrics exposition surface.
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

# A clearly-fake canary value; if it appears in any output, redaction failed.
CANARY = "canary-secret-do-not-use-9f3a"


def _providers() -> dict[str, object]:
    return {
        name: lambda *_args, **_kwargs: (_args, _kwargs)
        for name in get_required_in_process_provider_names()
    }


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):  # type: ignore[misc]
    monkeypatch.setenv("DATABASE_URL", "sqlite:///nfr-005-redaction.db")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10.0")
    graph = build_in_process_api_graph(_providers())
    app = create_api_app(build_api_settings(), in_process_graph=graph)
    with TestClient(app) as c:
        yield c


class TestNfrApi005Redaction:
    """NFR-API-005: secret redaction verification."""

    @staticmethod
    def test_password_never_appears_in_error_envelope(client: TestClient) -> None:
        """A failed login does not echo the password in the error response."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent-user", "password": CANARY},
        )
        assert response.status_code in (400, 401, 403, 422)
        body_text = response.text
        assert CANARY not in body_text

    @staticmethod
    def test_bearer_token_never_appears_in_settings_response(
        client: TestClient,
    ) -> None:
        """The session token used for auth does not appear in the response body."""
        user = register_api_user(
            username="nfr-005-reader",
            password=CANARY,  # pragma: allowlist secret
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
        body_text = response.text
        # The session token must not leak into the response body.
        assert session.session_token not in body_text
        # The canary password must not leak.
        assert CANARY not in body_text

    @staticmethod
    def test_metrics_exposition_contains_no_secrets(client: TestClient) -> None:
        """The Prometheus exposition surface carries no secret values."""
        user = register_api_user(
            username="nfr-005-ops",
            password=CANARY,  # pragma: allowlist secret
            permissions=("ops:metrics:read",),
            request_id=generate_id("req"),
        )
        session = create_api_session(
            user, request_id=generate_id("req"), ttl_seconds=60
        )
        response = client.get(
            "/api/v1/metrics",
            headers={"Authorization": f"Bearer {session.session_token}"},
        )
        # Metrics may be disabled (404/503) or exposed (200); either way no secret.
        assert response.status_code in (200, 404, 503)
        if response.status_code == 200:
            assert CANARY not in response.text
            assert session.session_token not in response.text
