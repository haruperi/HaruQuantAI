# Strategy

> **Package:** `app/services/strategy/`
> **Status:** `Missing`
> **Last updated:** `2026-09-18`
> **Domain ID:** `D-STRATEGY`

This README is the domain's single source of truth for its boundary, feature and FR registry,
domain-local workflows, semantic contract ownership, persisted-state model, acceptance evidence,
and deletion behavior. Reference-product evidence is a requirement source, never implementation
evidence.

`PROJECT.md` owns system scope and cross-domain behavior. `ARCHITECTURE.md` owns universal
structure and runtime constraints. `AGENTS.md` owns contributor workflow. The
[Feature Implementation Pipeline](../../../docs/dev/feature_implementation_pipeline.md) owns the
complete single-file feature delivery checklist.

## Code-aligned implementation convention

Backend features use the simplified modular-monolith layout:

```text
app/services/strategy/
|-- README.md
|-- __init__.py
|-- model.py
|-- validation.py
|-- authoring.py
|-- grammar.py
|-- generation.py
|-- evolution.py
`-- export.py

app/contracts/strategy.py
app/services/persistence/strategy.py
tests/services/strategy/<feature>/
tests/examples/06_strategy.py
```

Each feature module is one cohesive physical removal unit. It contains typed configuration,
service behavior, lifecycle wiring, immutable `SPEC`, and a zero-argument factory. Registration
is explicit in `app/registry.py`; import-time discovery and ambient singletons are forbidden.
Cross-boundary DTOs, protocols, events, errors, and capability keys live in
`app/contracts/strategy.py`. Features resolve dependencies through `FeatureContext` and
never import sibling implementations.

All schema, parameterized SQL, and transactions for this domain live in
`app/services/persistence/strategy.py`. A feature may be stateless, but it never accepts an
unrestricted database connection. Every completed feature contributes a deterministic, offline,
secret-safe example to `tests/examples/06_strategy.py`.

---

## 1. Purpose and boundary

### Purpose

Own the canonical strategy definition, validation, visual-rule editing, block grammar, candidate generation/evolution, lineage, and offline target export.

### Owns

- Typed event-rule-condition-action model, parameters, variables, data bindings, and immutable revisions.
- Grammar constraints, seeded generation, genetic operators, improvement scope, and candidate lineage.
- Restricted versioned export templates and target profiles.

### Does not own

- Fill simulation, authoritative result metrics, or broker submission.
- Indicator formulas or protective-policy calculations.

### Shared contracts


The public boundary is `app/contracts/strategy.py`; counterparty status never authorizes a private import.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Missing | `strategy.definitions@1` | `StrategyRepository` | `1` | Canonical strategy artifacts and revisions |
| Missing | `strategy.validation@1` | `StrategyValidator` | `1` | Schema, tree, parameter, and target validation |
| Missing | `strategy.authoring@1` | `StrategyAuthoring` | `1` | Atomic rule-tree editing and revision history |
| Missing | `strategy.grammar@1` | `GrammarService` | `1` | Allowed blocks, weights, limits, and distributions |
| Missing | `strategy.generation@1` | `StrategyGenerator` | `1` | Seeded candidate generation |
| Missing | `strategy.evolution@1` | `EvolutionService` | `1` | Typed genetic improvement and lineage |
| Missing | `strategy.export@1` | `StrategyExporter` | `1` | Validated deterministic source bundles |

### Persisted-state ownership


Semantic state remains feature-owned although database mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Missing | `strategy.v1` | `FEAT-STRATEGY-MODEL` and registry peers | `sqlite` | Explicit reference-safe policy | `strategy.definitions@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-STRATEGY-MODEL` | Canonical strategy artifacts and revisions | `app/services/strategy/model.py` | `strategy.definitions@1` | `persistence.artifacts@1` | Missing |
| `FEAT-STRATEGY-VALIDATION` | Schema, tree, parameter, and target validation | `app/services/strategy/validation.py` | `strategy.validation@1` | `indicator.extensions@1` | Missing |
| `FEAT-STRATEGY-AUTHORING` | Atomic rule-tree editing and revision history | `app/services/strategy/authoring.py` | `strategy.authoring@1` | `strategy.definitions@1` | Missing |
| `FEAT-STRATEGY-GRAMMAR` | Allowed blocks, weights, limits, and distributions | `app/services/strategy/grammar.py` | `strategy.grammar@1` | `indicator.extensions@1` | Missing |
| `FEAT-STRATEGY-GENERATION` | Seeded candidate generation | `app/services/strategy/generation.py` | `strategy.generation@1` | `strategy.grammar@1` | Missing |
| `FEAT-STRATEGY-EVOLUTION` | Typed genetic improvement and lineage | `app/services/strategy/evolution.py` | `strategy.evolution@1` | `strategy.generation@1` | Missing |
| `FEAT-STRATEGY-EXPORT` | Validated deterministic source bundles | `app/services/strategy/export.py` | `strategy.export@1` | `strategy.validation@1` | Missing |

Dependencies point to public contracts, never implementations. Removal withdraws only the named
capability; required consumers become attributed `BLOCKED`, optional operations return
unavailable, and retained state is not purged.

---

## 3. Domain workflows


### `WF-STRATEGY-GENERATE` — Generate and export a validated strategy

- **Lead owner:** `FEAT-STRATEGY-GENERATION`
- **Participants:** Grammar, validation, evaluator, artifact store, and optional exporter.
- **Input boundary:** Grammar/version, data bindings, architecture, constraints, budget, and named seed stream.
- **Output boundary:** Immutable candidates with lineage/rejection reasons and optional hashed export bundle.
- **Failure boundary:** Invalid trees fail with located diagnostics; exhausted budget is truthful; template faults publish nothing.
- **Acceptance:** `ATW-STRATEGY-GENERATE-001`

---

## 4. Feature specifications


This representative module card applies to every registry entry; algorithms and state semantics
are in Section 9.

### `model.py` — `FEAT-STRATEGY-MODEL`

> **Feature ID:** `FEAT-STRATEGY-MODEL`
> **Status:** `Missing`
> **Owner module:** `app/services/strategy/model.py`

#### Purpose

Provide canonical strategy artifacts and revisions without absorbing another registry entry's responsibility.

#### Capability declarations

- **Provides:** `strategy.definitions@1`
- **Requires:** `persistence.artifacts@1`
- **Optional / operation-gated:** absence returns typed unavailable; no silent substitution.

#### Configuration and limits

Each owner has a slotted immutable `<Feature>Config`; sample reference values are not defaults.

| Status | Setting | Type / unit | Default | Validation and failure |
| --- | --- | --- | --- | --- |
| Missing | `schema_version` | positive integer | `1` | Reject incompatibility |
| Missing | `operation_timeout_s` | finite seconds | operation-specific | Positive and bounded |
| Missing | `resource_limit` | positive integer | deployment-specific | Reject unbounded/nonpositive |

#### Runtime effects and cleanup

| Effect | Acquisition | Cleanup / failure behavior |
| --- | --- | --- |
| Capability | `FeatureContext.provide(...)` | Withdraw with scope |
| Managed effects | `FeatureContext` resource/task/subscription APIs | Reverse-order close; failed start unwinds |
| Durable mutation | Focused persistence protocol | Roll back; partial output remains unpublished |

#### Persistent state

- **Domain persistence module:** `app/services/persistence/strategy.py`
- **Namespace:** `strategy.v1`
- **Schema version:** `1` initially; forward migrations only
- **Retention and purge:** explicit and reference-safe; feature removal never purges state.

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Missing | `model.py` | Canonical strategy artifacts and revisions; config, service, lifecycle, immutable `SPEC`, factory | `StrategyRepository` |
| Missing | `validation.py` | Schema, tree, parameter, and target validation; config, service, lifecycle, immutable `SPEC`, factory | `StrategyValidator` |
| Missing | `authoring.py` | Atomic rule-tree editing and revision history; config, service, lifecycle, immutable `SPEC`, factory | `StrategyAuthoring` |
| Missing | `grammar.py` | Allowed blocks, weights, limits, and distributions; config, service, lifecycle, immutable `SPEC`, factory | `GrammarService` |
| Missing | `generation.py` | Seeded candidate generation; config, service, lifecycle, immutable `SPEC`, factory | `StrategyGenerator` |
| Missing | `evolution.py` | Typed genetic improvement and lineage; config, service, lifecycle, immutable `SPEC`, factory | `EvolutionService` |
| Missing | `export.py` | Validated deterministic source bundles; config, service, lifecycle, immutable `SPEC`, factory | `StrategyExporter` |
| Missing | `tests/examples/06_strategy.py` | Offline evidence | one `example_<NN>_<feature_slug>()` per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Missing | `FR-STRATEGY-001` | Canonical serialize/parse round-trips with stable content identity. | Golden fixtures |
| Missing | `FR-STRATEGY-002` | Identical grammar/config/seed/evaluator results reproduce candidates and lineage. | Determinism test |
| Missing | `FR-STRATEGY-003` | Genetic operators preserve types, bounds, limits, and lineage. | Property tests |
| Missing | `FR-STRATEGY-004` | Export is offline, deterministic, path-contained, and manifest-backed. | Golden/security tests |

#### Removal behavior

Withdraw capability and managed effects; retain schema-readable artifacts. Dependent operations
return attributed unavailable. Reinstall requires schema/version compatibility.

---

## 5. Domain-wide requirements and invariants

| Status | Requirement ID | Rule | Verification |
| --- | --- | --- | --- |
| Missing | `ARCH-001` | `__init__.py` is docstring-only. | `scripts/architecture_check.py` |
| Missing | `ARCH-002` | Tasks and resources are managed through `FeatureContext`. | Lifecycle tests |
| Missing | `ARCH-003` | Logging uses `app.kernel.logging`; no service configures handlers. | Architecture/logging tests |
| Missing | `ARCH-004` | Public contracts live in `app/contracts/strategy.py`. | Import/contract checks |
| Missing | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Missing | `ARCH-006` | SQL/schema operations live in `app/services/persistence/strategy.py`. | Architecture/schema checks |

---

## 6. Decisions and open evidence


| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-STRATEGY-001` | Canonical definitions are typed data, never executable source strings. | Model | E-O02/E-L02 |
| Open | `DEC-STRATEGY-002` | All proprietary node semantics, distributions, and archive compatibility are unverified. | Parity | Independent fixtures |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; filenames and bundled
sample values are not proof of runtime semantics.

