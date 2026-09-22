"""Comprehensive tests for host execution: single-run, batch trials, and export."""

import asyncio
from pathlib import Path
from typing import Any

import pytest
from app.host.bootstrap import approved_catalog_roots, create_runtime
from app.host.catalog import HOST_CATALOG
from app.host.execution import (
    HOST_EXECUTION,
    BatchExecutionRequest,
    BatchTrial,
    ExecutionBudget,
    ExecutionBudgetExceededError,
    ExportRequest,
    SingleExecutionRequest,
)
from app.plugins.algebra import (
    EdgeSpec,
    GraphDocument,
    GraphSpec,
    NodeSpec,
    OpaqueGraphDocument,
    PortRef,
)
from app.plugins.schema import (
    EMPTY_FROZEN_OBJECT,
    FrozenArray,
    FrozenObject,
    MissingValue,
)
from app.plugins.spec import PluginRef


def _build_slice_graph() -> GraphDocument:
    """Build a graph: values -> RSI(period=3) -> GreaterThan(70.0) -> result."""
    rsi_ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
    gt_ref = PluginRef(id="comparison.greater_than", version=(1, 0, 0))

    rsi_node = NodeSpec(
        id="rsi_1",
        plugin_ref=rsi_ref,
        operation_id="compute",
        parameters=FrozenObject.from_mapping({"period": 3}),
    )
    gt_node = NodeSpec(
        id="gt_1",
        plugin_ref=gt_ref,
        operation_id="compare",
        parameters=EMPTY_FROZEN_OBJECT,
    )

    edge = EdgeSpec(
        source=PortRef("rsi_1", "rsi"),
        target=PortRef("gt_1", "left"),
    )

    spec = GraphSpec(
        nodes=(rsi_node, gt_node),
        edges=(edge,),
        designated_roots=(PortRef("gt_1", "result"), PortRef("rsi_1", "rsi")),
    )
    return GraphDocument(spec=spec)


def test_execution_single_run_and_reproducibility() -> None:
    async def scenario() -> None:
        roots = approved_catalog_roots()
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            catalog = runtime.require(HOST_CATALOG)
            execution = runtime.require(HOST_EXECUTION)

            assert catalog.is_ready()
            snapshot = catalog.snapshot()
            assert len(snapshot.view.entries) >= 3

            doc = _build_slice_graph()

            # Rising prices -> RSI hits 100.0, which is > 70.0 (True)
            prices = (10.0, 11.0, 12.0, 13.0, 14.0)
            threshold = (70.0, 70.0, 70.0, 70.0, 70.0)

            inputs = {
                "values": prices,
                "gt_1.right": threshold,
            }

            req = SingleExecutionRequest(graph_document=doc, inputs=inputs)
            res = execution.execute(req)

            assert res.success
            assert res.reproducibility is not None

            rsi_out = res.outputs["rsi_1.rsi"]
            gt_out = res.outputs["gt_1.result"]
            assert isinstance(rsi_out, FrozenArray)
            assert isinstance(gt_out, FrozenArray)

            # 5 prices with period 3:
            # i=0, 1, 2 are WARMUP
            # i=3: seed RSI (100.0) -> gt 70.0 is True
            # i=4: smoothed RSI (100.0) -> gt 70.0 is True
            assert isinstance(rsi_out[0], MissingValue)
            assert isinstance(rsi_out[1], MissingValue)
            assert isinstance(rsi_out[2], MissingValue)
            assert rsi_out[3] == 100.0
            assert rsi_out[4] == 100.0

            assert isinstance(gt_out[0], MissingValue)
            assert isinstance(gt_out[1], MissingValue)
            assert isinstance(gt_out[2], MissingValue)
            assert gt_out[3] is True
            assert gt_out[4] is True

            # Check reproducibility record
            repro = res.reproducibility
            assert repro.catalog_fingerprint == snapshot.whole_fingerprint
            assert repro.dependency_fingerprint != ""
            assert repro.status == "completed"

    asyncio.run(scenario())


