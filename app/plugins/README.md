# Shared Plugin Metamodel and Wire Protocol

This package defines the universal vocabulary and wire representation for HaruQuantAI components:

- `schema.py` — Bounded immutable values, descriptors, ports, parameter schemas, units, constraints, and presentation hints.
- `lowering.py` — Semantic IR, universal operator vocabulary, and lowering protocols.
- `spec.py` — Plugin identity, versioning, operation declarations, capabilities, and wire-safe catalog views.
- `algebra.py` — Versioned graph documents, node/edge specifications, cycle detection, and catalog validation.
- `wire.py` — Strict UTF-8 JSON projection, canonical whitespace-free serialization, SHA-256 fingerprinting, and parsing with duplicate-key rejection.

## Architecture and Import Rules

The shared-module import DAG is strictly acyclic:

```text
schema
  ^
  |
lowering
  ^
  |
spec --------> app.kernel.capability only
  ^
  |
algebra
  ^
  |
wire
```

- `schema.py` depends only on the Python standard library.
- `lowering.py` depends on `schema.py` and the standard library.
- `spec.py` depends on `schema.py`, `lowering.py`, `app.kernel.capability`, and the standard library.
- `algebra.py` depends on `schema.py`, `lowering.py`, `spec.py`, and the standard library.
- `wire.py` may import all four shared modules and the standard library.
- **No shared module may import `app.host`, `app.ui`, or concrete plugins.**
- **No shared module may access filesystem paths, I/O, threads, or environment variables at import time.**

## Shared module responsibilities

| Module | Owns | Never contains |
|---|---|---|
| `schema.py` | Portable scalar/array/object value vocabulary with explicit `MissingValue`; depth, collection, string, and total-element bounds; parameter/port descriptors, units, alignments, numeric/text/enum constraints, optimization domains, presentation hints | Any concrete plugin's parameters, bounds, or behavior |
| `lowering.py` | Reserved `std.*` universal operator namespace; bounded semantic IR (schema version 1) with ordered-reference DAG validation; exact lowering targets; lowering issue/result and context protocols | Concrete plugin IDs, plugin registries, or target-specific code generation |
| `spec.py` | Validated dot-namespaced plugin IDs and exact `PluginRef`; semver; kinds as validated identifiers; `OperationSpec` with typed ports, policies, effects, capabilities, permissions, and lowering targets; operation implementation and binding protocols; workspace specs; wire-safe catalog views | Implementation objects, provider instances, exceptions, or callables inside descriptor views |
| `algebra.py` | Graph schema version 1: `NodeSpec`/`EdgeSpec`/`GraphSpec` bounds; cycle rejection (recurrence is node behavior, never a graph cycle); unit/alignment compatibility; unknown-plugin nodes kept readable but non-executable; `OpaqueGraphDocument` for unsupported versions | Plugin-specific validation or a central plugin list |
| `wire.py` | Strict UTF-8 JSON parse (duplicate-key and non-finite rejection, depth/size/string bounds); canonical sorted-key compact bytes; SHA-256 fingerprints; deterministic round trips; raw retention for unsupported graph versions | Capabilities, callables, exceptions, paths, or Python-specific representations |

## Concrete plugin families

Each subdirectory is one approved family discovered by the host catalog
(no central plugin list; no import-time registration, I/O, tasks,
threads, environment reads, or global mutation):

| Family | Kind | Plugins |
|---|---|---|
| [`indicators/`](indicators/README.md) | `indicator` | `indicator.rsi@1.0.0` |
| [`comparisons/`](comparisons/README.md) | `comparison` | `comparison.greater_than@1.0.0` |
| [`exporters/`](exporters/README.md) | `exporter` | `exporter.python@1.0.0` |
| [`workspaces/`](workspaces/README.md) | `workspace` | `workspace.builder@1.0.0`, `workspace.results@1.0.0` |

One quantitative concept is one cohesive Python file: behavior, parameter
schema, bounds, ports, numerical policy, warm-up, lowering, and
presentation metadata stay together. Plugins may import the shared
vocabulary above, the kernel `Capability` primitive, and designated
public host contracts — never the kernel runtime/context, host
implementations, live catalog objects, UI code, or sibling plugins
(enforced by ARCH-013 and ARCH-014).

Workspace and plugin construction and auditing follow
[`docs/dev/workspace_plugin_implementation_pipeline.md`](../../docs/dev/workspace_plugin_implementation_pipeline.md)
and
[`docs/dev/workspace_plugin_implementation_audit.md`](../../docs/dev/workspace_plugin_implementation_audit.md).

## Verification

```powershell
uv run pytest --no-cov tests/plugins -v
uv run python -m tests.examples.catalog_usage
uv run python -m tests.examples.slice_usage
uv run python scripts/architecture_check.py
```
