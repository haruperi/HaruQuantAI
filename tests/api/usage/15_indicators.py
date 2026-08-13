"""Standalone indicators API feature usage."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.api import create_api_app, get_canonical_route_contract_registry


def main() -> None:
    """Verify the indicators feature's routes use canonical contracts."""
    application = create_api_app()
    operations = {
        (method.upper(), path)
        for path, path_item in application.openapi()["paths"].items()
        for method in path_item
        if path.startswith("/api/v1/indicators")
    }
    declarations = {
        (item.method, item.path)
        for item in get_canonical_route_contract_registry().all()
    }
    assert operations <= declarations
    assert ("GET", "/api/v1/indicators/{indicator_id}/series") in operations
    assert len(operations) >= 4
    print({"feature": "indicators", "operations": len(operations)})


if __name__ == "__main__":
    main()
