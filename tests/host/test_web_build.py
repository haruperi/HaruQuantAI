"""Tests for web build static asset and SPA client route serving."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from app import main as backend
from fastapi.testclient import TestClient


@pytest.fixture
def synthetic_build(tmp_path: Path) -> Path:
    """Create a temporary build directory with index.html and assets."""
    build_dir = tmp_path / "web_dist"
    build_dir.mkdir(parents=True)
    index_file = build_dir / "index.html"
    index_file.write_text(
        "<!doctype html><html><head><title>Haru</title></head>"
        "<body><div id='synthetic-marker'>App Content</div></body></html>",
        encoding="utf-8",
    )
    assets_dir = build_dir / "assets"
    assets_dir.mkdir()
    js_file = assets_dir / "app-123.js"
    js_file.write_text("console.log('haru-web');", encoding="utf-8")
    return build_dir


def test_web_build_spa_and_asset_serving(synthetic_build: Path, monkeypatch) -> None:
    settings = Mock()
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    gateway = Mock()
    gateway.read_records.return_value = {"success": True, "data": {"records": []}}

    application = backend.create_app(gateway, web_build_dir=synthetic_build)

    with TestClient(application) as client:
        # 1. / and /builder return 200 text/html with synthetic marker and no-cache
        res_root = client.get("/")
        assert res_root.status_code == 200
        assert "synthetic-marker" in res_root.text
        assert res_root.headers["content-type"].startswith("text/html")
        assert res_root.headers["cache-control"] == "no-cache"

        res_builder = client.get("/builder")
        assert res_builder.status_code == 200
        assert "synthetic-marker" in res_builder.text
        assert res_builder.headers["content-type"].startswith("text/html")
        assert res_builder.headers["cache-control"] == "no-cache"

        # 2. /assets/app-123.js returns 200 JavaScript with immutable caching
        res_js = client.get("/assets/app-123.js")
        assert res_js.status_code == 200
        assert res_js.text == "console.log('haru-web');"
        assert "javascript" in res_js.headers["content-type"]
        assert res_js.headers["cache-control"] == "public, max-age=31536000, immutable"

        # 3. Missing assets return 404
        res_missing_js = client.get("/assets/missing.js")
        assert res_missing_js.status_code == 404

        res_missing_css = client.get("/missing.css")
        assert res_missing_css.status_code == 404

        # 4. /api/unknown returns 404 JSON and contains no HTML marker
        res_api = client.get("/api/unknown")
        assert res_api.status_code == 404
        assert res_api.headers["content-type"].startswith("application/json")
        assert "synthetic-marker" not in res_api.text
        assert res_api.json() == {"detail": "Not Found"}

        # 5. HEAD returns no body
        res_head = client.head("/")
        assert res_head.status_code == 200
        assert res_head.text == ""
        assert res_head.content == b""

        res_head_js = client.head("/assets/app-123.js")
        assert res_head_js.status_code == 200
        assert res_head_js.text == ""
        assert res_head_js.content == b""

        # 6. /health remains successful
        res_health = client.get("/health")
        assert res_health.status_code == 200
        assert res_health.json() == {"status": "ok"}

        # 7. Path traversal attempt does not expose files outside build_dir
        res_traversal = client.get("/assets/../../secret.txt")
        assert res_traversal.status_code == 404

        res_encoded_traversal = client.get("/%2e%2e/secret.txt")
        assert res_encoded_traversal.status_code == 404


def test_absent_build_fallback(tmp_path: Path, monkeypatch) -> None:
    settings = Mock()
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    gateway = Mock()
    gateway.read_records.return_value = {"success": True, "data": {"records": []}}

    empty_dir = tmp_path / "absent_dir"
    application = backend.create_app(gateway, web_build_dir=empty_dir)

    with TestClient(application) as client:
        # With absent build, /builder returns 503 JSON with Cache-Control: no-store
        res_builder = client.get("/builder")
        assert res_builder.status_code == 503
        assert res_builder.headers["cache-control"] == "no-store"
        assert res_builder.json() == {"detail": "Web build unavailable"}

        # /api/unknown remains 404
        res_api = client.get("/api/unknown")
        assert res_api.status_code == 404
        assert res_api.json() == {"detail": "Not Found"}

        # HEAD /builder returns 503 with empty body
        res_head = client.head("/builder")
        assert res_head.status_code == 503
        assert res_head.text == ""
        assert res_head.content == b""

        # /health remains successful
        res_health = client.get("/health")
        assert res_health.status_code == 200
        assert res_health.json() == {"status": "ok"}


def test_non_get_head_methods_not_spa_routed(
    synthetic_build: Path, monkeypatch
) -> None:
    settings = Mock()
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    gateway = Mock()
    gateway.read_records.return_value = {"success": True, "data": {"records": []}}

    application = backend.create_app(gateway, web_build_dir=synthetic_build)

    with TestClient(application) as client:
        res_post = client.post("/builder", json={"test": 1})
        assert res_post.status_code == 405

        res_delete = client.delete("/builder")
        assert res_delete.status_code == 405


def test_reserved_paths_boundaries(synthetic_build: Path, monkeypatch) -> None:
    settings = Mock()
    monkeypatch.setattr(backend, "SettingsManager", Mock(return_value=settings))
    gateway = Mock()
    gateway.read_records.return_value = {"success": True, "data": {"records": []}}

    application = backend.create_app(gateway, web_build_dir=synthetic_build)

    with TestClient(application) as client:
        for reserved in ("/api", "/api/v1/unknown", "/events/unknown", "/health/sub"):
            res = client.get(reserved)
            assert res.status_code == 404
            assert res.headers["content-type"].startswith("application/json")
            assert "synthetic-marker" not in res.text
