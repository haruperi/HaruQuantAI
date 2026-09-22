# Comparison Plugin Family

This directory contains standalone, cohesive comparison plugins.

## Architectural Constraints

1. **One Concept, One File:** Calculation, configuration, ports, bounds, lowering, and presentation metadata for one comparison concept stay together.
2. **Standard Interfaces Only:** Plugins import only the Python standard library and shared metamodel in `app/plugins/{schema,lowering,spec,algebra,wire}`.
3. **No Cross-Plugin Imports:** Plugins never import sibling plugins or host infrastructure.
4. **Pure Factory:** Each plugin module exports a zero-argument `plugin()` factory returning a `PluginContribution`.
