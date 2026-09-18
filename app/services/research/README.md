# Research

> **Package:** `app/services/research/`
> **Status:** `Missing`
> **Last updated:** `2026-09-18`
> **Domain ID:** `D-RESEARCH`

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
app/services/research/
|-- README.md
|-- __init__.py
|-- projects.py
|-- tasks.py
|-- routing.py
|-- runs.py
`-- automation.py

app/contracts/research.py
app/services/persistence/research.py
tests/services/research/<feature>/
tests/examples/14_research.py
```

Each feature module is one cohesive physical removal unit. It contains typed configuration,
service behavior, lifecycle wiring, immutable `SPEC`, and a zero-argument factory. Registration
is explicit in `app/registry.py`; import-time discovery and ambient singletons are forbidden.
Cross-boundary DTOs, protocols, events, errors, and capability keys live in
`app/contracts/research.py`. Features resolve dependencies through `FeatureContext` and
never import sibling implementations.

All schema, parameterized SQL, and transactions for this domain live in
`app/services/persistence/research.py`. A feature may be stateless, but it never accepts an
unrestricted database connection. Every completed feature contributes a deterministic, offline,
secret-safe example to `tests/examples/14_research.py`.

---

## 1. Purpose and boundary

### Purpose

Own versioned custom-project task graphs, task definitions, conditional routing, loops/waits, run evidence, automation, checkpoints, and reproducible orchestration.

### Owns

- Project/task graph definitions, validation, revisions, enabled order, and typed edges.
- Task adapters for build/retest/optimize/filter/portfolio/data/files/notify/control operations.
- Run/task-attempt transitions, routing evaluations, artifact handoffs, and recovery checkpoints.

### Does not own

- Job process mechanics, domain algorithm internals, or gateway transport.
- Implicit external/live authority from a task graph.

### Shared contracts


The public boundary is `app/contracts/research.py`; private implementation imports are forbidden.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Missing | `research.projects@1` | `ResearchProjectRepository` | `1` | Versioned project/task graphs |
| Missing | `research.tasks@1` | `TaskRegistry` | `1` | Typed task definitions and adapters |
| Missing | `research.routing@1` | `RoutingService` | `1` | Conditions, jumps, waits, loops, and stop/start |
| Missing | `research.runs@1` | `ResearchRunService` | `1` | Durable project execution and artifact flow |
| Missing | `research.automation@1` | `ResearchAutomation` | `1` | Bounded schedules and notifications |

### Persisted-state ownership


Semantic state remains feature-owned although storage mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Missing | `research.v1` | `FEAT-RESEARCH-PROJECTS` and registry peers | `sqlite` | Explicit reference-safe policy | `research.projects@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-RESEARCH-PROJECTS` | Versioned project/task graphs | `app/services/research/projects.py` | `research.projects@1` | `persistence.artifacts@1` | Missing |
| `FEAT-RESEARCH-TASKS` | Typed task definitions and adapters | `app/services/research/tasks.py` | `research.tasks@1` | `workspace.jobs@1` | Missing |
| `FEAT-RESEARCH-ROUTING` | Conditions, jumps, waits, loops, and stop/start | `app/services/research/routing.py` | `research.routing@1` | `analytics.metrics@1` | Missing |
| `FEAT-RESEARCH-RUNS` | Durable project execution and artifact flow | `app/services/research/runs.py` | `research.runs@1` | `research.projects@1`, `workspace.jobs@1` | Missing |
| `FEAT-RESEARCH-AUTOMATION` | Bounded schedules and notifications | `app/services/research/automation.py` | `research.automation@1` | `workspace.scheduler@1` | Missing |

Dependencies use versioned public contracts. Removing a contribution withdraws only its capability;
required consumers become attributed `BLOCKED`, optional operations return unavailable, and
retained state is not purged.

---

## 3. Domain workflows


### `WF-RESEARCH-RUN` — Execute and recover a custom research project

- **Lead owner:** `FEAT-RESEARCH-RUNS`
- **Participants:** Project graph, task registry, routing, workspace jobs, domain capabilities, and artifacts.
- **Input boundary:** Frozen project revision, parameters, inputs, code/config versions, run limits, and approval context.
- **Output boundary:** Ordered task-attempt evidence, evaluated routes, artifact lineage, checkpoints, and terminal run state.
- **Failure boundary:** Invalid graph blocks start; task failure follows explicit edge policy; resume uses safe checkpoint or new attempt.
- **Acceptance:** `ATW-RESEARCH-RUN-001`

