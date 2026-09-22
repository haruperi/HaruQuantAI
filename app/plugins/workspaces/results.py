"""Execution Results workspace plugin.

Cohesive single-file plugin owning its commands, views, and workspace
descriptor. Stable identity: ``workspace.results@1.0.0``. The
zero-argument ``plugin()`` factory is pure — no I/O, no registration,
no tasks or threads, no environment reads — and the plugin is
discovered through the host catalog, never imported by name.

Peer of ``workspace.builder``: a declarative workspace whose commands
inspect metrics, output series, and provenance of finished runs and
whose views render them. ``accepted_kinds`` (``indicator``,
``comparison``, ``exporter``) selects which plugin kinds the results
workspace concerns. Declaring the workspace starts no service. This
file imports only shared metamodel types — never other plugins, UI
code, or host implementations — and contributes no operations.
"""

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
    """Return the Execution Results workspace plugin contribution.

    Pure zero-argument factory returning the declarative PluginSpec
    (kind ``workspace``, identity workspace.results@1.0.0, no
    operations) without side effects; discovery happens through the
    host catalog.

    Returns:
        Immutable PluginContribution carrying only the workspace
        descriptor.
    """
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
