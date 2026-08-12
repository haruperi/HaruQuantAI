"""Standalone Settings boundary usage."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.api import create_api_app, get_canonical_route_contract_registry


def main() -> None:
    """Verify the Settings routes use declared canonical contracts."""
    application = create_api_app()
    operations = {
        (method.upper(), path)
        for path, path_item in application.openapi()["paths"].items()
        for method in path_item
    }
    contracts = get_canonical_route_contract_registry()
    declarations = {(item.method, item.path) for item in contracts.all()}
    settings = {(method, path) for method, path in operations if "/settings" in path}
    assert settings <= declarations
    assert settings == {
        ("GET", "/api/v1/settings"),
        ("GET", "/api/v1/settings/credentials"),
        ("GET", "/api/v1/settings/manifest"),
        ("PUT", "/api/v1/settings"),
        ("PUT", "/api/v1/settings/credentials/{slot}"),
    }
    print({"feature": "settings", "operations": len(settings)})


if __name__ == "__main__":
    main()
