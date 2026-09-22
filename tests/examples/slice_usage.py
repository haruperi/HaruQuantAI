"""Deterministic offline end-to-end slice example for Stage S3.

Run with `uv run python -m tests.examples.slice_usage`.
"""

import asyncio
from typing import Any

from app.host.bootstrap import approved_catalog_roots, create_runtime
from app.host.catalog import HOST_CATALOG
from app.host.execution import (
    HOST_EXECUTION,
    BatchExecutionRequest,
    BatchTrial,
    ExportRequest,
    SingleExecutionRequest,
)
from app.plugins.algebra import EdgeSpec, GraphDocument, GraphSpec, NodeSpec, PortRef
from app.plugins.schema import EMPTY_FROZEN_OBJECT, FrozenObject, MissingValue
from app.plugins.spec import PluginRef


def _build_graph_doc() -> GraphDocument:
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
    return GraphDocument(spec=graph_spec)


def _verify_single_execution(
    execution: Any, doc: GraphDocument, inputs: dict[str, Any]
) -> tuple[Any, ...]:
    single_req = SingleExecutionRequest(graph_document=doc, inputs=inputs)
    single_res = execution.execute(single_req)
    assert single_res.success
    assert single_res.reproducibility is not None

    rsi_series = single_res.outputs["rsi_node.rsi"]
    gt_series = single_res.outputs["gt_node.result"]
    assert len(rsi_series) == 6
    assert isinstance(rsi_series[0], MissingValue)
    assert isinstance(rsi_series[1], MissingValue)
    assert isinstance(rsi_series[2], MissingValue)
    assert rsi_series[3] == 100.0
    assert gt_series[3] is True
    return tuple(gt_series)


def _verify_batch_trials(
    execution: Any, doc: GraphDocument, inputs: dict[str, Any]
) -> None:
    trials = (
        BatchTrial(
            trial_id="period_2",
            parameter_overrides={"rsi_node": FrozenObject.from_mapping({"period": 2})},
        ),
        BatchTrial(
            trial_id="period_3",
            parameter_overrides={"rsi_node": FrozenObject.from_mapping({"period": 3})},
        ),
        BatchTrial(
            trial_id="period_4",
            parameter_overrides={"rsi_node": FrozenObject.from_mapping({"period": 4})},
        ),
    )
    batch_req = BatchExecutionRequest(graph_document=doc, inputs=inputs, trials=trials)
    batch_res = execution.execute_batch(batch_req)
    assert batch_res.success
    assert len(batch_res.trials) == 3


def _verify_export_parity(
    execution: Any,
    doc: GraphDocument,
    prices: tuple[float, ...],
    threshold: tuple[float, ...],
    gt_series: tuple[Any, ...],
) -> None:
    export_req = ExportRequest(graph_document=doc)
    export_res = execution.export(export_req)
    assert export_res.success
    assert export_res.source_code is not None
    assert export_res.manifest is not None
    assert export_res.manifest["target_id"] == "python"

    namespace: dict[str, Any] = {}
    exec(export_res.source_code, namespace)
    run_fn = namespace["execute"]
    exported_out = run_fn({"values": prices, "right": threshold})

    assert len(exported_out["gt_node_result"]) == len(gt_series)
    for n_v, e_v in zip(gt_series, exported_out["gt_node_result"], strict=True):
        if isinstance(n_v, MissingValue):
            assert type(e_v).__name__ == "MissingValue"
        else:
            assert n_v == e_v


async def example_slice() -> None:
    """Execute end-to-end quantitative slice: catalog, execution, batch trials, and export."""
    roots = approved_catalog_roots()
    async with create_runtime(catalog_roots=roots) as runtime:
        catalog = runtime.require(HOST_CATALOG)
        execution = runtime.require(HOST_EXECUTION)

        # 1. Verify approved plugins discovery
        snapshot = catalog.snapshot()
        entry_ids = {e.ref.id for e in snapshot.view.entries}
        assert "indicator.rsi" in entry_ids
        assert "comparison.greater_than" in entry_ids
        assert "exporter.python" in entry_ids

        # 2. Build quantitative graph
        doc = _build_graph_doc()

        # 3. Single execution
        prices = (10.0, 11.0, 12.0, 13.0, 14.0, 15.0)
        threshold = (70.0, 70.0, 70.0, 70.0, 70.0, 70.0)
        inputs = {"values": prices, "gt_node.right": threshold}
        gt_series = _verify_single_execution(execution, doc, inputs)

        # 4. Batch parameter trials
        _verify_batch_trials(execution, doc, inputs)

        # 5. Semantic IR lowering and Python export
        _verify_export_parity(execution, doc, prices, threshold, gt_series)


if __name__ == "__main__":
    asyncio.run(example_slice())
