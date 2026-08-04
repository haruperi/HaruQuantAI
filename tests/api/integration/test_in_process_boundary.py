"""HTTP evidence for the in-process owner composition boundary."""

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


def _providers(dashboard_source: object) -> dict[str, object]:
    """Build a complete graph with one observable dashboard owner source."""
    values: dict[str, object] = {
        name: lambda *args, **kwargs: (args, kwargs)
        for name in get_required_in_process_provider_names()
    }
    values["dashboard.source"] = dashboard_source
    return values


def test_in_process_route_authorizes_and_delegates_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Authorize one HTTP request and invoke its owner source exactly once."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///api-in-process.db")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10.0")
    calls: list[str] = []

    def dashboard_source(name: str, _context: object) -> dict[str, object]:
        """Return one owner-authored snapshot."""
        calls.append(name)
        return {"snapshot": name, "stale": False}

    graph = build_in_process_api_graph(_providers(dashboard_source))
    app = create_api_app(build_api_settings(), in_process_graph=graph)
    with TestClient(app) as client:
        user = register_api_user(
            username="in-process-operator",
            password="bounded in-process password",  # pragma: allowlist secret
            permissions=("dashboard:read",),
            request_id=generate_id("req"),
        )
        session = create_api_session(
            user,
            request_id=generate_id("req"),
            ttl_seconds=60,
        )
        response = client.get(
            "/api/v1/dashboard/broker",
            headers={"Authorization": f"Bearer {session.session_token}"},
        )
        assert response.status_code == 200
        assert response.json()["data"] == {"snapshot": "broker", "stale": False}
        assert calls == ["broker"]

        unauthorized = register_api_user(
            username="in-process-reader-without-permission",
            password="bounded unauthorized password",  # pragma: allowlist secret
            roles=("dashboard_reader_without_permission",),
            request_id=generate_id("req"),
        )
        unauthorized_session = create_api_session(
            unauthorized,
            request_id=generate_id("req"),
            ttl_seconds=60,
        )
        denied = client.get(
            "/api/v1/dashboard/broker",
            headers={"Authorization": f"Bearer {unauthorized_session.session_token}"},
        )
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "AUTHORIZATION_DENIED"
        assert calls == ["broker"]