def test_execution_batch_trials() -> None:
    async def scenario() -> None:
        roots = approved_catalog_roots()
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            execution = runtime.require(HOST_EXECUTION)
            doc = _build_slice_graph()

            prices = (10.0, 11.0, 12.0, 13.0, 14.0, 15.0)
            threshold = (70.0, 70.0, 70.0, 70.0, 70.0, 70.0)
            inputs = {"values": prices, "gt_1.right": threshold}

            trials = (
                BatchTrial(
                    trial_id="period_2",
                    parameter_overrides={
                        "rsi_1": FrozenObject.from_mapping({"period": 2})
                    },
                ),
                BatchTrial(
                    trial_id="period_3",
                    parameter_overrides={
                        "rsi_1": FrozenObject.from_mapping({"period": 3})
                    },
                ),
                BatchTrial(
                    trial_id="period_4",
                    parameter_overrides={
                        "rsi_1": FrozenObject.from_mapping({"period": 4})
                    },
                ),
            )

            batch_req = BatchExecutionRequest(
                graph_document=doc,
                inputs=inputs,
                trials=trials,
            )
            batch_res = execution.execute_batch(batch_req)

            assert batch_res.success
            assert len(batch_res.trials) == 3

            # Trial 1 (period 2): seed at index 2
            t1_rsi = batch_res.trials[0].result.outputs["rsi_1.rsi"]
            assert isinstance(t1_rsi, FrozenArray)
            assert isinstance(t1_rsi[1], MissingValue)
            assert t1_rsi[2] == 100.0

            # Trial 2 (period 3): seed at index 3
            t2_rsi = batch_res.trials[1].result.outputs["rsi_1.rsi"]
            assert isinstance(t2_rsi, FrozenArray)
            assert isinstance(t2_rsi[2], MissingValue)
            assert t2_rsi[3] == 100.0

            # Trial 3 (period 4): seed at index 4
            t3_rsi = batch_res.trials[2].result.outputs["rsi_1.rsi"]
            assert isinstance(t3_rsi, FrozenArray)
            assert isinstance(t3_rsi[3], MissingValue)
            assert t3_rsi[4] == 100.0

    asyncio.run(scenario())


def test_execution_budget_enforcement() -> None:
    async def scenario() -> None:
        roots = approved_catalog_roots()
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            execution = runtime.require(HOST_EXECUTION)
            doc = _build_slice_graph()

            # Exceed node count
            tight_budget = ExecutionBudget(max_nodes=1)
            req = SingleExecutionRequest(
                graph_document=doc,
                inputs={"values": (10.0,)},
                budget=tight_budget,
            )
            with pytest.raises(ExecutionBudgetExceededError, match="node count"):
                execution.execute(req)

            # Exceed sample count
            tight_samples = ExecutionBudget(max_samples=2)
            req_samples = SingleExecutionRequest(
                graph_document=doc,
                inputs={"values": (10.0, 11.0, 12.0), "gt_1.right": (5.0, 5.0, 5.0)},
                budget=tight_samples,
            )
            with pytest.raises(ExecutionBudgetExceededError, match="samples"):
                execution.execute(req_samples)

    asyncio.run(scenario())


def test_execution_unsupported_opaque_document() -> None:
    async def scenario() -> None:
        roots = approved_catalog_roots()
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            execution = runtime.require(HOST_EXECUTION)
            opaque_doc = OpaqueGraphDocument(
                schema_version=999, raw_data=EMPTY_FROZEN_OBJECT
            )
            req = SingleExecutionRequest(graph_document=opaque_doc)
            res = execution.execute(req)
            assert not res.success
            assert any(i.code == "UNSUPPORTED_VERSION" for i in res.issues)

    asyncio.run(scenario())


