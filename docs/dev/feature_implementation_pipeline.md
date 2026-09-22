# Plugin Implementation Pipeline

> **Status:** Canonical build standard for future HaruQuantAI backend plugins.
> **Architecture:** Owner-local paths and metamodel semantics are ratified in
> `ARCH-FINALIZE-001`, iteration 2, with iteration-3 single-file host ownership.
> Exact APIs and source changes still require
> their own approved implementation plans; no backend implementation is implied.

This pipeline standardizes how every plugin is specified, implemented, tested,
documented, discovered, and evidenced while preserving Spatial Composability.
It supplements `AGENTS.md`, `docs/PROJECT.md`, and `docs/ARCHITECTURE.md`; it does
not override them.

## 1. Core rule: the plugin file is the physical unit

The expected production shape is:

```text
app/plugins/<kind>/<plugin_slug>.py
```

One concrete plugin file owns everything specific to that quantitative concept:

- stable ID, version, kind, title, description, and compatibility;
- parameter schema, defaults, validation, units, optimization bounds, and UI hints;
- typed input/output ports and algebra contribution;
- deterministic calculation/execution behavior;
- warm-up, missing-data, numerical, and error policies;
- lowering/export contributions when supported;
- its side-effect-free factory/contribution declaration.

Do not create companion contract, model, schema, optimization-space, UI metadata,
or exporter files for the same concept. Universal, plugin-agnostic metamodels are
imported from the approved plugin API. Large test fixtures may live under tests,
but production behavior must remain local.

Package READMEs document a plugin family and its shared policy. They do not
duplicate the authoritative schema or behavior of individual plugin files.

The shared plugin API is `app/plugins/spec.py`, `schema.py`, `algebra.py`,
`lowering.py`, and `wire.py`; there is no `app/api/`. These are universal support
modules excluded from discovery before import. Concrete workspaces live under
`app/plugins/workspaces/` and comparisons under `app/plugins/comparisons/`.
Adding a concrete plugin within a supported family must not modify shared types.

Each host owner is one `app/host/<owner>.py` file containing public protocols,
tokens, request/result/error values, private implementation, and a composition-only
construction/lifecycle entry point. Consumers import only designated contract
symbols and never access provider classes or lifecycle entry points. Host
infrastructure remains distinct from quantitative plugins.

Importing a contract evaluates the whole owner module, including implementation
definitions. It must not instantiate/start the provider, acquire resources, or
require optional provider libraries. Defer those library imports to explicit
construction/start; public contract types must not depend on them. Check bases,
annotations, decorators, defaults, top-level code, transitive imports, and package
initializers for effects. Identify the public contract symbols inside their
owning file rather than through a separate central module or registry.

## 2. Required workflow

1. Read repository authorities and the owning plugin-family README.
2. Audit the universal plugin API, consumers, discovery, tests, and existing IDs.
3. Create the task implementation plan and stop at the owner approval gate.
4. Define acceptance examples before implementation.
5. Implement one cohesive plugin file without editing central registration code.
6. Add focused tests and one deterministic offline usage scenario.
7. Run focused tests while editing.
8. Run the plugin audit in `domain_implementation_audit.md`.
9. Run full candidate qualification.
10. Write the walkthrough and stop at the owner commit gate.

## 3. Canonical plugin anatomy

The exact universal API is architecture-owned, but every concrete plugin must
present these conceptual sections in this order where applicable:

1. Module docstring: purpose, semantics, units, edge policies, usage.
2. Standard-library, shared plugin API, and approved owner-local public host
   contract imports; approved numerical dependencies where needed.
3. Stable constants and immutable plugin-local enums/value types.
4. Immutable parameter/config type when the universal schema requires one.
5. Pure validation and calculation helpers.
6. Main behavior implementation.
7. Immutable self-description/contribution object.
8. Side-effect-free zero-argument `plugin()` factory returning the contribution.

Importing the module must not perform discovery, registration, file/network I/O,
environment reads, logging configuration, task/thread creation, or global
mutation.

Factory construction and operation execution are distinct. Constructing the
contribution must not acquire resources or instantiate an effectful session.
Operations later receive validated inputs, normalized parameters, and explicit
typed bindings. Declare effect requirements, run-local state, and lifecycle needs
per operation; do not infer them from indicator/workspace/exporter kind.

## 4. Identity and compatibility

- IDs are lowercase dot-separated namespaces, stable, and independent of display
  labels and file paths. IDs are unique across kinds within a catalog snapshot;
  initially one implementation version per ID is installed in each snapshot.
- Plugin implementation version, metamodel compatibility major, capability major,
  graph/wire schema version, and artifact schema version are distinct concepts.
- Breaking semantic or port/schema changes require the appropriate major/version
  transition and explicit migration/unsupported behavior.
- Aliases and deprecations are explicit metadata with bounded lifetimes.
- Duplicate IDs fail catalog publication; discovery never silently selects one.

## 5. Schema-driven self-description

Every user-configurable parameter declares:

