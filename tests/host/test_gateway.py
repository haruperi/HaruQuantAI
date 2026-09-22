"""Tests for host gateway owner, ASGI dispatch, and server lifecycle."""

import asyncio
import subprocess
import sys
import warnings
from collections.abc import Iterator
from typing import Any, ClassVar, cast

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


def test_request_timeout_enforced(active_runtime: Runtime) -> None:
    """A handler exceeding request_timeout_seconds returns a 504 envelope."""
    from typing import cast

    gw = active_runtime.require(HOST_GATEWAY)
    app = gw.create_asgi_app()
    provider = cast("_GatewayProvider", gw)

    # Shrink the effective timeout for this test (config is frozen)
    object.__setattr__(provider._config, "request_timeout_seconds", 0.001)

    async def slow_handler(request: Any) -> Any:
        await asyncio.sleep(1.0)
        return None

    wrapped = provider._timed(slow_handler, "TEST slow")
    with _test_client(app):
        # drive the wrapper directly on a fresh event loop
        loop = asyncio.new_event_loop()
        try:

            class _FakeRequest:
                headers: ClassVar[dict[str, str]] = {}

            import json as json_mod

            response = loop.run_until_complete(wrapped(_FakeRequest()))
            assert response.status_code == 504
            body = json_mod.loads(response.body.decode("utf-8"))
        finally:
            loop.close()
    assert body["error"]["code"] == "REQUEST_TIMEOUT"
    object.__setattr__(provider._config, "request_timeout_seconds", 30.0)


def test_payload_size_bound_rejected(active_runtime: Runtime) -> None:
    """Payloads beyond max_payload_bytes receive the stable error envelope."""
    gw = active_runtime.require(HOST_GATEWAY)
    app = gw.create_asgi_app()
    provider = cast("_GatewayProvider", gw)
    original = provider._config.max_payload_bytes
    object.__setattr__(provider._config, "max_payload_bytes", 64)
    try:
        with _test_client(app) as client:
            big = {"pad": "x" * 500}
            resp = client.post("/api/v1/graphs/validate", json=big)
            assert resp.status_code == 400
            envelope = resp.json()
            assert envelope["status"] == "error"
            assert envelope["error"]["code"] == "INVALID_PAYLOAD"
            assert "exceeds maximum" in envelope["error"]["message"]
    finally:
        object.__setattr__(provider._config, "max_payload_bytes", original)


