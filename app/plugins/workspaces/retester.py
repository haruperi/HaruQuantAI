"""Retester workspace plugin.

Cohesive single-file plugin owning its commands, views, and workspace
descriptor. Stable identity: ``workspace.retester@1.0.0``. The
zero-argument ``plugin()`` factory is pure — no I/O, no registration,
no tasks or threads, no environment reads — and the plugin is
discovered through the host catalog, never imported by name.

A workspace plugin is declarative only: ``RETESTER_COMMANDS`` and
``RETESTER_VIEWS`` name the retesting interactions and UI components
the retester supports, and ``accepted_kinds`` (``indicator``,
``comparison``, ``exporter``, ``crosscheck``) selects which plugin
kinds may participate in its graphs. Declaring the workspace starts
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

PLUGIN_REF = PluginRef("workspace.retester", (1, 0, 0))

RETESTER_COMMANDS = (
    WorkspaceCommand(
        command_id="retest_single",
        title="Retest Single",
        description="Evaluate candidate strategy graph on primary dataset.",
    ),
    WorkspaceCommand(
        command_id="retest_batch",
        title="Retest Batch",
        description=("Evaluate parameter variants across bars using batch execution."),
    ),
    WorkspaceCommand(
        command_id="evaluate_multimarket",
        title="Multi-Market Retest",
        description=(
            "Retest strategy across multiple market datasets (deferred to S6)."
        ),
    ),
    WorkspaceCommand(
        command_id="crosscheck_precision",
        title="Precision Cross-Check",
        description=(
            "Verify execution against higher precision tick data (deferred to S6)."
        ),
    ),
)

RETESTER_VIEWS = (
    WorkspaceView(
        view_id="setup",
        title="Retest Setup",
        component="RetestSetup",
    ),
    WorkspaceView(
        view_id="results",
        title="Retest Results",
        component="RetestResults",
    ),
)

WORKSPACE_SPEC = WorkspaceSpec(
    ref=PLUGIN_REF,
    title="Strategy Retester",
    description=(
        "Candidate strategy graph retesting, multi-market verification, and"
        " execution robustness workspace."
    ),
    commands=RETESTER_COMMANDS,
    views=RETESTER_VIEWS,
    accepted_kinds=("indicator", "comparison", "exporter", "crosscheck"),
)

RETESTER_PLUGIN_SPEC = PluginSpec(
    ref=PLUGIN_REF,
    kind="workspace",
    title="Strategy Retester",
    description=(
        "Candidate strategy graph retesting, multi-market verification, and"
        " execution robustness workspace."
    ),
    operations=(),
    workspace=WORKSPACE_SPEC,
)


def plugin() -> PluginContribution:
    """Return the Strategy Retester workspace plugin contribution.

    Pure zero-argument factory returning the declarative PluginSpec
    (kind ``workspace``, identity workspace.retester@1.0.0, no
    operations) without side effects; discovery happens through the
    host catalog.

    Returns:
        Immutable PluginContribution carrying only the workspace
        descriptor.
    """
    return PluginContribution(
        spec=RETESTER_PLUGIN_SPEC,
        operations=(),
    )


__all__ = (
    "PLUGIN_REF",
    "RETESTER_COMMANDS",
    "RETESTER_PLUGIN_SPEC",
    "RETESTER_VIEWS",
    "WORKSPACE_SPEC",
    "plugin",
)
