"""Tests for domain manifest discovery, validation, and route mounting."""

import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from app.host.catalog import (
    CatalogError,
    CatalogService,
    DomainManifest,
    parse_manifest,
    scan_domains,
)
from app.host.webserver import HostServices
from starlette.testclient import TestClient

VALID_MANIFEST: dict[str, Any] = {
    "id": "builder",
    "kind": "workspace",
    "route_base": "/api/v1/builder",
    "version": "0.1.0",
    "capabilities": ["strategy.build"],
}


def write_manifest(root: Path, name: str, raw: dict[str, Any]) -> Path:
    domain_dir = root / name
    domain_dir.mkdir(parents=True)
    (domain_dir / "manifest.json").write_text(json.dumps(raw), encoding="utf-8")
    return domain_dir


def test_valid_manifest_parses() -> None:
    manifest = parse_manifest(dict(VALID_MANIFEST))

    assert manifest == DomainManifest(
        domain_id="builder",
        kind="workspace",
        route_base="/api/v1/builder",
        version="0.1.0",
        capabilities=("strategy.build",),
        module=None,
    )


def test_invalid_manifest_reports_structured_issues() -> None:
    with pytest.raises(CatalogError) as excinfo:
        parse_manifest(
            {"id": "", "kind": "alien", "route_base": "relative", "version": 1}
        )

    paths = {issue.path for issue in excinfo.value.issues}
    assert {"id", "kind", "route_base", "version"} <= paths


def test_scan_skips_and_reports_invalid_domains(tmp_path: Path) -> None:
    write_manifest(tmp_path, "good", dict(VALID_MANIFEST))
    bad = write_manifest(tmp_path, "bad", {**VALID_MANIFEST, "id": ""})
    (tmp_path / "not-a-domain").mkdir()

    view = scan_domains([tmp_path])

    assert [m.domain_id for m in view.domains] == ["builder"]
    assert len(view.issues) == 1
    assert str(bad) in view.issues[0].path


def test_scan_reports_unreadable_manifests(tmp_path: Path) -> None:
    domain_dir = tmp_path / "broken"
    domain_dir.mkdir()
    (domain_dir / "manifest.json").write_text("{not json", encoding="utf-8")

    view = scan_domains([tmp_path])

    assert view.domains == ()
    assert view.issues[0].code == "unreadable"


def test_catalog_endpoint_serves_discovered_domains(
    client: TestClient,
    auth_headers: dict[str, str],
    services: HostServices,
    tmp_path: Path,
) -> None:
    write_manifest(tmp_path / "domains", "builder", dict(VALID_MANIFEST))
    services.catalog.refresh()

    stale_response = client.get("/api/v1/catalog", headers=auth_headers)
    assert stale_response.json()["data"]["domains"] == []

    from app.host.webserver import create_app

    new_client = TestClient(create_app(services))
    login = new_client.post("/api/v1/auth/login", json={"username": "tester"})
    headers = {"Authorization": f"Bearer {login.json()['data']['token']}"}
    response = new_client.get("/api/v1/catalog", headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["domains"][0]["id"] == "builder"
    assert data["domains"][0]["mounted"] is False
    assert data["issues"] == []


def test_manifest_declared_routes_are_mounted(tmp_path: Path) -> None:
    package_root = tmp_path / "packages"
    package_root.mkdir()
    package_dir = package_root / "fixture_domain"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text(
        "from starlette.responses import PlainTextResponse\n"
        "from starlette.routing import Route\n"
        "async def ping(request):\n"
        "    return PlainTextResponse('pong')\n"
        "def create_routes():\n"
        "    return [Route('/ping', ping, methods=['GET'])]\n",
        encoding="utf-8",
    )
    domain_root = tmp_path / "domains"
    write_manifest(
        domain_root,
        "fixture",
        {
            **VALID_MANIFEST,
            "id": "fixture",
            "route_base": "/api/v1/fixture",
            "module": "fixture_domain",
        },
    )

    sys.path.insert(0, str(package_root))
    sys.modules.pop("fixture_domain", None)
    try:
        from app.host.bootstrapper import build_services
        from app.host.webserver import create_app

        from tests.host.conftest import make_config

        services = build_services(make_config(tmp_path))
        services_with_mount = replace(services, catalog=CatalogService([domain_root]))
        app = create_app(services_with_mount)
        mount_client = TestClient(app)
        login = mount_client.post("/api/v1/auth/login", json={"username": "tester"})
        headers = {"Authorization": f"Bearer {login.json()['data']['token']}"}

        response = mount_client.get("/api/v1/fixture/ping", headers=headers)
        assert response.status_code == 200
        assert response.text == "pong"
        catalog = mount_client.get("/api/v1/catalog", headers=headers)
        assert catalog.json()["data"]["domains"][0]["mounted"] is True
    finally:
        sys.path.remove(str(package_root))
        sys.modules.pop("fixture_domain", None)


def test_scan_rejects_duplicate_domain_ids(tmp_path: Path) -> None:
    root = tmp_path / "domains"
    write_manifest(
        root,
        "first_dir",
        {**VALID_MANIFEST, "id": "dup_domain", "route_base": "/api/v1/first"},
    )
    write_manifest(
        root,
        "second_dir",
        {**VALID_MANIFEST, "id": "dup_domain", "route_base": "/api/v1/second"},
    )

    view = scan_domains([root])
    assert len(view.domains) == 1
    assert view.domains[0].route_base == "/api/v1/first"
    assert len(view.issues) == 1
    assert view.issues[0].code == "duplicate"
    assert "Duplicate domain id 'dup_domain'" in view.issues[0].message


def test_scan_rejects_duplicate_route_bases(tmp_path: Path) -> None:
    root = tmp_path / "domains"
    write_manifest(
        root,
        "dir_a",
        {**VALID_MANIFEST, "id": "domain_a", "route_base": "/api/v1/shared"},
    )
    write_manifest(
        root,
        "dir_b",
        {**VALID_MANIFEST, "id": "domain_b", "route_base": "/api/v1/shared"},
    )

    view = scan_domains([root])
    assert len(view.domains) == 1
    assert view.domains[0].domain_id == "domain_a"
    assert len(view.issues) == 1
    assert view.issues[0].code == "duplicate"
    assert "Duplicate route_base '/api/v1/shared'" in view.issues[0].message


def test_catalog_rejects_host_route_collision(tmp_path: Path) -> None:
    from app.host.bootstrapper import build_services
    from app.host.webserver import create_app

    from tests.host.conftest import make_config

    root = tmp_path / "domains"
    write_manifest(
        root,
        "collision",
        {**VALID_MANIFEST, "route_base": "/api/v1/settings"},
    )
    services = replace(
        build_services(make_config(tmp_path)), catalog=CatalogService([root])
    )
    client = TestClient(create_app(services))
    login = client.post("/api/v1/auth/login", json={"username": "tester"})
    headers = {"Authorization": f"Bearer {login.json()['data']['token']}"}
    catalog = client.get("/api/v1/catalog", headers=headers).json()["data"]
    assert catalog["domains"] == []
    assert catalog["issues"][0]["code"] == "reserved_route"
