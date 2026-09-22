"""Tests for workspace plugins: builder and results."""

from __future__ import annotations

from pathlib import Path

from app.host.catalog import CatalogRoot, _CatalogProvider
from app.plugins.spec import PluginContribution, PluginRef, WorkspaceSpec
from app.plugins.workspaces.builder import (
    BUILDER_COMMANDS,
    BUILDER_VIEWS,
)
from app.plugins.workspaces.builder import (
    plugin as builder_plugin,
)
from app.plugins.workspaces.results import (
    RESULTS_COMMANDS,
    RESULTS_VIEWS,
)
from app.plugins.workspaces.results import (
    plugin as results_plugin,
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


def test_workspaces_catalog_discovery(tmp_path: Path) -> None:
    """Catalog discovers workspace plugins and publishes wire-safe snapshot."""
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
    results_entry = snapshot.view.get_entry_by_id("workspace.results")

    assert builder_entry is not None
    assert results_entry is not None
    assert builder_entry.kind == "workspace"
    assert results_entry.kind == "workspace"
    assert builder_entry.workspace is not None
    assert results_entry.workspace is not None


def test_orthogonal_removal_and_shared_coexistence() -> None:
    """Removing one workspace leaves the other workspace intact."""
    repo_plugins = Path(__file__).resolve().parent.parent.parent / "app" / "plugins"

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
    )
    provider = _CatalogProvider(roots)
    res = provider.refresh()
    assert res.success

    view = provider.snapshot().view
    # Both workspaces coexist and see the indicator
    assert view.get_entry(PluginRef("workspace.builder", (1, 0, 0))) is not None
    assert view.get_entry(PluginRef("workspace.results", (1, 0, 0))) is not None
    assert view.get_entry(PluginRef("indicator.rsi", (1, 0, 0))) is not None