---

## 7. Tests and definition of done

```text
tests/services/strategy/<feature>/
|-- test_config.py
|-- test_<feature>.py
|-- test_lifecycle.py
|-- test_removal.py
`-- test_persistence.py       # when applicable

tests/examples/06_strategy.py
```

Editing uses explicit affected paths with `--no-cov`; the full candidate gate remains
`uv run python scripts/ci_check.py`.

- [ ] Stable feature and requirement IDs have one owner.
- [ ] Public contracts and exact `FeatureSpec` dependencies exist.
- [ ] Registration is explicit; imports have no runtime effects.
- [ ] Happy, invalid, boundary, unavailable, lifecycle, persistence, and removal tests pass.
- [ ] Numerical or stateful behavior has deterministic golden/fault fixtures.
- [ ] One offline usage example exists per completed feature.
- [ ] Domain status reflects repository evidence, not reference-product evidence.
- [ ] Architecture and full qualification gates pass.

---

## 8. Change process

1. Update this README and identify the exact feature/requirement scope.
2. Update `app/contracts/strategy.py` first when the public boundary changes.
3. Implement one cohesive owner module and immutable `SPEC`.
4. Change `app/services/persistence/strategy.py` only for database mechanics.
5. Update explicit registry, consolidated examples, and focused tests.
6. Verify feature removal and affected consumers.
7. Run the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

The model includes schema/version, identity, directions, markets/data bindings, parameters, variables, money-management reference, global protection, ordered event handlers/rules/actions, metadata, and lineage. Local XML shows initialization/bar-update/deinitialization and structured action parameters (E-L02), but vendor syntax is not copied. Validation covers IDs, types, bounds/dependencies, event legality, protection, target support, cycles/depth/count, and data. Generation uses named seed streams. Evolution versions selection, crossover, mutation, elitism, islands, migration, duplicate policy, budget, and stop rules (E-O06). Restricted exports have no file/network/process authority and record strategy/template/profile hashes (E-O02).
