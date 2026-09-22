# Indicator Plugin Family

This directory contains standalone, cohesive quantitative indicator plugins.

## Architectural Constraints

1. **One Concept, One File:** Each plugin lives in a single Python file implementing calculation, configuration schema, bounds, output ports, dynamic lookback/warmup, error handling, semantic lowering, and metadata.
2. **Standard Interfaces Only:** Plugins import only standard library modules and the shared metamodel in `app/plugins/{schema,lowering,spec,algebra,wire}`.
3. **No Cross-Plugin Imports:** Plugins never import sibling plugins or host infrastructure.
4. **Pure Factory:** Each plugin module exports a zero-argument `plugin()` factory returning a `PluginContribution`.