def test_execution_export_parity() -> None:
    async def scenario() -> None:
        roots = approved_catalog_roots()
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            execution = runtime.require(HOST_EXECUTION)
            doc = _build_slice_graph()

            export_req = ExportRequest(graph_document=doc)
            export_res = execution.export(export_req)

            assert export_res.success
            assert export_res.source_code is not None
            assert export_res.manifest is not None

            # Execute native
            prices = (10.0, 12.0, 11.0, 13.0, 14.0)
            threshold = (70.0, 70.0, 70.0, 70.0, 70.0)
            inputs = {"values": prices, "gt_1.right": threshold}

            native_res = execution.execute(
                SingleExecutionRequest(graph_document=doc, inputs=inputs)
            )
            assert native_res.success

            # Execute emitted Python in isolated exec()
            namespace: dict[str, Any] = {}
            exec(export_res.source_code, namespace)
            run_fn = namespace["execute"]
            exported_out = run_fn({"values": prices, "right": threshold})

            # Compare outputs
            native_gt = native_res.outputs["gt_1.result"]
            exported_gt = exported_out["gt_1_result"]
            assert isinstance(native_gt, FrozenArray)
            assert isinstance(exported_gt, (tuple, list))
            assert len(native_gt) == len(exported_gt)

            for n_v, e_v in zip(native_gt, exported_gt, strict=True):
                if isinstance(n_v, MissingValue):
                    assert type(e_v).__name__ == "MissingValue"
                else:
                    assert n_v == e_v

    asyncio.run(scenario())


def test_fingerprint_stability_with_unrelated_plugin_change(tmp_path: Path) -> None:
    """Removing/adding an unrelated plugin changes whole catalog fingerprint but preserves dependency fingerprint."""
    # Create a temp indicators root with rsi and dummy indicator
    ind_dir = tmp_path / "indicators"
    ind_dir.mkdir()

    # Copy rsi.py content to ind_dir
    rsi_src = (
        Path(__file__).resolve().parent.parent.parent
        / "app"
        / "plugins"
        / "indicators"
        / "rsi.py"
    ).read_text(encoding="utf-8")
    (ind_dir / "rsi.py").write_text(rsi_src, encoding="utf-8")

    # Dummy indicator
    dummy_src = '''"""Dummy indicator."""
from app.plugins.spec import PluginRef, PluginSpec, OperationSpec, PluginContribution, OperationContribution, OperationImplementation
from app.plugins.schema import ParameterSchema, PortSpec, ValueKind, ParameterBindingResult, FrozenObject
from app.plugins.lowering import LoweringResult

class DummyOp(OperationImplementation):
    def validate_parameters(self, v): return ParameterBindingResult(True)
    def warmup_samples(self, v): return 0
    def execute(self, i, p, b): return {"out": ()}
    def lower(self, c, p): return LoweringResult(True)

def plugin():
    op = OperationSpec(operation_id="compute", title="Dummy", inputs=(), outputs=(PortSpec(key="out", kind=ValueKind.NUMBER),))
    spec = PluginSpec(ref=PluginRef(id="indicator.dummy", version=(1, 0, 0)), kind="indicator", title="Dummy", operations=(op,))
    return PluginContribution(spec=spec, operations=(OperationContribution("compute", DummyOp()),))
'''
    dummy_file = ind_dir / "dummy.py"
    dummy_file.write_text(dummy_src, encoding="utf-8")

    comp_dir = (
        Path(__file__).resolve().parent.parent.parent
        / "app"
        / "plugins"
        / "comparisons"
    )
    exp_dir = (
        Path(__file__).resolve().parent.parent.parent / "app" / "plugins" / "exporters"
    )

    from app.host.catalog import CatalogRoot

    roots = (
        CatalogRoot("indicators", ind_dir, ("indicator",)),
        CatalogRoot("comparisons", comp_dir, ("comparison",)),
        CatalogRoot("exporters", exp_dir, ("exporter",)),
    )

    def remove_dummy() -> None:
        dummy_file.unlink()

    async def scenario() -> None:
        runtime = create_runtime(catalog_roots=roots)
        async with runtime:
            catalog = runtime.require(HOST_CATALOG)
            execution = runtime.require(HOST_EXECUTION)

            doc = _build_slice_graph()
            inputs = {
                "values": (10.0, 11.0, 12.0, 13.0, 14.0),
                "gt_1.right": (70.0,) * 5,
            }

            res1 = execution.execute(
                SingleExecutionRequest(graph_document=doc, inputs=inputs)
            )
            assert res1.success
            assert res1.reproducibility is not None
            dep_fp_1 = res1.reproducibility.dependency_fingerprint
            cat_fp_1 = res1.reproducibility.catalog_fingerprint

            # Now remove dummy.py and refresh catalog
            remove_dummy()
            refresh_res = catalog.refresh()
            assert refresh_res.success

            res2 = execution.execute(
                SingleExecutionRequest(graph_document=doc, inputs=inputs)
            )
            assert res2.success
            assert res2.reproducibility is not None
            dep_fp_2 = res2.reproducibility.dependency_fingerprint
            cat_fp_2 = res2.reproducibility.catalog_fingerprint

            # Whole catalog fingerprint must have changed
            assert cat_fp_1 != cat_fp_2
            # Dependency fingerprint for slice graph must remain IDENTICAL!
            assert dep_fp_1 == dep_fp_2
            # Output values must remain IDENTICAL!
            assert res1.outputs == res2.outputs

    asyncio.run(scenario())


