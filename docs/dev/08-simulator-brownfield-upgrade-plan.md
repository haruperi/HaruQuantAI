# Phase 08 Simulator Engine — Brownfield Upgrade and Migration Plan

**Target module:** `app/services/simulator/`  
**Current planning file:** `docs/dev/phase-implementation-plan/08-simulator.md`  
**Plan type:** Full brownfield upgrade plan with requirement coverage matrix  
**Status:** Builder-ready migration plan; not a greenfield replacement plan.

## 0. Brownfield Objective

The Simulator is a deterministic integration and replay engine. It owns simulation orchestration, event replay, simulated state, matching decisions, accounting replay, journals, artifacts, and run lifecycle. It must reuse deterministic feature modules from existing services instead of re-implementing their business rules.

This plan replaces the previous standalone simulator design with a brownfield migration path that preserves the current implementation and upgrades it incrementally.

The current implementation is not deleted. It becomes the first supported execution backend and characterization baseline while the production-realistic integration engine is introduced around it.

## 1. Repository Baseline Audit

### 1.1 Current simulator files inspected

Current implementation baseline:

```text
app/services/simulator/
├── __init__.py
├── engine.py
└── models.py

tests/usage/
└── 08_simulator.py
```

Direct checks found no `app/services/simulator/README.md`. Direct probes for common `tests/services/simulator/*` filenames did not find a dedicated simulator unit-test package, so the first migration task is to add deterministic characterization tests for the current baseline.

### 1.2 Current public exports

`app/services/simulator/__init__.py` currently exports:

```text
BacktestConfig
BacktestEvent
BacktestMetrics
BacktestResult
ClosedTrade
EquityPoint
FeatureProvider
FillReason
IntrabarConflictPolicy
SimpleBacktestEngine
load_ohlcv_csv
validate_bars
```

Brownfield rule: keep these imports stable until a controlled deprecation plan exists. Do not break notebook, CLI, or existing strategy usage.

### 1.3 Current implementation capabilities already present

Current `SimpleBacktestEngine` already provides:

- deterministic bar-by-bar execution
- completed-bar strategy evaluation
- next-bar market execution
- pending limit/stop order activation
- bid/ask spread modelling
- adverse slippage modelling
- simple commission modelling
- stop-loss and take-profit protection
- deterministic intrabar SL/TP conflict policy
- trailing-stop update semantics
- time-exit handling
- partial-close handling
- pending-order cancellation
- execution-event reactions
- multi-chart auxiliary bar support
- a `FeatureProvider` hook
- immutable result models for closed trades, equity points, events, metrics, diagnostics, open positions, and pending orders

These capabilities should be protected by characterization tests before any refactor.

### 1.4 Current implementation gaps against the old simulator plan

Major missing areas:

- no official `run_backtest` AI/tool envelope
- no `BacktestOrchestrator`
- no request/actor/RBAC validation
- no standard `SIM_*` error taxonomy
- no structured envelope for success/failed/queued/cancelled/diagnostic_failed
- no explicit strategy registry enforcement at simulator boundary
- no raw-code rejection wrapper
- no append-only journal or artifact manifest
- no run manifest/config hash/data manifest hash
- no checkpoint/resume
- no queue/service mode
- no tick-level event-driven engine
- no liquidity/depth model
- no latency model
- no Decimal accounting production-realistic ledger
- no margin/free-margin/margin-level state
- no canonical Analytics adapter
- no Risk replay/decision evidence adapter
- no Optimization work-unit interface
- no import-safety tests
- no dedicated simulator unit-test package

### 1.5 Code that exists but was underrepresented in the old standalone plan

The old plan over-emphasized a future tick-level simulator and underrepresented current useful behavior:

- existing `FeatureProvider`
- auxiliary chart/timeframe support
- strategy execution-event reactions
- strategy state reset compatibility
- trailing-stop one-bar delayed update rule
- deterministic intent priority ordering
- partial close behavior
- time-exit behavior
- direct reuse of `app.services.strategy` contracts

These must be preserved or explicitly migrated.

## 2. Core Architectural Change

The Simulator is not a standalone duplicate of Data, Indicators, Strategy, Trading, Risk, Analytics, or Optimization.

It owns:

- simulation orchestration
- deterministic replay
- simulated execution state
- matching decisions
- simulated accounting replay
- run journals
- artifacts
- run lifecycle
- compatibility wrappers for current backtest behavior

It does not own:

- market-data ingestion or cleaning
- indicator formulas
- strategy lifecycle or strategy-generated signal logic
- trading/live broker mutation
- canonical trading contracts when Trading owns them
- external risk policy authority
- analytics metric definitions
- optimization objective scoring when Optimization owns it
- UI/API route behavior
- Conversation/LLM behavior

## 3. Cross-Module Feature Import Policy

### 3.1 Direct Feature Imports Required

Use direct imports when the dependency is pure, deterministic, broker-free, import-safe, side-effect free, driven by injected `Clock`/`RNG` when needed, and already the canonical owner of the rule.

Required direct imports include:

```python
from app.services.data import validate_bars
from app.services.strategy import Bar, MarketContext, RuntimeMode, TradeIntent
from app.services.trading.contracts import TimeInForce, OrderState, PositionState
from app.utils.logger import logger
```

Direct imports are appropriate for:

- Data validators and canonical bar models that do not read external sources
- Strategy contracts and base lifecycle hooks
- Trading contracts, enums, lifecycle states, and pure validation helpers
- Indicator calculation kernels when pure and availability-safe
- Analytics metric kernels when read-only and side-effect free
- Utils logger, errors, envelopes, timestamps, IDs, redaction, hashing, and safe paths

### 3.2 Typed Ports Required

Use typed ports/adapters when the dependency owns I/O, persistence, broker reads, external SDKs, background jobs, caches, database state, runtime lifecycle, credentials, live trading state, or mutable global service state.

Typed ports required:

```text
MarketDataPort
StrategyRegistryPort
IndicatorResultPort
TradingValidationPort
RiskDecisionPort
RiskReplayPort
AnalyticsReportPort
JournalStore
ArtifactStore
SchedulerStore
OptimizationRunPort
Clock
RNG
```

Data reads should normally go through `MarketDataPort`, because Data owns source routing, cache, storage, broker-backed reads, persistence, provider policies, and data quality evidence.

Risk should use `RiskDecisionPort` or `RiskReplayPort`, because Risk owns external policy and approval authority.

Optimization should call the Simulator as an engine dependency through a deterministic run interface; the Simulator should not launch optimization workers internally unless an approved service-mode slice says so.

### 3.3 Forbidden Imports

The Simulator must not import:

- broker SDK sessions
- live broker clients
- live execution adapters
- credential loaders
- mutating Trading functions
- order submission/modification/cancellation functions
- live risk bypass tools
- UI/API route handlers
- Conversation/LLM providers
- background live runtime loops
- modules that start jobs, connect to brokers, open sockets, read secrets, or mutate external state at import time

If a needed rule currently lives inside a forbidden module, extract that rule into an import-safe pure module owned by the correct service. Do not copy the rule into Simulator.

## 4. Cross-Module Ownership Matrix

| Capability | Owning Module | Simulator Usage | Import Style |
|---|---|---|---|
| Historical bars/ticks, data quality, market hours, synthetic ticks | Data (`app.services.data`) | Read point-in-time data through a `MarketDataPort`; direct use of `validate_bars` remains compatibility-safe | Typed Port for reads; direct pure validators allowed |
| Indicator calculations and availability metadata | Indicators (`app.services.indicators`) | Consume official deterministic kernels/results; simulator only masks unavailable values at decision time | Direct import if pure; otherwise adapter |
| Strategy lifecycle, config validation, TradeIntent creation | Strategy (`app.services.strategy` legacy; future `app.services.strategies`) | Use registry-approved strategy instances and read-only `MarketContext`; never execute raw code strings | Direct contracts + StrategyAdapter |
| Trading order contracts, lifecycle states, TIF/fill policy enums, broker-independent validation | Trading (`app.services.trading`) | Reuse import-safe contracts/validation; simulator matching emits simulated states, not broker mutations | Direct import for contracts/pure validation |
| Risk policy and approval authority | Risk (`app.services.risk`) | Replay or request deterministic risk decisions for evidence; simulator does not define external policy | Typed RiskDecisionPort/RiskReplayPort |
| Analytics metrics, reports, scorecards | Analytics (`app.services.analytics`) | Convert BacktestResult to canonical analytics input and call official metrics/report builders | Direct import if read-only/pure; adapter for schema conversion |
| Optimization work units, scoring/objectives | Optimization (`app.services.optimization`) | Optimization calls simulator as an engine dependency; simulator may expose deterministic run port | Port for orchestration; direct pure scoring only |
| Logging, errors, envelopes, IDs, time, safe paths, redaction | Utils (`app.utils`) | Use as shared primitives; no simulator-specific clones | Direct import |
| Live broker sessions and broker mutation adapters | Live/Trading adapters/brokers | Forbidden inside simulator runtime | Forbidden import |
| UI/API routes and Conversation layer | API/UI/Conversation | Call simulator through service/client boundary only; no domain logic in routes/chat | Forbidden inside simulator core |

