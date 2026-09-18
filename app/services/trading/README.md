# Trading

> **Package:** `app/services/trading/`
> **Status:** `Missing`
> **Last updated:** `2026-09-18`
> **Domain ID:** `D-TRADING`

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
app/services/trading/
|-- README.md
|-- __init__.py
|-- sessions.py
|-- orders.py
|-- positions.py
|-- reconciliation.py
`-- ledger.py

app/contracts/trading.py
app/services/persistence/trading.py
tests/services/trading/<feature>/
tests/examples/09_trading.py
```

Each feature module is one cohesive physical removal unit. It contains typed configuration,
service behavior, lifecycle wiring, immutable `SPEC`, and a zero-argument factory. Registration
is explicit in `app/registry.py`; import-time discovery and ambient singletons are forbidden.
Cross-boundary DTOs, protocols, events, errors, and capability keys live in
`app/contracts/trading.py`. Features resolve dependencies through `FeatureContext` and
never import sibling implementations.

All schema, parameterized SQL, and transactions for this domain live in
`app/services/persistence/trading.py`. A feature may be stateless, but it never accepts an
unrestricted database connection. Every completed feature contributes a deterministic, offline,
secret-safe example to `tests/examples/09_trading.py`.

---

## 1. Purpose and boundary

### Purpose

Own normalized execution sessions, order and position state machines, authorization context, idempotent dispatch, reconciliation semantics, and immutable execution ledgers across simulation, demo, and live modes.

### Owns

- Normalized order, fill, position, account, and session DTOs/transitions.
- Idempotent intent lifecycle, authorization context, reconciliation, and audit events.
- Mode separation preventing simulation/demo/live conflation.

### Does not own

- Physical broker connectivity or SDK translation.
- Strategy decisions, risk calculation, or simulator matching.

### Shared contracts


The public boundary is `app/contracts/trading.py`; counterparty status never authorizes a private import.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Missing | `trading.sessions@1` | `ExecutionSessionService` | `1` | Mode/account session lifecycle |
| Missing | `trading.execution_intents@1` | `OrderService` | `1` | Validated idempotent order intents |
| Missing | `trading.positions@1` | `PositionService` | `1` | Position and fill-derived state |
| Missing | `trading.reconciliation@1` | `ReconciliationService` | `1` | External/local state convergence |
| Missing | `trading.ledger@1` | `ExecutionLedger` | `1` | Immutable execution audit records |

### Persisted-state ownership


Semantic state remains feature-owned although database mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Missing | `trading.v1` | `FEAT-TRADING-SESSIONS` and registry peers | `sqlite` | Explicit reference-safe policy | `trading.sessions@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-TRADING-SESSIONS` | Mode/account session lifecycle | `app/services/trading/sessions.py` | `trading.sessions@1` | `workspace.settings@1` | Missing |
| `FEAT-TRADING-ORDERS` | Validated idempotent order intents | `app/services/trading/orders.py` | `trading.execution_intents@1` | `risk.pretrade_limits@1` | Missing |
| `FEAT-TRADING-POSITIONS` | Position and fill-derived state | `app/services/trading/positions.py` | `trading.positions@1` | `trading.execution_intents@1` | Missing |
| `FEAT-TRADING-RECONCILIATION` | External/local state convergence | `app/services/trading/reconciliation.py` | `trading.reconciliation@1` | `trading.positions@1` | Missing |
| `FEAT-TRADING-LEDGER` | Immutable execution audit records | `app/services/trading/ledger.py` | `trading.ledger@1` | `persistence.artifacts@1` | Missing |

Dependencies point to public contracts, never implementations. Removal withdraws only the named
capability; required consumers become attributed `BLOCKED`, optional operations return
unavailable, and retained state is not purged.

---

## 3. Domain workflows


### `WF-TRADING-INTENT` — Authorize, dispatch, and reconcile an order intent

