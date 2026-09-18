# Simulator

> **Package:** `app/services/simulator/`
> **Status:** `Missing`
> **Last updated:** `2026-09-18`
> **Domain ID:** `D-SIMULATOR`

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
app/services/simulator/
|-- README.md
|-- __init__.py
|-- engine.py
|-- precision.py
|-- matching.py
|-- costs.py
`-- account.py

app/contracts/simulator.py
app/services/persistence/simulator.py
tests/services/simulator/<feature>/
tests/examples/10_simulator.py
```

Each feature module is one cohesive physical removal unit. It contains typed configuration,
service behavior, lifecycle wiring, immutable `SPEC`, and a zero-argument factory. Registration
is explicit in `app/registry.py`; import-time discovery and ambient singletons are forbidden.
Cross-boundary DTOs, protocols, events, errors, and capability keys live in
`app/contracts/simulator.py`. Features resolve dependencies through `FeatureContext` and
never import sibling implementations.

All schema, parameterized SQL, and transactions for this domain live in
`app/services/persistence/simulator.py`. A feature may be stateless, but it never accepts an
unrestricted database connection. Every completed feature contributes a deterministic, offline,
secret-safe example to `tests/examples/10_simulator.py`.

---

## 1. Purpose and boundary

### Purpose

Own deterministic historical event sequencing, strategy callbacks, matching/fills, costs, account/margin state, and reproducible backtest artifacts.

### Owns

- Precision profiles and total market-event ordering.
- Pending/market/protective matching, fills, gaps, ambiguity policy, and costs.
- Simulated account, equity/margin, orders/positions, and ledgers.

### Does not own

- Data acquisition, strategy definition, risk calculation, or metrics.
- Live sessions or optimization scheduling.

### Shared contracts


The public boundary is `app/contracts/simulator.py`; counterparty status never authorizes a private import.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Missing | `simulator.backtest@1` | `BacktestEngine` | `1` | Deterministic backtest orchestration |
| Missing | `simulator.precision@1` | `PrecisionService` | `1` | Bar, minute, and tick event construction |
| Missing | `simulator.matching@1` | `MatchingEngine` | `1` | Orders, fills, gaps, and ambiguity |
| Missing | `simulator.costs@1` | `CostModel` | `1` | Spread, slippage, commission, swap, conversion |
| Missing | `simulator.account@1` | `SimulatedAccount` | `1` | Balance, equity, margin, positions, liquidation |

### Persisted-state ownership


Semantic state remains feature-owned although database mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Missing | `simulator.v1` | `FEAT-SIMULATOR-ENGINE` and registry peers | `sqlite` | Explicit reference-safe policy | `simulator.backtest@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-SIMULATOR-ENGINE` | Deterministic backtest orchestration | `app/services/simulator/engine.py` | `simulator.backtest@1` | `data.datasets@1`, `strategy.definitions@1` | Missing |
| `FEAT-SIMULATOR-PRECISION` | Bar, minute, and tick event construction | `app/services/simulator/precision.py` | `simulator.precision@1` | `data.datasets@1` | Missing |
| `FEAT-SIMULATOR-MATCHING` | Orders, fills, gaps, and ambiguity | `app/services/simulator/matching.py` | `simulator.matching@1` | `trading.execution_intents@1` | Missing |
| `FEAT-SIMULATOR-COSTS` | Spread, slippage, commission, swap, conversion | `app/services/simulator/costs.py` | `simulator.costs@1` | `data.instruments@1` | Missing |
| `FEAT-SIMULATOR-ACCOUNT` | Balance, equity, margin, positions, liquidation | `app/services/simulator/account.py` | `simulator.account@1` | `trading.positions@1` | Missing |

Dependencies point to public contracts, never implementations. Removal withdraws only the named
capability; required consumers become attributed `BLOCKED`, optional operations return
unavailable, and retained state is not purged.

---

## 3. Domain workflows


### `WF-SIMULATOR-BACKTEST` — Execute a reproducible historical simulation

- **Lead owner:** `FEAT-SIMULATOR-ENGINE`
- **Participants:** Data, strategy, indicator, risk, trading, matching, costs, account, artifacts.
- **Input boundary:** Frozen strategy/data/config/code, sample, precision, costs, account, limits, seed.
- **Output boundary:** Event/trade/order ledger, equity/account series, diagnostics, assumption manifest.
- **Failure boundary:** Invalid input fails before run; cancellation is staged partial evidence; invariant breach fails.
- **Acceptance:** `ATW-SIMULATOR-BACKTEST-001`