---

## 4. Feature specifications


This representative card applies to every registry entry; exact algorithms and states are in Section 9.

### `projects.py` — `FEAT-RESEARCH-PROJECTS`

> **Feature ID:** `FEAT-RESEARCH-PROJECTS`
> **Status:** `Missing`
> **Owner module:** `app/services/research/projects.py`

#### Purpose

Provide versioned project/task graphs without absorbing another feature's responsibility.

#### Capability declarations

- **Provides:** `research.projects@1`
- **Requires:** `persistence.artifacts@1`
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

- **Domain persistence module:** `app/services/persistence/research.py`
- **Namespace:** `research.v1`
- **Schema version:** `1` initially; forward migration only
- **Retention and purge:** explicit and reference-safe; removal never implicitly purges.

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Missing | `projects.py` | Versioned project/task graphs; configuration, service, lifecycle, immutable specification, factory/contribution | `ResearchProjectRepository` |
| Missing | `tasks.py` | Typed task definitions and adapters; configuration, service, lifecycle, immutable specification, factory/contribution | `TaskRegistry` |
| Missing | `routing.py` | Conditions, jumps, waits, loops, and stop/start; configuration, service, lifecycle, immutable specification, factory/contribution | `RoutingService` |
| Missing | `runs.py` | Durable project execution and artifact flow; configuration, service, lifecycle, immutable specification, factory/contribution | `ResearchRunService` |
| Missing | `automation.py` | Bounded schedules and notifications; configuration, service, lifecycle, immutable specification, factory/contribution | `ResearchAutomation` |
| Missing | `tests/examples/14_research.py` | Offline primary-purpose evidence | one named scenario per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Missing | `FR-RESEARCH-001` | Graph validation rejects missing capabilities, invalid edges, unsafe cycles, and unbounded loops. | Graph property tests |
| Missing | `FR-RESEARCH-002` | Every route stores expression version, input metric identities, result, and chosen edge. | Routing golden |
| Missing | `FR-RESEARCH-003` | Artifact handoffs are immutable and type/schema checked. | Contract tests |
| Missing | `FR-RESEARCH-004` | Restart/resume never reruns an externally effectful task without idempotency proof. | Fault test |

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
| Missing | `ARCH-004` | Public contracts live in `app/contracts/research.py`. | Import/contract checks |
| Missing | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Missing | `ARCH-006` | SQL/schema operations live in `app/services/persistence/research.py`. | Architecture/schema checks |

---

## 6. Decisions and open evidence


| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-RESEARCH-001` | Research orchestrates public capabilities and never imports domain implementations. | Boundary | Architecture |
| Open | `DEC-RESEARCH-002` | Exact reference conditional expression language and wait behavior are unverified. | Parity | Safe black-box fixtures |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; installed names and
sample values are not runtime proof.

---

## 7. Tests and definition of done

```text
tests/services/research/<feature>/
|-- test_config.py
|-- test_<feature>.py
|-- test_lifecycle.py
|-- test_removal.py
`-- test_persistence.py       # when applicable

tests/examples/14_research.py
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
2. Update `app/contracts/research.py` first when the public boundary changes.
3. Implement one cohesive owner module and immutable `SPEC`.
4. Change `app/services/persistence/research.py` only for database mechanics.
5. Update explicit registry, consolidated examples, and focused tests.
6. Verify feature removal and affected consumers.
7. Run the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

A project is a versioned directed graph; nodes have stable ID/type/config/enabled state/input-output ports/failure policy, and edges may carry typed conditions. Exact-version task XML shows Build, Retest, Optimize, Automatic Retest/Portfolio, Filter, Clear, Create Portfolio, Load/Save, Go To, Wait, Stop/Start, Notification and Update Data shapes (E-L03); these are structural evidence, not defaults. Conditions reference a versioned expression subset and immutable metric/artifact inputs—no eval. Loops require iteration/time budgets. Each transition records evaluated input and edge. File/notification/data/live effects retain their own domain approvals; a graph cannot grant authority.