def test_execution_cancellation_surface() -> None:
    async def scenario() -> None:
        from app.host.execution import CancellationToken

        roots = approved_catalog_roots()
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            execution = runtime.require(HOST_EXECUTION)
            doc = _build_slice_graph()
            inputs = {
                "values": (10.0, 11.0, 12.0, 13.0, 14.0),
                "gt_1.right": (70.0,) * 5,
            }

            # Pre-cancelled token: run fails with the attributed issue
            token = CancellationToken()
            token.cancel()
            res = execution.execute(
                SingleExecutionRequest(
                    graph_document=doc, inputs=inputs, cancellation=token
                )
            )
            assert not res.success
            assert any(i.code == "EXECUTION_CANCELLED" for i in res.issues)
            assert res.outputs == EMPTY_FROZEN_OBJECT
            assert res.reproducibility is None

            # Run-owned state was discarded: a fresh run after cancellation
            # produces the identical result as an untouched run
            clean = execution.execute(
                SingleExecutionRequest(graph_document=doc, inputs=inputs)
            )
            after = execution.execute(
                SingleExecutionRequest(graph_document=doc, inputs=inputs)
            )
            assert clean.success and after.success
            assert clean.reproducibility is not None
            assert after.reproducibility is not None
            assert (
                after.reproducibility.output_hash == clean.reproducibility.output_hash
            )

            # Batch: pre-cancelled token stops before any trial; an uncancelled
            # token leaves the identical batch succeeding
            cancelled_batch_token = CancellationToken()
            cancelled_batch_token.cancel()
            trials = (
                BatchTrial(
                    trial_id="t1",
                    parameter_overrides={
                        "rsi_1": FrozenObject.from_mapping({"period": 2})
                    },
                ),
            )
            batch = execution.execute_batch(
                BatchExecutionRequest(
                    graph_document=doc,
                    inputs=inputs,
                    trials=trials,
                    cancellation=cancelled_batch_token,
                )
            )
            assert not batch.success
            assert batch.trials == ()
            assert any(i.code == "EXECUTION_CANCELLED" for i in batch.issues)

            uncancelled = execution.execute_batch(
                BatchExecutionRequest(
                    graph_document=doc,
                    inputs=inputs,
                    trials=trials,
                    cancellation=CancellationToken(),
                )
            )
            assert uncancelled.success
            assert len(uncancelled.trials) == 1

    asyncio.run(scenario())


def test_execution_deterministic_repeats_and_concurrent_runs() -> None:
    async def scenario() -> None:
        from concurrent.futures import ThreadPoolExecutor

        roots = approved_catalog_roots()
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            execution = runtime.require(HOST_EXECUTION)
            doc = _build_slice_graph()
            inputs = {
                "values": (10.0, 12.0, 11.0, 13.0, 14.0, 10.0, 15.0),
                "gt_1.right": (70.0,) * 7,
            }

            def run_once() -> tuple[bool, str]:
                res = execution.execute(
                    SingleExecutionRequest(graph_document=doc, inputs=inputs)
                )
                assert res.reproducibility is not None
                return res.success, res.reproducibility.output_hash

            ok1, hash1 = run_once()
            ok2, hash2 = run_once()
            assert ok1 and ok2 and hash1 == hash2

            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda _: run_once(), range(8)))
            assert all(ok for ok, _ in results)
            assert len({h for _, h in results}) == 1

    asyncio.run(scenario())


