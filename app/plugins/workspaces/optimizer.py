"""Optimizer workspace plugin.

Cohesive single-file plugin owning its commands, views, and workspace
descriptor. Stable identity: ``workspace.optimizer@1.0.0``. The
zero-argument ``plugin()`` factory is pure — no I/O, no registration,
no tasks or threads, no environment reads — and the plugin is
discovered through the host catalog, never imported by name.

A workspace plugin is declarative only: ``OPTIMIZER_COMMANDS`` and
``OPTIMIZER_VIEWS`` name the parameter search interactions and UI
components the optimizer supports, and ``accepted_kinds`` (``indicator``,
``comparison``, ``exporter``, ``optimizer``) selects which plugin kinds
may participate in its parameter space. Declaring the workspace starts
no service; behavior lives in the host and UI. This file imports only
shared metamodel types — never other plugins, UI code, or host
implementations — and contributes no operations.
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

PLUGIN_REF = PluginRef("workspace.optimizer", (1, 0, 0))

OPTIMIZER_COMMANDS = (
    WorkspaceCommand(
        command_id="optimize_user_trials",
        title="Run User Trials",
        description=(
            "Execute explicit user-supplied parameter trial combinations via"
            " batch execution."
        ),
    ),
    WorkspaceCommand(
        command_id="optimize_genetic",
        title="Genetic Optimization",
        description=(
            "Run genetic strategy optimization against objective function"
            " (deferred to S6)."
        ),
    ),
    WorkspaceCommand(
        command_id="walk_forward_matrix",
        title="Walk-Forward Matrix",
        description=(
            "Perform walk-forward cluster analysis across parameters (deferred to S6)."
        ),
    ),
    WorkspaceCommand(
        command_id="sequential_optimization",
        title="Sequential Optimization",
        description=(
            "Optimize parameters sequentially across evaluation periods"
            " (deferred to S6)."
        ),
    ),
)

OPTIMIZER_VIEWS = (
    WorkspaceView(
        view_id="setup",
        title="Optimizer Setup",
        component="OptimizerSetup",
    ),
    WorkspaceView(
        view_id="results",
        title="Optimization Results",
        component="OptimizerResults",
    ),
)

WORKSPACE_SPEC = WorkspaceSpec(
    ref=PLUGIN_REF,
    title="Strategy Optimizer",
    description=(
        "Parameter space optimization, sensitivity analysis, and walk-forward"
        " matrix cluster evaluation workspace."
    ),
    commands=OPTIMIZER_COMMANDS,
    views=OPTIMIZER_VIEWS,
    accepted_kinds=("indicator", "comparison", "exporter", "optimizer"),
)

OPTIMIZER_PLUGIN_SPEC = PluginSpec(
    ref=PLUGIN_REF,
    kind="workspace",
    title="Strategy Optimizer",
    description=(
        "Parameter space optimization, sensitivity analysis, and walk-forward"
        " matrix cluster evaluation workspace."
    ),
    operations=(),
    workspace=WORKSPACE_SPEC,
)


def plugin() -> PluginContribution:
    """Return the Strategy Optimizer workspace plugin contribution.

    Pure zero-argument factory returning the declarative PluginSpec
    (kind ``workspace``, identity workspace.optimizer@1.0.0, no
    operations) without side effects; discovery happens through the
    host catalog.

    Returns:
        Immutable PluginContribution carrying only the workspace
        descriptor.
    """
    return PluginContribution(
        spec=OPTIMIZER_PLUGIN_SPEC,
        operations=(),
    )


__all__ = (
    "OPTIMIZER_COMMANDS",
    "OPTIMIZER_PLUGIN_SPEC",
    "OPTIMIZER_VIEWS",
    "PLUGIN_REF",
    "WORKSPACE_SPEC",
    "plugin",
)
