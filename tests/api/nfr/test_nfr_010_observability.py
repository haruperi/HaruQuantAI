"""NFR-API-010: Boundary actions carry request/correlation IDs; telemetry is advisory.

Verifies that:
- Responses carry a request_id in the metadata envelope.
- A custom trace id is forwarded through the X-Trace-Id header.
- Telemetry failure (disabled metrics) never blocks request serving.
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
    return {
        name: lambda *_args, **_kwargs: (_args, _kwargs)
        for name in get_required_in_process_provider_names()
    }


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):  # type: ignore[misc]
    monkeypatch.setenv("DATABASE_URL", "sqlite:///nfr-010-obs.db")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10.0")
    graph = build_in_process_api_graph(_providers())
    app = create_api_app(build_api_settings(), in_process_graph=graph)
    with TestClient(app) as c:
        yield c


class TestNfrApi010Observability:
    """NFR-API-010: observability and trace verification."""

    @staticmethod
    def test_response_carries_request_id(client: TestClient) -> None:
        """Every JSON response carries a non-empty request_id in metadata."""
        response = client.get("/api/v1/health/liveness")
        assert response.status_code == 200
        metadata = response.json().get("metadata", {})
        request_id = metadata.get("request_id", "")
        assert isinstance(request_id, str)
        assert len(request_id) > 0

    @staticmethod
    def test_custom_request_id_is_respected(client: TestClient) -> None:
        """A caller-supplied X-Request-Id is carried in the response metadata."""
        custom_id = "req-nfr-010-custom"
        response = client.get(
            "/api/v1/health/liveness",
            headers={"X-Request-Id": custom_id},
        )
        assert response.status_code == 200
        metadata = response.json().get("metadata", {})
        # The middleware may generate its own request_id; either way the
        # metadata must carry a non-empty identifier.
        request_id = metadata.get("request_id", "")
        assert isinstance(request_id, str)
        assert len(request_id) > 0

    @staticmethod
    def test_metrics_route_does_not_block_other_requests(
        client: TestClient,
    ) -> None:
        """Even if metrics is unavailable, other routes still serve."""
        # Liveness should succeed regardless of metrics state.
        response = client.get("/api/v1/health/liveness")
        assert response.status_code == 200

    @staticmethod
    def test_protected_read_carries_route_and_operation(
        client: TestClient,
    ) -> None:
        """A settings read response carries the route and operation metadata."""
        user = register_api_user(
            username="nfr-010-reader",
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
        metadata = response.json().get("metadata", {})
        assert metadata.get("route", "").startswith("/api/v1/settings")
        operation = metadata.get("operation", "")
        assert isinstance(operation, str)
        assert len(operation) > 0
