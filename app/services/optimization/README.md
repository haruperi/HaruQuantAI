# Optimization

> **Package:** `app/services/optimization/`
> **Status:** `Missing`
> **Last updated:** `2026-09-18`
> **Domain ID:** `D-OPTIMIZATION`

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
app/services/optimization/
|-- README.md
|-- __init__.py
|-- parameter_spaces.py
|-- studies.py
|-- exhaustive.py
|-- genetic.py
|-- sequential.py
`-- walk_forward.py

app/contracts/optimization.py
app/services/persistence/optimization.py
tests/services/optimization/<feature>/
tests/examples/11_optimization.py
```

Each feature module is one cohesive physical removal unit. It contains typed configuration,
service behavior, lifecycle wiring, immutable `SPEC`, and a zero-argument factory. Registration
is explicit in `app/registry.py`; import-time discovery and ambient singletons are forbidden.
Cross-boundary DTOs, protocols, events, errors, and capability keys live in
`app/contracts/optimization.py`. Features resolve dependencies through `FeatureContext` and
never import sibling implementations.

All schema, parameterized SQL, and transactions for this domain live in
`app/services/persistence/optimization.py`. A feature may be stateless, but it never accepts an
unrestricted database connection. Every completed feature contributes a deterministic, offline,
secret-safe example to `tests/examples/11_optimization.py`.

---

## 1. Purpose and boundary

### Purpose

Own typed parameter spaces, deterministic trial schedules, exhaustive/random/genetic search, multi-objective scoring, sequential optimization, and walk-forward schedules.

### Owns

- Parameter/range/constraint validation and finite combination counting.
- Study/trial lifecycle, search algorithms, objectives, pruning, checkpoints, and artifacts.
- Explicit in-sample/out-of-sample window schedules and aggregation inputs.

### Does not own

- Backtest execution, metric formulas, robustness verdicts, or job process supervision.
- Strategy grammar semantics or portfolio combination search.

### Shared contracts


The public boundary is `app/contracts/optimization.py`; private implementation imports are forbidden.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Missing | `optimization.parameter_spaces@1` | `ParameterSpaceService` | `1` | Typed ranges, constraints, and schedules |
| Missing | `optimization.studies@1` | `StudyService` | `1` | Studies, trials, objectives, and artifacts |
| Missing | `optimization.exhaustive@1` | `ExhaustiveOptimizer` | `1` | Deterministic grid enumeration |
| Missing | `optimization.genetic@1` | `GeneticOptimizer` | `1` | Seeded population search |
| Missing | `optimization.sequential@1` | `SequentialOptimizer` | `1` | Ordered parameter-stage optimization |
| Missing | `optimization.walk_forward@1` | `WalkForwardScheduler` | `1` | Versioned IS/OOS schedules |

### Persisted-state ownership


Semantic state remains feature-owned although storage mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Missing | `optimization.v1` | `FEAT-OPTIMIZATION-SPACES` and registry peers | `sqlite` | Explicit reference-safe policy | `optimization.parameter_spaces@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-OPTIMIZATION-SPACES` | Typed ranges, constraints, and schedules | `app/services/optimization/parameter_spaces.py` | `optimization.parameter_spaces@1` | `strategy.definitions@1` | Missing |
| `FEAT-OPTIMIZATION-STUDIES` | Studies, trials, objectives, and artifacts | `app/services/optimization/studies.py` | `optimization.studies@1` | `workspace.jobs@1` | Missing |
| `FEAT-OPTIMIZATION-EXHAUSTIVE` | Deterministic grid enumeration | `app/services/optimization/exhaustive.py` | `optimization.exhaustive@1` | `simulator.backtest@1` | Missing |
| `FEAT-OPTIMIZATION-GENETIC` | Seeded population search | `app/services/optimization/genetic.py` | `optimization.genetic@1` | `simulator.backtest@1`, `analytics.metrics@1` | Missing |
| `FEAT-OPTIMIZATION-SEQUENTIAL` | Ordered parameter-stage optimization | `app/services/optimization/sequential.py` | `optimization.sequential@1` | `optimization.studies@1` | Missing |
| `FEAT-OPTIMIZATION-WINDOWS` | Versioned IS/OOS schedules | `app/services/optimization/walk_forward.py` | `optimization.walk_forward@1` | `data.datasets@1` | Missing |

Dependencies use versioned public contracts. Removing a contribution withdraws only its capability;
required consumers become attributed `BLOCKED`, optional operations return unavailable, and
retained state is not purged.

---

## 3. Domain workflows


### `WF-OPTIMIZATION-STUDY` — Plan and execute a reproducible parameter study

- **Lead owner:** `FEAT-OPTIMIZATION-STUDIES`
- **Participants:** Parameter space, simulator, metrics, workspace jobs, artifacts, and optional search algorithm.
- **Input boundary:** Strategy/data/config versions, ranges/constraints, algorithm/seed, objectives, budget, and windows.
- **Output boundary:** Materialized schedule, immutable trial records, best/Pareto selection, checkpoint, and manifest.
- **Failure boundary:** Invalid or nonfinite space fails before dispatch; failed/cancelled/pruned trials retain distinct states.
- **Acceptance:** `ATW-OPTIMIZATION-STUDY-001`

---

## 4. Feature specifications


This representative card applies to every registry entry; exact algorithms and states are in Section 9.

### `parameter_spaces.py` — `FEAT-OPTIMIZATION-SPACES`

> **Feature ID:** `FEAT-OPTIMIZATION-SPACES`
> **Status:** `Missing`
> **Owner module:** `app/services/optimization/parameter_spaces.py`

#### Purpose

Provide typed ranges, constraints, and schedules without absorbing another feature's responsibility.