- **Lead owner:** `FEAT-TRADING-ORDERS`
- **Participants:** Risk, session, simulator/broker adapter, positions, ledger, reconciler.
- **Input boundary:** Intent ID, mode/account, instrument, side/type/quantity/prices, time policy, run, approval.
- **Output boundary:** Ordered transitions, acknowledgements/fills, reconciled state, and ledger identity.
- **Failure boundary:** Invalid/unauthorized rejects before send; post-send timeout is unknown; duplicates return prior state.
- **Acceptance:** `ATW-TRADING-INTENT-001`

---

## 4. Feature specifications


This representative module card applies to every registry entry; algorithms and state semantics
are in Section 9.

### `sessions.py` — `FEAT-TRADING-SESSIONS`

> **Feature ID:** `FEAT-TRADING-SESSIONS`
> **Status:** `Missing`
> **Owner module:** `app/services/trading/sessions.py`

#### Purpose

Provide mode/account session lifecycle without absorbing another registry entry's responsibility.

#### Capability declarations

- **Provides:** `trading.sessions@1`
- **Requires:** `workspace.settings@1`
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

- **Domain persistence module:** `app/services/persistence/trading.py`
- **Namespace:** `trading.v1`
- **Schema version:** `1` initially; forward migrations only
- **Retention and purge:** explicit and reference-safe; feature removal never purges state.

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Missing | `sessions.py` | Mode/account session lifecycle; config, service, lifecycle, immutable `SPEC`, factory | `ExecutionSessionService` |
| Missing | `orders.py` | Validated idempotent order intents; config, service, lifecycle, immutable `SPEC`, factory | `OrderService` |
| Missing | `positions.py` | Position and fill-derived state; config, service, lifecycle, immutable `SPEC`, factory | `PositionService` |
| Missing | `reconciliation.py` | External/local state convergence; config, service, lifecycle, immutable `SPEC`, factory | `ReconciliationService` |
| Missing | `ledger.py` | Immutable execution audit records; config, service, lifecycle, immutable `SPEC`, factory | `ExecutionLedger` |
| Missing | `tests/examples/09_trading.py` | Offline evidence | one `example_<NN>_<feature_slug>()` per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Missing | `FR-TRADING-001` | Order/position transitions are exhaustive and version-checked. | State tables |
| Missing | `FR-TRADING-002` | Intent idempotency prevents duplicate effects across retry/restart. | Fault test |
| Missing | `FR-TRADING-003` | Simulation, demo, and live identities cannot mix or relabel. | Isolation tests |
| Missing | `FR-TRADING-004` | Live commands require enabled profile, authorization, limits, and audit. | Negative test |

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
| Missing | `ARCH-004` | Public contracts live in `app/contracts/trading.py`. | Import/contract checks |
| Missing | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Missing | `ARCH-006` | SQL/schema operations live in `app/services/persistence/trading.py`. | Architecture/schema checks |

---

## 6. Decisions and open evidence


| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-TRADING-001` | Live is disabled by default and separately governed. | Safety | SYS-013 |
| Open | `DEC-TRADING-002` | Provider partial-fill/cancel-replace mapping remains adapter evidence. | Mapping | Sandbox matrices |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; filenames and bundled
sample values are not proof of runtime semantics.

---

## 7. Tests and definition of done

```text
tests/services/trading/<feature>/
|-- test_config.py
|-- test_<feature>.py
|-- test_lifecycle.py
|-- test_removal.py
`-- test_persistence.py       # when applicable

tests/examples/09_trading.py
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
2. Update `app/contracts/trading.py` first when the public boundary changes.
3. Implement one cohesive owner module and immutable `SPEC`.
4. Change `app/services/persistence/trading.py` only for database mechanics.
5. Update explicit registry, consolidated examples, and focused tests.
6. Verify feature removal and affected consumers.
7. Run the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

Canonical order states are created/validated/submitted/acknowledged/partially_filled/filled/cancel_pending/cancelled/rejected/expired/unknown with versioned legal transitions. Events carry source and observed timestamps plus monotonic sequence. Positions derive from fills, never UI mutation. Each intent binds environment, account, instrument version, strategy/run, risk decision, and approval. Reconciliation records corrections without rewriting history. Disconnect never implies cancel/reject. Simulator implements the same public contracts without broker authority.