## 5. Brownfield Target Structure

The target structure is incremental. Only create files when they reduce migration risk or remove duplicated ownership.

```text
app/services/simulator/
├── __init__.py                         # preserve legacy exports; later add deliberate tool exports
├── engine.py                           # preserve SimpleBacktestEngine baseline
├── models.py                           # preserve legacy dataclasses
├── api/
│   ├── tools.py                        # run_backtest official tool wrapper
│   └── envelopes.py                    # simulator envelope normalization
├── contracts/
│   ├── models.py                       # new canonical request/result/snapshot contracts
│   ├── enums.py                        # simulator enum strings
│   ├── errors.py                       # SIM_* error taxonomy
│   └── ports.py                        # typed cross-module ports
├── orchestration/
│   ├── backtest_orchestrator.py        # wraps current engine first
│   ├── idempotency.py                  # deterministic run identity
│   ├── checkpoints.py                  # optional active-scope slice
│   └── scheduler.py                    # optional service-mode slice
├── integration/
│   ├── data_adapter.py                 # MarketDataPort implementation boundary
│   ├── strategy_adapter.py             # registry-approved strategy boundary
│   ├── indicator_adapter.py            # availability-safe indicators/features
│   ├── trading_contract_adapter.py     # Trading pure contracts/validation
│   ├── analytics_adapter.py            # Analytics report/metric conversion
│   └── risk_replay_adapter.py          # Risk evidence/replay boundary
├── journal/
│   ├── append_only.py
│   ├── artifacts.py
│   └── manifest.py
├── reporting/
│   ├── results.py
│   ├── realism.py
│   └── renderers.py
├── operations/
│   ├── instrumentation.py
│   ├── quotas.py
│   ├── environment.py
│   └── security.py
└── verification/
    ├── characterization.py
    ├── replay.py
    └── provider_contracts.py
```

## 6. Current File Preservation Plan

| Current file | Preserve? | Brownfield action | Reason |
|---|---:|---|---|
| `app/services/simulator/__init__.py` | Yes | Keep current exports; add new exports only after classification | Existing imports depend on it |
| `app/services/simulator/engine.py` | Yes | Treat `SimpleBacktestEngine` as baseline research/bar engine | It already encodes deterministic behavior and strategy compatibility |
| `app/services/simulator/models.py` | Yes | Keep dataclasses; add adapters to new canonical contracts | Avoid breaking existing result consumers |
| `tests/usage/08_simulator.py` | Yes, revise | Keep as usage example but remove mandatory live MT5 dependency from default smoke path | Current example depends on staging broker availability and uses `print()` |

## 7. Migration Actions

### BF-SIM-001 — Baseline characterization

Add tests that freeze current behavior before refactoring:

- deterministic repeated run equality
- no-lookahead next-bar execution
- invalid timeframe failure
- invalid bar validation from Data
- SL/TP conflict policy
- trailing-stop delayed update
- partial close
- pending limit/stop order fill
- execution-event reaction
- auxiliary chart cutoff behavior
- result `to_dict()` shape

### BF-SIM-002 — Import safety

Add tests proving imports do not:

- read market data
- connect to brokers
- resolve secrets
- write files
- open sockets
- start background workers
- mutate durable state

### BF-SIM-003 — Official tool boundary

Introduce `run_backtest` as the official user/agent boundary. It must:

