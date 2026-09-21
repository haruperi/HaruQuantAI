# [Product Name] Project Specification

> **Status:** `[Draft | Ratified | Implementing | Operational]`
> **Architecture version:** `[version]`
> **Last verified revision:** `[commit SHA]`

This template owns system scope, component topology, cross-component workflows,
shared contracts, global requirements, and acceptance. Concrete plugin behavior
belongs in its single plugin file; do not duplicate executable plugin schemas here.

## 1. Product goal and boundaries

### Outcome

[Describe the user/business outcome and why the system exists.]

### In scope

- [Capability or workflow]

### Out of scope

- [Explicit non-goal]

### Users and operating environment

[Users, local/remote deployment, trust boundary, supported platforms.]

## 2. Spatial Composability laws

Record how this project applies each mandatory law:

| Law | Project interpretation | Acceptance evidence |
|---|---|---|
| Locality of Behavior | [One plugin file owns one concept] | [Static/audit test] |
| Orthogonality | [Permitted and forbidden effects] | [Add/remove test] |
| Explicit Typed Interfaces | [Capability and port model] | [Typing/runtime validation] |
| Algebraic Composition | [Shared tree/document] | [Consumer parity test] |
| Schema-Driven Self-Description | [Catalog and renderer vocabulary] | [No-source-edit test] |

## 3. System topology

```text
[Processes, packages, and trust boundaries]
```

| Component | Responsibility | Owns state/effects | Public boundary | Status |
|---|---|---|---|---|
| Kernel | [Business-neutral primitives] | [None] | [Modules] | [Status] |
| Host | [Lifecycle/discovery/execution] | [State/effects] | [Capabilities] | [Status] |
| Plugin catalog | [Validated descriptions] | [Snapshot] | [Schema] | [Status] |
| UI | [Presentation/view state] | [UI-only] | [Gateway DTOs] | [Status] |

Rules:

- Every responsibility and durable state has one owner.
- Host infrastructure is not modeled as a quantitative plugin.
- UI and plugins do not import host implementations.
- Arrows in diagrams represent public capability/document consumption, not
  private source imports.

## 4. Capability slots

| Capability ID@major | Protocol/value type | Provider owner | Consumers | Required/optional semantics |
|---|---|---|---|---|
| `[id]@1` | `[type]` | `[owner]` | `[consumers]` | `[behavior]` |

Document failure, compatibility, lifecycle, authorization, and effect semantics.
Do not list concrete plugin-specific parameter contracts here.

## 5. Plugin families and catalog

| Plugin kind | Purpose | Owning package README | Algebra role | Enablement policy | Status |
|---|---|---|---|---|---|
| `[kind]` | `[purpose]` | `[path]` | `[node/leaf/task/etc.]` | `[default]` | `[status]` |

Define:

- discovery roots and deterministic ordering;
- stable ID/version grammar;
- duplicate and incompatible plugin behavior;
- available/enabled/unavailable states;
- catalog snapshot schema and fingerprint;
- removal and unresolved-document behavior.

## 6. Algebraic documents

### Document types

| Document | Root type | Node/port system | Schema version | Consumers |
|---|---|---|---|---|
| `[Strategy]` | `[root]` | `[types]` | `[version]` | `[UI/simulator/exporter]` |

### Invariants

- Stable node identity and plugin ID/version reference.
- Canonical parameter encoding and deterministic ordering.
- Static port/type validation before execution.
- Unknown nodes are preserved losslessly and marked unavailable.
- Migrations are explicit, versioned, and tested.

## 7. Schema-driven UI

List the closed generic renderer vocabulary:

| Renderer/control | Supported schema | Accessibility/validation | Security boundary |
|---|---|---|---|
| `[number]` | `[constraints]` | `[behavior]` | `[limits]` |

State which backend additions require no UI source edit and which genuinely novel
interactions require a reviewed renderer or UI extension.

## 8. State, persistence, and artifacts

| State/artifact | Owner | Identity/schema | Writers | Readers | Retention/lineage |
|---|---|---|---|---|---|
| `[item]` | `[owner]` | `[version]` | `[writer]` | `[reader]` | `[policy]` |

Include transactions, migrations, concurrency, integrity, recovery, encryption,
backup, and database-test isolation. Plugins never perform ad-hoc persistence.

## 9. Cross-component workflows

### `[WF-ID] [Workflow name]`

1. [Actor/component and action]
2. [Typed capability/document handoff]
3. [Result/artifact]

**Failure and recovery:** [fail-closed behavior, retry/idempotency, cleanup]

**Acceptance:** [integration test and observable result]

## 10. Configuration, limits, and authorization

| Key/policy | Type | Default | Bounds | Owner | Security/scope |
|---|---|---|---|---|---|
| `[key]` | `[type]` | `[value]` | `[bounds]` | `[owner]` | `[policy]` |

## 11. Non-functional requirements

| ID | Requirement | Measurable acceptance | Evidence |
|---|---|---|---|
| `SYS-NFR-001` | Determinism | [criterion] | [test] |
| `SYS-NFR-002` | Orthogonal removal | [criterion] | [test] |
| `SYS-NFR-003` | Bounded resources | [criterion] | [test] |
| `SYS-NFR-004` | Security/privacy | [criterion] | [test] |
| `SYS-NFR-005` | Accessibility | [criterion] | [test] |

## 12. Verification strategy

- Unit/golden/property/equivalence tests.
- Plugin discovery, schema, enablement, and removal tests.
- Algebra migration and consumer parity tests.
- Host lifecycle and failure-isolation tests.
- UI typecheck, unit, accessibility, and bounded E2E tests.
- Architecture, lint, format, strict typing, coverage, and secret detection.

## 13. Open decisions and risks

| Status | Decision/risk | Options/evidence needed | Owner |
|---|---|---|---|
| Open | `[decision]` | `[options]` | `[owner]` |

## 14. Change protocol

1. Update the owning authority before or with behavior changes.
2. Plan the smallest complete change and identify compatibility impact.
3. Obtain owner approval.
4. Change universal contracts before consumers, then one cohesive plugin/host unit.
5. Verify focused behavior, cross-consumer parity, and full qualification.
6. Record walkthrough and obtain commit authorization.
