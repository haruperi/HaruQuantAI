"""Verify landing workspace contracts and authorization using isolated stores.

Description:
    Exercises public Home/About methods and HTTP responses without live data.
Purpose:
    FEAT-HOME-DASHBOARD: Verify host reuse and failure boundaries.
Key Capabilities:
    - FR-HOME-INDEX: Assert local content and logs.
    - FR-HOME-RECENT: Assert persisted order, limits, validation and logs.
    - FR-HOME-ABOUT: Assert metadata projection and logs.
    - FR-HOME-DIAGNOSTICS: Assert resource delegation and logs.
    - FR-HOME-UPDATES: Assert provider-unavailable state and logs.
    - FR-HOME-CLI: Assert formatter and logs.
Python API Usage:
    pytest.main(["tests/unit/workspace/home/test_routes.py", "--no-cov"])
CLI Usage:
    uv run pytest tests/unit/workspace/home/test_routes.py --no-cov
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from app.host.persistence import HostPersistence
from app.host.resources import ResourceMonitor
from app.host.session import SessionManager
from app.host.settings import SettingsManager
from app.host.transport import ServletConstants, register_transport_exception_handlers
from app.workspace.home import About, Home, HomeCLI, create_home_router
from app.workspace.home._releases import ReleaseFeed
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def services(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Home, About, SessionManager, Mock]:
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", tmp_path / "home.db")
    sessions = SessionManager(host_instance_id="home-tests")
    constants = ServletConstants(sessions)
    resources = Mock(spec=ResourceMonitor)
    resources.inspect_resources.return_value.to_dict.return_value = {
        "status": "DEGRADED",
        "database": {"exists": False},
        "hardware": {"ram_available_bytes": 1000},
    }
    settings = SettingsManager()
    settings.reload()
    settings.set_in_memory("workspace_paths", "projects_dir", "data/projects")
    return (
        Home(constants, ReleaseFeed(None)),
        About(constants, resources, settings, tmp_path),
        sessions,
        resources,
    )


def _project(
    identity: str, date: str, payload: dict[str, Any] | str, *, scope: str = "workspace"
) -> None:
    HostPersistence.create_record(
        "host_entities",
        {
            "entity_id": identity,
            "entity_type": "project",
            "scope": scope,
            "payload": json.dumps(payload) if isinstance(payload, dict) else payload,
            "created_at_utc": date,
            "updated_at_utc": date,
        },
    )


def test_public_methods_and_requirement_logs(
    services: tuple[Any, ...], caplog: pytest.LogCaptureFixture
) -> None:
    home, about, _, resources = services
    caplog.set_level(logging.INFO)
    assert home.index()["recent_projects"] == []
    resources.inspect_resources.assert_not_called()
    assert home.check_updates()["state"] == "unavailable"
    info = about.about()
    assert info["version"] == "1.0.0"
    assert info["license"]["state"] == "unavailable"
    assert "host_instance_id" not in info
    assert about.diagnostics()["directories"] == {"projects_dir": "data/projects"}
    resources.inspect_resources.assert_called_once()
    assert json.loads(HomeCLI.format_output(info)) == info
    assert {
        f"FR-HOME-{name}"
        for name in ("INDEX", "RECENT", "UPDATES", "ABOUT", "DIAGNOSTICS", "CLI")
    } <= {r.__dict__.get("fr_id") for r in caplog.records}


def test_recent_order_window_and_payload_redaction(
    services: tuple[Any, ...], caplog: pytest.LogCaptureFixture
) -> None:
    home = services[0]
    _project("z", "2026-10-20T00:00:00Z", {"name": "Earlier", "workspace": "builder"})
    for identity in ("b", "a"):
        _project(
            identity,
            "2026-10-21T00:00:00Z",
            {"name": identity, "workspace": "projects", "secret": "excluded"},
        )
    _project(
        "private",
        "2026-10-22T00:00:00Z",
        {"name": "Private", "workspace": "projects"},
        scope="other",
    )
    _project("bad", "2026-10-22T00:00:00Z", "raw-sensitive-invalid-json")
    rows = home.get_recent_projects(3)
    assert [r["id"] for r in rows] == ["a", "b"]
    assert set(rows[0]) == {"id", "name", "workspace", "last_activity"}
    assert "raw-sensitive" not in caplog.text
    assert "Ignored invalid" in caplog.text


@pytest.mark.parametrize("limit", [0, -1, 101, True, 1.5, "1"])
def test_invalid_limit(services: tuple[Any, ...], limit: Any) -> None:
    with pytest.raises(ValueError, match="limit"):
        services[0].get_recent_projects(limit)


def test_persistence_failure_is_not_an_empty_success(
    services: tuple[Any, ...],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(
        HostPersistence,
        "read_records",
        Mock(side_effect=HostPersistence.Error("not logged")),
    )
    with pytest.raises(HostPersistence.Error):
        services[0].get_recent_projects()
    assert "Project summary read failed" in caplog.text
    assert "not logged" not in caplog.text


def test_http_session_scopes_query_validation_and_envelopes(
    services: tuple[Any, ...], monkeypatch: pytest.MonkeyPatch
) -> None:
    home, about, sessions, _ = services
    app = FastAPI()
    register_transport_exception_handlers(app)
    app.include_router(
        create_home_router(home, about, session_mgr=sessions, require_auth=True)
    )
    token, record = sessions.create_session("test-user", "test-peer")
    with TestClient(app) as client:
        for path in (
            "/home",
            "/home/about",
            "/home/updates",
            "/home/diagnostics",
            "/home/recent-projects",
        ):
            assert client.get(path).status_code == 401
            response = client.get(
                path,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Request-Id": "home-test",
                },
            )
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            assert response.json()["metadata"]["request_id"] == "home-test"
        assert (
            client.get(
                "/home/recent-projects?limit=101",
                headers={"Authorization": f"Bearer {token}"},
            ).status_code
            == 422
        )
        monkeypatch.setattr(
            sessions, "authorize", lambda record, scope: scope == "settings:read"
        )
        assert (
            client.get(
                "/home/diagnostics", headers={"Authorization": f"Bearer {token}"}
            ).status_code
            == 403
        )
        assert (
            client.get(
                "/home", headers={"Authorization": f"Bearer {token}"}
            ).status_code
            == 200
        )
        sessions.revoke_session(record.session_id)
        assert (
            client.get(
                "/home", headers={"Authorization": f"Bearer {token}"}
            ).status_code
            == 401
        )