def test_batch_trials_derived_from_descriptor_optimization_domain() -> None:
    async def scenario() -> None:
        roots = approved_catalog_roots()
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            catalog = runtime.require(HOST_CATALOG)
            execution = runtime.require(HOST_EXECUTION)

            rsi_ref = PluginRef(id="indicator.rsi", version=(1, 0, 0))
            entry = catalog.snapshot().view.get_entry(rsi_ref)
            assert entry is not None
            op = entry.operations[0]
            period_param = op.parameters.get("period")
            assert period_param is not None
            domain = period_param.optimization
            assert domain is not None
            assert domain.min_value is not None
            assert domain.max_value is not None
            assert domain.step is not None

            periods = [
                int(domain.min_value),
                int(domain.min_value + domain.step),
                int(domain.min_value + 3 * domain.step),
            ]
            doc = _build_slice_graph()
            prices = tuple(10.0 + i for i in range(max(periods) + 4))
            inputs = {"values": prices, "gt_1.right": (70.0,) * len(prices)}

            trials = tuple(
                BatchTrial(
                    trial_id=f"period_{p}",
                    parameter_overrides={
                        "rsi_1": FrozenObject.from_mapping({"period": p})
                    },
                )
                for p in periods
            )
            batch = execution.execute_batch(
                BatchExecutionRequest(graph_document=doc, inputs=inputs, trials=trials)
            )
            assert batch.success
            assert len(batch.trials) == len(periods)

            for trial, period in zip(batch.trials, periods, strict=True):
                rsi_out = trial.result.outputs["rsi_1.rsi"]
                assert isinstance(rsi_out, FrozenArray)
                assert isinstance(rsi_out[period - 1], MissingValue)
                assert not isinstance(rsi_out[period], MissingValue)

    asyncio.run(scenario())


def test_reproducibility_records_warmup_and_policies() -> None:
    async def scenario() -> None:
        roots = approved_catalog_roots()
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            execution = runtime.require(HOST_EXECUTION)
            doc = _build_slice_graph()
            inputs = {
                "values": (10.0, 11.0, 12.0, 13.0, 14.0),
                "gt_1.right": (70.0,) * 5,
            }
            res = execution.execute(
                SingleExecutionRequest(graph_document=doc, inputs=inputs)
            )
            assert res.success and res.reproducibility is not None
            repro = res.reproducibility
            assert dict(repro.node_warmup_samples)["rsi_1"] == 3
            assert dict(repro.node_warmup_samples)["gt_1"] == 0
            assert {nid for nid, _ in repro.node_policies} == {"rsi_1", "gt_1"}

    asyncio.run(scenario())


def test_export_unsupported_target_attributed_to_node() -> None:
    async def scenario() -> None:
        from app.plugins.lowering import LoweringTarget

        roots = approved_catalog_roots()
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            execution = runtime.require(HOST_EXECUTION)
            doc = _build_slice_graph()
            res = execution.export(
                ExportRequest(
                    graph_document=doc,
                    target=LoweringTarget(target_id="rust", version=(1, 0, 0)),
                )
            )
            assert not res.success
            from app.plugins.lowering import LoweringIssue

            attributed = [
                i for i in res.issues if isinstance(i, LoweringIssue) and i.node_id
            ]
            assert attributed, f"expected node-attributed issues, got {res.issues}"
            assert all(i.node_id in {"rsi_1", "gt_1"} for i in attributed)

    asyncio.run(scenario())