---

## 4. Feature specifications


This representative module card applies to every registry entry; algorithms and state semantics
are in Section 9.

### `engine.py` — `FEAT-SIMULATOR-ENGINE`

> **Feature ID:** `FEAT-SIMULATOR-ENGINE`
> **Status:** `Missing`
> **Owner module:** `app/services/simulator/engine.py`

#### Purpose

Provide deterministic backtest orchestration without absorbing another registry entry's responsibility.

#### Capability declarations

- **Provides:** `simulator.backtest@1`
- **Requires:** `data.datasets@1`, `strategy.definitions@1`
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

- **Domain persistence module:** `app/services/persistence/simulator.py`
- **Namespace:** `simulator.v1`
- **Schema version:** `1` initially; forward migrations only
- **Retention and purge:** explicit and reference-safe; feature removal never purges state.

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Missing | `engine.py` | Deterministic backtest orchestration; config, service, lifecycle, immutable `SPEC`, factory | `BacktestEngine` |
| Missing | `precision.py` | Bar, minute, and tick event construction; config, service, lifecycle, immutable `SPEC`, factory | `PrecisionService` |
| Missing | `matching.py` | Orders, fills, gaps, and ambiguity; config, service, lifecycle, immutable `SPEC`, factory | `MatchingEngine` |
| Missing | `costs.py` | Spread, slippage, commission, swap, conversion; config, service, lifecycle, immutable `SPEC`, factory | `CostModel` |
| Missing | `account.py` | Balance, equity, margin, positions, liquidation; config, service, lifecycle, immutable `SPEC`, factory | `SimulatedAccount` |
| Missing | `tests/examples/10_simulator.py` | Offline evidence | one `example_<NN>_<feature_slug>()` per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Missing | `FR-SIMULATOR-001` | Frozen inputs reproduce event, fill, ledger, and account identities. | Golden backtest |
| Missing | `FR-SIMULATOR-002` | Ties use a total order independent of map/thread/filesystem order. | Permutation test |
| Missing | `FR-SIMULATOR-003` | Visibility rules prevent same/future-event look-ahead. | Adversarial test |
| Missing | `FR-SIMULATOR-004` | Costs, rounding, margin, and accounts reconcile per event. | Accounting test |

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
| Missing | `ARCH-004` | Public contracts live in `app/contracts/simulator.py`. | Import/contract checks |
| Missing | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Missing | `ARCH-006` | SQL/schema operations live in `app/services/persistence/simulator.py`. | Architecture/schema checks |

---

## 6. Decisions and open evidence


| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-SIMULATOR-001` | Precision/cost/ambiguity are explicit input and result metadata. | Reproducibility | E-O03 |
| Open | `DEC-SIMULATOR-002` | Exact OHLC traversal, same-bar, multi-symbol ties, and gaps are unverified. | Parity | Minimal black-box fixtures |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; filenames and bundled
sample values are not proof of runtime semantics.

---

## 7. Tests and definition of done

```text
tests/services/simulator/<feature>/
|-- test_config.py
|-- test_<feature>.py
|-- test_lifecycle.py
|-- test_removal.py
`-- test_persistence.py       # when applicable

tests/examples/10_simulator.py
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
2. Update `app/contracts/simulator.py` first when the public boundary changes.
3. Implement one cohesive owner module and immutable `SPEC`.
4. Change `app/services/persistence/simulator.py` only for database mechanics.
5. Update explicit registry, consolidated examples, and focused tests.
6. Verify feature removal and affected consumers.
7. Run the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

Reference modes expose four synthetic events per selected bar, four per minute, recorded bid plus configured-spread ask, or recorded bid/ask (E-O03). The target versions a total order across timestamp, symbol, market update, pending activation, protective exit, callback, submission, fill, account update, and snapshot. Until measured, a profile states its policy and does not claim parity. Spread, slippage, commission, swap, minimum distance, volume step, margin, conversion, gap and same-event ambiguity are frozen inputs. Closed-bar calculations see only available history. Parallelism may split trials but never reorder one simulation.
