"""Drift checks between canonical OpenAPI routes and route contracts."""

from app.services.api import create_api_app, get_canonical_route_contract_registry


def test_every_openapi_operation_has_exactly_one_contract() -> None:
    """The canonical route registry completely covers the HTTP surface."""
    app = create_api_app()
    registry = get_canonical_route_contract_registry()
    operations = {
        (method.upper(), path)
        for path, path_item in app.openapi()["paths"].items()
        for method in path_item
    }
    declarations = {(item.method, item.path) for item in registry.all()}
    assert operations == declarations
    assert registry.size == 32
    assert registry.get("GET", "/api/v1/auth/me") is not None
    assert registry.get("GET", "/api/v1/data/stream") is not None
    assert registry.get("GET", "/api/v1/agentic/runs/concrete-id") is None


def test_excluded_workflow_routes_are_absent() -> None:
    """Uncomposed owner workflow families stay outside backend v1."""
    paths = create_api_app().openapi()["paths"]
    assert not any("/simulation/sessions" in path for path in paths)
    assert not any("/backtest/" in path for path in paths)
    assert "/api/v1/risk/kill-switch" in paths
    assert "/api/v1/trading/session" in paths
    assert not any("/optimization/" in path for path in paths)
    assert not any("/portfolio/" in path for path in paths)
    assert not any("/agentic/" in path for path in paths)
