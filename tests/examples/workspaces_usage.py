"""Deterministic offline primary-purpose usage scenario for Tier 1 Workspaces.

Demonstrates discovering and utilizing the 4 Tier 1 workspaces
(Builder, Retester, Optimizer, Results) through public catalog
introspection, graph validation, and host execution boundaries.

Run with: `uv run python -m tests.examples.workspaces_usage`
"""

from __future__ import annotations

import asyncio

from app.host.bootstrap import approved_catalog_roots, create_runtime
from app.host.catalog import HOST_CATALOG, SelectionRequest
from app.host.execution import (
    HOST_EXECUTION,
    BatchExecutionRequest,
    BatchTrial,
    ExportRequest,
    SingleExecutionRequest,
)
from app.plugins.algebra import EdgeSpec, GraphDocument, GraphSpec, NodeSpec, PortRef
from app.plugins.schema import EMPTY_FROZEN_OBJECT, FrozenArray, FrozenObject
from app.plugins.spec import PluginRef


def _build_strategy_graph() -> GraphDocument:
    """Construct an indicator and comparison strategy graph."""
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
        designated_roots=(
            PortRef("rsi_node", "rsi"),
            PortRef("gt_node", "result"),
        ),
    )
    return GraphDocument(spec=graph_spec)


async def run_workspaces_usage() -> None:
    """Execute end-to-end workspaces usage flow."""
    roots = approved_catalog_roots()
    async with create_runtime(catalog_roots=roots) as runtime:
        catalog = runtime.require(HOST_CATALOG)
        execution = runtime.require(HOST_EXECUTION)

        # 1. Discover all 4 Tier 1 Workspaces
        snapshot = catalog.snapshot()
        builder = snapshot.view.get_entry_by_id("workspace.builder")
        retester = snapshot.view.get_entry_by_id("workspace.retester")
        optimizer = snapshot.view.get_entry_by_id("workspace.optimizer")
        results = snapshot.view.get_entry_by_id("workspace.results")

        assert builder is not None and builder.workspace is not None, (
            "Builder workspace not discovered"
        )
        assert retester is not None and retester.workspace is not None, (
            "Retester workspace not discovered"
        )
        assert optimizer is not None and optimizer.workspace is not None, (
            "Optimizer workspace not discovered"
        )
        assert results is not None and results.workspace is not None, (
            "Results workspace not discovered"
        )
        assert any(
            cmd.command_id == "generate_genetic" for cmd in builder.workspace.commands
        )
        assert any(
            cmd.command_id == "trading_metrics" for cmd in results.workspace.commands
        )

        # 2. Builder Workflow: Validate AST and evaluate single graph execution
        doc = _build_strategy_graph()
        prices = [44.0, 44.25, 44.5, 43.75, 44.1, 44.6]
        threshold = [50.0, 50.0, 50.0, 50.0, 50.0, 50.0]
        inputs = {"values": prices, "gt_node.right": threshold}

        single_req = SingleExecutionRequest(graph_document=doc, inputs=inputs)
        single_res = execution.execute(single_req)
        assert single_res.success, f"Builder evaluation failed: {single_res.issues}"
        assert "rsi_node.rsi" in single_res.outputs
        assert "gt_node.result" in single_res.outputs

        # 3. Retester Workflow: Bounded batch evaluation of parameter variants
        trial_fast = BatchTrial(
            trial_id="fast_period",
            parameter_overrides={"rsi_node": FrozenObject.from_mapping({"period": 2})},
        )
        trial_slow = BatchTrial(
            trial_id="slow_period",
            parameter_overrides={"rsi_node": FrozenObject.from_mapping({"period": 4})},
        )
        batch_req = BatchExecutionRequest(
            graph_document=doc,
            trials=(trial_fast, trial_slow),
            inputs=inputs,
        )
        batch_res = execution.execute_batch(batch_req)
        assert batch_res.success
        assert len(batch_res.trials) == 2

        # 4. Optimizer Workflow: Explicit user parameter trial combinations
        # Verify that deferred optimization commands remain unavailable in catalog
        select_req = SelectionRequest(allowed_kinds=optimizer.workspace.accepted_kinds)
        selection = catalog.select(select_req)
        # Verify no unbacked genetic optimization algorithm is admitted
        assert not any("genetic" in op[1] for op in selection.available_operations)

        # 5. Results Workflow: Inspect outputs, reproducibility, and export code
        rsi_out = single_res.outputs["rsi_node.rsi"]
        assert isinstance(rsi_out, (list, tuple, FrozenArray))
        assert len(rsi_out) == len(prices)
        assert single_res.reproducibility is not None
        assert single_res.reproducibility.elapsed_seconds >= 0

        # Export lowered code to python
        export_req = ExportRequest(graph_document=doc)
        export_res = execution.export(export_req)
        assert export_res.success
        assert export_res.source_code is not None
        assert len(export_res.source_code) > 0


if __name__ == "__main__":
    asyncio.run(run_workspaces_usage())
