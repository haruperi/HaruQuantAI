"""Deterministic offline end-to-end HTTP gateway usage example for Stage S4.

Run with `uv run python -m tests.examples.gateway_usage`.
"""

from __future__ import annotations

import asyncio
import warnings
from typing import Any

from app.host.bootstrap import approved_catalog_roots, create_runtime
from app.host.gateway import HOST_GATEWAY, GatewayConfig
from app.plugins.algebra import EdgeSpec, GraphDocument, GraphSpec, NodeSpec, PortRef
from app.plugins.schema import EMPTY_FROZEN_OBJECT, FrozenObject
from app.plugins.spec import PluginRef
from app.plugins.wire import graph_document_to_wire
from starlette.testclient import TestClient

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="The anyio.abc.BlockingPortal alias is deprecated.*",
)


def _build_test_graph_wire() -> dict[str, Any]:
    rsi_ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    gt_ref = PluginRef(id="comparison.greater_than", version=(1, 0, 0))
    rsi_node = NodeSpec(
        id="rsi_node",
        plugin_ref=rsi_ref,
        operation_id="compute",
        parameters=FrozenObject.from_mapping({"period": 3}),
    )
    gt_node = NodeSpec(
        id="gt_node",
        plugin_ref=gt_ref,
        operation_id="compare",
        parameters=EMPTY_FROZEN_OBJECT,
    )
    edge = EdgeSpec(
        source=PortRef("rsi_node", "rsi"),
        target=PortRef("gt_node", "left"),
    )
    graph_spec = GraphSpec(
        nodes=(rsi_node, gt_node),
        edges=(edge,),
        designated_roots=(PortRef("rsi_node", "rsi"), PortRef("gt_node", "result")),
    )
    return graph_document_to_wire(GraphDocument(spec=graph_spec))


def _verify_health_and_catalog(client: TestClient) -> None:
    # 1. Health check
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200, resp.text
    health_envelope = resp.json()
    assert health_envelope["status"] == "success"
    assert health_envelope["data"]["status"] == "ready"
    assert health_envelope["data"]["services"]["gateway"] == "ready"
    request_id = resp.headers.get("x-request-id")
    assert request_id is not None and len(request_id) > 0

    # 2. Complete catalog discovery
    resp = client.get("/api/v1/catalog")
    assert resp.status_code == 200, resp.text
    catalog_envelope = resp.json()
    assert catalog_envelope["status"] == "success"
    catalog_entries = catalog_envelope["data"]["entries"]
    refs = {entry["ref"] for entry in catalog_entries}
    assert "indicator.rsi@1.0.0" in refs
    assert "comparison.greater_than@1.0.0" in refs
    assert "exporter.python@1.0.0" in refs
    assert "workspace.builder@1.0.0" in refs
    assert "workspace.results@1.0.0" in refs

    # 3. Filtered catalog selection
    resp = client.post(
        "/api/v1/catalog/select",
        json={"enabled_refs": ["indicator.rsi@1.0.0"]},
    )
    assert resp.status_code == 200, resp.text
    select_envelope = resp.json()
    assert select_envelope["status"] == "success"
    available_ops = select_envelope["data"]["available_operations"]
    rsi_ops = {
        op["operation_id"]
        for op in available_ops
        if op["plugin_ref"] == "indicator.rsi@1.0.0"
    }
    assert "compute" in rsi_ops


def _verify_execution_and_export(
    client: TestClient,
    doc_wire: dict[str, Any],
) -> None:
    # 4. Graph validation
    resp = client.post(
        "/api/v1/graphs/validate",
        json={"graph_document": doc_wire},
    )
    assert resp.status_code == 200, resp.text
    validate_envelope = resp.json()
    assert validate_envelope["status"] == "success"
    assert validate_envelope["data"]["can_execute"] is True
    assert validate_envelope["data"]["issues"] == []

    # 5. Single execution evaluation
    prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
    threshold = [70.0, 70.0, 70.0, 70.0, 70.0, 70.0]
    resp = client.post(
        "/api/v1/executions/evaluate",
        json={
            "graph_document": doc_wire,
            "inputs": {"values": prices, "gt_node.right": threshold},
        },
    )
    assert resp.status_code == 200, resp.text
    exec_envelope = resp.json()
    assert exec_envelope["status"] == "success"
    exec_data = exec_envelope["data"]
    assert exec_data["success"] is True
    assert "rsi_node.rsi" in exec_data["outputs"]
    assert "gt_node.result" in exec_data["outputs"]
    assert exec_data["reproducibility"] is not None

    # 6. Batch execution trials
    resp = client.post(
        "/api/v1/executions/batch",
        json={
            "graph_document": doc_wire,
            "inputs": {"values": prices, "gt_node.right": threshold},
            "trials": [
                {
                    "trial_id": "trial_fast",
                    "parameter_overrides": {"rsi_node": {"period": 2}},
                },
                {
                    "trial_id": "trial_slow",
                    "parameter_overrides": {"rsi_node": {"period": 4}},
                },
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    batch_envelope = resp.json()
    assert batch_envelope["status"] == "success"
    assert len(batch_envelope["data"]["trials"]) == 2
    assert batch_envelope["data"]["success"] is True

    # 7. Semantic IR lowering and Python export
    resp = client.post(
        "/api/v1/exports",
        json={
            "graph_document": doc_wire,
            "target": {"target_id": "python", "version": [1, 0, 0]},
        },
    )
    assert resp.status_code == 200, resp.text
    export_envelope = resp.json()
    assert export_envelope["status"] == "success"
    source_code = export_envelope["data"]["source_code"]
    assert "def execute(" in source_code

    # Execute the exported Python code and verify outputs
    scope: dict[str, Any] = {}
    exec(source_code, scope)
    exported_func = scope["execute"]
    exported_res = exported_func({"values": tuple(prices), "right": tuple(threshold)})
    assert "gt_node_result" in exported_res
    assert len(exported_res["gt_node_result"]) == len(prices)


async def run_gateway_example() -> None:
    """Execute end-to-end HTTP gateway API calls against in-process runtime."""
    roots = approved_catalog_roots()
    async with create_runtime(
        catalog_roots=roots,
        gateway_config=GatewayConfig(),
        gateway_auto_start=False,
    ) as runtime:
        gateway = runtime.require(HOST_GATEWAY)
        app = gateway.create_asgi_app()
        doc_wire = _build_test_graph_wire()

        with TestClient(app) as client:
            _verify_health_and_catalog(client)
            _verify_execution_and_export(client, doc_wire)


def main() -> None:
    """Entry point for gateway usage example."""
    asyncio.run(run_gateway_example())


if __name__ == "__main__":
    main()
