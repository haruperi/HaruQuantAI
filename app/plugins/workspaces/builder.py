"""Strategy Builder workspace plugin.

Cohesive single-file plugin owning its commands, views, and workspace
descriptor. Stable identity: ``workspace.builder@1.0.0``. The
zero-argument ``plugin()`` factory is pure — no I/O, no registration,
no tasks or threads, no environment reads — and the plugin is
discovered through the host catalog, never imported by name.

A workspace plugin is declarative only: ``BUILDER_COMMANDS`` and
``BUILDER_VIEWS`` name the graph-editing interactions and UI components
the builder supports, and ``accepted_kinds`` (``indicator``,
``comparison``, ``exporter``) selects which plugin kinds may
participate in its graphs. Declaring the workspace starts no service;
behavior lives in the host and UI. This file imports only shared
metamodel types — never other plugins, UI code, or host
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

PLUGIN_REF = PluginRef("workspace.builder", (1, 0, 0))

BUILDER_COMMANDS = (
    WorkspaceCommand(
        command_id="add_node",
        title="Add Node",
        description="Add a quantitative plugin node to the strategy graph.",
    ),
    WorkspaceCommand(
        command_id="remove_node",
        title="Remove Node",
        description="Remove a node and its incident edges from the graph.",
    ),
    WorkspaceCommand(
        command_id="connect",
        title="Connect Ports",
        description="Connect a source node output port to a target node input port.",
    ),
    WorkspaceCommand(
        command_id="disconnect",
        title="Disconnect Ports",
        description="Disconnect an existing edge between ports.",
    ),
    WorkspaceCommand(
        command_id="validate",
        title="Validate Graph",
        description="Validate graph structure and port compatibility against catalog.",
    ),
    WorkspaceCommand(
        command_id="evaluate",
        title="Evaluate Graph",
        description="Execute bounded synchronous single graph run.",
    ),
    WorkspaceCommand(
        command_id="batch",
        title="Batch Trials",
        description="Execute bounded batch parameter trials.",
    ),
    WorkspaceCommand(
        command_id="export",
        title="Export Code",
        description="Export graph to target source code via an admitted exporter.",
    ),
    WorkspaceCommand(
        command_id="generate_genetic",
        title="Genetic Strategy Generation",
        description=(
            "Run evolutionary genetic strategy generation and search (deferred to S6)."
        ),
    ),
)

BUILDER_VIEWS = (
    WorkspaceView(
        view_id="canvas",
        title="Graph Canvas",
        component="GraphEditor",
    ),
    WorkspaceView(
        view_id="parameters",
        title="Parameter Form",
        component="ParameterForm",
    ),
)

WORKSPACE_SPEC = WorkspaceSpec(
    ref=PLUGIN_REF,
    title="Strategy Builder",
    description=(
        "Interactive visual strategy graph builder and parameter configuration"
        " workspace."
    ),
    commands=BUILDER_COMMANDS,
    views=BUILDER_VIEWS,
    accepted_kinds=("indicator", "comparison", "exporter"),
)

BUILDER_PLUGIN_SPEC = PluginSpec(
    ref=PLUGIN_REF,
    kind="workspace",
    title="Strategy Builder",
    description=(
        "Interactive visual strategy graph builder and parameter configuration"
        " workspace."
    ),
    operations=(),
    workspace=WORKSPACE_SPEC,
)


def plugin() -> PluginContribution:
    """Return the Strategy Builder workspace plugin contribution.

    Pure zero-argument factory returning the declarative PluginSpec
    (kind ``workspace``, identity workspace.builder@1.0.0, no
    operations) without side effects; discovery happens through the
    host catalog.

    Returns:
        Immutable PluginContribution carrying only the workspace
        descriptor.
    """
    return PluginContribution(
        spec=BUILDER_PLUGIN_SPEC,
        operations=(),
    )


__all__ = (
    "BUILDER_COMMANDS",
    "BUILDER_PLUGIN_SPEC",
    "BUILDER_VIEWS",
    "PLUGIN_REF",
    "WORKSPACE_SPEC",
    "plugin",
)
