"""Execution Results workspace plugin.

Cohesive single-file plugin owning its commands, views, and workspace
descriptor. Stable identity: ``workspace.results@1.0.0``. The
zero-argument ``plugin()`` factory is pure — no I/O, no registration,
no tasks or threads, no environment reads — and the plugin is
discovered through the host catalog, never imported by name.

Peer of ``workspace.builder``, ``workspace.retester``, and
``workspace.optimizer``: a declarative workspace whose commands
inspect calculation outputs, reproducibility metadata, and execution
issues of finished runs and whose views render them. ``accepted_kinds``
(``indicator``, ``comparison``, ``exporter``) selects which plugin kinds
the results workspace concerns. Declaring the workspace starts no
service. This file imports only shared metamodel types — never other
plugins, UI code, or host implementations — and contributes no
operations.
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
        command_id="inspect_outputs",
        title="Inspect Outputs",
        description=(
            "Inspect calculation output series and scalar values keyed by node"
            " and port."
        ),
    ),
    WorkspaceCommand(
        command_id="inspect_reproducibility",
        title="Inspect Reproducibility",
        description=(
            "Inspect execution reproducibility record, graph fingerprint, seed,"
            " and elapsed duration."
        ),
    ),
    WorkspaceCommand(
        command_id="inspect_issues",
        title="Inspect Issues",
        description="Inspect structured validation or execution issues.",
    ),
    WorkspaceCommand(
        command_id="export_strategy",
        title="Export Strategy",
        description="Export candidate strategy graph to target source code.",
    ),
    WorkspaceCommand(
        command_id="trading_metrics",
        title="Trading Performance Metrics",
        description=(
            "Compute financial backtest metrics such as Sharpe, Drawdown, Profit"
            " Factor, and trade list (deferred to S6)."
        ),
    ),
    WorkspaceCommand(
        command_id="monte_carlo",
        title="Monte Carlo Permutation",
        description=(
            "Execute Monte Carlo trade order reshuffling and parameter"
            " permutation analysis (deferred to S6)."
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
        "Execution result analysis, output inspection, and chart rendering workspace."
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
        "Execution result analysis, output inspection, and chart rendering workspace."
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