- stable key and value type;
- required/default behavior;
- valid values or numeric constraints;
- unit and semantic meaning;
- optimization eligibility, bounds, scale, and step/distribution where valid;
- generic presentation hints from the approved vocabulary;
- cross-field constraints in deterministic validation logic.

The schema is executable truth used by the UI, generators, optimizers, validation,
serialization, and documentation tooling. Consumers may project it but may not
maintain separate plugin-specific copies.

Validity limits and optimizer search bounds are separate constraints. Normalize
and validate without silent coercion. Use bounded typed values and recursively
validated immutable collections; reject mutable/unsupported leaves instead of
passing arbitrary objects through a freeze helper. Define series ownership so
concurrent runs cannot mutate shared inputs or accumulator state. A cached Python
hash or copied dictionary is not proof of immutability or a durable fingerprint.

## 6. Typed algebra and execution

- Inputs and outputs use explicit immutable port types.
- Algebra nodes reference stable plugin identity/version and canonical parameters.
- Connections are validated before execution; implicit coercion is prohibited
  unless the universal type system names it.
- Behavior is deterministic for identical frozen inputs, settings, catalog, and
  seed.
- Warm-up, lookback, missing values, NaN/infinity, division by zero, insufficient
  data, ordering, timezone, precision, and rounding are explicit.
- Warm-up and lookback derive from validated bound parameters through plugin-owned
  policy, not a fixed default in metadata. Seeding, flat-series behavior, and
  recovery after missing data require explicit numerical semantics and goldens.
- Optimizer and exporter consumers use the same node/schema semantics as the
  simulator. Consumer-specific reinterpretation is prohibited.

The algebra is a versioned typed DAG with stable node IDs, plugin ID/exact version,
named ports and connections, and hierarchical subgraphs. Comparisons and sizing
rules are plugin nodes, not central enums or workspace-specific interpreters.
Validate units, alignment, cycles, domain compatibility, and resource bounds.
Recurrence is explicit per-node state, not an implicit graph cycle.

Every claimed export target needs actual plugin-owned lowering into the supported
semantic IR and an exporter providing generic target emission. Test semantic
parity, including numerical policies, not merely emitted text. Unsupported
nodes/targets fail with attributed reasons. New universal IR semantics require
reviewed evolution; plugin-specific formulas remain local.

## 7. Capabilities and dependencies

- Host services are requested through typed `Capability[T]` slots.
- Required and optional slots are declared in immutable metadata.
- Optional capability absence disables only the named operation that needs it.
- Concrete plugins and workspaces may import designated contract symbols from
  approved `app/host/<owner>.py` modules and the kernel capability type. They
  cannot access kernel runtime/context, host implementation/catalog objects,
  provider construction/lifecycle entry points, or another concrete plugin.
  Follow the import matrix in [ARCHITECTURE.md](../ARCHITECTURE.md), including
  transitive imports, aliases, and module-qualified access.
- Plugins never enumerate the ambient provider registry or import host internals.
- Plugins never import sibling plugin implementations. Composition occurs through
  algebra documents and public universal types.
- Availability is separate from enablement. Installation alone must not activate
  externally mutating or computationally expensive behavior.

An explicitly declared immutable scoped catalog description is a valid input to
selection/generation. A live registry or service locator is not. The host alone
resolves admitted operations against frozen dependencies. Discovery scans bounded
configured concrete-family roots only at startup or explicit refresh, excludes
shared modules/initializers/tests/caches before import, sorts canonically, and
atomically validates all candidate identities/schemas. A failed refresh keeps the
last valid snapshot; initial failure leaves catalog readiness unavailable with
diagnostics. No central concrete-plugin list or import is permitted, including
for workspaces. Import purity is an approved-local-code discipline, not a sandbox.

## 8. Effects, security, and resources

Factory purity does not imply operation purity. A calculation may use private
run-local state without a host service lifecycle. An exporter can produce text
purely and persist it through a separate effectful operation. A workspace does
not need a lifecycle merely because it is a workspace. A plugin that legitimately
needs an external resource must use an approved host capability and owned scope:

- explicit timeout, retry, rate, and circuit policies;
- bounded memory, records, payloads, concurrency, and execution time;
- managed cancellation and cleanup;
- no credentials in plugin metadata, artifacts, errors, or logs;
- no raw connections, SQL, filesystem roots, subprocesses, or network clients;
- fail-closed authorization for mutations.

The host stops admission and drains/cancels consumers before withdrawing their
providers. Bindings remain valid during consumer cleanup. Failed/cancelled startup
unwinds the whole composition attempt, and asynchronous cleanup is awaited.
Failures do not skip unrelated safe cleanup; they remain attributed and aggregated.
No shutdown success is claimed while consumers remain live. Plugins do not receive
`FeatureContext`, `AsyncExitStack`, or raw process registries. Host provider
replacement initially requires restart; refresh does not rebind active jobs.

## 9. Tests and usage evidence

Each plugin requires:

- identity/schema construction and invalid-schema tests;
- hand-calculated golden examples for numerical behavior;
- boundary and degenerate-input tests;
- determinism and immutability tests;
- nested mutable-leaf rejection, input isolation, and independent run-state tests;
- algebra port/type compatibility tests;
- optimizer-bound and serialization round-trip tests where applicable;
- discovery without registry edit;
- pre-import exclusion of shared modules and transitive contract-import purity;
- contract import with optional provider libraries unavailable, no provider
  instantiation/resource acquisition on import, and rejection of direct/aliased/
  module-qualified access to another owner's implementation or lifecycle entry;
- disable/removal test proving unrelated catalog entries and behavior are stable;
- a new comparison and indicator within supported vocabulary with no shared
  schema/algebra/engine/UI edits, plus discoverable workspace selection/removal;
- consumer parity tests across every claimed consumer;
- dynamic warm-up, declared ports, and an implemented lowering/parity check for
  every advertised export target;
- a deterministic, offline, secret-safe primary-purpose usage example.

Accelerated implementations require equivalence tests against the clearest scalar
reference. Coverage never replaces semantic or numerical evidence.

Integration fixtures must distinguish a changed whole-catalog fingerprint from
stable unrelated entries/dependency fingerprints and results. Unknown or removed
nodes round-trip losslessly as unavailable; unsupported whole-document versions
remain read-only. Admitted runs use their pinned versions or fail explicitly,
never silently substitute new code. Two workspaces can share a plugin, and removing
one workspace must preserve the other's selection and shared host services.

Use `tests/plugins/<kind>/test_<slug>.py` for concrete tests, `tests/host/` and
`tests/integration/` for host/composition proofs, and `tests/examples/<scenario>.py`
for deterministic offline usage. Stage plans approve exact paths and commands.

## 10. Documentation and evidence

The plugin module docstring explains behavior and edge policy. The family README
indexes stable IDs and shared constraints without copying individual parameter
schemas. Project-level docs change only for system scope, workflow, or
architecture changes.

Acceptance evidence records exact source hash, plugin/catalog identity, tests,
commands, exit codes, environment, example, and relevant artifact fingerprints.
Evidence is regenerated when behavior or schema changes; stale evidence is a
failure, not historical truth. Git and `.agents/logs` hold history.

## 11. Verification cadence

Focused iteration:

```powershell
uv run pytest --no-cov tests/plugins/<kind>/test_<plugin_slug>.py -v
```

Candidate qualification:

```powershell
uv run python scripts/architecture_check.py
uv run python scripts/ci_check.py
```

Run UI typecheck/unit/build when catalog, algebra, schema, transport, or renderer
behavior changes.

## 12. Mandatory control matrix

| ID | Obligation |
|---|---|
| `PIP-01 OWNER` | One stable plugin identity has one owning production file and one family. |
| `PIP-02 LOCAL` | Plugin-specific behavior, schema, bounds, outputs, and metadata are co-located. |
| `PIP-03 IMPORT` | Contract imports may define co-located implementation but never instantiate/start it or require optional provider libraries; consumers access only designated contract symbols; concrete sibling/runtime/private host access is prohibited. |
| `PIP-04 ID` | IDs and versions are canonical, collision-safe, and migration-aware. |
| `PIP-05 SCHEMA` | Parameters are immutable, typed, bounded, unit-aware, and introspectable. |
| `PIP-06 PORTS` | Inputs/outputs and algebra placement are explicitly typed. |
| `PIP-07 SEMANTICS` | Parameter-derived warm-up/lookback, seeding, missing-data recovery, numerical errors, and determinism policies are explicit. |
| `PIP-08 CAP` | Host collaboration uses declared typed capability slots only. |
| `PIP-09 DISCOVERY` | Bounded canonical discovery excludes support modules before import and needs no concrete-plugin/workspace list edits. |
| `PIP-10 ENABLE` | Availability and enablement are distinct; unsafe behavior defaults disabled. |
| `PIP-11 ORTHO` | Add/change/disable/remove affects only explicit dependents. |
| `PIP-12 ALGEBRA` | All consumers share one versioned algebra and canonical parameters. |
| `PIP-13 UI` | UI is generated from schema within the approved renderer vocabulary. |
| `PIP-14 EFFECT` | Operation effects/state/lifecycles are separate; resource scopes, drain/cleanup, authorization, bounds, and secrets are enforced. |
| `PIP-15 TEST` | Goldens, edges, determinism, schema, and failure behavior are tested. |
| `PIP-16 REMOVE` | Physical removal and unresolved-document behavior are tested. |
| `PIP-17 PARITY` | Every claimed consumer/target has actual implementation and semantic parity evidence. |
| `PIP-18 EXAMPLE` | A deterministic offline primary-purpose scenario passes. |
| `PIP-19 EVIDENCE` | Source-bound acceptance evidence is current and reproducible. |
| `PIP-20 QUALIFY` | Architecture, lint, format, typing, tests, coverage, and applicable UI checks pass. |