#### Capability declarations

- **Provides:** `optimization.parameter_spaces@1`
- **Requires:** `strategy.definitions@1`
- **Optional / operation-gated:** absence is explicit; no silent substitution.

#### Configuration and limits

Configuration is immutable, typed, versioned, and bounded. Reference sample values are not defaults.

| Status | Setting | Type / unit | Default | Validation and failure |
| --- | --- | --- | --- | --- |
| Missing | `schema_version` | positive integer | `1` | Reject incompatible versions |
| Missing | `operation_timeout_s` | finite seconds | operation-specific | Positive and bounded |
| Missing | `resource_limit` | positive integer | deployment-specific | Reject unbounded/nonpositive |

#### Runtime effects and cleanup

| Effect | Acquisition | Cleanup / failure behavior |
| --- | --- | --- |
| Capability/contribution | Managed feature scope | Withdraw with scope |
| Task/subscription/resource | Managed lifecycle API | Reverse-order close; failed start unwinds |
| Durable mutation | Focused persistence/API protocol | Roll back; partial output remains unpublished |

#### Persistent state

- **Domain persistence module:** `app/services/persistence/optimization.py`
- **Namespace:** `optimization.v1`
- **Schema version:** `1` initially; forward migration only
- **Retention and purge:** explicit and reference-safe; removal never implicitly purges.

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Missing | `parameter_spaces.py` | Typed ranges, constraints, and schedules; configuration, service, lifecycle, immutable specification, factory/contribution | `ParameterSpaceService` |
| Missing | `studies.py` | Studies, trials, objectives, and artifacts; configuration, service, lifecycle, immutable specification, factory/contribution | `StudyService` |
| Missing | `exhaustive.py` | Deterministic grid enumeration; configuration, service, lifecycle, immutable specification, factory/contribution | `ExhaustiveOptimizer` |
| Missing | `genetic.py` | Seeded population search; configuration, service, lifecycle, immutable specification, factory/contribution | `GeneticOptimizer` |
| Missing | `sequential.py` | Ordered parameter-stage optimization; configuration, service, lifecycle, immutable specification, factory/contribution | `SequentialOptimizer` |
| Missing | `walk_forward.py` | Versioned IS/OOS schedules; configuration, service, lifecycle, immutable specification, factory/contribution | `WalkForwardScheduler` |
| Missing | `tests/examples/11_optimization.py` | Offline primary-purpose evidence | one named scenario per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Missing | `FR-OPTIMIZATION-001` | Typed steps and constraints yield deterministic finite schedules/counts. | Boundary/enumeration tests |
| Missing | `FR-OPTIMIZATION-002` | Identical study inputs and seeds reproduce trial order and selection. | Golden study |
| Missing | `FR-OPTIMIZATION-003` | Failed/cancelled/pruned trials never become objective winners. | Fault tests |
| Missing | `FR-OPTIMIZATION-004` | Walk-forward windows expose anchoring, overlap, warm-up, IS/OOS, and aggregation. | Window table tests |

#### Removal behavior

Withdraw the capability and managed effects while retaining schema-readable artifacts. Dependent
operations return attributed unavailable; reinstall requires schema/version compatibility.

---

## 5. Domain-wide requirements and invariants

| Status | Requirement ID | Rule | Verification |
| --- | --- | --- | --- |
| Missing | `ARCH-001` | `__init__.py` is docstring-only. | `scripts/architecture_check.py` |
| Missing | `ARCH-002` | Tasks and resources are managed through `FeatureContext`. | Lifecycle tests |
| Missing | `ARCH-003` | Logging uses `app.kernel.logging`; no service configures handlers. | Architecture/logging tests |
| Missing | `ARCH-004` | Public contracts live in `app/contracts/optimization.py`. | Import/contract checks |
| Missing | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Missing | `ARCH-006` | SQL/schema operations live in `app/services/persistence/optimization.py`. | Architecture/schema checks |

---

## 6. Decisions and open evidence


| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-OPTIMIZATION-001` | Worker processes isolate trials; SQLite ledger and artifacts preserve truth. | Runtime | E-T01 |
| Open | `DEC-OPTIMIZATION-002` | Reference mutation/selection distributions and sequential tie rules are unverified. | Parity | Seeded bounded fixtures |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; installed names and
sample values are not runtime proof.

---

## 7. Tests and definition of done

```text
tests/services/optimization/<feature>/
|-- test_config.py
|-- test_<feature>.py
|-- test_lifecycle.py
|-- test_removal.py
`-- test_persistence.py       # when applicable

tests/examples/11_optimization.py
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
2. Update `app/contracts/optimization.py` first when the public boundary changes.
3. Implement one cohesive owner module and immutable `SPEC`.
4. Change `app/services/persistence/optimization.py` only for database mechanics.
5. Update explicit registry, consolidated examples, and focused tests.
6. Verify feature removal and affected consumers.
7. Run the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

Ranges declare type, unit, inclusive/exclusive bounds, step or distribution, conditional activation, and constraint predicates. Decimal/integer schedules avoid float accumulation and reject empty/overflowing spaces. A study freezes algorithm/version, ordered objective definitions, ranking direction, constraints, budget, concurrency, seed streams, and evaluator inputs. Genetic options explicitly version population/generation, selection, crossover, mutation, elitism, islands and migration (E-O06); bundled task values are examples only (E-L03). Every trial is queued/running/succeeded/failed/cancelled/pruned with parameters and source result identity. Sequential stages declare parameter order and carry-forward rule. Walk-forward schedules declare anchored/rolling windows, lengths, step, warm-up, overlap, incomplete-window policy, and OOS aggregation.
