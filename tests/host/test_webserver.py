"""Tests for the wired host application: routing, auth, errors, static UI."""

import logging
from dataclasses import replace
from pathlib import Path

from app.host.bootstrapper import build_services
from app.host.webserver import HOST_VERSION, create_app
from starlette.testclient import TestClient

from tests.host.conftest import make_config


def test_health_is_public_and_returns_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"] == {
        "status": "ready",
        "version": HOST_VERSION,
        "services": {"host": "ready", "ui": "pending"},
    }
    assert response.headers["X-Request-Id"] == body["request_id"]


def test_supplied_request_id_is_echoed(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-Id": "req-test-1"})

    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "req-test-1"
    assert response.json()["request_id"] == "req-test-1"


def test_app_loaded_requires_auth_then_acknowledges(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    denied = client.post("/api/v1/app-loaded")
    allowed = client.post(
        "/api/v1/app-loaded", json={"product": "web"}, headers=auth_headers
    )

    assert denied.status_code == 401
    assert allowed.status_code == 200
    assert allowed.json()["data"] == {"acknowledged": True}


def test_unknown_route_fails_closed_with_not_found_envelope(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/executions/evaluate", json={"graph_document": {}}, headers=auth_headers
    )

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["issues"] == []


def test_method_mismatch_returns_405_envelope(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/app-loaded", headers=auth_headers)

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_malformed_json_returns_400_malformed_request(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/app-loaded",
        content=b"{not json",
        headers={**auth_headers, "Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MALFORMED_REQUEST"


def test_non_object_json_body_returns_400_malformed_request(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/app-loaded",
        content=b"[1, 2, 3]",
        headers={**auth_headers, "Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MALFORMED_REQUEST"


def make_static_client(tmp_path: Path) -> TestClient:
    ui_dist = tmp_path / "dist"
    ui_dist.mkdir()
    (ui_dist / "index.html").write_text(
        "<html><body>HaruQuantAI UI</body></html>", encoding="utf-8"
    )
    (ui_dist / "app.css").write_text("body{color:#fff}", encoding="utf-8")

    services = build_services(make_config(tmp_path))
    static_services = replace(services, ui_dist=ui_dist)
    return TestClient(create_app(static_services, logging.getLogger("tests.host")))


def test_static_ui_is_served_with_spa_fallback(tmp_path: Path) -> None:
    static_client = make_static_client(tmp_path)

    index = static_client.get("/")
    spa_route = static_client.get("/builder")
    asset = static_client.get("/app.css")

    assert index.status_code == 200
    assert "HaruQuantAI UI" in index.text
    assert spa_route.status_code == 200
    assert "HaruQuantAI UI" in spa_route.text
    assert asset.status_code == 200
    assert asset.text == "body{color:#fff}"


def test_missing_ui_dist_leaves_root_unhandled(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_cors_headers_and_preflight(client: TestClient) -> None:
    preflight = client.options(
        "/api/v1/files/exists",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert preflight.status_code == 200
    assert (
        preflight.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"
    )
    assert preflight.headers.get("access-control-allow-credentials") == "true"

    resp = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_options_preflight_bypasses_auth(client: TestClient) -> None:
    preflight = client.options(
        "/api/v1/settings",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "PUT",
        },
    )
    assert preflight.status_code == 200
    assert (
        preflight.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"
    )
