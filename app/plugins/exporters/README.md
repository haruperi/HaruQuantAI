# Exporter Plugin Family

This directory contains standalone, cohesive code and model exporter plugins.

## Architectural Constraints

1. **One Concept, One File:** Translation from universal semantic IR into target formats stays completely together.
2. **Standard Interfaces Only:** Exporter plugins import only the Python standard library and shared metamodel in `app/plugins/{schema,lowering,spec,algebra,wire}`.
3. **No Specific Plugin Coupling:** Exporter plugins consume only universal IR (`std.*`) and never reference specific indicator or comparison IDs.
4. **Pure Factory:** Each plugin module exports a zero-argument `plugin()` factory returning a `PluginContribution`.