- accept registered strategy identifiers or pre-approved strategy references only
- reject raw Python code strings
- validate actor context for external/network/agent usage
- return standard simulator envelopes
- log safe structured diagnostics
- delegate to `BacktestOrchestrator`

### BF-SIM-004 — Orchestrator wrapper over current engine

Implement `BacktestOrchestrator` around `SimpleBacktestEngine` first. Do not replace the engine until tests prove parity.

### BF-SIM-005 — Cross-module adapters

Introduce ports/adapters in this order:

1. `MarketDataPort`
2. `StrategyRegistryPort`
3. `IndicatorResultPort`
4. `TradingValidationPort`
5. `RiskReplayPort`
6. `AnalyticsReportPort`
7. `JournalStore`
8. `ArtifactStore`

### BF-SIM-006 — Trading contract reuse

Simulator matching must use import-safe Trading contracts for canonical order states, TIF, response/result fields, and validation where the Trading module owns the rule.

Simulator may own simulated fill matching, but not duplicate broker-independent order validation if Trading already exposes it safely.

### BF-SIM-007 — Analytics metric reuse

The current `_build_metrics()` remains compatibility behavior for `BacktestMetrics`. New reporting must route richer metrics through Analytics adapters instead of duplicating formulas.

### BF-SIM-008 — Risk replay/evidence

Simulator may replay simulation-only risk effects and include risk evidence, but external risk policy, approval, live authority, and human governance remain in Risk.

### BF-SIM-009 — Tick/event engine introduction

Only after baseline parity exists, introduce `EventDrivenExecutionEngine` behind the same orchestrator interface. The first slice should support a narrow subset:

- deterministic event priority
- tick stream adapter
- market order lifecycle
- pending order lifecycle
- order/deal/position state containers
- journal event emission
- current bar-engine result parity where applicable

### BF-SIM-010 — Controlled deprecation

Legacy imports remain available until:

- replacement path is implemented
- migration guide exists
- tests cover both old and new imports
- deprecation warnings are explicit
- owner approves removal window

## 8. Module-by-Module Implementation Order

| Order | Slice | Files | Outcome | Dependency rule |
|---:|---|---|---|---|
| 0 | Baseline freeze and characterization | Current `__init__.py`, `engine.py`, `models.py`, `tests/usage/08_simulator.py` | No production behavior changes; capture current output fixtures; document public exports | Before every later step |
| 1 | Import-safety and compatibility tests | tests/services/simulator/test_import_safety.py; test_public_exports.py | Assert import has no broker/network/data reads; assert legacy imports still work | Depends on 0 |
| 2 | Contracts, enums, errors, ports | contracts/models.py, enums.py, errors.py, ports.py | Add new typed request/result/envelope/port models while keeping legacy models available | Depends on 1 |
| 3 | Public tool wrapper | api/tools.py, api/envelopes.py | Add `run_backtest` wrapper that rejects raw code, validates actor/context, returns standard envelope, delegates to orchestrator | Depends on 2 |
| 4 | Brownfield orchestrator | orchestration/backtest_orchestrator.py | Wrap `SimpleBacktestEngine.run()` as the first execution backend; no tick-engine replacement yet | Depends on 3 |
| 5 | Data and strategy adapters | integration/data_adapter.py, strategy_adapter.py, indicator_adapter.py | Resolve registered strategies, point-in-time bars, auxiliary charts, features, and availability masks through ports | Depends on 4 |
| 6 | Trading-contract parity layer | execution/order_contract_adapter.py, validation/trading_validation.py | Reuse `app.services.trading` import-safe contracts/pure validation; remove simulator-owned duplicates where present | Depends on 5 |
| 7 | Journal/artifact layer | journal/append_only.py, artifacts.py, manifest.py | Persist deterministic run manifests and receipts; keep BacktestResult compatibility | Depends on 4 |
| 8 | Analytics reporting adapter | reporting/analytics_adapter.py, report_renderer.py | Map simulator result to Analytics contracts; stop duplicating non-baseline metrics in simulator | Depends on 7 |
| 9 | Risk replay/evidence adapter | controls/risk_replay.py | Consume Risk decision packages or replay configured simulation-only gates; no external policy ownership | Depends on 6 |
| 10 | Event-driven engine slice | engine/event_driven_execution.py, event_priority.py, state.py | Introduce tick/event engine behind same orchestrator after parity tests; do not remove SimpleBacktestEngine | Depends on 6–9 |
| 11 | Scheduler/checkpoint optional slice | orchestration/scheduler.py, checkpoints.py, worker_recovery.py | Only after service mode is approved; keep synchronous local mode default | Depends on 7 |
| 12 | Optimization integration | ports + optimization adapter docs | Optimization calls simulator via deterministic run interface; parallel workers isolated | Depends on 10 or approved bar-engine scope |
| 13 | Release hardening | operations/quotas.py, environment.py, security.py, docs | Resource quotas, environment drift, retention, supply-chain gates, examples | Depends on active release scope |