BOGUS_LOWERING_SOURCE = '''"""Bogus lowering plugin for attribution testing."""
from app.plugins.spec import (
    OperationContribution, OperationImplementation, PluginContribution,
    PluginRef, PluginSpec, OperationSpec,
)
from app.plugins.schema import (
    FrozenObject, ParameterBindingResult, PortSpec, ValueKind,
)
from app.plugins.lowering import (
    IRNode, LoweringResult, ProgramInput, ProgramOutput, SemanticProgram,
    ValueRef,
)


class BogusOp(OperationImplementation):
    def validate_parameters(self, v):
        return ParameterBindingResult(True)

    def warmup_samples(self, v):
        return 0

    def execute(self, i, p, b):
        return {"out": ()}

    def lower(self, context, parameters):
        prog = SemanticProgram(
            inputs=(ProgramInput(key="x", kind=ValueKind.NUMBER),),
            nodes=(IRNode(
                id="bogus_1",
                operator="std.nonexistent_op",
                inputs=(),
                parameters=FrozenObject(),
                outputs=("out",),
            ),),
            outputs=(ProgramOutput(
                key="out", source=ValueRef("bogus_1", "out"),
                kind=ValueKind.NUMBER,
            ),),
        )
        return LoweringResult(success=True, program=prog)


def plugin():
    op = OperationSpec(
        operation_id="compute",
        title="Bogus",
        inputs=(PortSpec(key="x", kind=ValueKind.NUMBER),),
        outputs=(PortSpec(key="out", kind=ValueKind.NUMBER),),
    )
    spec = PluginSpec(
        ref=PluginRef(id="indicator.bogus", version=(1, 0, 0)),
        kind="indicator", title="Bogus", operations=(op,),
    )
    return PluginContribution(
        spec=spec, operations=(OperationContribution("compute", BogusOp()),)
    )
'''


def test_export_unsupported_primitive_attributed(tmp_path: Path) -> None:
    from app.host.catalog import CatalogRoot

    ind_dir = tmp_path / "indicators"
    ind_dir.mkdir()
    (ind_dir / "bogus.py").write_text(BOGUS_LOWERING_SOURCE, encoding="utf-8")
    exp_dir = (
        Path(__file__).resolve().parent.parent.parent / "app" / "plugins" / "exporters"
    )
    roots = (
        CatalogRoot("indicators", ind_dir, ("indicator",)),
        CatalogRoot("exporters", exp_dir, ("exporter",)),
    )

    async def scenario() -> None:
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            execution = runtime.require(HOST_EXECUTION)
            node = NodeSpec(
                id="bogus_1",
                plugin_ref=PluginRef(id="indicator.bogus", version=(1, 0, 0)),
                operation_id="compute",
            )
            doc = GraphDocument(
                spec=GraphSpec(
                    nodes=(node,), designated_roots=(PortRef("bogus_1", "out"),)
                )
            )
            res = execution.export(ExportRequest(graph_document=doc))
            assert not res.success
            # unknown primitives are rejected at IR construction, attributed
            # to the offending node during lowering
            from app.plugins.schema import ValidationIssue

            assert any(
                isinstance(i, ValidationIssue)
                and i.code == "LOWERING_FAILED"
                and "nonexistent_op" in i.message
                and i.path == "nodes.bogus_1"
                for i in res.issues
            ), res.issues

    asyncio.run(scenario())


