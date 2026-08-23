# Runtime Kernel

> **Package:** `app/kernel/`
> **Category:** Non-domain shared substrate
> **Status:** `Implemented`

## Purpose

`app/kernel/` is the independent spatiotemporal composability core. It contains no business-domain policy and does not depend on contracts, composition, API, or services.

## Implemented ownership

- `CapabilityKey` and capability errors.
- `FeatureSpec`, `Feature`, optional health/quiesce/drain protocols, and `FeatureState`.
- `FeatureContext`/`DefaultFeatureContext` and lifecycle-owned `FeatureScope`.
- `ServiceRegistry`, provider owner/generation metadata, and atomic provider-bundle operations.
- `DependencyGraph` and `Reconciler`, including conflicts, required/optional dependencies, cycles, affected closures, staged mount, and teardown.
- Typed `EventBus` modes and exact contributor disposal.
- Supervised feature tasks and owner-attributed runtime-failure handling hooks.
- `StateDeclaration`/retention vocabulary and transactional replacement result models.

## Boundary

`app/kernel/` may use the standard library and approved low-level libraries only. It must not import `app/contracts/`, `app/composition/`, or `app/services/`. Import Linter, AST architecture checks, strict typing, and kernel tests enforce this direction.

Discovery, TOML configuration, readiness profiles, file watching, runtime diagnostics, and application orchestration belong to `app/composition/`. Cross-boundary application/domain DTOs, ports, events, and capability constants belong to `app/contracts/`. Product-facing facades and transports belong to registered Interfaces features. Business implementations belong to feature packages.

## Lifecycle rule

`Feature.mount(context, config)` is the only mandatory feature lifecycle method. Providers and reversible acquisitions are staged in a private `FeatureScope`; publication occurs only after successful mount and exact provider-bundle validation. There is no mandatory feature-owned `unmount()`: reconciliation closes the scope idempotently in LIFO order. Optional health/quiesce/drain hooks apply to explicit transactional replacement.

The authoritative procedural detail is the [Feature Implementation Pipeline](../../docs/dev/feature_implementation_pipeline.md).

---

## Normative Kernel Specification

The stable `§x.y` labels below are preserved for cross-document references. They are authoritative here and no longer identify sections in `docs/PROJECT.md`.

### §6.4 — Feature context, effects, events, state, and lifecycle

`Feature.mount(context, config)` is the only mandatory lifecycle method. `FeatureContext` exposes declared required/optional capability lookup, staged capability provision, owned background-task creation, cleanup callbacks, sync/async context-manager acquisition, typed event subscription/publication, and pipeline dispatch. A feature cannot resolve an undeclared dependency or publish an undeclared capability.

`FeatureScope` owns reversible effects. Closing it is idempotent, runs synchronous/asynchronous cleanup in LIFO order, continues independent cleanup after an error, and retains cleanup diagnostics. There is no mandatory feature-owned `unmount()` method. Optional `health_check()`, `quiesce()`, and `drain()` methods participate in explicit transactional replacement.

`EventBus` supports four modes: `PUBLISH` isolates handler failures during concurrent observation; `SERIAL` dispatches in registration order and propagates failure; `PARALLEL` dispatches concurrently and propagates failure; `PIPELINE` transforms in registration order and short-circuits on `None`. Contributor registration returns an exact disposer so one owner cannot remove another owner's contribution.

`StateDeclaration` records a unique namespace, schema version, retention policy (`retain` or `purge_on_uninstall`), and description. It declares ownership only: current reconciliation does not automatically purge durable state.

`FeatureState` defines `DISCOVERED`, `DISABLED`, `MISSING`, `BLOCKED`, `PREPARING`, `ACTIVE`, `QUIESCING`, `STOPPING`, `STOPPED`, `FAILED_IMPORT`, `FAILED_CONFIG`, `FAILED_START`, and `FAILED_RUNTIME`. Current reconciliation assigns `DISABLED`, `MISSING`, `BLOCKED`, `PREPARING`, `ACTIVE`, `STOPPING`, `STOPPED`, `FAILED_START`, and `FAILED_RUNTIME`. Discovery errors and invalid application configuration are reported outside reconciliation; enum vocabulary alone must not be presented as an observed transition.


### §6.7 — Shared-foundation functional requirements

The stable `FR-KERN-*` IDs below provide product traceability aligned to the implemented feature-granular substrate. They do not create separate `fr_kern_*` runtime modules or require one runtime registration per FR.

