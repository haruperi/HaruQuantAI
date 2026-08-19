"""Drift checks between canonical OpenAPI routes and route contracts."""

from app.services.api import create_api_app, get_canonical_route_contract_registry
from app.services.api.composition.adapters import get_absent_capability_ids


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
    # Every mounted operation is covered by exactly one contract, and every
    # uncovered declaration belongs to a capability absent from this build.
    assert operations <= declarations
    unmounted_capabilities = {
        path.split("/")[3] for _, path in declarations - operations
    }
    assert unmounted_capabilities <= set(get_absent_capability_ids())
    assert registry.size == 174
    assert registry.get("GET", "/api/v1/data/bars") is not None
    assert registry.get("GET", "/api/v1/workstation") is not None
    assert registry.get("POST", "/api/v1/workstation/commands") is not None
    assert registry.get("GET", "/api/v1/indicators") is not None
    assert registry.get("GET", "/api/v1/indicators/capabilities") is not None
    assert registry.get("GET", "/api/v1/indicators/{indicator_id}") is not None
    assert registry.get("GET", "/api/v1/auth/me") is not None
    assert registry.get("GET", "/api/v1/data/stream") is not None
    assert registry.get("GET", "/api/v1/data/datasets") is not None
    assert (
        registry.get("GET", "/api/v1/trading/execution-sessions/{session_id}/activity")
        is not None
    )
    assert registry.get("GET", "/api/v1/data/snapshot-stream") is not None
    assert registry.get("POST", "/api/v1/portfolio/construct") is not None
    assert registry.get("POST", "/api/v1/portfolio/{portfolio_id}/activate") is not None
    assert registry.get("POST", "/api/v1/portfolio/{portfolio_id}/rollback") is not None
    assert registry.get("POST", "/api/v1/portfolio/{portfolio_id}/drift") is not None
    assert registry.get("POST", "/api/v1/portfolio/rebalance") is not None
    assert registry.get("POST", "/api/v1/portfolio/measurement/recompute") is not None
    assert registry.get("POST", "/api/v1/strategies") is not None
    assert (
        registry.get("PATCH", "/api/v1/strategies/{strategy_id}/parameters") is not None
    )
    assert registry.get("POST", "/api/v1/data/datasets/prepare") is not None
    assert registry.get("POST", "/api/v1/risk/kill-switch") is not None
    assert registry.get("POST", "/api/v1/simulation/live-sessions") is not None
    assert (
        registry.get("GET", "/api/v1/simulation/live-sessions/{session_id}") is not None
    )
    assert (
        registry.get("POST", "/api/v1/simulation/live-sessions/{session_id}/step")
        is not None
    )
    assert (
        registry.get("POST", "/api/v1/simulation/live-sessions/{session_id}/branch")
        is not None
    )
    assert registry.get("POST", "/api/v1/data/imports") is not None
    assert registry.get("GET", "/api/v1/data/imports/dialects") is not None
    assert registry.get("GET", "/api/v1/agentic/runs/concrete-id") is not None
    assert registry.get("POST", "/api/v1/optimization/parameter-sweep") is not None
    assert registry.get("GET", "/api/v1/optimization/results/concrete-id") is not None
    assert registry.get("POST", "/api/v1/simulation/sessions") is not None
    assert (
        registry.get("GET", "/api/v1/simulation/sessions/{session_id}/frames")
        is not None
    )
    assert registry.get("GET", "/api/v1/simulator/strategies") is not None
    assert registry.get("POST", "/api/v1/simulator/runs") is not None
    assert registry.get("GET", "/api/v1/simulator/runs") is not None
    assert registry.get("GET", "/api/v1/simulator/runs/concrete-id") is not None
    assert registry.get("DELETE", "/api/v1/simulator/runs/concrete-id") is not None
    assert registry.get("GET", "/api/v1/simulator/runs/concrete-id/stream") is not None
    assert registry.get("POST", "/api/v1/research/expectancy") is not None
    assert registry.get("POST", "/api/v1/research/stress-scenarios") is not None


def test_excluded_workflow_routes_are_absent() -> None:
    """Uncomposed owner workflow families stay outside backend v1."""
    paths = create_api_app().openapi()["paths"]
    assert "/api/v1/simulation/sessions" in paths
    assert not any("/backtest/" in path for path in paths)
    assert "/api/v1/risk/kill-switch" in paths
    assert "/api/v1/trading/session" in paths
    assert "/api/v1/optimization/parameter-sweep" in paths
    assert "/api/v1/portfolio/construct" in paths
    assert "/api/v1/agentic/runs" in paths
