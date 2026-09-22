"""Execution Results workspace plugin."""

from __future__ import annotations

from app.plugins.spec import (
    PluginContribution,
    PluginRef,
    PluginSpec,
    WorkspaceCommand,
    WorkspaceSpec,
    WorkspaceView,
)

PLUGIN_REF = PluginRef("workspace.results", (1, 0, 0))

RESULTS_COMMANDS = (
    WorkspaceCommand(
        command_id="inspect_metrics",
        title="Inspect Metrics",
        description="Inspect calculated execution metrics and summary statistics.",
    ),
    WorkspaceCommand(
        command_id="inspect_series",
        title="Inspect Series",
        description="Inspect output series data points and timestamps.",
    ),
    WorkspaceCommand(
        command_id="inspect_provenance",
        title="Inspect Provenance",
        description=(
            "Inspect execution reproducibility record, hashes, and fingerprints."
        ),
    ),
)

RESULTS_VIEWS = (
    WorkspaceView(
        view_id="overview",
        title="Results Overview",
        component="ExecutionResult",
    ),
    WorkspaceView(
        view_id="series_chart",
        title="Series Chart",
        component="SeriesChart",
    ),
    WorkspaceView(
        view_id="outputs_table",
        title="Outputs Table",
        component="OutputsTable",
    ),
)

WORKSPACE_SPEC = WorkspaceSpec(
    ref=PLUGIN_REF,
    title="Execution Results",
    description=(
        "Quantitative execution result analysis, metric calculation, and chart"
        " inspection workspace."
    ),
    commands=RESULTS_COMMANDS,
    views=RESULTS_VIEWS,
    accepted_kinds=("indicator", "comparison", "exporter"),
)

RESULTS_PLUGIN_SPEC = PluginSpec(
    ref=PLUGIN_REF,
    kind="workspace",
    title="Execution Results",
    description=(
        "Quantitative execution result analysis, metric calculation, and chart"
        " inspection workspace."
    ),
    operations=(),
    workspace=WORKSPACE_SPEC,
)


def plugin() -> PluginContribution:
    """Return the Execution Results workspace plugin contribution."""
    return PluginContribution(
        spec=RESULTS_PLUGIN_SPEC,
        operations=(),
    )


__all__ = (
    "PLUGIN_REF",
    "RESULTS_COMMANDS",
    "RESULTS_PLUGIN_SPEC",
    "RESULTS_VIEWS",
    "WORKSPACE_SPEC",
    "plugin",
)