def test_no_socket_opened_by_import_or_construction() -> None:
    """Import and construction of the gateway never bind a socket."""
    import socket

    script = r"""
import socket
from app.host.gateway import GatewayConfig, _GatewayProvider
provider = _GatewayProvider(GatewayConfig(port=0))
assert provider.is_running is False
assert provider.bound_address is None
import sys
assert "starlette" not in sys.modules and "uvicorn" not in sys.modules
print("no-socket-ok")
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert "no-socket-ok" in result.stdout
    del socket


def test_error_sanitization_no_leakage(active_runtime: Runtime) -> None:
    """Unknown exceptions degrade to a generic message with no path leakage."""
    from app.host.gateway import _safe_error_code_and_message

    leak_marker = "C:/Users/rharu/INTERNAL_MARKER_XYZ_517"
    code, message = _safe_error_code_and_message(
        RuntimeError(f"failed opening {leak_marker}"), "EXPORT_FAILED"
    )
    assert code == "EXPORT_FAILED"
    assert message == "Internal gateway error; see host diagnostics"
    assert leak_marker not in message

    # host-authored execution errors keep their bounded message
    from app.host.execution import ExecutionBudgetExceededError

    code2, message2 = _safe_error_code_and_message(
        ExecutionBudgetExceededError("max_nodes exceeded"), "EXECUTION_FAILED"
    )
    assert code2 == "ExecutionBudgetExceededError"
    assert "max_nodes" in message2


def test_http_level_unknown_and_opaque_graph(active_runtime: Runtime) -> None:
    """Unknown-plugin graphs stay readable; opaque versions return 4xx/5xx."""
    gw = active_runtime.require(HOST_GATEWAY)
    app = gw.create_asgi_app()
    with _test_client(app) as client:
        unknown_graph = {
            "schema_version": 1,
            "spec": {
                "nodes": [
                    {
                        "id": "ghost",
                        "plugin_ref": "indicator.ghost@9.9.9",
                        "operation_id": "compute",
                        "parameters": {},
                    }
                ],
                "edges": [],
                "designated_roots": [],
            },
        }
        resp = client.post(
            "/api/v1/graphs/validate", json={"graph_document": unknown_graph}
        )
        assert resp.status_code == 200
        envelope = resp.json()
        assert envelope["status"] == "success"
        result = envelope["data"]
        assert result["can_execute"] is False
        assert any(i["code"] == "UNAVAILABLE_PLUGIN" for i in result["issues"])
        # structurally intact normalized document for lossless round trip
        assert result["normalized_document"] is not None
        assert result["normalized_document"]["spec"]["nodes"][0]["id"] == "ghost"

        opaque_graph = {"schema_version": 999, "custom": "future-field"}
        resp2 = client.post(
            "/api/v1/graphs/validate", json={"graph_document": opaque_graph}
        )
        envelope2 = resp2.json()
        data2 = envelope2["data"]
        assert data2["can_execute"] is False
        assert any(i["code"] == "UNSUPPORTED_VERSION" for i in data2["issues"])


def test_gateway_emits_request_telemetry(active_runtime: Runtime) -> None:
    """Every dispatched request emits a bounded gateway telemetry event."""
    from app.host.telemetry import HOST_TELEMETRY

    telemetry = active_runtime.require(HOST_TELEMETRY)
    gw = active_runtime.require(HOST_GATEWAY)
    app = gw.create_asgi_app()

    events: list[object] = []

    def handler(event: object) -> None:
        events.append(event)

    subscription = telemetry.subscribe(handler)
    try:
        with _test_client(app) as client:
            resp = client.get("/api/v1/health")
            assert resp.status_code == 200
    finally:
        subscription.close()

    from app.host.telemetry import TelemetryEvent as _Evt

    typed = [cast("_Evt", e) for e in events]
    gateway_events = [e for e in typed if e.name == "gateway.request"]
    assert gateway_events, f"expected gateway.request events, got {events}"
    fields = dict(gateway_events[-1].fields)
    assert fields["route"] == "GET /api/v1/health"
    assert fields["status"] == "completed"
    assert isinstance(fields["elapsed_ms"], float)


def test_timeout_interrupts_cpu_bound_execution(active_runtime: Runtime) -> None:
    """A blocking execution cannot defeat the request timeout.

    The handler offloads execution to a worker thread; when the timeout
    fires the wrapper cancels the execution token, the client receives a
    prompt 504, and the abandoned thread observes cancellation instead of
    running to completion.
    """
    import time as time_mod

    from app.host.catalog import HOST_CATALOG
    from app.host.execution import SingleExecutionResult
    from app.host.gateway import (
        GatewayConfig as _Cfg,
    )
    from app.host.gateway import (
        _GatewayProvider as _Provider,
    )

    class _BlockingExecution:
        def __init__(self) -> None:
            self.saw_cancellation = False
            self.ran_to_completion = False

        def execute(self, request: Any) -> SingleExecutionResult:
            deadline = time_mod.monotonic() + 10.0
            while time_mod.monotonic() < deadline:
                if request.cancellation is not None and request.cancellation.cancelled:
                    self.saw_cancellation = True
                    return SingleExecutionResult(success=False)
                time_mod.sleep(0.01)
            self.ran_to_completion = True
            return SingleExecutionResult(success=True)

        def execute_batch(self, request: Any) -> Any:
            return self.execute(request)

        def export(self, request: Any) -> Any:
            return None

    catalog = active_runtime.require(HOST_CATALOG)
    stub = _BlockingExecution()
    provider = _Provider(_Cfg(port=0, request_timeout_seconds=0.2))
    provider.set_dependencies(catalog, stub)
    app = provider.create_asgi_app()

    rsi_node = NodeSpec(
        id="rsi_1",
        plugin_ref=PluginRef("indicator.rsi", (1, 0, 0)),
        operation_id="compute",
        parameters=FrozenObject.from_mapping({"period": 2}),
    )
    doc = GraphDocument(spec=GraphSpec(nodes=(rsi_node,), designated_roots=()))
    payload = {"graph_document": graph_document_to_wire(doc), "inputs": {}}

    with _test_client(app) as client:
        started = time_mod.monotonic()
        response = client.post("/api/v1/executions/evaluate", json=payload)
        elapsed = time_mod.monotonic() - started

    assert response.status_code == 504
    assert response.json()["error"]["code"] == "REQUEST_TIMEOUT"
    # the 504 arrived promptly despite the 10s blocking loop
    assert elapsed < 5.0
    # the abandoned worker thread observed cancellation
    deadline = time_mod.monotonic() + 5.0
    while not stub.saw_cancellation and time_mod.monotonic() < deadline:
        time_mod.sleep(0.05)
    assert stub.saw_cancellation is True
    assert stub.ran_to_completion is False


def test_select_rejects_body_provided_authorization(active_runtime: Runtime) -> None:
    """Entitlement claims in the body are rejected; policy is host-owned."""
    gateway = active_runtime.require(HOST_GATEWAY)
    app = gateway.create_asgi_app()
    with _test_client(app) as client:
        resp = client.post(
            "/api/v1/catalog/select",
            json={"enabled_refs": [], "permissions": ["admin:all"]},
        )
        assert resp.status_code == 400
        envelope = resp.json()
        assert envelope["error"]["code"] == "AUTHORIZATION_FIELDS_REJECTED"

        resp2 = client.post(
            "/api/v1/catalog/select",
            json={"enabled_refs": [], "available_capabilities": ["host.jobs"]},
        )
        assert resp2.status_code == 400

        # narrowing the effect policy is allowed; widening is not
        resp3 = client.post(
            "/api/v1/catalog/select",
            json={"enabled_refs": [], "allowed_effects": ["io"]},
        )
        assert resp3.status_code == 200
        data = resp3.json()["data"]
        assert data["available_operations"] == []
        reasons = data["unavailable_reasons"]
        assert reasons and reasons[0]["reason"] == "NOT_ENABLED"


def test_select_grants_host_configured_permissions(active_runtime: Runtime) -> None:
    from app.host.catalog import HOST_CATALOG
    from app.host.gateway import (
        GatewayConfig as _Cfg,
    )
    from app.host.gateway import (
        _GatewayProvider as _Provider,
    )

    catalog = active_runtime.require(HOST_CATALOG)
    provider = _Provider(_Cfg(port=0, permissions=("quant:run",)))
    provider.set_dependencies(catalog, None)
    app = provider.create_asgi_app()
    with _test_client(app) as client:
        resp = client.post(
            "/api/v1/catalog/select",
            json={"enabled_refs": ["indicator.rsi@1.0.0"]},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        ops = data["available_operations"]
        assert ("indicator.rsi@1.0.0", "compute") in [
            (o["plugin_ref"], o["operation_id"]) for o in ops
        ]
