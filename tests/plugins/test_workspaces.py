"""Tests for workspace plugins: builder, retester, optimizer, and results."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from app.host.bootstrap import create_runtime
from app.host.catalog import HOST_CATALOG, CatalogRoot, _CatalogProvider
from app.host.execution import HOST_EXECUTION, SingleExecutionRequest
from app.plugins.algebra import EdgeSpec, GraphDocument, GraphSpec, NodeSpec, PortRef
from app.plugins.schema import EMPTY_FROZEN_OBJECT, FrozenObject
from app.plugins.spec import PluginContribution, PluginRef, WorkspaceSpec
from app.plugins.workspaces.builder import (
    BUILDER_COMMANDS,
    BUILDER_VIEWS,
)
from app.plugins.workspaces.builder import (
    plugin as builder_plugin,
)
from app.plugins.workspaces.optimizer import (
    OPTIMIZER_COMMANDS,
    OPTIMIZER_VIEWS,
)
from app.plugins.workspaces.optimizer import (
    plugin as optimizer_plugin,
)
from app.plugins.workspaces.results import (
    RESULTS_COMMANDS,
    RESULTS_VIEWS,
)
from app.plugins.workspaces.results import (
    plugin as results_plugin,
)
from app.plugins.workspaces.retester import (
    RETESTER_COMMANDS,
    RETESTER_VIEWS,
)
from app.plugins.workspaces.retester import (
    plugin as retester_plugin,
)


def test_builder_plugin_contribution() -> None:
    """Builder workspace provides valid contribution without side effects."""
    contrib = builder_plugin()
    assert isinstance(contrib, PluginContribution)
    assert contrib.spec.ref.id == "workspace.builder"
    assert contrib.spec.ref.version == (1, 0, 0)
    assert contrib.spec.kind == "workspace"
    assert contrib.spec.title == "Strategy Builder"
    assert contrib.spec.operations == ()
    assert isinstance(contrib.spec.workspace, WorkspaceSpec)
    assert len(contrib.spec.workspace.commands) == len(BUILDER_COMMANDS)
    assert len(contrib.spec.workspace.views) == len(BUILDER_VIEWS)
    assert "indicator" in contrib.spec.workspace.accepted_kinds
    assert "comparison" in contrib.spec.workspace.accepted_kinds
    assert "exporter" in contrib.spec.workspace.accepted_kinds
    assert any(
        cmd.command_id == "generate_genetic" for cmd in contrib.spec.workspace.commands
    )


def test_retester_plugin_contribution() -> None:
    """Retester workspace provides valid contribution without side effects."""
    contrib = retester_plugin()
    assert isinstance(contrib, PluginContribution)
    assert contrib.spec.ref.id == "workspace.retester"
    assert contrib.spec.ref.version == (1, 0, 0)
    assert contrib.spec.kind == "workspace"
    assert contrib.spec.title == "Strategy Retester"
    assert contrib.spec.operations == ()
    assert isinstance(contrib.spec.workspace, WorkspaceSpec)
    assert len(contrib.spec.workspace.commands) == len(RETESTER_COMMANDS)
    assert len(contrib.spec.workspace.views) == len(RETESTER_VIEWS)
    assert "indicator" in contrib.spec.workspace.accepted_kinds
    assert "comparison" in contrib.spec.workspace.accepted_kinds
    assert "exporter" in contrib.spec.workspace.accepted_kinds
    assert "crosscheck" in contrib.spec.workspace.accepted_kinds


def test_optimizer_plugin_contribution() -> None:
    """Optimizer workspace provides valid contribution without side effects."""
    contrib = optimizer_plugin()
    assert isinstance(contrib, PluginContribution)
    assert contrib.spec.ref.id == "workspace.optimizer"
    assert contrib.spec.ref.version == (1, 0, 0)
    assert contrib.spec.kind == "workspace"
    assert contrib.spec.title == "Strategy Optimizer"
    assert contrib.spec.operations == ()
    assert isinstance(contrib.spec.workspace, WorkspaceSpec)
    assert len(contrib.spec.workspace.commands) == len(OPTIMIZER_COMMANDS)
    assert len(contrib.spec.workspace.views) == len(OPTIMIZER_VIEWS)
    assert "indicator" in contrib.spec.workspace.accepted_kinds
    assert "comparison" in contrib.spec.workspace.accepted_kinds
    assert "exporter" in contrib.spec.workspace.accepted_kinds
    assert "optimizer" in contrib.spec.workspace.accepted_kinds


def test_results_plugin_contribution() -> None:
    """Results workspace provides valid contribution without side effects."""
    contrib = results_plugin()
    assert isinstance(contrib, PluginContribution)
    assert contrib.spec.ref.id == "workspace.results"
    assert contrib.spec.ref.version == (1, 0, 0)
    assert contrib.spec.kind == "workspace"
    assert contrib.spec.title == "Execution Results"
    assert contrib.spec.operations == ()
    assert isinstance(contrib.spec.workspace, WorkspaceSpec)
    assert len(contrib.spec.workspace.commands) == len(RESULTS_COMMANDS)
    assert len(contrib.spec.workspace.views) == len(RESULTS_VIEWS)
    assert any(
        cmd.command_id == "trading_metrics" for cmd in contrib.spec.workspace.commands
    )
    assert any(
        cmd.command_id == "monte_carlo" for cmd in contrib.spec.workspace.commands
    )


def test_workspaces_catalog_discovery() -> None:
    """Catalog discovers all 4 workspace plugins and publishes wire-safe snapshot."""
    repo_plugins = Path(__file__).resolve().parent.parent.parent / "app" / "plugins"
    workspaces_dir = repo_plugins / "workspaces"

    root = CatalogRoot(
        logical_family="workspaces",
        path=workspaces_dir,
        accepted_kinds=("workspace",),
    )
    provider = _CatalogProvider((root,))
    res = provider.refresh()

    assert res.success
    snapshot = provider.snapshot()
    builder_entry = snapshot.view.get_entry_by_id("workspace.builder")
    retester_entry = snapshot.view.get_entry_by_id("workspace.retester")
    optimizer_entry = snapshot.view.get_entry_by_id("workspace.optimizer")
    results_entry = snapshot.view.get_entry_by_id("workspace.results")

    assert builder_entry is not None
    assert retester_entry is not None
    assert optimizer_entry is not None
    assert results_entry is not None

    for entry in (builder_entry, retester_entry, optimizer_entry, results_entry):
        assert entry.kind == "workspace"
        assert entry.workspace is not None


def test_orthogonal_removal_in_tmp_path(tmp_path: Path) -> None:
    """Removing one workspace in an isolated temporary tree leaves peers intact."""
    repo_plugins = Path(__file__).resolve().parent.parent.parent / "app" / "plugins"
    src_workspaces = repo_plugins / "workspaces"
    tmp_workspaces = tmp_path / "workspaces"
    shutil.copytree(src_workspaces, tmp_workspaces)

    # Initial state in tmp_path has all 4 workspaces
    provider = _CatalogProvider(
        (
            CatalogRoot(
                logical_family="workspaces",
                path=tmp_workspaces,
                accepted_kinds=("workspace",),
            ),
        )
    )
    res = provider.refresh()
    assert res.success
    snapshot = provider.snapshot()
    assert snapshot.view.get_entry_by_id("workspace.retester") is not None
    assert snapshot.view.get_entry_by_id("workspace.builder") is not None
    assert snapshot.view.get_entry_by_id("workspace.optimizer") is not None
    assert snapshot.view.get_entry_by_id("workspace.results") is not None

    # Remove retester.py from isolated tmp_path
    retester_file = tmp_workspaces / "retester.py"
    retester_file.unlink()

    # Refresh catalog from tmp_path
    res2 = provider.refresh()
    assert res2.success
    snapshot2 = provider.snapshot()

    # Retester is removed; builder, optimizer, results remain discoverable and intact
    assert snapshot2.view.get_entry_by_id("workspace.retester") is None
    assert snapshot2.view.get_entry_by_id("workspace.builder") is not None
    assert snapshot2.view.get_entry_by_id("workspace.optimizer") is not None
    assert snapshot2.view.get_entry_by_id("workspace.results") is not None

    # Verify active repository source remains completely untouched
    assert (src_workspaces / "retester.py").exists()


def test_decoupled_command_availability_regression(tmp_path: Path) -> None:
    """Adding an unrelated candidate plugin does NOT enable deferred workspace commands.

    Control WP-W04: Commands remain unavailable regardless of installed kinds.
    Installing an unrelated candidate crosscheck or optimizer plugin into the
    catalog must not enable deferred commands in Retester or Optimizer.
    """
    repo_plugins = Path(__file__).resolve().parent.parent.parent / "app" / "plugins"

    # Create dummy candidate crosscheck plugin in isolated tmp_path
    dummy_crosscheck_root = tmp_path / "crosschecks"
    dummy_crosscheck_root.mkdir()
    (dummy_crosscheck_root / "__init__.py").write_text("", encoding="utf-8")
    (dummy_crosscheck_root / "dummy_monte_carlo.py").write_text(
        '''"""Dummy candidate crosscheck plugin."""
from __future__ import annotations
from app.plugins.spec import PluginContribution, PluginRef, PluginSpec

def plugin() -> PluginContribution:
    ref = PluginRef("crosscheck.dummy_monte_carlo", (1, 0, 0))
    spec = PluginSpec(
        ref=ref,
        kind="crosscheck",
        title="Dummy Monte Carlo",
        description="Dummy candidate plugin for testing command isolation.",
        operations=(),
        workspace=None,
    )
    return PluginContribution(spec=spec, operations=())
''',
        encoding="utf-8",
    )

    roots = (
        CatalogRoot(
            logical_family="workspaces",
            path=repo_plugins / "workspaces",
            accepted_kinds=("workspace",),
        ),
        CatalogRoot(
            logical_family="indicators",
            path=repo_plugins / "indicators",
            accepted_kinds=("indicator",),
        ),
        CatalogRoot(
            logical_family="comparisons",
            path=repo_plugins / "comparisons",
            accepted_kinds=("comparison",),
        ),
        CatalogRoot(
            logical_family="exporters",
            path=repo_plugins / "exporters",
            accepted_kinds=("exporter",),
        ),
        CatalogRoot(
            logical_family="crosschecks",
            path=dummy_crosscheck_root,
            accepted_kinds=("crosscheck",),
        ),
    )
    provider = _CatalogProvider(roots)
    res = provider.refresh()
    assert res.success
    snapshot = provider.snapshot()

    # The dummy candidate plugin is discovered in catalog
    assert snapshot.view.get_entry_by_id("crosscheck.dummy_monte_carlo") is not None

    # Check that deferred commands in retester/optimizer are NOT enabled by this unrelated plugin
    retester_entry = snapshot.view.get_entry_by_id("workspace.retester")
    assert retester_entry is not None
    assert retester_entry.workspace is not None
    command_ids = [cmd.command_id for cmd in retester_entry.workspace.commands]
    assert "evaluate_multimarket" in command_ids
    assert "crosscheck_precision" in command_ids

    # Query admitted operations for retester's accepted kinds
    from app.host.catalog import SelectionRequest

    request = SelectionRequest(allowed_kinds=retester_entry.workspace.accepted_kinds)
    admitted = provider.select(request)

    # Even though a crosscheck candidate plugin is installed, no operations enable deferred commands
    assert not any("precision" in op[1] for op in admitted.available_operations)
    assert not any("multimarket" in op[1] for op in admitted.available_operations)

    # Verify Optimizer deferred commands remain unbacked
    optimizer_entry = snapshot.view.get_entry_by_id("workspace.optimizer")
    assert optimizer_entry is not None
    assert optimizer_entry.workspace is not None
    opt_command_ids = [cmd.command_id for cmd in optimizer_entry.workspace.commands]
    assert "walk_forward_matrix" in opt_command_ids
    assert "sequential_optimization" in opt_command_ids
    assert not any("walk_forward" in op[1] for op in admitted.available_operations)


def test_shared_plugin_selection_and_execution() -> None:
    """Multiple workspaces concurrently select indicator.rsi and execute valid graphs.

    Control WP-W07: Workspaces share underlying domain plugins through HOST_EXECUTION.
    """
    from app.host.bootstrap import approved_catalog_roots

    async def _run() -> None:
        async with create_runtime(catalog_roots=approved_catalog_roots()) as runtime:
            catalog = runtime.require(HOST_CATALOG)
            execution = runtime.require(HOST_EXECUTION)

            snapshot = catalog.snapshot()
            builder = snapshot.view.get_entry_by_id("workspace.builder")
            retester = snapshot.view.get_entry_by_id("workspace.retester")
            optimizer = snapshot.view.get_entry_by_id("workspace.optimizer")

            assert (
                builder is not None and retester is not None and optimizer is not None
            )

            # All 3 workspaces accept 'indicator' kind
            assert "indicator" in builder.workspace.accepted_kinds  # type: ignore[union-attr]
            assert "indicator" in retester.workspace.accepted_kinds  # type: ignore[union-attr]
            assert "indicator" in optimizer.workspace.accepted_kinds  # type: ignore[union-attr]

            # Build and execute a valid graph using shared indicator.rsi
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
            doc = GraphDocument(spec=graph_spec)

            inputs = {
                "values": [44.0, 44.25, 44.5, 43.75, 44.1, 44.6],
                "gt_node.right": [50.0, 50.0, 50.0, 50.0, 50.0, 50.0],
            }

            # Execute graph as requested by builder/retester
            single_req = SingleExecutionRequest(graph_document=doc, inputs=inputs)
            res = execution.execute(single_req)

            assert res.success
            assert "rsi_node.rsi" in res.outputs
            assert "gt_node.result" in res.outputs
            assert res.reproducibility is not None
            assert res.reproducibility.elapsed_seconds >= 0

    asyncio.run(_run())
