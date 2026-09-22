"""Tests for host gateway owner, ASGI dispatch, and server lifecycle."""

import asyncio
import subprocess
import sys
import warnings
from collections.abc import Iterator
from typing import Any

import pytest
from app.host.bootstrap import approved_catalog_roots, create_runtime
from app.host.gateway import (
    GATEWAY_API_VERSION,
    HOST_GATEWAY,
    GatewayConfig,
    _GatewayProvider,
)
from app.kernel.bootstrapper import Runtime
from app.plugins.algebra import (
    GraphDocument,
    GraphSpec,
    NodeSpec,
    PortRef,
)
from app.plugins.schema import FrozenObject
from app.plugins.spec import PluginRef
from app.plugins.wire import graph_document_to_wire


def _test_client(app: Any) -> Any:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning,
            message="The anyio.abc.BlockingPortal alias is deprecated.*",
        )
        from starlette.testclient import TestClient

        return TestClient(app)


def test_gateway_contract_import_does_not_require_server_libraries() -> None:
    """Verify importing gateway protocol does not import starlette or uvicorn."""
    script = r"""
import sys
for forbidden in ("starlette", "uvicorn"):
    if forbidden in sys.modules:
        raise AssertionError(f"{forbidden} already imported before gateway")
from app.host.gateway import HOST_GATEWAY, Gateway, GatewayConfig
for forbidden in ("starlette", "uvicorn"):
    if forbidden in sys.modules:
        raise AssertionError(f"{forbidden} imported during gateway import")
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def test_gateway_feature_requires_catalog_and_execution() -> None:
    """Gateway feature explicitly requires host.catalog and host.execution."""
    from app.host.gateway import _GatewayFeature

    feature = _GatewayFeature()
    assert "host.catalog@1" in {c.identifier for c in feature.spec.requires}
    assert "host.execution@1" in {c.identifier for c in feature.spec.requires}
    assert "host.gateway@1" in {c.identifier for c in feature.spec.provides}


def test_gateway_config_validation() -> None:
    """GatewayConfig rejects invalid hosts, ports, origins, and bounds."""
    # Wildcard origin rejected
    with pytest.raises(ValueError, match="Wildcard"):
        GatewayConfig(allowed_origins=("*",))

    # Invalid port
    with pytest.raises(ValueError, match="port"):
        GatewayConfig(port=70000)

    # Empty host
    with pytest.raises(ValueError, match="bind_host"):
        GatewayConfig(bind_host="")

    # Valid config
    cfg = GatewayConfig(bind_host="127.0.0.1", port=8000)
    assert cfg.bind_host == "127.0.0.1"


@pytest.fixture
def active_runtime() -> Iterator[Runtime]:
    """Provide initialized host runtime with gateway, catalog, and execution."""
    rt = create_runtime(
        catalog_roots=approved_catalog_roots(),
        gateway_config=GatewayConfig(port=0),
    )

    async def _start() -> Runtime:
        await rt.__aenter__()
        return rt

    loop = asyncio.new_event_loop()
    runtime = loop.run_until_complete(_start())
    yield runtime
    loop.run_until_complete(runtime.__aexit__(None, None, None))
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


def test_health_endpoint(active_runtime: Runtime) -> None:
    """GET /api/v1/health returns versioned readiness envelope."""
    gateway = active_runtime.require(HOST_GATEWAY)
    app = gateway.create_asgi_app()
    with _test_client(app) as client:
        response = client.get(
            "/api/v1/health", headers={"X-Request-Id": "test-req-health"}
        )
        assert response.status_code == 200
        assert response.headers["X-Request-Id"] == "test-req-health"

        data = response.json()
        assert data["api_version"] == GATEWAY_API_VERSION
        assert data["request_id"] == "test-req-health"
        assert data["status"] == "success"
        assert data["data"]["status"] == "ready"
        assert data["data"]["services"]["gateway"] == "ready"
        assert data["data"]["services"]["catalog"] == "ready"
        assert data["data"]["services"]["execution"] == "ready"


def test_catalog_endpoint(active_runtime: Runtime) -> None:
    """GET /api/v1/catalog returns wire-safe catalog view."""
    gateway = active_runtime.require(HOST_GATEWAY)
    app = gateway.create_asgi_app()
    with _test_client(app) as client:
        response = client.get("/api/v1/catalog")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        entries = data["data"]["entries"]
        assert len(entries) >= 4  # rsi, greater_than, python, builder, results
        refs = {e["ref"] for e in entries}
        assert "indicator.rsi@1.0.0" in refs
        assert "comparison.greater_than@1.0.0" in refs
        assert "exporter.python@1.0.0" in refs
        assert "workspace.builder@1.0.0" in refs


def test_catalog_select_endpoint(active_runtime: Runtime) -> None:
    """POST /api/v1/catalog/select evaluates operation availability."""
    gateway = active_runtime.require(HOST_GATEWAY)
    app = gateway.create_asgi_app()
    with _test_client(app) as client:
        payload = {
            "enabled_refs": ["indicator.rsi@1.0.0"],
            "allowed_effects": ["pure"],
        }
        response = client.post("/api/v1/catalog/select", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        avail = data["data"]["available_operations"]
        assert any(
            op["plugin_ref"] == "indicator.rsi@1.0.0"
            and op["operation_id"] == "compute"
            for op in avail
        )


def test_graphs_validate_endpoint(active_runtime: Runtime) -> None:
    """POST /api/v1/graphs/validate validates graph document."""
    gateway = active_runtime.require(HOST_GATEWAY)
    app = gateway.create_asgi_app()
    with _test_client(app) as client:
        rsi_node = NodeSpec(
            id="rsi_1",
            plugin_ref=PluginRef("indicator.rsi", (1, 0, 0)),
            operation_id="compute",
            parameters=FrozenObject.from_mapping({"period": 14}),
        )
        doc = GraphDocument(
            spec=GraphSpec(
                schema_version=1,
                nodes=(rsi_node,),
                edges=(),
                designated_roots=(PortRef(node_id="rsi_1", port_key="rsi"),),
            )
        )
        payload = {"graph_document": graph_document_to_wire(doc)}

        response = client.post("/api/v1/graphs/validate", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["can_execute"] is True
        assert data["data"]["issues"] == []
        assert data["data"]["normalized_document"] is not None


def test_executions_evaluate_endpoint(active_runtime: Runtime) -> None:
    """POST /api/v1/executions/evaluate runs single in-process execution."""
    gateway = active_runtime.require(HOST_GATEWAY)
    app = gateway.create_asgi_app()
    with _test_client(app) as client:
        rsi_node = NodeSpec(
            id="rsi_1",
            plugin_ref=PluginRef("indicator.rsi", (1, 0, 0)),
            operation_id="compute",
            parameters=FrozenObject.from_mapping({"period": 2}),
        )
        doc = GraphDocument(
            spec=GraphSpec(
                schema_version=1,
                nodes=(rsi_node,),
                edges=(),
                designated_roots=(PortRef(node_id="rsi_1", port_key="rsi"),),
            )
        )
        payload = {
            "graph_document": graph_document_to_wire(doc),
            "inputs": {"values": [10.0, 11.0, 12.0, 13.0, 14.0]},
        }

        response = client.post("/api/v1/executions/evaluate", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["success"] is True
        assert "rsi_1.rsi" in data["data"]["outputs"]
        assert data["data"]["reproducibility"]["graph_id"] == "rsi_1"
        assert data["data"]["reproducibility"]["status"] == "completed"


def test_executions_batch_endpoint(active_runtime: Runtime) -> None:
    """POST /api/v1/executions/batch runs multiple parameter trials."""
    gateway = active_runtime.require(HOST_GATEWAY)
    app = gateway.create_asgi_app()
    with _test_client(app) as client:
        rsi_node = NodeSpec(
            id="rsi_1",
            plugin_ref=PluginRef("indicator.rsi", (1, 0, 0)),
            operation_id="compute",
            parameters=FrozenObject.from_mapping({"period": 2}),
        )
        doc = GraphDocument(
            spec=GraphSpec(
                schema_version=1,
                nodes=(rsi_node,),
                edges=(),
                designated_roots=(PortRef(node_id="rsi_1", port_key="rsi"),),
            )
        )
        payload = {
            "graph_document": graph_document_to_wire(doc),
            "inputs": {"values": [10.0, 11.0, 12.0, 13.0, 14.0]},
            "trials": [
                {
                    "trial_id": "trial_p2",
                    "parameter_overrides": {"rsi_1": {"period": 2}},
                },
                {
                    "trial_id": "trial_p3",
                    "parameter_overrides": {"rsi_1": {"period": 3}},
                },
            ],
        }

        response = client.post("/api/v1/executions/batch", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["success"] is True
        assert len(data["data"]["trials"]) == 2
        assert data["data"]["trials"][0]["trial_id"] == "trial_p2"
        assert data["data"]["trials"][1]["trial_id"] == "trial_p3"


def test_exports_endpoint(active_runtime: Runtime) -> None:
    """POST /api/v1/exports lowers graph and emits target Python code."""
    gateway = active_runtime.require(HOST_GATEWAY)
    app = gateway.create_asgi_app()
    with _test_client(app) as client:
        rsi_node = NodeSpec(
            id="rsi_1",
            plugin_ref=PluginRef("indicator.rsi", (1, 0, 0)),
            operation_id="compute",
            parameters=FrozenObject.from_mapping({"period": 14}),
        )
        doc = GraphDocument(
            spec=GraphSpec(
                schema_version=1,
                nodes=(rsi_node,),
                edges=(),
                designated_roots=(PortRef(node_id="rsi_1", port_key="rsi"),),
            )
        )
        payload = {
            "graph_document": graph_document_to_wire(doc),
            "target": {"target_id": "python", "version": [1, 0, 0]},
        }

        response = client.post("/api/v1/exports", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["success"] is True
        assert "def execute" in data["data"]["source_code"]
        assert data["data"]["manifest"] is not None


def test_duplicate_json_keys_rejected(active_runtime: Runtime) -> None:
    """Duplicate JSON keys in request payload are strictly rejected."""
    gateway = active_runtime.require(HOST_GATEWAY)
    app = gateway.create_asgi_app()
    with _test_client(app) as client:
        # Raw body with duplicate key
        dup_body = b'{"enabled_refs": [], "enabled_refs": []}'
        response = client.post(
            "/api/v1/catalog/select",
            content=dup_body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "INVALID_PAYLOAD"


def test_unready_catalog_returns_503() -> None:
    """Unready catalog returns stable 503 error envelope."""
    unready_provider = _GatewayProvider(GatewayConfig(), catalog=None, execution=None)
    app = unready_provider.create_asgi_app()
    with _test_client(app) as client:
        response = client.get("/api/v1/catalog")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "CATALOG_UNAVAILABLE"


def test_server_start_stop_lifecycle() -> None:
    """Gateway start() binds address and stop() clears it cleanly."""
    provider = _GatewayProvider(GatewayConfig(bind_host="127.0.0.1", port=0))
    provider.start()
    try:
        assert provider.bound_address is not None
        host, port = provider.bound_address
        assert host == "127.0.0.1"
        assert port > 0
    finally:
        provider.stop()
        assert provider.bound_address is None