def test_temporary_comparison_plugin_addition(tmp_path: Path) -> None:
    """A new comparison joins the family without editing shared sources."""

    from app.host.catalog import CatalogRoot

    comp_dir = tmp_path / "comparisons"
    comp_dir.mkdir()
    gt_path = (
        Path(__file__).resolve().parent.parent.parent
        / "app"
        / "plugins"
        / "comparisons"
        / "greater_than.py"
    )
    gt_src = gt_path.read_text(encoding="utf-8")
    (comp_dir / "greater_than.py").write_text(gt_src, encoding="utf-8")
    less_src = (
        gt_src.replace("comparison.greater_than", "comparison.less_than")
        .replace("Elementwise greater-than", "Elementwise less-than")
        .replace(
            "results.append(bool(float(l_val) > float(r_val)))",
            "results.append(bool(float(l_val) < float(r_val)))",
        )
    )
    (comp_dir / "less_than.py").write_text(less_src, encoding="utf-8")

    ind_dir = gt_path.parent.parent / "indicators"
    roots = (
        CatalogRoot("indicators", ind_dir, ("indicator",)),
        CatalogRoot("comparisons", comp_dir, ("comparison",)),
    )

    async def scenario() -> None:
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            execution = runtime.require(HOST_EXECUTION)
            rsi_node = NodeSpec(
                id="rsi_1",
                plugin_ref=PluginRef(id="indicator.rsi", version=(1, 0, 0)),
                operation_id="compute",
                parameters=FrozenObject.from_mapping({"period": 3}),
            )
            lt_node = NodeSpec(
                id="lt_1",
                plugin_ref=PluginRef(id="comparison.less_than", version=(1, 0, 0)),
                operation_id="compare",
            )
            doc = GraphDocument(
                spec=GraphSpec(
                    nodes=(rsi_node, lt_node),
                    edges=(
                        EdgeSpec(
                            source=PortRef("rsi_1", "rsi"),
                            target=PortRef("lt_1", "left"),
                        ),
                    ),
                    designated_roots=(PortRef("lt_1", "result"),),
                )
            )
            inputs = {
                "values": (10.0, 11.0, 12.0, 13.0, 14.0),
                "lt_1.right": (95.0,) * 5,
            }
            res = execution.execute(
                SingleExecutionRequest(graph_document=doc, inputs=inputs)
            )
            assert res.success
            out = res.outputs["lt_1.result"]
            assert isinstance(out, FrozenArray)
            assert out[4] is False  # rising series: RSI 100 -> 100 < 95 is False

    asyncio.run(scenario())


GOLDEN_SERIES: tuple[tuple[str, tuple[Any, ...]], ...] = (
    ("empty", ()),
    ("single", (10.0,)),
    ("shorter_than_warmup", (10.0, 11.0, 12.0)),
    ("equal_to_warmup", (10.0, 11.0, 12.0, 13.0)),
    ("longer_than_warmup", (10.0, 11.0, 12.0, 13.0, 10.0, 14.0, 15.0)),
    ("flat", (10.0, 10.0, 10.0, 10.0, 10.0, 10.0)),
    ("rising", (10.0, 11.0, 12.0, 13.0, 14.0, 15.0)),
    ("falling", (15.0, 14.0, 13.0, 12.0, 11.0, 10.0)),
    ("gap_reseed", (10.0, 11.0, 12.0, 13.0, None, 12.0, 13.0, 14.0, 15.0, 16.0)),
)


@pytest.mark.parametrize("name,series", GOLDEN_SERIES)
def test_export_parity_on_every_golden(name: str, series: tuple[Any, ...]) -> None:
    async def scenario() -> None:
        rsi_node = NodeSpec(
            id="rsi_1",
            plugin_ref=PluginRef(id="indicator.rsi", version=(1, 0, 0)),
            operation_id="compute",
            parameters=FrozenObject.from_mapping({"period": 3}),
        )
        doc = GraphDocument(
            spec=GraphSpec(
                nodes=(rsi_node,),
                designated_roots=(PortRef("rsi_1", "rsi"),),
            )
        )
        roots = approved_catalog_roots()
        runtime = create_runtime(catalog_roots=roots)

        async with runtime:
            execution = runtime.require(HOST_EXECUTION)
            export_res = execution.export(ExportRequest(graph_document=doc))
            assert export_res.success, export_res.issues
            assert export_res.source_code is not None

            native = execution.execute(
                SingleExecutionRequest(graph_document=doc, inputs={"values": series})
            )
            assert native.success

            namespace: dict[str, Any] = {}
            exec(export_res.source_code, namespace)
            exported = namespace["execute"]({"values": series})

            native_out = native.outputs["rsi_1.rsi"]
            exported_out = exported["rsi_1_rsi"]
            assert isinstance(native_out, FrozenArray)
            assert isinstance(exported_out, (tuple, list))
            assert len(native_out) == len(exported_out)
            for n_v, e_v in zip(native_out, exported_out, strict=True):
                if isinstance(n_v, MissingValue):
                    assert type(e_v).__name__ == "MissingValue"
                else:
                    assert n_v == pytest.approx(e_v, rel=1e-9)

    asyncio.run(scenario())
