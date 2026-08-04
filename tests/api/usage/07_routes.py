"""Standalone canonical HTTP route inventory usage."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.api import create_api_app, get_canonical_route_contract_registry


def main() -> None:
    """Verify every canonical HTTP operation has one declared contract."""
    application = create_api_app()
    operations = {
        (method.upper(), path)
        for path, path_item in application.openapi()["paths"].items()
        for method in path_item
    }
    contracts = get_canonical_route_contract_registry()
    declarations = {(item.method, item.path) for item in contracts.all()}
    assert operations == declarations
    assert len(operations) == 55
    assert ("POST", "/api/v1/simulation/run") in operations
    assert ("GET", "/api/v1/risk/kill-switch") in operations
    assert ("GET", "/api/v1/trading/session") in operations
    assert ("POST", "/api/v1/simulation/sessions") in operations
    assert ("GET", "/api/v1/simulation/sessions/{session_id}/frames") in operations
    assert not any("/backtest/" in path for _, path in operations)
    assert not any("/live/" in path for _, path in operations)
    assert any("/optimization/" in path for _, path in operations)
    assert any("/portfolio/" in path for _, path in operations)
    assert any("/agentic/" in path for _, path in operations)
    print({"operations": len(operations), "prefix": "/api/v1"})


if __name__ == "__main__":
    main()