## 9. Requirement Coverage Matrix

Coverage matrix rule: contiguous requirement ranges are used where every ID in the range shares the same brownfield task, file anchor, dependency, migration action, evidence target, and status. Every original requirement ID is covered exactly once by the ranges below.

| Requirement ID(s) | Brownfield upgrade task | Current code/file anchor | Cross-module dependency | Migration action | Test/evidence target | Status |
|---|---|---|---|---|---|---|
| SIM-FR-001–SIM-FR-013 | Simulator documentation and operating manuals | docs/dev/phase-implementation-plan/08-simulator.md; new docs/simulator/* | Utils docs conventions; Data/Strategy/Trading docs | Rewrite as brownfield docs; add realism/migration/import-policy guide | docs review checklist; executable examples | Gap -> Plan |
| SIM-FR-014–SIM-FR-024 | Package scope, export policy, import-time safety | app/services/simulator/__init__.py | app.utils.logger/envelopes; app.services.data current exports | Preserve current exports; classify support exports vs official tools; add import-safety test | tests/services/simulator/test_import_safety.py | Partial |
| SIM-FR-025–SIM-FR-085 | run_backtest tool, BacktestOrchestrator, request validation, queue/checkpoint contracts | current: engine.py run(); new: api/tools.py, orchestration/backtest_orchestrator.py | Data MarketDataPort; Strategy registry/contracts; Utils envelope/auth | Introduce run_backtest wrapper around SimpleBacktestEngine before replacing internals; reject raw code | tool contract tests, usage examples, security tests | Gap -> Incremental |
| SIM-FR-086–SIM-FR-216 | Execution engine, deterministic event order, state, matching, costs, accounting, SIM_* codes | current: engine.py, models.py | Trading contracts/validation; Strategy TradeIntent; Analytics metrics; Risk replay port | Keep SimpleBacktestEngine as legacy bar engine; extract pure kernels; add event-driven engine only after characterization tests | engine regression tests, parity fixtures, deterministic replay tests | Partial |
| SIM-FR-217–SIM-FR-320 | Market data, tick generation, spread/slippage/liquidity/latency, symbol metadata | current: engine._quote/_side_ohlc; new market/* and costs/* | Data get_data/validate_bars/generate_synthetic_ticks; Trading symbol contracts | Move configurable market/tick/cost assumptions behind ports and deterministic kernels | market/cost model tests; data-quality fixtures | Partial |
| SIM-FR-321–SIM-FR-430 | Portfolio/accounting, margin, currency conversion, cashflows, position lifecycle | current: engine._close_position/_unrealized_pnl, models.SimPosition | Trading PositionState/OrderState; Risk snapshots; Analytics adapters | Preserve current float research accounting; add Decimal accounting adapter before production-realistic classification | accounting golden fixtures; float-vs-decimal migration tests | Partial |
| SIM-FR-431–SIM-FR-540 | Journal, artifact manifests, retention, reproducibility, environment hashes | current: BacktestResult.to_dict; new journal/* operations/* | Utils safe paths, hashing, redaction, time; Data manifests | Add append-only run journal and manifest without changing SimpleBacktestEngine output first | artifact checksum tests; replay manifest tests | Gap |
| SIM-FR-541–SIM-FR-650 | Reporting, analytics, scorecards, realism disclosure, risk evidence | current: _build_metrics, BacktestMetrics; new reporting/* | Analytics official metrics/report adapters; Risk decision packages | Replace duplicated metric calculations with Analytics adapters where canonical; keep _build_metrics compatibility | analytics adapter tests; report snapshot tests | Partial |
| SIM-FR-651–SIM-FR-760 | Service-mode operations: quotas, scheduler, worker recovery, canary, synthetic probes | new: operations/* orchestration/scheduler.py | Utils metrics/event bus; Optimization work units; UI/API client contracts | Define ports now; implement only local synchronous run in Phase 1 unless service mode approved | quota/queue contract tests when enabled | Deferred/Planned |
| SIM-FR-761–SIM-FR-832 | Verification, provider contracts, examples, release gates, deferred-scope register | current: tests/usage/08_simulator.py | All owning services by ports/import policy | Convert usage example away from print-heavy MT5 dependency; add executable docs and traceability gates | coverage matrix test; examples smoke test | Partial |
| SIM-NFR-001–SIM-NFR-090 | Import safety, side-effect isolation, official export classification | __init__.py, engine.py, models.py | Utils logger/errors/envelopes | Add import probes and `__all__` classification; avoid broker/session imports | import-time side-effect tests | Partial |
| SIM-NFR-091–SIM-NFR-180 | Security, raw-code rejection, actor/RBAC, redaction | new api/tools.py, operations/security.py | Utils redaction/auth; Strategy registry | Implement wrapper validation before orchestration; never pass code strings to strategy loader | security contract tests | Gap |
| SIM-NFR-181–SIM-NFR-270 | Determinism, Clock/RNG injection, replayability, idempotency | engine.py; new contracts/ports.py, orchestration/idempotency.py | Utils time/clock; Strategy state; Optimization candidate hashes | Add deterministic seed/run-id material and prohibit global random/wall clock in core engine | determinism/replay tests | Partial |
| SIM-NFR-271–SIM-NFR-360 | Data integrity, no-lookahead, multi-timeframe alignment, data manifests | engine._make_context; contracts.strategies.MarketContext | Data validation/manifests; Indicator availability metadata | Harden current auxiliary chart cutoff; add explicit no-lookahead guard/adapters | no-lookahead tests; data manifest tests | Partial |
| SIM-NFR-361–SIM-NFR-450 | Performance, quotas, memory, batching, optimization safety | new operations/quotas.py; tick_batching.py | Optimization runner; Utils monotonic timers | Keep benchmarks non-blocking until profile approved; add local limits before service mode | benchmark profile evidence | Deferred/Planned |
| SIM-NFR-451–SIM-NFR-520 | Persistence durability, journals, checkpoints, resume compatibility | new journal/*, orchestration/checkpoints.py | Utils safe paths; Data/SQLite conventions | Add append-only artifacts before restartable checkpointing | checkpoint compatibility tests | Gap |
| SIM-NFR-521–SIM-NFR-582 | Governance, promotion, vendor/supply-chain, release certification | docs/dev/phase-implementation-plan/08-simulator.md; operations/environment.py | Utils security; Data vendor manifests; CI tooling | Document gates and defer production-promotion automation until approved | release gate checklist; SBOM/scan evidence | Planned |
| SIM-BR-001–SIM-BR-033 | Business rules for determinism, ownership, no-live reach-through, realism labels | all simulator public boundaries | Data/Strategy/Trading/Risk/Analytics ownership matrix | Make business rules explicit in brownfield policy; block duplicated logic | requirements traceability review | Plan |
| SIM-EX-001 | Executable example and quality standard | tests/usage/08_simulator.py; examples/run_simulator_examples.py | Data and Strategy examples | Convert current staging MT5 example into deterministic local fixture example plus optional MT5 demo | doctest/smoke example | Partial |

## 10. Detailed Coverage Notes

### 10.1 Requirements already substantially supported

Current implementation already supports parts of:

- deterministic bar execution
- next-bar no-lookahead execution
- completed-bar strategy views
- read-only strategy snapshots
- market/pending/protection fills
- simple spread/slippage/commission
- partial closes
- trailing stops
- basic metrics
- result diagnostics
- Strategy contract reuse
- Data bar validation reuse

These are not to be rewritten from scratch.

### 10.2 Requirements partially supported

Partially supported requirements should be hardened in place first:

- data quality and no-lookahead
- strategy lifecycle
- order state handling
- fill reasons and event audit
- metrics
- cost modelling
- result serialization
- examples

### 10.3 Requirements not implemented yet

Major gaps become planned migration tasks:

- official tool wrapper
- standard envelopes
- SIM error taxonomy
- actor/RBAC validation
- registry-only strategy execution
- raw code rejection
- orchestrator lifecycle
- journaling
- artifact manifests
- run hashes
- Analytics adapter
- Risk evidence adapter
- Trading contract validation adapter
- checkpoint/resume
- queue/service mode
- event/tick engine
- production-realistic accounting

### 10.4 Deferred scope

The following remain deferred unless explicitly approved for the active release slice:

- distributed workers
- canary production comparison
- synthetic transaction monitoring
- equity/ETF corporate actions
- tax/regulatory engines
- futures roll production realism
- perpetual funding production realism
- external report distribution
- production promotion automation
- alternative-data feature-store integration
- live broker mutation

## 11. Test and Evidence Plan

| Evidence class | Required tests |
|---|---|
| Characterization | Current engine golden fixtures and repeated-run equality |
| Import safety | No filesystem write, network, broker access, secret read, worker startup on import |
| Tool contract | `run_backtest` success, failed, diagnostic_failed, queued/cancelled if enabled |
| Security | Raw strategy code rejected with `SIM_ARBITRARY_CODE_REJECTED`; payload redacted |
| Strategy boundary | Registered strategy only; arbitrary path/code rejected |
| Data boundary | Point-in-time data retrieval; no-lookahead auxiliary chart cutoff |
| Trading contract reuse | TIF/order-state/fill-policy validation from Trading contracts where import-safe |
| Risk boundary | Risk evidence consumed through port; no policy duplication |
| Analytics boundary | Backtest result converted to Analytics-compatible input |
| Journaling | Manifest checksums, append-only sequence, replay comparison |
| Determinism | Same config, data, seed, dependency versions produce same events/results |
| Compatibility | Existing imports from `app.services.simulator` continue to work |

## 12. Acceptance Gates

A simulator migration slice is accepted only when:

1. Existing simulator imports still work.
2. Current `SimpleBacktestEngine` behavior is characterized by tests.
3. New files do not import forbidden broker/live/credential/runtime modules.
4. `run_backtest` rejects raw arbitrary code before execution.
5. Data reads are point-in-time and no-lookahead safe.
6. Strategy snapshots are read-only.
7. Trading validation/contracts are reused where import-safe.
8. Analytics metrics are reused for canonical reports.
9. Risk authority is consumed, not duplicated.
10. Every failure returns deterministic `SIM_*` or mapped standard error codes.
11. Examples run without requiring live broker availability by default.
12. Coverage stays above the project threshold for modified simulator files.

## 13. Builder Handoff Rules

Builder must:

- read this file first
- preserve the existing files unless the slice explicitly says otherwise
- create tests before refactoring current behavior
- keep `SimpleBacktestEngine` available
- add wrappers/adapters around current behavior before replacing internals
- avoid direct live broker SDK imports
- avoid raw strategy-code execution
- reuse upstream modules instead of duplicating rules
- report every changed file and mapped requirement range

## 14. Open Decisions Before Production-Realistic Classification

| Decision | Owner | Required before |
|---|---|---|
| Approved simulator public envelope schema | Architecture/Owner | Official external tool exposure |
| Canonical strategy registry source | Strategy/Architecture | Registry-only `run_backtest` |
| Trading pure validation import locations | Trading/Architecture | Contract parity layer |
| Risk replay vs decision-port mode | Risk/Architecture | Risk evidence reports |
| Analytics canonical adapter schema | Analytics/Architecture | Official report replacement |
| Benchmark profile and memory limits | Owner/Architecture | Production-realistic label |
| Service-mode queue backend | Architecture/Operations | Queued/scheduled runs |
| Checkpoint retention and artifact root policy | Architecture/Operations | Resume support |

## 15. Final Brownfield Rule

Do not replace the simulator with a greenfield standalone engine.

First protect the current deterministic bar engine. Then surround it with the official tool boundary, ports, adapters, journals, and cross-module feature reuse. Only then introduce the event-driven tick engine behind the same orchestrator interface.
