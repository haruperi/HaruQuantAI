# HaruQuantAI Architecture

> **Status:** Owner-local target architecture ratified on 2026-09-22 through
> `ARCH-FINALIZE-001`, iteration 2, amended by iteration 3 for single-file host
> owners. S1 kernel, composition, and telemetry ownership, and S2 shared plugin
> metamodel and host catalog are implemented; later source stages require their
> own approved implementation plans.

This document owns structural constraints. [PROJECT.md](PROJECT.md) owns product
scope and implementation status; [AGENTS.md](../AGENTS.md) owns workflow and
verification. Ratification establishes paths, ownership, and required semantics;
it does not supply implemented APIs or authorize source scaffolding.

## Current implementation

```text
app/
|-- __init__.py
|-- host/
|   |-- __init__.py
|   |-- bootstrap.py  # S1/S2 application composition root (HOST_TELEMETRY, HOST_CATALOG)
|   |-- catalog.py    # S2 filesystem discovery, validation, snapshots, and admission
|   `-- telemetry.py  # S1 observation contract, provider, and lifecycle
|-- kernel/           # remediated S1 composition/lifecycle primitives
|-- plugins/          # S2 shared plugin metamodel
|   |-- __init__.py
|   |-- algebra.py    # GraphSpec, GraphDocument, Kahn cycle check, validate_graph
|   |-- lowering.py   # Universal semantic IR and lowering target specs
|   |-- schema.py     # Bounded immutable values, parameter specs, port specs
|   |-- spec.py       # PluginRef, PluginSpec, OperationSpec, CatalogView
|   `-- wire.py       # Canonical JSON serialization and SHA-256 fingerprinting
`-- ui/               # retained mock-backed prototype
```

Execution, gateway, durable infrastructure, and concrete quantitative plugins
below remain future implementation stages. S2 provides the universal metamodel
and catalog; it does not claim strategy execution or live trading.

## D1. Runtime layers and target folders

Retain host infrastructure -> workspace plugins -> selected plugins as an
orchestration hierarchy. It is not a chain of concrete Python imports. A workspace
selects installed contributions; it does not own their code or infrastructure.
Keep the host capability dependency graph distinct from the quantitative algebra
graph. One declared host capability graph does not turn indicator nodes into
services or replace typed strategy composition.

```text
app/
  __init__.py
  kernel/
    capability.py               # immutable versioned Capability[T]
    feature.py                  # generic host lifecycle/slot declarations
    context.py                  # restricted host composition scope
    bootstrapper.py             # canonical startup and reverse cleanup
  host/
    bootstrap.py                # application composition root
    catalog.py                  # discovery, validation, snapshots, enablement
    execution.py                # execution contracts, graph planning, dispatch
    jobs.py                     # jobs contracts, implementation, lifecycle
    workers.py                  # workers contracts, implementation, lifecycle
    storage.py                  # storage contracts, implementation, lifecycle
    artifacts.py                # artifact contracts, implementation, lifecycle
    gateway.py                  # transport envelopes, implementation, lifecycle
    telemetry.py                # telemetry contracts, implementation, lifecycle
  plugins/
    spec.py                     # PluginSpec, operations, contribution/view types
    schema.py                   # parameters, ports, values, safe UI vocabulary
    algebra.py                  # generic graph nodes, edges, references
    lowering.py                 # shared semantic IR and lowering protocols
    wire.py                     # plugin/catalog/graph JSON projections
    workspaces/
      builder.py
      retester.py
      optimizer.py
      results.py
    indicators/
      rsi.py
    comparisons/
      greater_than.py
    blocks/
    metrics/
    columns/
    crosschecks/
    optimizers/
    exporters/
    data_sources/
    brokers/
    tasks/
  ui/
