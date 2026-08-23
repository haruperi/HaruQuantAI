# Composition Runtime

> **Package:** `app/composition/`
> **Category:** Non-domain shared substrate
> **Status:** `Implemented`

## Purpose

`app/composition/` applies application policy around the independent kernel. It discovers installed features, validates desired configuration, selects providers, reports readiness, watches configuration, and serializes high-level runtime mutations.

## Implemented ownership

- `FeatureDiscoverer` loading the `haruquantai.features` Python entry-point group plus explicit test/embedded registration.
- Strict TOML `AppConfig` with `[application]`, `[features]`, and `[providers]` tables.
- Deployment-profile readiness for `offline`, `research`, `backtest`, and `live`.
- `CompositionEngine` orchestration over kernel registry/graph/reconciler/event primitives.
- Serialized configuration reload, provider selection, runtime-failure recovery, and transactional feature replacement.
- Configuration-file watching and code-aligned runtime diagnostics.

## Boundary

`app/composition/` may import `app/kernel/` and `app/contracts/`; it never imports `app/services/`. It does not own the service registry, dependency graph, `FeatureContext`, `FeatureScope`, event bus, state declarations, or replacement models—those are kernel primitives.

Features are not discovered through domain registries or YAML manifests. Each installed feature is an independent Python entry point and supplies a validated `FeatureSpec` from its `manifest.py`. Feature dependencies/effects use `FeatureContext`; composition chooses provider bindings and invokes reconciliation.

## Failure and mutation rules

Entry-point/package errors, capability dependency errors, blocked reasons, cleanup errors, runtime-task failures, and replacement outcomes remain distinct diagnostics. Configuration reload and explicit replacement share one mutation lock. Pre-commit replacement failure retains the old generation; post-commit consumer/cleanup failure is reported as committed but degraded.

The authoritative procedural detail is the [Feature Implementation Pipeline](../../docs/dev/feature_implementation_pipeline.md).

---

## Normative Composition Specification

The stable `§x.y` labels below are preserved for cross-document references. They are authoritative here and no longer identify sections in `docs/PROJECT.md`.

### §6.3 — Feature specifications, capabilities, discovery, and configuration

`manifest.py` exports a `FeatureSpec` with exactly these architectural fields:

| Field | Meaning |
|---|---|
| `feature_id` | Stable `FEAT-*` configuration and diagnostic identity |
| `domain` | Lowercase semantic owner |
| `provides` | Capabilities the mounted provider bundle must publish exactly |
| `requires` | Required capabilities that gate activation |
| `optional` | Optional capabilities available through explicit optional lookup |
| `conflicts` | Feature IDs that cannot be active together |
| `description` | Human-readable purpose |
| `state` | Optional persistent-state declaration |
| `config_keys` | Exact accepted feature configuration keys |

A `CapabilityKey` has a lowercase name and positive major version; its formatted identifier is `<name>@<major>`, normally `<domain>.<capability>@<major>`. The key does not contain a schema hash, implementation hash, permission set, or full semantic version. Those belong in the relevant application contract or reproducibility evidence.

`FeatureDiscoverer` loads installed `haruquantai.features` entry points with `importlib.metadata` and also supports explicit registration for tests/embedded composition. A failing entry point is isolated and reported without crashing unrelated discovery.

D-UI does not use `FeatureSpec` or Python discovery. Its typed manifests declare stable `FEAT-UI-*` identity, capability dependencies, contributions, configuration, and removal metadata; the UI composition bridge consumes public capability snapshots and withdraws only the affected view contribution when a dependency disappears.

Application desired state is strict TOML with only `[application]`, `[features]`, and `[providers]` top-level tables. Supported profiles are `offline`, `research`, `backtest`, and `live`. Each `[features.FEAT-*]` table declares `enabled` and either inline feature keys or a nested `.config` table, never both. `[providers]` maps a capability identifier to the selected provider feature ID. Unknown profiles, sections, keys, invalid IDs, and ambiguous unselected providers fail explicitly.


### §6.5 — Dependency resolution, activation, reconciliation, removal, and replacement

- The dependency graph rejects required cycles. Optional-only cycles do not gate activation.
- Exactly one compatible provider binds automatically. Multiple candidates without a valid `[providers]` selection block the consumer.
- Mount is staged in a fresh scope. The provider bundle must exactly match `FeatureSpec.provides`; only then is it atomically published.
- Mount/config/provider-publication failure closes the staged scope, publishes no partial provider, and records `FAILED_START`.
- Enablement, configuration, selected-provider, provider arrival/removal, and runtime-failure changes reconcile the exact transitive affected consumer closure in dependency order.
- Optional provider arrival/removal remounts the consumer so its committed dependency view never changes underneath a running instance.
- Configuration reload and explicit replacement share one mutation lock, preventing overlapping feature mounts.
- An unexpected `context.spawn()` task failure withdraws the owner capabilities, records `FAILED_RUNTIME`, publishes `FeatureRuntimeFailedEvent`, reconciles dependents, and preserves unrelated branches.
- Explicit replacement requires the same provided-capability set, mounts and health-checks a shadow generation, optionally quiesces/drains the old feature, then atomically swaps registry bindings.
- Any pre-commit replacement failure closes the shadow scope and retains the old generation. Post-commit consumer-remount or old-scope cleanup failure is reported as committed but degraded, not rolled back.
- Physical removal deletes the feature package, feature-local tests, entry point, and Import Linter module entry in an isolated copy, then proves stale desired state becomes `MISSING` while unrelated features continue.

### §6.6 — Interfaces, readiness, plugins, and diagnostics

`RuntimeStatus`, `CompositionEngine.get_status()`, and the capability registry expose profile readiness, missing profile capabilities, active features/capabilities and owner generations, feature states, blocked reasons, package/capability errors, runtime failures, replacement reports, effects, and cleanup errors. The launcher may serialize this state for local diagnostics. Product-facing HTTP, SSE, CLI, MCP, and automation projections are removable D-IFACE features and must not become a second runtime model.

Trusted installed Python feature distributions run in process through `haruquantai.features` and receive normal `FeatureContext` lifecycle ownership. Untrusted plugins, scripts, connectors, compilers, AI tools, and native extensions remain a different product boundary: they execute in supervised processes/containers and exchange public wire contracts and artifact handles. Installing an in-process feature grants trusted-code authority and cannot satisfy an untrusted-plugin isolation requirement.
