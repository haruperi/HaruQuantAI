# Workspace Plugin Family

This directory contains standalone, cohesive workspace plugins under the governing standard [`docs/dev/workspace_plugin_implementation_pipeline.md`](../../docs/dev/workspace_plugin_implementation_pipeline.md) (**Track W: Workspace Plugins**).

## Registered Workspace Plugins (Tier 1 Core)

| Plugin Ref | Production File | Title | Description | Accepted Kinds |
|---|---|---|---|---|
| `workspace.builder@1.0.0` | [`builder.py`](builder.py) | Strategy Builder | Visual graph builder and parameter configuration | `indicator`, `comparison`, `exporter` |
| `workspace.retester@1.0.0` | [`retester.py`](retester.py) | Strategy Retester | Graph retesting, multi-market verification, and execution robustness | `indicator`, `comparison`, `exporter`, `crosscheck` |
| `workspace.optimizer@1.0.0` | [`optimizer.py`](optimizer.py) | Strategy Optimizer | Parameter space optimization and sensitivity analysis | `indicator`, `comparison`, `exporter`, `optimizer` |
| `workspace.results@1.0.0` | [`results.py`](results.py) | Execution Results | Execution result analysis, output inspection, and chart rendering | `indicator`, `comparison`, `exporter` |

## Architectural Constraints

1. **One Concept, One File:** Each workspace lives in a single Python file implementing workspace declarations, accepted child kinds, commands, view descriptors, capability requirements, and metadata.
2. **Standard Interfaces Only:** Plugins import only standard library modules and the shared metamodel in `app/plugins/{schema,lowering,spec,algebra,wire}`.
3. **No Cross-Plugin Imports:** Plugins never import sibling plugins, concrete indicator/comparison/exporter plugins, UI code, or host infrastructure.
4. **Pure Factory:** Each plugin module exports a zero-argument `plugin()` factory returning a `PluginContribution`.
5. **Orthogonal Removal:** Removing or disabling one workspace does not uninstall shared child plugins or prevent peer workspaces from functioning.
6. **Declarative Only:** Workspaces publish UI view descriptors and command metadata. They do not implement quantitative algorithms, direct persistence, or private execution switches.