```

This is a target ownership map, not a scaffolding checklist or an allowed-write
list. Add settings, scheduling, security, authorization, resource controls,
notifications, health, and network providers under their cohesive host owners
only as approved use cases require. Host services may start lazily; startup
necessity is not the criterion for ownership. Artifact access is the public
resource abstraction; storage owns its physical persistence and transactions.

Each host owner is one cohesive `app/host/<owner>.py` file containing its public
protocols, immutable tokens and public values/errors, private implementation,
and composition-only construction/lifecycle entry point. Public and private
boundaries are defined by symbols in that file, not by companion modules.

No `app/api/`, `app/workspaces/`, `app/contracts/`, `app/services/`, root
`app/registry.py`, or `app/main.py`. Composition begins in `app/host/bootstrap.py`.
All package initializers remain empty or docstring-only.

## D2. Public ownership and import rules

The five shared modules directly beneath `app/plugins/` are universal support
modules, not concrete plugins and not discovery candidates. Their admission test
is whether the definition describes a reusable plugin mechanism without naming
a concrete quantitative concept or requiring an edit for each new plugin.

| Importing code | Allowed application dependencies | Forbidden dependencies |
|---|---|---|
| Kernel | Other kernel primitives | Host, plugins, UI, product schemas |
| Shared plugin modules | Acyclic shared plugin modules; kernel capability primitive where needed | Concrete plugins, host modules, UI, kernel runtime/context |
| Host contract definitions in `<owner>.py` | Kernel capability primitive; shared plugin types; explicitly declared acyclic contract symbols from other host owners | Provider instances or optional provider libraries required to define/import the contract; concrete plugins |
| Concrete plugin/workspace | Shared plugin modules; designated contract symbols from approved host owner files; kernel capability type as needed | Other concrete plugins, host implementation/catalog objects or lifecycle entry points, kernel runtime/context/bootstrapper, UI |
| Host implementation in `<owner>.py` | Kernel, shared plugin vocabulary, own private code, other owners' designated contract symbols | Other owners' private implementation or lifecycle entry points; concrete-plugin source imports |
| Host composition root | Host implementation entry points and generic catalog loader | Central imports/list of concrete plugin identities |
| UI | Versioned gateway data and generated/conformance-checked client types | Python runtime objects, private host state, copied quantitative algorithms |

Shared support types may be imported by multiple plugins; that is not a sibling
implementation import. Consumers import only designated contract symbols from a
host owner, never its concrete classes or construction/lifecycle entry point.
Only host composition may construct the provider through that entry point.

Importing a contract evaluates the entire owner module and therefore defines its
implementation too. It must not instantiate/start a provider, acquire resources,
read the environment, self-register, configure logging, or start tasks/threads.
Check top-level code, bases, annotations, decorators, defaults, and transitive
imports. Optional provider libraries load only inside explicit construction/start;
public types must be usable without those libraries installed. Package
initializers remain empty or docstring-only.

Contract exports are identified in the owning module when its exact source API
is ratified. They are not moved into a central contract registry. Architecture
checks must enforce symbol access, including aliases and module attributes,
rather than prohibit the owner module merely because it also defines concrete
implementation. Cross-owner contract imports remain acyclic; shared plugin
support still cannot import host modules. Discovery is the host's explicitly
bounded dynamic-loading responsibility; ordinary host execution never imports
concrete plugin modules by hard-coded name.

Example ownership: `Capability[T]` is generic kernel vocabulary. `Jobs`,
`HOST_JOBS`, `JobRequest`, `JobRef`, and `JobStatus` live together in
`app/host/jobs.py`, alongside its private implementation. Builder imports only
the designated contract symbols and receives the service through typed slots.
RSI's parameter type
and policies live only in `rsi.py`. A shared parameter descriptor defines how to
describe a parameter; it does not define RSI's period or optimizer bounds.

## D3. Effects, local state, and lifecycle are independent

Use two execution mechanisms, without forcing plugin kinds into a false binary:

1. Host components acquire long-lived resources through the kernel runtime and
   expose scoped services through capabilities.
2. Plugin operations execute from immutable declarations, inputs, normalized
   parameters, and explicit typed bindings. Pure operations need no host startup.

Each operation declares effect requirements and any run-owned lifecycle needs.
A pure batch indicator has no external effects. A streaming indicator may own
private per-run accumulator state; it must not share mutable state across runs.
Data-source and broker operations declare network/effect capabilities. An exporter
may produce text purely while artifact persistence is a separate authorized
operation. A cross-check can orchestrate simulations through declared execution
capabilities rather than being mislabelled an inherently pure calculation.

A workspace's definition is immutable; opening it need not start a service. If a
workspace operation genuinely requires a subscription/session, a host-owned scope
provides an explicit resource lease and cleanup. Workspaces receive neither
`FeatureContext` nor direct access to `AsyncExitStack` or process registries.

Factory purity and operation purity are separately verified. The zero-argument
`plugin()` factory returns a contribution with pure construction and no I/O;
typed operation bindings are supplied later. Metadata cannot enforce isolation
against malicious Python; the initial implementation trusts approved local code.

## D4. Kernel disposition and lifecycle correctness

The kernel uses only the Python standard library and business-neutral kernel
primitives. Plugin, product, persistence, transport, and UI knowledge stay outside.

S1 retains and remediates the concepts and filenames of `Capability`,
`FeatureSpec`, `Feature`, `FeatureContext`, and `Runtime`. The rules below remain
normative for later extensions of that lifecycle foundation.

- Keep immutable capability names and compatibility majors; reject ambiguous
  same-identity incompatible contracts before startup. Static typing is not
  sufficient runtime contract validation.
- Limit contexts to declared slots. Remove ambient `available_capabilities` and
  unrestricted `has/get` access from consumer scopes. Root diagnostics may expose
  immutable composition reports without giving plugins a service locator.
- Startup graph ordering uses required edges and stable canonical identity tie
  breaks. Optional operation capabilities never introduce startup edges. Resolve
  optional bindings explicitly at admission; unavailable bindings gate only the
  dependent operation.
- Preserve transactional startup, staged publication, cancellation, bounded
  cleanup, and reverse ownership order. Await async cleanup, including failed
  startup cleanup; do not register async stop with a synchronous callback API.
- Validate duplicate feature names, duplicate providers, unknown enabled names,
  required-dependency closure, and cycles before starting any required component.
  Do not silently skip a required provider and report successful composition.
- A failed or cancelled startup unwinds both the partially started component and
  previously activated components in that composition attempt. Withdraw staged
  or published capabilities as appropriate; closed scopes cannot resolve or
  publish values. Preserve the initiating error and report cleanup failures.
- Stop new operation admission before shutdown; drain/cancel consumers and await
  their cleanup while their provider bindings remain valid. Only then withdraw
  those bindings and release providers. A reverse activation list is sufficient
  for dependency order only for the validated fixed graph with all active
  consumers accounted for. LIFO within each component does not supply that
  system-wide guarantee on its own.
- Cleanup errors must not skip unrelated safe cleanup scopes. Record and aggregate
  failures, keep shutdown idempotent, and distinguish a failed callback from a
  still-live consumer. If a consumer cannot quiesce, do not claim safe provider
  withdrawal or successful cleanup; report the affected dependency chain and
  use the stage's explicit bounded shutdown policy.
- Initial host composition is startup/shutdown based. Host provider replacement
  requires a controlled restart; reactive host hot-swapping is deferred. Catalog
  refresh updates future selection/admission, not the bindings of active runs.
- Move concrete logging and event delivery out of `app/kernel/`. A minimal
  injected diagnostic callback/protocol may remain business-neutral. Host-owned
  typed observation streams isolate subscriber failures and enforce bounded
  delivery. Observer errors are diagnosed, not silently swallowed.
- Pure plugin evaluation must not acquire kernel lifecycle machinery.

No kernel source is removed during architecture ratification. The kernel stage
must explicitly inventory event/logging consumers, tests, and examples before
authorizing exact deletion/migration targets.

## D5. Minimal public metamodel and its owners

These names define conceptual public types to be made signature-complete in the
implementation-stage plan; they do not claim existing APIs.

| Module/owner | Public concepts and required semantics |
|---|---|
| `plugins/spec.py` | `PluginRef`, `PluginSpec`, `OperationSpec`, `PluginContribution`, `WorkspaceSpec`, immutable catalog descriptions/views; side-effect-free construction and bounded typed operation interfaces. Host components do not pretend to be quantitative plugin kinds. |
| `plugins/schema.py` | Parameter/port/value descriptors, units/alignment, defaults, validity constraints, optimization domains, numerical-policy descriptions, safe UI hints. Distinguish valid range from optimization search range. |
| `plugins/algebra.py` | Versioned `GraphDocument`, stable `NodeId`, `NodeSpec`, typed edges, literals/references, hierarchical subgraphs and designated roots. No RSI fields, central `CompareOp`, or fixed entry/exit `Comparison` class. |
| `plugins/lowering.py` | Versioned bounded semantic IR and lowering/result protocols. Generic primitives are language semantics, not a registry of plugin names. |
| `plugins/wire.py` | Canonical versioned JSON projection and validation for shared descriptors/graphs/values. No HTTP or persistence implementation. |
| Public symbols in `host/<owner>.py` | Cohesive service protocol, versioned token, public request/result/error values, effect and cancellation semantics; implementation is private in the same file. Job, worker, and transport envelopes belong to `jobs.py`, `workers.py`, and `gateway.py` respectively. |
| Concrete plugin file | Actual parameter types, constants/enums, schema instances, normalization/validation, dynamic lookback/warm-up, numerical behavior, operation implementations and target lowering. |

Use bounded typed value unions and recursive validation, not arbitrary `Any`
dictionaries as the public model. Freeze nested collections, reject undeclared
coercions, and specify array/series ownership so consumers cannot mutate another
operation's input. Warm-up and lookback are evaluated from validated parameters;
the UI and optimizers do not independently reconstruct these functions.

Initial stable IDs are lowercase dot-separated namespace segments, independent
of labels and paths. Identity uniqueness is global within a snapshot, not merely
within a `(kind, id)` pair. Start with one installed implementation version per
ID per snapshot. Plugin implementation version, metamodel compatibility major,
capability major, graph/wire schema version, and artifact schema version remain
distinct. Runs pin exact versions and content identities.

## D6. Discovery, validation, enablement, and removal

`host/catalog.py` scans configured roots at startup or explicit refresh. Scan
approved concrete family directories such as `plugins/indicators/` and
`plugins/workspaces/`; do not import every file recursively beneath `plugins/`.
Shared root modules, initializers, tests, and caches are excluded before import.
Declared family roots describe a supported extension boundary, not a list of
concrete plugin IDs. New plugins within a supported family need no central edit.
Adding a genuinely new family/metamodel operation requires deliberate evolution.

Bound enumeration and imports, sort candidates canonically, call `plugin()`,
validate schemas/identities/compatibility, and publish atomically. Reject duplicate
IDs or invalid candidate snapshots with structured errors. Failed refresh keeps
the last valid snapshot; initial failure leaves catalog readiness unavailable
while diagnostics remain accessible. Candidate admission failure is not claimed
as successful installation. Per-plugin quarantine is not silently added.

Keep installed availability separate from profile/workspace enablement and
authorization. Installation alone never starts effects. Build the workspace's
effective selection from accepted kinds, operations, port compatibility, target
support, permissions, and explicit enablement.

The host owns mutable registry construction and runtime operation resolution.
Plugins can receive a declared immutable scoped catalog description for selection
or generation, never the live registry. Jobs execute against an admitted frozen
catalog/dependency set; no filesystem rediscovery occurs during operations.

Removal changes the global catalog fingerprint but not unrelated entry content,
relative execution order, or results. New requests cannot select removed entries.
Unknown references preserve their data and become explicitly unavailable. Existing
jobs use retained verified code/data or fail with an attributed missing dependency;
they must never silently rebind to a replacement version. Lossless editing and
storage of unknown nodes is distinct from permission to execute them.

## D7. Algebra, execution, optimization, and export

Use an immutable typed DAG with hierarchical subgraphs. Tree editors are views
of that document. Node references include stable IDs, plugin ID/exact version,
normalized parameters, ports, and connections. Validate types, units, alignment,
resource bounds, domain compatibility, and graph cycles before execution.
Recurrence is explicit node behavior with run-local state, not an implicit cycle.

An indicator, comparison, sizing rule, or strategy block contributes a typed node.
For example, `greater_than.py` owns its comparison behavior and descriptor; adding
another comparison expressible through existing ports/operations changes no AST
enum or generic executor. Do not generalize all effects into freely interchangeable
nodes: numerical, trading-rule, and workflow domains retain explicit compatibility.

Builder and optimization algorithms create new document revisions. Workspaces
submit requests to host execution/jobs; they do not implement competing evaluators.
Host execution validates and dispatches generic operations. Strategy semantics
remain in the contributing plugins and shared operation contracts. Sharing a
document alone is not accepted as evidence of semantic parity.

Export invokes node-owned lowering into the declared semantic IR; exporter plugins
own generic target emission. Do not centralize RSI-specific math in an exporter or
declare targets with no working lowering. Export must preserve warm-up, alignment,
missing-data, precision, and state semantics, or fail as unsupported. A novel IR
primitive requires reviewed metamodel evolution; new indicators expressible in
the existing vocabulary do not. Export delivery/persistence is separately scoped.

## D8. Workspace, UI, wire, and reproducibility boundaries

`WorkspaceSpec` in `plugins/spec.py` declares identity/version, commands,
configuration, accepted child kinds/operations, operation-specific capability
slots and authorization, and a generic view/route or installed-extension reference.
Builder, Retester, Optimizer, and Results are peer concrete plugins. Workspaces
may construct compositions by explicit IDs without importing their implementations.
Disabling one workspace does not uninstall shared children or stop shared host
services needed by another.

The UI receives versioned JSON catalog/resource descriptions. It owns catalog
cache, recoverable drafts, and view state; durable truth and authorization remain
backend-owned. Bounded controls include numeric/text/boolean/enum forms, groups,
typed ports, tables, and charts. A route string cannot install React behavior;
novel interactions need a reviewed generic renderer or installed UI extension.
Prototype routes, mock services, and hard-coded schemas remain labelled prototype
until replaced under a UI source plan.

Wire boundaries serialize immutable values and references, not Python instances,
callables, capability objects, or pickle. Use explicit missing-value encodings,
not JSON NaN/Infinity. Generate or conformance-check client representations from
the owning wire definitions; do not duplicate plugin metadata in TypeScript.
Process boundaries reconstruct validated values and scoped capability bindings;
credentials never enter graph or job documents. Unknown graph fields/nodes remain
structurally lossless. Preserve raw documents when the entire version is unknown;
do not execute or automatically rewrite them. Explicit deterministic migrations
retain the original representation.

Record data/artifact hashes, document identity/version, plugin versions and content
hashes, full catalog provenance plus referenced-dependency fingerprints,
engine/exporter version, normalized settings, units, timezone, numerical policy,
seed, environment, status/timestamps, and lineage. Reproducibility applies to
frozen inputs and declared numerical environments; live data/effects are not
made deterministic merely by labelling the plugin deterministic.

## Required usage evidence for later source stages

These scenarios are planned acceptance, not implemented demonstrations:

1. A cohesive RSI plugin exposes validated period-dependent policies and actual
   calculation/lowering. Golden cases cover empty/short input, flat and monotonic
   series, missing/non-finite samples, invalid periods, and mutable-input isolation.
2. Add a probe indicator and a new comparison in already supported families.
   Discover/enable them without registry, metamodel, engine, or UI source edits.
3. Select the same probe in two workspace profiles. Build and round-trip the same
   graph, execute it, optimize declared parameters, and run every claimed export
   against supported output semantics. Generic UI controls use the same schema.
4. Disable/remove the probe and one workspace. Preserve unknown references and
   unrelated results; the second workspace retains access to shared valid plugins.
5. Concurrent independent runs have no shared mutable calculation state. Missing
   optional capabilities gate only their operation. Cancellation/startup failures
   release owned resources; observer failure does not fail an unrelated publisher.

## Enforcement and implementation gates

The five Spatial Composability laws apply to every source stage. Architecture
checks, strict typing, boundary validation, plugin tests, removal tests, and
consumer parity evidence must enforce the ownership and semantics above.
Documentation, an advertised export target, or a shared graph object alone is not
proof of implementation correctness.

The S1 architecture tests enforce the exact current kernel/host topology, kernel
purity, initializer purity, superseded-root exclusions, and composition-only
access to private host construction symbols. Each later approved source stage
must deliberately extend this enforcement with its new owners and import rules.

Follow the [workspace and plugin implementation pipeline](dev/workspace_plugin_implementation_pipeline.md)
and [companion audit](dev/workspace_plugin_implementation_audit.md). Focused tests and offline
usage examples belong to each source plan; candidate qualification remains
`uv run python scripts/ci_check.py` plus applicable UI checks.

Historical task records and external designs are context, not proof of current
behavior. This architecture does not claim SQX parity or a formal implementation
of the Cordis reactive calculus. The first host lifecycle is startup/shutdown
based; reactive host replacement is deferred. Live trading and other irreversible
external mutations require distinct authorization.
