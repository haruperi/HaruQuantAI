# Workspace Plugin Family

This directory contains standalone, cohesive workspace plugins.

## Architectural Constraints

1. **One Concept, One File:** Each workspace lives in a single Python file implementing workspace declarations, accepted child kinds, commands, view descriptors, capability requirements, and metadata.
2. **Standard Interfaces Only:** Plugins import only standard library modules and the shared metamodel in `app/plugins/{schema,lowering,spec,algebra,wire}`.
3. **No Cross-Plugin Imports:** Plugins never import sibling plugins, concrete indicator/comparison/exporter plugins, UI code, or host infrastructure.
4. **Pure Factory:** Each plugin module exports a zero-argument `plugin()` factory returning a `PluginContribution`.
5. **Orthogonal Removal:** Removing or disabling one workspace does not uninstall shared child plugins or prevent peer workspaces from functioning.
