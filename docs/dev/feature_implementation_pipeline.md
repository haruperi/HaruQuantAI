# Plugin Implementation Pipeline

> **Status:** Canonical build standard for future HaruQuantAI backend plugins.
> **Activation condition:** Use only after the replacement plugin API and host
> paths are ratified in an approved architecture plan.

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
2. Standard-library and approved universal API imports.
3. Stable constants and immutable plugin-local enums/value types.
4. Immutable parameter/config type when the universal schema requires one.
5. Pure validation and calculation helpers.
6. Main behavior implementation.
7. Immutable self-description/contribution object.
8. Side-effect-free zero-argument factory such as `plugin()`.

Importing the module must not perform discovery, registration, file/network I/O,
environment reads, logging configuration, task/thread creation, or global
mutation.

## 4. Identity and compatibility

- IDs are lowercase, namespaced, stable, and independent of display labels.
- Plugin implementation version, capability major version, wire schema version,
  and artifact schema version are distinct concepts.
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

## 6. Typed algebra and execution

- Inputs and outputs use explicit immutable port types.
- Algebra nodes reference stable plugin identity/version and canonical parameters.
- Connections are validated before execution; implicit coercion is prohibited
  unless the universal type system names it.
- Behavior is deterministic for identical frozen inputs, settings, catalog, and
  seed.
- Warm-up, lookback, missing values, NaN/infinity, division by zero, insufficient
  data, ordering, timezone, precision, and rounding are explicit.
- Optimizer and exporter consumers use the same node/schema semantics as the
  simulator. Consumer-specific reinterpretation is prohibited.

## 7. Capabilities and dependencies

- Host services are requested through typed `Capability[T]` slots.
- Required and optional slots are declared in immutable metadata.
- Optional capability absence disables only the named operation that needs it.
- Plugins never enumerate the ambient provider registry or import host internals.
- Plugins never import sibling plugin implementations. Composition occurs through
  algebra documents and public universal types.
- Availability is separate from enablement. Installation alone must not activate
  externally mutating or computationally expensive behavior.

## 8. Effects, security, and resources

Pure quantitative plugins should be effect-free. A plugin that legitimately
needs an external resource must use an approved host capability and lifecycle:

- explicit timeout, retry, rate, and circuit policies;
- bounded memory, records, payloads, concurrency, and execution time;
- managed cancellation and cleanup;
- no credentials in plugin metadata, artifacts, errors, or logs;
- no raw connections, SQL, filesystem roots, subprocesses, or network clients;
- fail-closed authorization for mutations.

## 9. Tests and usage evidence

Each plugin requires:

- identity/schema construction and invalid-schema tests;
- hand-calculated golden examples for numerical behavior;
- boundary and degenerate-input tests;
- determinism and immutability tests;
- algebra port/type compatibility tests;
- optimizer-bound and serialization round-trip tests where applicable;
- discovery without registry edit;
- disable/removal test proving unrelated catalog entries and behavior are stable;
- consumer parity tests across every claimed consumer;
- a deterministic, offline, secret-safe primary-purpose usage example.

Accelerated implementations require equivalence tests against the clearest scalar
reference. Coverage never replaces semantic or numerical evidence.

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
| `PIP-03 IMPORT` | Import is side-effect-free and uses no private/sibling/host implementation imports. |
| `PIP-04 ID` | IDs and versions are canonical, collision-safe, and migration-aware. |
| `PIP-05 SCHEMA` | Parameters are immutable, typed, bounded, unit-aware, and introspectable. |
| `PIP-06 PORTS` | Inputs/outputs and algebra placement are explicitly typed. |
| `PIP-07 SEMANTICS` | Warm-up, missing-data, numerical, error, and determinism policies are explicit. |
| `PIP-08 CAP` | Host collaboration uses declared typed capability slots only. |
| `PIP-09 DISCOVERY` | Installation requires no central registry, engine, or UI source edit. |
| `PIP-10 ENABLE` | Availability and enablement are distinct; unsafe behavior defaults disabled. |
| `PIP-11 ORTHO` | Add/change/disable/remove affects only explicit dependents. |
| `PIP-12 ALGEBRA` | All consumers share one versioned algebra and canonical parameters. |
| `PIP-13 UI` | UI is generated from schema within the approved renderer vocabulary. |
| `PIP-14 EFFECT` | Effects are bounded, authorized, lifecycle-owned, and secret-safe. |
| `PIP-15 TEST` | Goldens, edges, determinism, schema, and failure behavior are tested. |
| `PIP-16 REMOVE` | Physical removal and unresolved-document behavior are tested. |
| `PIP-17 PARITY` | Every claimed consumer proves semantic parity. |
| `PIP-18 EXAMPLE` | A deterministic offline primary-purpose scenario passes. |
| `PIP-19 EVIDENCE` | Source-bound acceptance evidence is current and reproducible. |
| `PIP-20 QUALIFY` | Architecture, lint, format, typing, tests, coverage, and applicable UI checks pass. |
