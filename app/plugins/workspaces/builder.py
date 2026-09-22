"""Strategy Builder workspace plugin."""

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
    """Return the Strategy Builder workspace plugin contribution."""
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