| ID | Status | Code-aligned requirement and acceptance |
|---|---|---|
| `FR-KERN-DEFINE_REQUIREMENT_BEHAVIOR` | Implemented | Every runtime unit has one validated `FeatureSpec`; FR IDs remain documented/tested behaviors inside the owning feature. |
| `FR-KERN-DEFINE_LIFECYCLE_CONTEXT` | Implemented | Kernel, contracts, composition, and services obey the enforced import boundaries and substrate code contains no business-domain policy. |
| `FR-KERN-DECLARE_BEHAVIOR_DEPENDENCIES` | Implemented | Cross-feature needs are declared at feature granularity in `requires`/`optional`, never inferred from service imports. |
| `FR-KERN-REGISTER_FEATURE_MODULES` | Implemented | Each installed feature is independently discoverable through `haruquantai.features`; sibling implementations are never imported. |
| `FR-KERN-DEFINE_RESPONSIBILITY_FILES` | Implemented convention | Focused responsibility modules remain internal to one feature and do not self-register as components. |
| `FR-KERN-IMPLEMENT_REQUIREMENT_FUNCTIONS` | Implemented convention | Feature/domain documentation and tests trace each FR to focused implementation evidence without imposing an artificial one-symbol runtime rule. |
| `FR-KERN-DEPEND_PUBLIC_PORTS` | Implemented | Cross-boundary code uses contracts/capabilities; architecture checks reject feature-to-feature implementation imports. |
| `FR-KERN-NAMESPACE_CAPABILITY_KEYS` | Implemented | Capability identifiers match `<lowercase-name>@<positive-major>` and normally use a domain-qualified name. |
| `FR-KERN-DECLARE_DEPENDENCY_RULES` | Implemented | `FeatureSpec.requires` gates activation and `optional` is resolved explicitly; overlap and undeclared lookup are rejected. |
| `FR-KERN-REEVALUATE_DEPENDENCIES` | Implemented | Provider/configuration changes reconcile the exact transitive affected closure; optional provider changes remount consumers. |
| `FR-KERN-DEFINE_SCOPE_HIERARCHY` | Implemented baseline | Each mounted feature owns one private `FeatureScope`; the current kernel does not claim parent/child realm or policy-interception semantics. |
| `FR-KERN-PASS_EFFECT_SCOPES` | Implemented | Capability contributions, subscriptions, tasks, context managers, and callbacks are acquired through the feature context/scope. |
| `FR-KERN-REGISTER_EFFECT_REVERSALS` | Implemented | Reversible acquisitions register their cleanup with the owning scope at acquisition time. |
| `FR-KERN-REVERSE_EFFECTS_LIFO` | Implemented | Scope close is idempotent and executes sync/async cleanup exactly once in reverse order while retaining errors. |
| `FR-KERN-ROLLBACK_FAILED_ACTIVATION` | Implemented | Failed staged mount closes its scope and publishes none of its declared capabilities. |
| `FR-KERN-MANAGE_COMPONENT_LIFECYCLE` | Implemented | Runtime reports the exact `FeatureState` vocabulary and only claims states assigned by the active code path. |
| `FR-KERN-COMMIT_CAPABILITY_SWAP` | Implemented | Provider bundles publish atomically with owner/generation metadata; consumers remount instead of observing an in-place binding change. |
| `FR-KERN-QUIESCE_DEPENDENT_WORK` | Implemented replacement hook | `quiesce()` is optional and used during explicit replacement; ordinary teardown relies on scope-owned cleanup. |
| `FR-KERN-REMOVE_DEPENDENT_COMPONENTS` | Implemented | Removal/reconfiguration closes and remounts or blocks the transitive dependent closure without disturbing unrelated branches. |
| `FR-KERN-ISOLATE_DISPOSAL_FAILURES` | Implemented | Activation, runtime-task, and cleanup failures remain owner/closure-local and appear in diagnostics. |
| `FR-KERN-RECONCILE_DESIRED_STATE` | Implemented | Strict TOML enablement, configuration, profile, and provider selection reconcile serially to a deterministic runtime state. |
| `FR-KERN-REPLACE_COMPONENTS_TRANSACTIONALLY` | Implemented | Compatible shadow replacement rolls back before commit and reports committed degradation after commit; it never fabricates rollback. |
| `FR-KERN-PROVIDE_SCOPED_REGISTRARS` | Implemented core | Context APIs cover capabilities, events, tasks, context managers, and arbitrary cleanup; adapters register other resources with callbacks. |
| `FR-KERN-DRAIN_REMOVED_BEHAVIORS` | Implemented replacement hook | `drain()` is optional for explicit replacement; background tasks and other ordinary effects terminalize through scope cleanup. |
| `FR-KERN-CLASSIFY_COMPONENT_EFFECTS` | Implemented boundary | Reversible effects are scope-owned; durable state/external emissions are documented explicitly and are not blindly reversed. |
| `FR-KERN-NAMESPACE_COMPONENT_STATE` | Implemented declaration | Optional `StateDeclaration` records namespace/schema/retention; storage adapters enforce it and reconciliation does not auto-purge. |
| `FR-KERN-REGISTER_EXTENSION_POINTS` | Implemented primitives | Event contributions and capability-aware Interfaces surfaces have exact owner disposal; new adapters use the same scope callback contract. |
| `FR-KERN-EMIT_CAUSAL_EVENTS` | Implemented baseline | Configuration reload, reconfiguration, and runtime failure publish typed system events; domain events use the same typed bus. |
| `FR-KERN-REJECT_DEPENDENCY_CYCLES` | Implemented | Required cycles block with diagnostics; optional-only cycles do not gate activation. |
| `FR-KERN-PIN_CAPABILITY_SNAPSHOTS` | Product rule | Durable runs pin active capability/provider/configuration evidence exposed by runtime diagnostics. |
| `FR-KERN-TEST_COMPONENT_REMOVAL` | Implemented | Shared lifecycle tests, architecture checks, feature tests, and targeted physical-removal verification cover each installed feature. |
| `FR-KERN-VERIFY_EXACT_REMOVAL` | Implemented | Repeated lifecycle/removal checks prove no scoped provider, listener, task, callback, or context-manager leak remains. |
| `FR-KERN-ROUTE_MULTIPLE_PROVIDERS` | Implemented | One provider binds automatically; ambiguity blocks until `[providers]` selects a valid feature deterministically. |
