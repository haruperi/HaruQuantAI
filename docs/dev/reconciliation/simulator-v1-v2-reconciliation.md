# Simulation — V1/V2 Reconciliation
## 1. Reconciliation Scope
* **Domain:** simulator (`sim`)
* **Canonical intended package:** `app/services/simulation/`
* **V1 audit report:** `docs/dev/audits/simulator-v1-audit.md`
* **V2 requirements:** `08-simulation.md`
* **V2 requirement identification:** The V2 source has no stable IDs. This reconciliation assigns `V2-SIM-REQ-0001` through `V2-SIM-REQ-1636` in source order; every checkbox requirement appears once in Section 6.
* **Comparison limitations:** Only the two supplied documents were used. No code, repository, roadmap, top-level architecture, ADR, broker fixture, strategy/indicator/data contract, or deployment configuration was inspected. V1 evidence is therefore limited to the audit conclusions, and V2 contract items explicitly marked pending remain open.
## 2. Executive Summary
The V1 audit confirms that the requested `app.services.simulator` package is absent. Its nine catalogued capabilities are either stale intentions, broken conditional integration, mock-only test surfaces, or deleted historical code. There is no proven working V1 implementation to preserve unchanged.

The useful V1 intent is limited to deterministic strategy simulation, next-period/no-lookahead behavior, pending/protective order handling, multi-timeframe visibility, broker-neutral strategy compatibility, and structured trades/equity results. Those behaviors should be **modified and re-specified**, not restored under the missing package.

V2 correctly identifies the essential future direction: one canonical FX tick-execution path, deterministic no-lookahead timing, engine-owned simulated state, explicit execution costs, fixed-precision accounting, immutable journal evidence, replay, data/strategy manifest validation, safe tool envelopes, and canonical JSON/Markdown artifacts. These are approved as 13 focused capabilities.

V2 is nevertheless far too broad for the initial rebuild. It mixes Phase 1 FX execution with optimization algorithms, analytics formulas, data-platform governance, enterprise scheduling, distributed workers, multi-asset realism, regulatory engines, model governance, external report distribution, and production promotion automation. Those items are rejected as Simulation-owned behavior, delegated to their owning domains, or deferred.

**V2 disposition totals:** 841 Add, 171 Modify, 143 Merge, 22 Keep, 423 Defer, 9 Reject, and 27 Open Decision.

The recommended direction is a clean canonical package at `app/services/simulation/`, with explicit migration away from `app.services.simulator`. Build the local deterministic FX single-run path first. Do not add service-mode infrastructure or future asset classes until the core journal-replay-accounting path is correct and benchmarked.
## 3. Decision Principles
1. Preserve valuable behavior only when the V1 audit demonstrates a real need; stale tests are design evidence, not working code.
2. Use `app/services/simulation/` as the canonical package and remove the missing legacy package identity after caller verification.
3. Keep one official execution clock: deterministic bid/ask ticks.
4. Keep one official public tool: an explicit versioned `run_backtest` wrapper.
5. Use classes only where state or lifecycle is intrinsic: execution engine, simulated Trader state, journal writer/replayer.
6. Prefer pure functions/configuration types for stateless validation, pricing, costs, rounding, and report transformation.
7. Simulation owns simulated execution state and evidence; it does not own strategy logic, indicator formulas, data acquisition, live adapters, optimization search, analytics formulas, risk policy, or release governance.
8. Implement only the approved FX canonical slice initially; deferred features must fail deterministically or remain unreachable.
9. Canonical artifacts are the immutable journal, versioned result, JSON report, Markdown report, and artifact manifest.
10. Determinism, no-lookahead, fixed precision, accounting invariants, safe errors, and no-live-side-effects are non-negotiable.
11. Do not introduce managers, repositories, adapters, factories, schedulers, or extension layers without an accepted workflow that requires them.
12. Exact external contracts and project-wide policies remain open until their owning documents are available.
## 4. Capability Reconciliation Matrix
| Capability ID | Capability | V1 evidence | V2 requirement | Gap | Decision | Final behaviour | Reuse approach | Reason |
|---|---|---|---|---|---|---|---|---|
| CAP-SIM-001 | Official simulation tool and versioned contracts | `V1-CAP-SIMULATOR-001`, `V1-CAP-SIMULATOR-002`; no current implementation | `V2-SIM-REQ-0020–0041`, `0679–0699` | No importable V1 tool, request schema, response envelope, safe errors, or explicit tool registration. | Add / Modify | Expose one explicit `run_backtest` tool with a versioned request, deterministic envelope, registered-strategy references, safe errors, artifact references, and no import-time side effects. | New contract; reuse only terminology from the V1 tests. | A stable tool boundary is essential, but the exact V2 scaffold is still overbroad and partly pending. |
| CAP-SIM-002 | Run validation, orchestration, and lifecycle | `V1-WF-SIMULATOR-001` is broken; `V1-CAP-SIMULATOR-003` describes only test intent. | `V2-SIM-REQ-0042–0049`, `0715–0729`, `1621–1632` | No working run coordinator, lifecycle, idempotency, cancellation result, or stage validation. | Add | Validate request, permissions, strategy/data/broker references, and simulation configuration; execute a deterministic stage sequence; record lifecycle transitions and return a structured result. | New implementation; reuse the V1 workflow concept, not the missing package. | This is the smallest end-to-end capability that makes Simulation operational. |
| CAP-SIM-003 | Signal timing, tick construction, and no-lookahead | `V1-CAP-SIMULATOR-003`, `V1-CAP-SIMULATOR-005`; test evidence only. | `V2-SIM-REQ-0050–0094` | V1 intended next-bar behavior and auxiliary charts, but no current code exists and V2 requires canonical tick timing. | Modify | Consume approved timestamped strategy intents, construct deterministic FX tick streams, enforce previous-closed-bar visibility by default, and fail deterministically on lookahead. | Re-express V1 no-lookahead and multi-timeframe intent in a new tick-timeline implementation. | The underlying behavior is valuable; the official clock must change from the missing bar simulator to the canonical tick loop. |
| CAP-SIM-004 | Canonical FX execution, matching, and realism | `V1-CAP-SIMULATOR-004`; pending/stop/protection behavior exists only in stale tests. | `V2-SIM-REQ-0095–0213`, `0357–0390`, `0516–0542`, `0659–0678` | No working execution state machine, matching, spread/slippage/liquidity, fill-policy, gap, priority, or broker-rule implementation. | Modify / Add | Implement deterministic FX market and supported pending-order execution, bid/ask pricing, Phase 1 spread/slippage/liquidity models, FOK/IOC partial-fill semantics, gaps, same-tick priority, and selected MT5-parity broker rules. | New engine; preserve V1 behavioral expectations where compatible. | These behaviors answer the simulation question directly; richer order-book, exchange, and batching features are deferred. |
| CAP-SIM-005 | Simulated Trader interface and authoritative execution state | `V1-CAP-SIMULATOR-007`, `V1-WF-SIMULATOR-002`; conditional broker path is broken. | `V2-SIM-REQ-0311–0356`, `0654–0658` | No current simulated broker module, state containers, stable request/query semantics, or read-only snapshots. | Modify / Merge | Implement only the simulated side of an approved shared Trader contract: Phase 1 order submission/close, required queries, margin/profit calculations, and read-only snapshots backed by engine-owned state. | Replace the global `active_broker=simulator` package route with an explicit simulation-bound implementation after cross-domain approval. | Shared strategy semantics are useful, but Simulation must not impersonate or import live adapters. |
| CAP-SIM-006 | Sizing application, accounting, costs, margin, and FX conversion | `V1-CAP-SIMULATOR-002`, `V1-CAP-SIMULATOR-006`; expected outputs only. | `V2-SIM-REQ-0180–0199`, `0214–0249`, `0294–0310`, `0391–0400`, `0616–0653` | No authoritative accounting or fixed-precision execution ledger exists. | Add / Modify | Normalize approved volume, apply Phase 1 FX commission/swap/margin rules, maintain balance/equity/free-margin invariants, and perform deterministic direct/inverse FX conversion with staleness rejection. | New accounting core; retain V1 expected trade/equity result concepts. | Accounting is essential, while advanced sizing policy and non-FX cashflows belong elsewhere or are deferred. |
| CAP-SIM-007 | Immutable journal, replay, persistence, and run idempotency | `V1-CAP-SIMULATOR-006`; no current journal implementation. | `V2-SIM-REQ-0401–0427`, `0709–0714`, `0840–0883` | No canonical event source, persistence contract, hash continuity, replay, or request-id behavior. | Add / Merge | Use append-only versioned JSONL journal events with monotonic sequence, hash chain, bounded streaming persistence, deterministic replay, lifecycle/idempotency events, and fail-closed production persistence. | New implementation; merge proposed compliance records into typed journal events. | A canonical journal is the minimum auditable source of truth; mandatory SQLite sidecar indexing is deferred pending measured need. |
| CAP-SIM-008 | Canonical reports, artifacts, and analytics boundary | `V1-CAP-SIMULATOR-006`; stale tests expect metrics and serialization. | `V2-SIM-REQ-0433–0481`, `0654–0658`, reporting/documentation repetitions | No current result schema, artifact manifest, JSON/Markdown report, or validated analytics integration. | Modify / Add | Produce canonical SimulationResult, JSON and Markdown reports, artifact checksums, execution/accounting diagnostics, and realism/data-quality disclosures; consume specialized metrics from Analytics. | Preserve V1 result concepts but replace the absent contract. | Simulation owns execution evidence and report assembly, not the full analytics formula catalog. |
| CAP-SIM-009 | Inbound data authority and simulation-specific quality gate | No working implementation; `V1-WF-SIMULATOR-001` manually fetched data. | `V2-SIM-REQ-0250–0280`, `0730–0736`, data-governance repetitions | No manifest validation, pre-execution quality gate, checksum binding, or deterministic severe-failure behavior. | Add / Modify | Consume Data-owned immutable manifests and normalized inputs, validate checksums and execution-critical schema/timing/spread/OHLC conditions, and block severe invalid inputs before execution. | New boundary code; do not recreate source acquisition, vendor governance, caches, or full lineage ownership. | Simulation must trust but verify its inputs while preserving Data ownership. |
| CAP-SIM-010 | Strategy and indicator integration boundary | `V1-CAP-SIMULATOR-003`, `V1-CAP-SIMULATOR-005`; stale strategy callback tests. | `V2-SIM-REQ-0421–0432` | No approved registry contract, intent schema, state-mutation boundary, or point-in-time input contract. | Modify | Accept only approved registered strategies and timestamped TradeIntent outputs; expose read-only execution snapshots; validate timing metadata; never own indicator formulas or raw strategy-code execution. | Retain the V1 strategy-run concept while replacing direct legacy imports. | This preserves reusable strategies without leaking Strategy/Indicator responsibilities into Simulation. |
| CAP-SIM-011 | Determinism, precision, reliability, security, and verification | `V1-CAP-SIMULATOR-009` historical deterministic intent; current package absent and tests disconnected. | `V2-SIM-REQ-0737–0938`, `1016–1388` | No current deterministic replay guarantee, fixed-precision accounting policy, safe error envelope, import-safety gate, or runnable Phase 1 verification suite. | Add / Modify | Pin the reproducibility profile, use fixed-precision execution/accounting, enforce invariants and safe SIM_* errors, prevent live/network/import side effects, add traceable tests and non-blocking benchmarks. | Replace stale tests with contract, golden, replay, fault, boundary, and integration tests for the canonical package. | Trustworthiness is required; production service operations and speculative enterprise gates are deferred. |
| CAP-SIM-012 | Explicit non-canonical fast research mode | No current implementation; V1 historical engine was bar-based. | `V2-SIM-REQ-0055`, modelling-mode and disclosure requirements | No clear distinction between official execution and approximation. | Add | Optionally allow a clearly labelled FAST_RESEARCH approximation that cannot emit official fills, promotion evidence, or canonical reports. | Do not restore the missing V1 package; use a separate internal path or mode behind explicit classification. | Research speed is useful only when it cannot be confused with canonical evidence. |
| CAP-SIM-013 | Optimization and robustness execution boundary | `V1-CAP-SIMULATOR-008`, `V1-WF-SIMULATOR-003`; current tests mock nonexistent modules. | `V2-SIM-REQ-0482–0515`, research-integrity requirements | No real integration contract; V2 assigns algorithms, workers, and research governance to Simulation. | Merge / Modify / Defer | Expose deterministic canonical single-run execution and provenance for Optimization/Research callers. Search algorithms, ranking policy, Monte Carlo/bootstrap analysis, workers, and research governance remain outside Simulation. | Remove legacy simulator mocks after the Optimization domain consumes the canonical run contract. | This preserves cross-domain value while eliminating duplicate ownership and premature service infrastructure. |

## 5. V1 Disposition Register
| V1 capability ID | V1 capability | Current implementation | Current value | Decision | Final destination | Removal condition |
|---|---|---|---|---|---|---|
| V1-CAP-SIMULATOR-001 | Importable simulator service | No current `app.services.simulator` package | No demonstrated value | Remove | Canonical `app.services.simulation` package / `CAP-SIM-001` | Verify no external deployment or local package depends on `app.services.simulator`; migrate all repository callers. |
| V1-CAP-SIMULATOR-002 | Simulator configuration | Referenced `SimulatorConfig` only in stale tests/examples | Questionable | Modify | Versioned Phase 1 request/config contracts in `CAP-SIM-001` and `CAP-SIM-006` | Do not delete test terminology until equivalent contract fields are mapped. |
| V1-CAP-SIMULATOR-003 | Bar-by-bar strategy execution | Referenced `TradeSimulator.run()`; implementation absent | Questionable | Modify | Canonical tick orchestration in `CAP-SIM-002`–`004` | Replace only after canonical FX golden and replay tests pass. |
| V1-CAP-SIMULATOR-004 | Pending, stop, limit, protective, and time-exit handling | Behavior asserted by stale tests; no implementation | Questionable | Modify | Supported matching behavior in `CAP-SIM-004` | Confirm which order types are Phase 1 and return deterministic unsupported-scope codes for the rest. |
| V1-CAP-SIMULATOR-005 | Multi-timeframe strategy context | Private `_make_context()` expected by tests | Questionable | Modify | Point-in-time strategy/indicator boundary in `CAP-SIM-003` and `CAP-SIM-010` | Validate shared timing contract with Strategy/Data before removing private-test assumptions. |
| V1-CAP-SIMULATOR-006 | Simulation result, trades, equity, and analytics | Expected result fields only | Supporting intent | Modify | `CAP-SIM-006`–`008` | Map every still-needed result field to the new schemas; Analytics ownership must be approved. |
| V1-CAP-SIMULATOR-007 | Broker-compatible simulator provider | Broken dynamic import selected by broker router | Questionable | Merge | Simulated implementation of shared Trader contract in `CAP-SIM-005` | Confirm shared contract ownership and remove global router branch only after callers migrate. |
| V1-CAP-SIMULATOR-008 | Optimization integration through legacy simulator engine/orchestrator | Optimization tests inject fake modules | No demonstrated value | Merge | Canonical execution boundary for Optimization in `CAP-SIM-013` | Replace mocks after an integration test invokes the real canonical runner. |
| V1-CAP-SIMULATOR-009 | Historical deterministic simulator implementation | Deleted `app/services/NEW/simulator/*` | No demonstrated current value | Remove | None; selected behavioral ideas are re-specified in final capabilities | Confirm no branch/deployment imports deleted files and preserve only tests/spec concepts that pass reconciliation. |

## 6. V2 Requirement Disposition Register
Every V2 checkbox requirement is listed below exactly once. IDs are reconciliation-generated in source order. Repeated requirements are marked **Merge** rather than being silently omitted. Requirements assigned **Defer** remain outside the initial FX rebuild. Requirements assigned **Reject** are not accepted as Simulation-owned or structurally necessary behavior.

**Register completeness:** 1636 of 1636 source checkbox requirements classified.

### 2.1 Owns

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0001 | Simulation orchestration through `BacktestOrchestrator`. | Add | Adopt as Simulation-owned behavior within the Phase 1 FX slice. | No current V1 implementation exists. |
| V2-SIM-REQ-0002 | Canonical tick-based execution through `EventDrivenExecutionEngine`. | Add | Adopt as Simulation-owned behavior within the Phase 1 FX slice. | No current V1 implementation exists. |
| V2-SIM-REQ-0003 | Conversion of timestamped `TradeIntent` objects into sized `TradeRequest` objects. | Add | Adopt as Simulation-owned behavior within the Phase 1 FX slice. | No current V1 implementation exists. |
| V2-SIM-REQ-0004 | Simulation-only trader interface and MT5-style simulated order/query semantics. | Add | Adopt as Simulation-owned behavior within the Phase 1 FX slice. | No current V1 implementation exists. |
| V2-SIM-REQ-0005 | Official simulated orders, deals, positions, pending orders, account state, balance, equity, margin, free margin, margin level, realized PnL, floating PnL, execution timestamps, and immutable simulation journal. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0006 | Tick generation, tick stream construction, spread modelling, slippage modelling, liquidity modelling, matching, partial-fill handling, same-tick event priority, gap handling, commission/fee/swap/funding/borrow-fee accounting, and portfolio-level simulation state. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0007 | Simulation reports, metrics, artifact manifests, replay metadata, journal persistence, run lifecycle, run idempotency, optimization/walk-forward/Monte Carlo execution evidence, and production-promotion evidence. | Modify | Simulation owns run evidence and execution artifacts; specialized policy/analysis remains in its owning domain. | The proposed ownership is broader than the confirmed Simulation boundary. |
| V2-SIM-REQ-0008 | Simulation-specific data-quality gating, realism classification, asset-class realism disclosures, benchmark manifests, model-governance evidence, research-integrity evidence, and execution-calibration evidence. | Modify | Simulation owns run evidence and execution artifacts; specialized policy/analysis remains in its owning domain. | The proposed ownership is broader than the confirmed Simulation boundary. |
| V2-SIM-REQ-0009 | Mandatory inbound-contract validation for `MarketDataAuthorityManifest` supplied by `app/services/data/` and strategy registry references supplied by `tools/strategies/` before official runs. | Add | Adopt as Simulation-owned behavior within the Phase 1 FX slice. | No current V1 implementation exists. |

### 2.2 Does Not Own

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0010 | The module does not own strategy logic, strategy lifecycle approval, or strategy-generated signal logic; those belong to `tools/strategies/`. | Keep | Preserve this ownership exclusion. | It prevents cross-domain leakage and live-side effects. |
| V2-SIM-REQ-0011 | The module does not own indicator formula implementation or indicator result contracts; those belong to `tools/indicators/`. | Keep | Preserve this ownership exclusion. | It prevents cross-domain leakage and live-side effects. |
| V2-SIM-REQ-0012 | The module does not own raw market-data acquisition, source readiness, external source adapters, or normalized data contracts; those belong to `app/services/data/`. | Keep | Preserve this ownership exclusion. | It prevents cross-domain leakage and live-side effects. |
| V2-SIM-REQ-0013 | The module does not own final live broker execution against real accounts. | Keep | Preserve this ownership exclusion. | It prevents cross-domain leakage and live-side effects. |
| V2-SIM-REQ-0014 | The module does not own production risk-governor policy, external governance policy, or human approval workflows. | Keep | Preserve this ownership exclusion. | It prevents cross-domain leakage and live-side effects. |
| V2-SIM-REQ-0015 | The module may simulate configured simulation risk-rule effects for replay and evidence, but external policy definition, live approval authority, and human governance decisions live outside Simulation. | Keep | Preserve this ownership exclusion. | It prevents cross-domain leakage and live-side effects. |
| V2-SIM-REQ-0016 | The module does not execute arbitrary user-provided Python strategy code through `run_backtest`. | Keep | Preserve this ownership exclusion. | It prevents cross-domain leakage and live-side effects. |
| V2-SIM-REQ-0017 | The module does not treat research approximation, visual mode, notebook objects, or derived exports as canonical execution or reporting artifacts. | Keep | Preserve this ownership exclusion. | It prevents cross-domain leakage and live-side effects. |
| V2-SIM-REQ-0018 | The module does not own live adapter implementation, live broker session management, live broker credentials, or imports of live execution modules; those must remain in Live/Trading/execution adapter ownership. | Keep | Preserve this ownership exclusion. | It prevents cross-domain leakage and live-side effects. |
| V2-SIM-REQ-0019 | The module does not own OS-level resource management such as process pools, thread-pool orchestration, global memory management, or platform scheduler policy beyond enforcing configured Simulation resource quotas and reporting quota diagnostics. | Keep | Preserve this ownership exclusion. | It prevents cross-domain leakage and live-side effects. |

### 3.1 Public Capabilities

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0020 | Expose the official AI tool boundary for `run_backtest`. | Add | Add the official versioned `run_backtest` tool or supporting Phase 1 contract behavior. | The V1 package exposes no working public API. |
| V2-SIM-REQ-0021 | Validate simulation configuration, strategy references, data dependencies, broker profiles, market-data authority manifests, realism requirements, and run permissions before execution. | Add | Add the official versioned `run_backtest` tool or supporting Phase 1 contract behavior. | The V1 package exposes no working public API. |
| V2-SIM-REQ-0022 | Run official tick-based backtests and return standard official tool envelopes. | Add | Add the official versioned `run_backtest` tool or supporting Phase 1 contract behavior. | The V1 package exposes no working public API. |
| V2-SIM-REQ-0023 | Produce `SimulationResult`, immutable journal artifacts, canonical JSON reports, required Markdown reports, derived CSV/HTML/visual replay artifacts where configured, and structured error responses. | Defer | Exclude from the initial public tool surface; add only through a later approved release. | The source itself makes these phase-gated and they are not needed for the core FX workflow. |
| V2-SIM-REQ-0024 | Provide simulation-compatible MT5-style accessors and trader methods for controlled strategy integration, including historical tick/bar accessors, symbol/account accessors, order submission/modification/deletion, position queries, order queries, deal/order history, margin/profit calculation, and terminal-style simulation status. | Add | Add the official versioned `run_backtest` tool or supporting Phase 1 contract behavior. | The V1 package exposes no working public API. |
| V2-SIM-REQ-0025 | Support optimization, walk-forward, Monte Carlo, bootstrap, deterministic replay, step-through replay, visual replay export, benchmark reporting, production-promotion manifests, and service-mode run lifecycle operations where enabled. | Defer | Exclude from the initial public tool surface; add only through a later approved release. | The source itself makes these phase-gated and they are not needed for the core FX workflow. |

### Public Capability Contract Requirements

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0026 | Before Builder handoff, each public simulator capability shall define name, purpose, caller type, stability level, official/internal status, request schema, response schema, deterministic error codes, side effects, required permissions, artifact behavior, network behavior, persistence behavior, compatibility guarantees, and at least one success and one deterministic-error example. | Open Decision | Complete the exact versioned contract before implementation; retain only fields required by the approved Phase 1 workflow. | The document explicitly marks the callable contract as pending. |
| V2-SIM-REQ-0027 | `run_backtest` shall define required fields, optional fields, defaults, enum values, unknown-field behavior, malformed-payload behavior, size limits, path resolution rules, validation order, authorization behavior, and artifact-root behavior before implementation. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0028 | `run_backtest` shall define response envelopes for `success`, `failed`, `queued`, `cancelled`, and `diagnostic_failed` statuses before implementation. | Open Decision | Complete the exact versioned contract before implementation; retain only fields required by the approved Phase 1 workflow. | The document explicitly marks the callable contract as pending. |
| V2-SIM-REQ-0029 | `SimulationResult`, official tool envelopes, artifact manifests, journal events, report JSON, broker profiles, and market-data authority manifests shall have schema references before Builder handoff. | Open Decision | Complete the exact versioned contract before implementation; retain only fields required by the approved Phase 1 workflow. | The document explicitly marks the callable contract as pending. |
| V2-SIM-REQ-0030 | Every MT5-style `SimTrader` method exposed to strategies shall define request fields, return fields, mutable-state effects, deterministic rejection codes, and read-only snapshot guarantees before implementation. | Open Decision | Complete the exact versioned contract before implementation; retain only fields required by the approved Phase 1 workflow. | The document explicitly marks the callable contract as pending. |
| V2-SIM-REQ-0031 | Optimization, walk-forward, Monte Carlo, visual replay export, production-promotion manifests, and service-mode lifecycle operations shall be implemented only when their requirements are explicitly tagged for the active release phase. | Defer | Exclude from the initial public tool surface; add only through a later approved release. | The source itself makes these phase-gated and they are not needed for the core FX workflow. |

### Draft `run_backtest` Contract Scaffold

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0032 | `SimulationBacktestRequestV1` fields: `schema_version`, `request_id`, `actor_context`, `strategy_ref`, `strategy_config`, `symbols`, `timeframe`, `start`, `end`, `initial_balance`, `account_currency`, `tick_model`, `spread_model`, `slippage_model`, `commission_model`, `swap_model`, `broker_profile_ref`, `market_data_authority_ref`, `journal_persistence`, `artifact_root_ref`, `realism_profile`, and `metadata`. | Add | Add the official versioned `run_backtest` tool or supporting Phase 1 contract behavior. | The V1 package exposes no working public API. |
| V2-SIM-REQ-0033 | `strategy_ref` shall be a registered strategy identifier plus version or hash; raw Python code strings are invalid. | Add | Add the official versioned `run_backtest` tool or supporting Phase 1 contract behavior. | The V1 package exposes no working public API. |
| V2-SIM-REQ-0034 | `actor_context` shall define authenticated actor identity and roles for any networked, multi-user, or agent-orchestrated invocation. | Open Decision | Complete the exact versioned contract before implementation; retain only fields required by the approved Phase 1 workflow. | The document explicitly marks the callable contract as pending. |
| V2-SIM-REQ-0035 | `market_data_authority_ref` shall reference an approved `MarketDataAuthorityManifest`; inline raw provider credentials are invalid. | Add | Add the official versioned `run_backtest` tool or supporting Phase 1 contract behavior. | The V1 package exposes no working public API. |
| V2-SIM-REQ-0036 | `broker_profile_ref` shall reference an approved broker profile manifest; inline broker credentials are invalid. | Add | Add the official versioned `run_backtest` tool or supporting Phase 1 contract behavior. | The V1 package exposes no working public API. |
| V2-SIM-REQ-0037 | `artifact_root_ref` shall resolve through an allowlisted root or registry entry, not an arbitrary filesystem path. | Add | Add the official versioned `run_backtest` tool or supporting Phase 1 contract behavior. | The V1 package exposes no working public API. |
| V2-SIM-REQ-0038 | `SimulationToolEnvelopeV1` fields: `schema_version`, `request_id`, `status`, `result`, `error`, `warnings`, `metadata`, and `artifacts`. | Add | Add the official versioned `run_backtest` tool or supporting Phase 1 contract behavior. | The V1 package exposes no working public API. |
| V2-SIM-REQ-0039 | `status` values shall include `success`, `failed`, `queued`, `cancelled`, and `diagnostic_failed` before implementation. | Modify | Keep a versioned envelope, but make `queued` conditional on a later asynchronous service mode. | A synchronous Phase 1 tool does not need queue semantics. |
| V2-SIM-REQ-0040 | `error` shall include deterministic `SIM_*` code, safe message, field path where applicable, severity, retryability, and redacted details. | Add | Add the official versioned `run_backtest` tool or supporting Phase 1 contract behavior. | The V1 package exposes no working public API. |
| V2-SIM-REQ-0041 | `metadata` shall include module, operation, tool risk level, side-effect classification, actor/audit references where authorized, engine version, config hash, data manifest hash, execution timing, and created timestamp. | Add | Add the official versioned `run_backtest` tool or supporting Phase 1 contract behavior. | The V1 package exposes no working public API. |

### 1.1 Simulation Orchestration

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0042 | The system shall provide a `BacktestOrchestrator` that validates configuration and data dependencies before executing a simulation. | Modify | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0043 | The system shall run data-quality checks before indicator calculation, signal generation, or tick generation. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0044 | The system shall build indicator and signal data before constructing the executable signal timeline. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0045 | The system shall align bar-based signals using the configured signal timing policy. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0046 | The system shall build a canonical bid/ask tick stream before official execution. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0047 | The system shall execute official backtests through the tick-based `EventDrivenExecutionEngine`. | Modify | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0048 | The system shall produce a structured `SimulationResult`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0049 | The system shall produce a report from the immutable journal and computed metrics. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.2 Canonical Tick-Based Execution

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0050 | The system shall use tick execution as the only official production execution mode. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0051 | The system shall use the canonical bid/ask tick stream as the official execution clock. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0052 | The system shall convert bar-level or vectorized signals into timestamped `TradeIntent` objects before execution. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0053 | The system shall execute `TradeIntent` objects only when the tick loop reaches an eligible tick. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0054 | The system shall prevent vectorized execution from producing official fills, account state, trade journals, or reports. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0055 | The system shall support an optional approximate `FAST_RESEARCH` mode only when the result is clearly marked as non-canonical, non-MT5-parity, and non-production-realistic. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |

### 1.3 Signal Timing and No-Lookahead

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0056 | The system shall use `BAR_OPEN_PREVIOUS_CLOSE` as the default signal timing policy. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0057 | At the first tick of bar `N`, the system shall allow strategies to use only bars up to and including fully closed bar `N-1`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0058 | At the first tick of bar `N`, the system shall prohibit use of current incomplete bar `N` high, low, close, or volume. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0059 | The system shall enter at the first valid tick of bar `N` when a valid trade intent is emitted from previous-closed-bar data. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0060 | The system shall reject or flag lookahead usage in bar-open strategies. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0061 | The system shall require vectorized signal generation to shift current-bar conditions so that bar-open entries are based on previous closed-bar values. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0062 | The system shall support `INTRABAR_EVENT` strategies only for event strategies using current tick data. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0063 | At the first tick of bar `N`, the engine shall mask, drop, or reject any raw OHLCV data point with timestamp greater than or equal to bar `N` open time. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0064 | At the first tick of bar `N`, the engine shall mask, drop, or reject any indicator-derived data point with timestamp greater than or equal to bar `N` open time. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0065 | At the first tick of bar `N`, the engine shall mask, drop, or reject any multi-timeframe aligned data point with timestamp greater than or equal to bar `N` open time. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0066 | At the first tick of bar `N`, the engine shall mask, drop, or reject strategy metadata used for sizing or trade decisions when that metadata depends on data with timestamp greater than or equal to bar `N` open time. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0067 | The engine shall raise `SIM_LOOKAHEAD_DETECTED` when a strategy attempts to access prohibited current-bar or future data during first-tick processing for bar `N`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.4 Tick Models

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0068 | The system shall support `TIMEFRAME_TICKS`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0069 | The system shall support `M1_TICKS`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0070 | The system shall support `REAL_TICKS`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0071 | The system shall support `SYNTHETIC_TICKS`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0072 | The system shall represent every execution tick with time, symbol, bid, ask, optional last price, optional volume, source, optional bar time, sequence-in-bar, and bar-open flag. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0073 | The system shall open buy positions at ask. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0074 | The system shall close buy positions at bid. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0075 | The system shall open sell positions at bid. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0076 | The system shall close sell positions at ask. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0077 | The system shall convert strategy-timeframe OHLC bars into four-tick paths when using `TIMEFRAME_TICKS`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0078 | The system shall convert M1 OHLC bars into four-tick paths when using `M1_TICKS`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0079 | The system shall pass broker real ticks through in `REAL_TICKS` mode when bid/ask data is available. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0080 | The system shall merge bar-based signal timelines into the real tick stream in `REAL_TICKS` mode. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0081 | The system shall generate `SYNTHETIC_TICKS` from M1 OHLCV bars using an MQL5 Article #75-style support-point algorithm, not a simple four-price path. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0082 | The system shall treat generated OHLC-derived synthetic prices as bid prices and derive ask prices through the spread model. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0083 | The system shall produce deterministic synthetic ticks for identical M1 data, symbol spec, spread config, and random seed. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0084 | Synthetic tick generation shall derive a deterministic per-bar seed instead of relying only on a single mutable global random sequence. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0085 | The per-bar synthetic-tick seed shall be derived with SHA-256 from schema version, `global_seed`, `symbol_hash`, UTC `bar_open_timestamp`, and synthetic tick algorithm version. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0086 | `symbol_hash` shall be derived from the canonical JSON representation of the full `SymbolSpec`, including normalized symbol, broker profile id, point, tick size, tick value, contract size, currencies, sessions, and volume constraints. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0087 | Synthetic tick generation shall remain reproducible when bars are processed out of chronological order. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0088 | Synthetic tick generation shall remain reproducible when bars are processed in date chunks or parallelized by symbol. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0089 | Synthetic tick generation shall remain reproducible when a run resumes from a checkpoint. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0090 | Synthetic tick generation shall journal or expose per-bar seed derivation metadata sufficient to replay a generated bar's tick path. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0091 | The simulator shall support data modelling modes equivalent to real ticks, simulated ticks, M1 OHLC, trading-timeframe OHLC, and calculation-only research data where explicitly labelled. | Modify | Permit only clearly labelled non-canonical FAST_RESEARCH output with no official fills or reports. | Research acceleration must not blur canonical execution. |
| V2-SIM-REQ-0092 | The simulator shall expose MT5-style historical tick accessors `copy_ticks_from` and `copy_ticks_range` for simulation-compatible data providers. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0093 | The simulator shall expose MT5-style historical bar accessors `copy_rates_from`, `copy_rates_from_pos`, and `copy_rates_range` for simulation-compatible data providers. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0094 | The simulator shall expose MT5-style `symbol_info_tick` and `symbol_info` accessors for simulation-compatible symbol metadata and latest tick state. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.5 Spread Models

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0095 | The system shall support `NATIVE_SPREAD`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0096 | The system shall support `FIXED_SPREAD`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0097 | The system shall support `VARIABLE_SPREAD`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0098 | The system shall calculate ask for generated ticks as bid plus spread points multiplied by symbol point. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0099 | The system shall validate that spreads are non-negative. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0100 | The system shall reject or explicitly repair missing spread data according to configuration. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0101 | The system shall generate variable spreads deterministically using configured min/max spread and random seed. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0102 | The system shall record spread source and spread points per tick or journal checkpoint. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.6 Execution Realism

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0103 | The system shall provide an `ExecutionRealismConfig` containing liquidity, slippage, latency, commission, swap, borrow-fee, market-hours, gap-handling, broker-rules, portfolio-risk, data-quality, corporate-action, futures-rollover, perpetual-funding, and currency-conversion configuration. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0104 | The system shall allow simplified realism modes only when explicitly configured. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0105 | The system shall prevent production-realistic labelling when infinite liquidity, no slippage, no commission, no swap, or disabled portfolio checks are used without appropriate disclosure. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0106 | The system shall disclose every enabled, disabled, or simplified realism model in the final report. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0107 | The system shall support configurable execution latency models covering strategy computation delay, broker or network routing delay, venue or exchange gateway delay, and matching-engine delay. | Defer | Support disabled/fixed latency first; add richer calibrated latency only with evidence. | The advanced model is premature. |
| V2-SIM-REQ-0108 | Latency models shall support fixed, distribution-based, venue-profile-based, and disabled modes. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |
| V2-SIM-REQ-0109 | Trade intents shall become eligible for matching only after the configured latency delay has elapsed on the canonical tick clock. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0110 | Latency diagnostics shall record signal timestamp, request timestamp, eligible execution timestamp, latency components, and latency model id. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.7 Liquidity and Order Book

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0111 | The system shall support infinite liquidity for MT5-parity or early research use only. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0112 | The system shall support fixed-slippage liquidity mode. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0113 | The system shall support volume-dependent liquidity mode. | Defer | Start with infinite/fixed deterministic liquidity and explicit realism downgrade. | Depth-dependent realism lacks an approved Phase 1 data contract. |
| V2-SIM-REQ-0114 | The system shall support order-book liquidity mode where depth data is available. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |
| V2-SIM-REQ-0115 | The system shall estimate available volume from tick volume, M1 volume, or configured symbol liquidity when using volume-dependent liquidity. | Defer | Start with infinite/fixed deterministic liquidity and explicit realism downgrade. | Depth-dependent realism lacks an approved Phase 1 data contract. |
| V2-SIM-REQ-0116 | The system shall walk order-book levels and calculate VWAP execution price when using order-book liquidity. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |
| V2-SIM-REQ-0117 | The system shall produce diagnostics for requested volume, filled volume, unfilled volume, VWAP, slippage points, and market impact. | Defer | Start with infinite/fixed deterministic liquidity and explicit realism downgrade. | Depth-dependent realism lacks an approved Phase 1 data contract. |
| V2-SIM-REQ-0118 | The system shall make liquidity decisions deterministically for the same tick, configuration, seed, and order request. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0119 | When volume-dependent liquidity and slippage models are both active, liquidity constraints shall be evaluated before slippage. | Defer | Start with infinite/fixed deterministic liquidity and explicit realism downgrade. | Depth-dependent realism lacks an approved Phase 1 data contract. |
| V2-SIM-REQ-0120 | Partial-fill diagnostics shall separately record requested volume, filled volume, unfilled volume, liquidity impact, slippage impact, and cancelled or pending remainder. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0121 | Execution-quality metrics shall distinguish liquidity shortfall from slippage cost. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.8 Slippage

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0122 | The system shall support no slippage. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0123 | The system shall support fixed-point slippage. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0124 | The system shall support spread-relative slippage. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0125 | The system shall support volatility-based slippage. | Defer | Start with none/fixed/spread-relative deterministic slippage. | Advanced slippage requires calibration and extra data. |
| V2-SIM-REQ-0126 | The system shall support volume-dependent slippage. | Defer | Start with none/fixed/spread-relative deterministic slippage. | Advanced slippage requires calibration and extra data. |
| V2-SIM-REQ-0127 | The system shall support queue-position slippage. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |
| V2-SIM-REQ-0128 | The system shall apply slippage after spread and before final fill-price acceptance. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0129 | The system shall apply slippage directionally so that it worsens execution price according to order direction. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0130 | The system shall cap slippage when a maximum slippage is configured. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0131 | The system shall use deterministic seeded randomness when randomized slippage is enabled. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0132 | The system shall journal expected price, executable bid/ask, slippage points, and final fill price. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0133 | Slippage shall apply only to actually filled volume after liquidity constraints determine fillable quantity. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0134 | Slippage shall not be charged, journaled as cost, or attributed to an unfilled remainder. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.9 Fill Policies and Partial Fills

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0135 | The system shall support `FOK`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0136 | The system shall support `IOC`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0137 | The system shall support `RETURN`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0138 | The system shall support explicit partial-fill behavior. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0139 | The system shall reject `FOK` orders when full requested volume is unavailable. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0140 | The system shall fill available volume and cancel the remainder for `IOC` orders. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0141 | The system shall keep unfilled `RETURN` remainders pending only when the broker or symbol supports it. | Defer | Support FOK/IOC first; add RETURN remainder persistence after exact order-lifecycle contracts are approved. | Not necessary for the minimal initial engine. |
| V2-SIM-REQ-0142 | The system shall create a separate deal record for every partial fill. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0143 | The system shall recalculate position average price from actual filled volumes and prices. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0144 | The system shall update margin, exposure, commission, and risk immediately after partial fills. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0145 | When an `IOC` order is partially filled, the unfilled remainder shall be cancelled. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0146 | When an `IOC` order remainder is cancelled, the system shall journal `SIM_IOC_REMAINDER_CANCELLED` as a non-fatal diagnostic event. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0147 | `SIM_IOC_REMAINDER_CANCELLED` shall not be treated as a fatal simulation error when the partial fill itself is valid. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0148 | Reports shall include IOC remainder cancellations in execution-quality diagnostics. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.10 Limit Order Queue Handling

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0149 | The system shall support configurable limit-order queue behavior. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0150 | The system shall not guarantee a limit-order fill merely because price touches the limit unless touch-fill is enabled and liquidity is available. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0151 | The system shall reduce available fill volume by estimated or configured queue-ahead volume. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0152 | The system shall resolve FIFO and pro-rata behavior deterministically. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0153 | The system may document hidden-order and iceberg support while keeping them disabled until order-book data is available. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |
| V2-SIM-REQ-0154 | Before Phase 1 Builder handoff, limit-order queue configuration shall explicitly define valid values for `queue_model`, `touch_fill_enabled`, `queue_ahead_volume`, `queue_ahead_estimation_method`, `fill_allocation_method`, `minimum_fill_volume`, and `partial_fill_policy`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0155 | Phase 1 queue behavior shall be limited to deterministic `touch_fill_enabled=false` rejection or deterministic configured queue-ahead reduction unless the owner approves richer order-book queue realism. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |
| V2-SIM-REQ-0156 | Hidden-order and iceberg reservation behavior shall be `[PHASE2]` and must return deterministic unsupported-scope diagnostics if requested during Phase 1. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |

### 1.11 Market Hours, Weekends, and Gaps

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0157 | The system shall support market-hours configuration including session start, session end, timezone, weekend closure, holiday calendar, and 24/7 asset flag. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0158 | The system shall detect market open and closed state. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0159 | The system shall detect session breaks, weekends, holidays, and rollover boundaries. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0160 | The system shall detect market-wide halts, exchange halts, symbol halts, and limit-up/limit-down states when halt data is available. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |
| V2-SIM-REQ-0161 | The system shall mark the first tick after a session break or weekend as a gap tick. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0162 | The system shall prevent market orders outside allowed sessions unless explicitly configured for 24/7 assets. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0163 | The system shall prevent or defer trading during market halts and limit-up/limit-down states according to exchange and broker policy. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |
| V2-SIM-REQ-0164 | The system shall support gap handling by rejection. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0165 | The system shall support gap handling by fill at open. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0166 | The system shall support gap handling by fill with slippage. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0167 | The system shall support treating gap-crossed stop losses as market orders at the first available tick. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0168 | The system shall use the conservative worse outcome by default when both SL and TP are crossed in the same ambiguous gap. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0169 | The system shall record gap-handling rules in the report. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0170 | Before Phase 1 Builder handoff, gap configuration shall explicitly define `gap_policy`, `ambiguous_sl_tp_policy`, `fill_price_source`, `gap_slippage_model`, `max_gap_fill_slippage_points`, and `session_calendar_ref`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0171 | The default `ambiguous_sl_tp_policy` shall be `conservative_worst_outcome`, meaning the engine selects the lower resulting account equity after applying valid SL-first and TP-first interpretations under the same first-available-tick and cost model. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0172 | Gap ambiguity handling shall journal candidate outcomes, selected outcome, rejected alternative, first available tick, affected order ids, and the deterministic reason code. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.12 Same-Tick Event Priority

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0173 | The system shall process same-tick events through a deterministic priority queue. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0174 | The system shall order same-tick events by tick time, explicit priority, and monotonic sequence number. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0175 | The system shall process stopout before other same-tick events by default. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0176 | The system shall process expiration before new triggers for the same timestamp. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0177 | The system shall process existing position exits before new signal intents by default. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0178 | The system shall use conservative SL/TP tie-breaking by default unless another mode is explicitly configured. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0179 | The system shall journal priority decisions for replay. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.13 Commission, Fees, and Rebates

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0180 | The system shall support no commission. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0181 | The system shall support per-lot commission. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0182 | The system shall support per-trade commission. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0183 | The system shall support percent-notional commission. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0184 | The system shall support tiered commission. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |
| V2-SIM-REQ-0185 | The system shall support maker/taker commission. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |
| V2-SIM-REQ-0186 | The system shall support pass-through regulatory, exchange, clearing, transaction, activity, and rebate fee models when configured. | Defer | Support no/per-lot/per-trade/percent-notional FX commissions first. | Advanced venue fees are out of Phase 1. |
| V2-SIM-REQ-0187 | US equity and ETF fee models may include SEC Section 31 fees, FINRA TAF, exchange-specific maker/taker fees or rebates, and payment-for-order-flow disclosure where relevant. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0188 | The system shall apply minimum and maximum commission limits when configured. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0189 | The system shall calculate commission per actual fill, not only per requested order. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0190 | The system shall support commission currency conversion when account currency differs. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0191 | The system shall include spread, slippage, commission, fees, swap, borrow fees, dividends, funding, and configured cashflows in net PnL. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0192 | The system shall report gross PnL, total costs, and net PnL. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.14 Swap and Rollover

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0193 | The system shall support swap types in points, money, percent, and interest. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0194 | The system shall support daily end-of-day, tick-by-tick, and on-close-only swap calculation modes. | Defer | Implement approved daily FX rollover/triple-swap behavior first. | Additional accrual modes are not required initially. |
| V2-SIM-REQ-0195 | The system shall apply swap only to positions open across the configured rollover boundary. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0196 | The system shall support configurable triple-swap day per symbol. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0197 | The system shall journal swap charges and credits. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0198 | The system shall reflect swap in account balance and equity. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0199 | The system shall label overnight backtests with disabled swap as cost-incomplete. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.15 Broker Rules

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0200 | The system shall enforce margin-call percentage. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0201 | The system shall enforce stop-out percentage. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0202 | The system shall enforce maximum pending orders. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0203 | The system shall enforce maximum total positions when configured. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0204 | The system shall enforce maximum positions per symbol when configured. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0205 | The system shall reject unsupported fill policies with deterministic error codes. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0206 | The system shall support hedging account behavior when configured. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0207 | The system shall support netting account behavior when configured. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0208 | The system shall support negative-balance-protection configuration. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0209 | The system shall liquidate deterministically during stopout, defaulting to largest losing position first. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0210 | Initial MT5 parity tests shall use a versioned broker profile named `mt5_demo_reference_fx_v1`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0211 | Broker profiles shall capture symbol rules, sessions, swap rules, margin rules, fee rules, fill policies, precision, and supported order types. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0212 | MT5 parity evidence shall record broker profile id, broker server label, account type, MT5 build, capture timestamp, symbol specification hash, and fixture data hash. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0213 | No external broker brand or live account shall be globally authoritative; production parity applies only to approved broker profiles and fixtures. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.16 Portfolio Risk and Margin

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0214 | The system shall maintain portfolio-level state for multi-symbol backtests. | Add | Maintain deterministic portfolio/account exposure and FX margin state required by execution. | Multi-symbol FX simulation needs this execution state. |
| V2-SIM-REQ-0215 | The system shall calculate gross exposure. | Add | Maintain deterministic portfolio/account exposure and FX margin state required by execution. | Multi-symbol FX simulation needs this execution state. |
| V2-SIM-REQ-0216 | The system shall calculate net exposure. | Add | Maintain deterministic portfolio/account exposure and FX margin state required by execution. | Multi-symbol FX simulation needs this execution state. |
| V2-SIM-REQ-0217 | The system shall calculate currency exposure. | Add | Maintain deterministic portfolio/account exposure and FX margin state required by execution. | Multi-symbol FX simulation needs this execution state. |
| V2-SIM-REQ-0218 | The system shall calculate margin contribution by symbol. | Add | Maintain deterministic portfolio/account exposure and FX margin state required by execution. | Multi-symbol FX simulation needs this execution state. |
| V2-SIM-REQ-0219 | The system shall calculate concentration. | Modify | Apply a supplied simulation risk profile/decision contract and journal outcomes; policy and analytics remain in Risk. | Risk policy ownership is outside Simulation. |
| V2-SIM-REQ-0220 | The system shall support optional VaR values. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0221 | The system shall validate portfolio risk after sizing and before matching. | Modify | Apply a supplied simulation risk profile/decision contract and journal outcomes; policy and analytics remain in Risk. | Risk policy ownership is outside Simulation. |
| V2-SIM-REQ-0222 | The system shall support independent-symbol margin. | Add | Maintain deterministic portfolio/account exposure and FX margin state required by execution. | Multi-symbol FX simulation needs this execution state. |
| V2-SIM-REQ-0223 | The system shall support netted FX margin. | Add | Maintain deterministic portfolio/account exposure and FX margin state required by execution. | Multi-symbol FX simulation needs this execution state. |
| V2-SIM-REQ-0224 | The system shall support cross-margin. | Defer | Defer advanced margin regimes; Phase 1 supports approved FX margin behavior only. | Not needed for the initial FX slice. |
| V2-SIM-REQ-0225 | The system shall support SPAN-like margin mode. | Defer | Defer advanced margin regimes; Phase 1 supports approved FX margin behavior only. | Not needed for the initial FX slice. |
| V2-SIM-REQ-0226 | The system shall enforce correlation limits when enabled. | Modify | Apply a supplied simulation risk profile/decision contract and journal outcomes; policy and analytics remain in Risk. | Risk policy ownership is outside Simulation. |
| V2-SIM-REQ-0227 | The system shall enforce concentration limits when enabled. | Modify | Apply a supplied simulation risk profile/decision contract and journal outcomes; policy and analytics remain in Risk. | Risk policy ownership is outside Simulation. |
| V2-SIM-REQ-0228 | The system shall enforce gross, symbol, and cluster exposure limits when enabled. | Add | Maintain deterministic portfolio/account exposure and FX margin state required by execution. | Multi-symbol FX simulation needs this execution state. |
| V2-SIM-REQ-0229 | The system shall evaluate pair, basket, grid, and martingale strategies at portfolio level. | Modify | Apply a supplied simulation risk profile/decision contract and journal outcomes; policy and analytics remain in Risk. | Risk policy ownership is outside Simulation. |
| V2-SIM-REQ-0230 | The system shall support portfolio-level kill switches that halt new trading when configured drawdown, loss, exposure, margin, volatility, or error thresholds are breached. | Modify | Apply a supplied simulation risk profile/decision contract and journal outcomes; policy and analytics remain in Risk. | Risk policy ownership is outside Simulation. |
| V2-SIM-REQ-0231 | Kill-switch events shall liquidate, block new orders, cancel pending orders, or enter monitor-only mode according to configuration. | Add | Maintain deterministic portfolio/account exposure and FX margin state required by execution. | Multi-symbol FX simulation needs this execution state. |
| V2-SIM-REQ-0232 | Kill-switch decisions shall be journaled with threshold, observed value, action, and actor or policy id. | Add | Maintain deterministic portfolio/account exposure and FX margin state required by execution. | Multi-symbol FX simulation needs this execution state. |

### 1.17 Data Quality

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0233 | The system shall validate OHLCV and tick schemas. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0234 | The system shall detect missing required columns. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0235 | The system shall detect missing bars. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0236 | The system shall detect duplicate timestamps. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0237 | The system shall detect non-monotonic timestamps. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0238 | The system shall detect negative spreads. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0239 | The system shall detect zero or negative prices. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0240 | The system shall detect price outliers. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0241 | The system shall detect impossible OHLC bars. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0242 | The system shall produce a `DataQualityReport`. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0243 | The system shall block production runs when severe data-quality thresholds fail unless diagnostic mode is explicitly enabled. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0244 | The system shall include the data-quality report in the final report. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0245 | Production simulations shall consume normalized data through the data module contract and an approved `MarketDataAuthorityManifest`. | Modify | Consume and validate a Data-owned manifest; do not own provider policy or source acquisition. | The contract is required, but ownership must remain in Data. |
| V2-SIM-REQ-0246 | The `MarketDataAuthorityManifest` shall declare authoritative sources for bars, real ticks, spreads, corporate actions, futures chains, funding rates, FX conversion rates, and benchmark series. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0247 | Missing or staging-only authoritative data shall block a production-realistic label unless the affected model is proven unnecessary for the selected instruments. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0248 | The system shall define a `PartialDataPolicy` for incomplete provider files or partial symbol-day data. | Modify | Consume and validate a Data-owned manifest; do not own provider policy or source acquisition. | The contract is required, but ownership must remain in Data. |
| V2-SIM-REQ-0249 | `PartialDataPolicy` shall support quarantining the affected symbol and date with `SIM_DATA_PARTIAL`, using stale prior data with `SIM_DATA_STALE` and a configurable staleness limit, or failing the entire run. | Modify | Consume and validate a Data-owned manifest; do not own provider policy or source acquisition. | The contract is required, but ownership must remain in Data. |
| V2-SIM-REQ-0250 | Stale-data recovery shall be unavailable for production-realistic classification unless explicitly approved and disclosed. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0251 | The system shall record queryable data lineage for every data point used in fill-price, mark-to-market, margin, fee, swap, funding, dividend, benchmark, and PnL calculations. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0252 | Data lineage shall form a directed acyclic graph tracing from journaled deal or account event to generated tick, support point, M1 bar, normalized source row, raw vendor data file, source manifest, and checksum where applicable. | Defer | Keep in Data/Future Extensions; Simulation only validates referenced immutable manifests and execution suitability. | This is data-platform scope, not the minimal simulator. |
| V2-SIM-REQ-0253 | Data lineage shall be queryable for audit, replay, model validation, and production-promotion evidence. | Defer | Keep in Data/Future Extensions; Simulation only validates referenced immutable manifests and execution suitability. | This is data-platform scope, not the minimal simulator. |
| V2-SIM-REQ-0254 | The market-data authority client shall support a warm cache for frequently read immutable or rarely changed datasets. | Defer | Keep in Data/Future Extensions; Simulation only validates referenced immutable manifests and execution suitability. | This is data-platform scope, not the minimal simulator. |
| V2-SIM-REQ-0255 | Warm data cache keys shall include `DataManifestHash`, provider id, dataset id, symbol, timeframe, date range, adjustment mode, and schema version. | Defer | Keep in Data/Future Extensions; Simulation only validates referenced immutable manifests and execution suitability. | This is data-platform scope, not the minimal simulator. |
| V2-SIM-REQ-0256 | Cache hits shall skip network transfer only after validating the cached artifact checksum against the authoritative manifest. | Add | Add deterministic simulation-entry data checks and block severe invalid inputs before execution. | The V1 package has no working gate. |
| V2-SIM-REQ-0257 | Cache entries shall expire according to a configured TTL and shall never override point-in-time data snapshot requirements. | Defer | Keep in Data/Future Extensions; Simulation only validates referenced immutable manifests and execution suitability. | This is data-platform scope, not the minimal simulator. |
| V2-SIM-REQ-0258 | The simulator shall support optional feature-store integration for machine-learning features. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0259 | Feature-store integration shall default to disabled in Phase 1. If enabled in a later approved phase, it MUST enforce point-in-time correctness, feature availability timestamps, publication lag, ingestion lag, and deterministic `SIM_FEATURE_LOOKAHEAD_DETECTED` rejection before any feature can influence a decision. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0260 | Feature-store retrieval shall enforce point-in-time correctness at the canonical decision timestamp, including sub-second or microsecond availability timestamps where provided. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0261 | Feature-store retrieval shall reject or mask any feature whose computation or publication time is later than the strategy decision time. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0262 | Alternative data inputs such as sentiment, fundamentals, news, options flow, and external signals shall include event time, ingestion time, publication time, source id, and availability timestamp. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0263 | Alternative data shall align to the canonical tick clock without lookahead, using explicit as-of joins and configured lag or embargo policies. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |

### 1.18 Position Sizing

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0264 | The system shall centralize final position sizing in the engine. | Modify | Simulation normalizes and validates executable volume; sizing policy originates from Strategy/Risk contracts. | Final execution volume belongs here, but policy ownership does not. |
| V2-SIM-REQ-0265 | The system shall allow strategies to request a sizing mode but not directly finalize official volume. | Modify | Simulation normalizes and validates executable volume; sizing policy originates from Strategy/Risk contracts. | Final execution volume belongs here, but policy ownership does not. |
| V2-SIM-REQ-0266 | The system shall support fixed-lot sizing. | Add | Add deterministic Phase 1 volume calculation/normalization and explicit rejection behavior. | Required for official simulated fills. |
| V2-SIM-REQ-0267 | The system shall support fixed-risk sizing. | Add | Add deterministic Phase 1 volume calculation/normalization and explicit rejection behavior. | Required for official simulated fills. |
| V2-SIM-REQ-0268 | The system shall support milestone sizing. | Defer | Defer advanced sizing policies; accept only approved simple sizing requests initially. | No confirmed workflow requires these policies in the first slice. |
| V2-SIM-REQ-0269 | The system shall support Kelly-criterion sizing. | Defer | Defer advanced sizing policies; accept only approved simple sizing requests initially. | No confirmed workflow requires these policies in the first slice. |
| V2-SIM-REQ-0270 | The system shall support volatility-based sizing. | Add | Add deterministic Phase 1 volume calculation/normalization and explicit rejection behavior. | Required for official simulated fills. |
| V2-SIM-REQ-0271 | The system shall support fixed-fractional sizing. | Add | Add deterministic Phase 1 volume calculation/normalization and explicit rejection behavior. | Required for official simulated fills. |
| V2-SIM-REQ-0272 | The system shall reject fixed-risk sizing when stop loss is missing. | Add | Add deterministic Phase 1 volume calculation/normalization and explicit rejection behavior. | Required for official simulated fills. |
| V2-SIM-REQ-0273 | The system shall reject zero or negative stop distance. | Add | Add deterministic Phase 1 volume calculation/normalization and explicit rejection behavior. | Required for official simulated fills. |
| V2-SIM-REQ-0274 | The system shall reject missing tick value or point value when required for sizing. | Add | Add deterministic Phase 1 volume calculation/normalization and explicit rejection behavior. | Required for official simulated fills. |
| V2-SIM-REQ-0275 | The system shall reject missing or invalid Kelly inputs. | Defer | Defer advanced sizing policies; accept only approved simple sizing requests initially. | No confirmed workflow requires these policies in the first slice. |
| V2-SIM-REQ-0276 | The system shall reject missing, zero, negative, or misaligned ATR values for volatility sizing. | Add | Add deterministic Phase 1 volume calculation/normalization and explicit rejection behavior. | Required for official simulated fills. |
| V2-SIM-REQ-0277 | The system shall normalize volume using symbol minimum, maximum, and step constraints. | Add | Add deterministic Phase 1 volume calculation/normalization and explicit rejection behavior. | Required for official simulated fills. |
| V2-SIM-REQ-0278 | The system shall support explicit volume rounding policies. | Add | Add deterministic Phase 1 volume calculation/normalization and explicit rejection behavior. | Required for official simulated fills. |
| V2-SIM-REQ-0279 | The system shall default to floor-to-step rounding. | Add | Add deterministic Phase 1 volume calculation/normalization and explicit rejection behavior. | Required for official simulated fills. |
| V2-SIM-REQ-0280 | The system shall record raw and normalized volume and shall not silently adjust volume. | Add | Add deterministic Phase 1 volume calculation/normalization and explicit rejection behavior. | Required for official simulated fills. |

### 1.19 Trade Requests and Trader Interface

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0281 | The system shall transform `TradeIntent` into a sized `TradeRequest`. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0282 | The system shall support MT5-style `order_send`. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0283 | `order_send` shall accept action, magic, order, symbol, volume, price, stop-limit price, stop loss, take profit, deviation, order type, fill policy, time policy, expiration, comment, position id, and opposite position id where supported by account mode. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0284 | The system shall support position modification. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0285 | The system shall expose MT5-style `position_modify` for stop-loss, take-profit, and supported mutable position fields. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0286 | The system shall support position close. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0287 | The system shall expose MT5-style `position_close`. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0288 | The system shall support order modification. | Defer | Phase 1 may return deterministic unsupported-scope responses until exact contracts are approved. | The API scaffold explicitly leaves these methods deferred. |
| V2-SIM-REQ-0289 | The system shall expose MT5-style `order_modify` for pending-order price, stop-limit price, stop loss, take profit, expiration mode, and expiration timestamp. | Defer | Phase 1 may return deterministic unsupported-scope responses until exact contracts are approved. | The API scaffold explicitly leaves these methods deferred. |
| V2-SIM-REQ-0290 | The system shall support order deletion. | Defer | Phase 1 may return deterministic unsupported-scope responses until exact contracts are approved. | The API scaffold explicitly leaves these methods deferred. |
| V2-SIM-REQ-0291 | The system shall expose MT5-style `order_delete`. | Defer | Phase 1 may return deterministic unsupported-scope responses until exact contracts are approved. | The API scaffold explicitly leaves these methods deferred. |
| V2-SIM-REQ-0292 | The system shall support atomic cancel-replace operations for pending orders where broker or venue semantics allow them. | Defer | Phase 1 may return deterministic unsupported-scope responses until exact contracts are approved. | The API scaffold explicitly leaves these methods deferred. |
| V2-SIM-REQ-0293 | Cancel-replace operations shall preserve, reset, or recompute queue priority according to configured venue rules and shall journal the chosen behavior. | Defer | Phase 1 may return deterministic unsupported-scope responses until exact contracts are approved. | The API scaffold explicitly leaves these methods deferred. |
| V2-SIM-REQ-0294 | The system shall support querying open positions. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0295 | The system shall expose MT5-style `positions_get` and `positions_total`. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0296 | The system shall support querying open orders. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0297 | The system shall expose MT5-style `orders_get` and `orders_total`. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0298 | The system shall support querying historical deals. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0299 | The system shall expose MT5-style `history_deals_get` and `deals_total`. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0300 | The system shall support querying historical orders. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0301 | The system shall expose MT5-style `history_orders_get` and `history_orders_total`. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0302 | The system shall support querying account info. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0303 | The system shall expose MT5-style `account_info`. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0304 | The system shall expose MT5-style `order_calc_margin` for pre-trade margin estimation. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0305 | The system shall expose MT5-style `order_calc_profit` for mark-to-market or hypothetical trade profit estimation. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0306 | The same Trader protocol shall support both simulation and live adapters where live trading is enabled outside the simulator. | Modify | Implement only the simulated side of an externally owned shared Trader contract; never import live implementations. | Shared semantics are useful, but ownership is cross-domain. |
| V2-SIM-REQ-0307 | The simulated Trader protocol shall preserve the same request, response, and query semantics as the live adapter for shared strategy code. | Modify | Implement only the simulated side of an externally owned shared Trader contract; never import live implementations. | Shared semantics are useful, but ownership is cross-domain. |
| V2-SIM-REQ-0308 | Shared Trader protocol definitions may be shared across Simulation and Live/Trading, but Simulation shall implement only simulated behavior and shall not import, instantiate, or call live adapter implementation code. | Modify | Implement only the simulated side of an externally owned shared Trader contract; never import live implementations. | Shared semantics are useful, but ownership is cross-domain. |
| V2-SIM-REQ-0309 | The system shall support `on_tick` callbacks for event-driven strategy execution. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0310 | The system shall support `on_bar` callbacks for bar-boundary strategy execution. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0311 | The system shall provide a terminal-style interface for simulation status, account state, open positions, pending orders, and trade events. | Add | Add the minimal simulated Trader mutations/queries required by registered strategies and the tick engine. | No working V1 provider exists. |
| V2-SIM-REQ-0312 | Terminal-style output shall be controlled by an explicit `verbose` configuration flag. | Defer | Exclude diagnostic UI/debug service features from the initial canonical engine. | Useful later but not necessary to answer the core backtest workflow. |
| V2-SIM-REQ-0313 | Visual simulation mode shall be supported only as a diagnostic or research view and shall not alter canonical execution results. | Defer | Exclude diagnostic UI/debug service features from the initial canonical engine. | Useful later but not necessary to answer the core backtest workflow. |
| V2-SIM-REQ-0314 | Progress reporting shall be available for long-running official simulations, optimizations, walk-forward runs, and Monte Carlo runs. | Defer | Exclude diagnostic UI/debug service features from the initial canonical engine. | Useful later but not necessary to answer the core backtest workflow. |
| V2-SIM-REQ-0315 | The system shall support deterministic step-through replay for debugging. | Defer | Exclude diagnostic UI/debug service features from the initial canonical engine. | Useful later but not necessary to answer the core backtest workflow. |
| V2-SIM-REQ-0316 | Step-through replay shall allow pausing at a configured timestamp, journal sequence, order event, deal event, bar boundary, strategy callback, or error condition. | Defer | Exclude diagnostic UI/debug service features from the initial canonical engine. | Useful later but not necessary to answer the core backtest workflow. |
| V2-SIM-REQ-0317 | Debugger hooks shall expose read-only snapshots of tick state, order book where available, orders, deals, positions, account state, strategy-visible inputs, and selected strategy diagnostics. | Defer | Exclude diagnostic UI/debug service features from the initial canonical engine. | Useful later but not necessary to answer the core backtest workflow. |
| V2-SIM-REQ-0318 | Resuming from a debugger pause shall preserve deterministic replay and shall not alter official results unless a diagnostic mutation mode is explicitly enabled. | Defer | Exclude diagnostic UI/debug service features from the initial canonical engine. | Useful later but not necessary to answer the core backtest workflow. |

### 1.20 State Containers and Trade Objects

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0319 | The engine shall maintain an authoritative positions container for open positions. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0320 | The engine shall maintain an authoritative orders container for active pending orders. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0321 | The engine shall maintain an authoritative deals container for executed deal records. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0322 | Position records shall include time, id, magic, symbol, side or type, volume, open price, current price, stop loss, take profit, commission, margin required, fee, swap, profit, and comment. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0323 | Pending-order records shall include all applicable position record fields plus order price, stop-limit price, expiry date, and expiration mode. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0324 | Deal records shall include all applicable position record fields plus deal reason, deal direction, order id, position id, fill price, filled volume, and execution timestamp. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0325 | Trade-info snapshots shall include time, id, magic, symbol, side or type, volume, price, stop loss, take profit, commission, fee, swap, profit, comment, and margin required. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0326 | State containers shall be mutated only by the execution engine and shall be exposed to strategies through read-only snapshots. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.21 Validation

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0327 | The system shall validate symbol availability. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0328 | The system shall validate market session availability. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0329 | The system shall validate volume minimum, maximum, and step. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0330 | The system shall validate margin availability. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0331 | The system shall validate portfolio risk availability. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0332 | The system shall validate price correctness. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0333 | The system shall validate slippage and deviation rules. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0334 | The system shall validate stop-loss and take-profit direction. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0335 | The system shall validate stops level. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0336 | The system shall validate freeze level. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0337 | The system shall validate broker maximum orders and positions. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0338 | The system shall validate fill-policy compatibility. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0339 | The system shall validate expiration and time policy. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0340 | The system shall validate liquidity-model compatibility. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.22 Matching

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0341 | The system shall execute market orders. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0342 | The system shall trigger pending orders. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0343 | The system shall support buy limit pending orders. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0344 | The system shall support buy stop pending orders. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0345 | The system shall support sell limit pending orders. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0346 | The system shall support sell stop pending orders. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0347 | The system shall support buy stop-limit pending orders. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0348 | The system shall support sell stop-limit pending orders. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0349 | The system shall support trailing stops when configured. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0350 | Trailing stops shall update deterministically from eligible tick data and shall never use future bar high, low, close, or volume. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0351 | The system shall support pegged orders when configured, including orders pegged to best bid, best ask, mid price, or another approved reference. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |
| V2-SIM-REQ-0352 | Pegged-order repricing shall follow explicit tick-size, latency, queue-priority, and market-data availability rules. | Defer | Return deterministic unsupported-scope behavior in Phase 1 and retain as a later extension. | The richer microstructure model is not required for the approved FX core. |
| V2-SIM-REQ-0353 | The system shall activate stop-limit orders. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0354 | The system shall trigger SL/TP. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0355 | The system shall handle gap execution. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0356 | The system shall enforce fill policies. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0357 | The system shall simulate partial fills. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0358 | The system shall apply liquidity and slippage results. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0359 | The matching engine shall determine fillable volume from liquidity constraints before applying slippage to filled volume. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0360 | The system shall produce orders, deals, position events, and execution diagnostics. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.23 Accounting

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0361 | The system shall mark open positions to market on ticks. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0362 | The system shall apply deals to positions and account state. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0363 | The system shall apply commission events. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0364 | The system shall apply swap events. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0365 | The system shall apply borrow-fee events for equity and ETF short positions when configured. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0366 | The system shall recalculate account state. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0367 | The system shall enforce `Equity = Balance + FloatingPnL`. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0368 | The system shall enforce `FreeMargin = Equity - Margin`. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0369 | The system shall enforce `MarginLevel = Equity / Margin * 100` when margin is greater than zero. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0370 | The system shall change balance only from closed realized PnL, commission, fee, swap, borrow-fee, dividend, funding, and configured cashflow events. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |

### 1.24 Journal and Audit Trail

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0371 | The system shall maintain an immutable trade journal. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0372 | The journal shall record config hash. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0373 | The journal shall record data checksum. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0374 | The journal shall record tick model. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0375 | The journal shall record spread model. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0376 | The journal shall record liquidity model. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0377 | The journal shall record slippage model. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0378 | The journal shall record fee and commission model. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0379 | The journal shall record swap model. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0380 | The journal shall record sizing model. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0381 | The journal shall record signal timing policy. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0382 | The journal shall record data-quality report. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0383 | The journal shall record every event priority decision. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0384 | The journal shall record every order state transition. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0385 | The journal shall record every deal and partial fill. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0386 | The journal shall record every position update. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0387 | The journal shall record every account snapshot. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0388 | The journal shall record every rejection and error. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0389 | The journal shall record every margin event. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0390 | The journal shall record every swap event. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0391 | The journal shall record every compliance record. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0392 | The canonical journal storage format shall be append-only JSON Lines with one event per line. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0393 | Every journal event shall include schema version, run id, monotonic sequence number, event timestamp, event type, payload, previous event hash, and event hash. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0394 | Every journal shall include a `journal_manifest.json` containing configuration hash, data manifest hash, engine version, schema version, artifact checksums, and retention tier. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0395 | Optional Parquet and CSV journal exports may be generated for analysis, but they shall be derived artifacts and not the canonical replay source. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0396 | Artifact integrity checks shall fail when journal hashes, manifest checksums, or sequence continuity are invalid. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0397 | The immutable journal shall support streaming append-to-disk persistence. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0398 | Append-only journal storage shall support long optimization, walk-forward, and Monte Carlo runs without materializing every run journal in process memory. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0399 | Holding all optimization, walk-forward, or Monte Carlo journals in memory shall be forbidden for production runs. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0400 | Journal persistence failures shall fail closed with `SIM_PERSISTENCE_FAILED`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0401 | Streaming journal writes shall preserve event ordering, replayability, config hash, data checksum, parameter hash, random seed, and objective metadata for each run. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0402 | The report shall disclose the journal storage backend and durability mode used for the run. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0403 | `JournalPersistenceConfig` shall include backend selection, durability mode, flush batch size, maximum in-memory buffer size, and sidecar index configuration. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0404 | Phase 1 shall use append-only JSON Lines as the mandatory canonical streaming journal backend. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0405 | Phase 1 shall use a SQLite sidecar index as the initial random-access journal query format for report generation and diagnostics. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0406 | Phase 1 journal durability shall default to fsync per batch, with a maximum batch of 1,000 events, five seconds, or 16 MB before flush, whichever occurs first. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0407 | Production journal persistence shall fsync before marking a run complete or before emitting final reports. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0408 | If a journal write, flush, fsync, sidecar transaction, or commit fails, the run shall stop in production mode and return `SIM_PERSISTENCE_FAILED`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0409 | After persistence failure, diagnostics shall include journal backend, run id, failed operation, and last committed sequence number. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.25 Compliance Records

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0410 | The system shall create a compliance or audit record for every accepted trade request. | Merge | Represent accepted/rejected pre-trade evidence as typed immutable journal events rather than a separate compliance subsystem. | This preserves audit value with less structure. |
| V2-SIM-REQ-0411 | The system shall create a compliance or audit record for every rejected trade request. | Merge | Represent accepted/rejected pre-trade evidence as typed immutable journal events rather than a separate compliance subsystem. | This preserves audit value with less structure. |
| V2-SIM-REQ-0412 | Compliance records shall include request id. | Merge | Represent accepted/rejected pre-trade evidence as typed immutable journal events rather than a separate compliance subsystem. | This preserves audit value with less structure. |
| V2-SIM-REQ-0413 | Compliance records shall include timestamp. | Merge | Represent accepted/rejected pre-trade evidence as typed immutable journal events rather than a separate compliance subsystem. | This preserves audit value with less structure. |
| V2-SIM-REQ-0414 | Compliance records shall include decision rationale. | Merge | Represent accepted/rejected pre-trade evidence as typed immutable journal events rather than a separate compliance subsystem. | This preserves audit value with less structure. |
| V2-SIM-REQ-0415 | Compliance records shall include risk-check result. | Merge | Represent accepted/rejected pre-trade evidence as typed immutable journal events rather than a separate compliance subsystem. | This preserves audit value with less structure. |
| V2-SIM-REQ-0416 | Compliance records shall include pre-trade checks. | Merge | Represent accepted/rejected pre-trade evidence as typed immutable journal events rather than a separate compliance subsystem. | This preserves audit value with less structure. |
| V2-SIM-REQ-0417 | Compliance records shall include optional compliance tag. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0418 | Compliance records shall include optional strategy name and version. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0419 | Advanced stateful strategies and agent-generated strategies shall provide decision rationale. | Merge | Represent accepted/rejected pre-trade evidence as typed immutable journal events rather than a separate compliance subsystem. | This preserves audit value with less structure. |

### 1.26 Strategy Integration Boundary

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0420 | The simulation module shall consume strategy outputs through the strategy module contract defined in `docs/source-requirements/04-strategy.md`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0421 | The simulation module shall accept timestamped `TradeIntent` objects from approved strategies and shall convert them into sized `TradeRequest` objects before execution. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0422 | The simulation module shall execute strategy-generated trade intents only when the canonical tick loop reaches an eligible tick. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0423 | The simulation module shall enforce that strategies cannot mutate official account, order, deal, position, margin, equity, journal, or execution timestamp state. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0424 | The simulation module shall provide approved read-only execution state to advanced strategies when required. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0425 | The simulation module shall journal strategy id, strategy version, configuration hash, rationale where provided, and strategy-input rejection diagnostics. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0426 | The `run_backtest` AI Tool shall enforce the strategy registry and sandbox rules defined in `docs/source-requirements/04-strategy.md`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.27 Indicator Integration Boundary

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0427 | The simulation module shall consume indicator outputs through the indicator module contract defined in `docs/source-requirements/03-indicator.md`. | Modify | Accept validated point-in-time indicator/signal evidence through the Strategy/Indicator contracts; do not implement indicators here. | The boundary is valid but orchestration of indicator formulas belongs elsewhere. |
| V2-SIM-REQ-0428 | The simulation module shall run data-quality checks before indicator calculation, signal generation, or tick generation. | Reject | Simulation consumes approved `TradeIntent` timelines and must not own indicator calculation or signal conversion logic. | This duplicates Strategy/Indicator responsibilities. |
| V2-SIM-REQ-0429 | The simulation module shall consume indicator result manifests containing input checksum, parameter hash, implementation version, output schema version, and timing metadata. | Modify | Accept validated point-in-time indicator/signal evidence through the Strategy/Indicator contracts; do not implement indicators here. | The boundary is valid but orchestration of indicator formulas belongs elsewhere. |
| V2-SIM-REQ-0430 | The simulation module shall reject, mask, or downgrade runs when indicator-derived data violates the configured no-lookahead policy. | Modify | Accept validated point-in-time indicator/signal evidence through the Strategy/Indicator contracts; do not implement indicators here. | The boundary is valid but orchestration of indicator formulas belongs elsewhere. |
| V2-SIM-REQ-0431 | The simulation module shall convert indicator-derived signals into timestamped trade intents before official execution. | Reject | Simulation consumes approved `TradeIntent` timelines and must not own indicator calculation or signal conversion logic. | This duplicates Strategy/Indicator responsibilities. |
| V2-SIM-REQ-0432 | The simulation module shall prevent vectorized indicator or signal generation from producing official fills, account state, trade journals, or reports. | Reject | Simulation consumes approved `TradeIntent` timelines and must not own indicator calculation or signal conversion logic. | This duplicates Strategy/Indicator responsibilities. |

### 1.28 Metrics and Reporting

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0433 | The system shall produce a trades list. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0434 | The system shall produce orders history. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0435 | The system shall produce deals history. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0436 | The system shall produce partial-fill history. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0437 | The system shall produce position lifecycle history. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0438 | The system shall produce equity, balance, margin, and exposure curves. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0439 | The system shall produce liquidity and slippage diagnostics. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0440 | The system shall produce commission, fee, and swap summaries. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0441 | The system shall produce portfolio-risk summary. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0442 | The system shall produce data-quality summary. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0443 | The system shall produce realism-disclosure summary. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0444 | The system shall calculate data-quality metrics. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0445 | The system shall calculate PnL metrics. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0446 | The system shall calculate cost metrics. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0447 | The system shall calculate trade statistics. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0448 | The system shall calculate streak statistics. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0449 | The system shall calculate regression metrics. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0450 | The system shall calculate return metrics. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0451 | The system shall calculate drawdown metrics. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0452 | The system shall calculate MT5-style history quality. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0453 | The system shall report bars processed. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0454 | The system shall report ticks processed. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0455 | The system shall report symbols involved. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0456 | The system shall calculate total net profit, gross profit, gross loss, profit factor, expected payoff, recovery factor, and Sharpe ratio. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0457 | The system shall calculate Z-score for win/loss sequence randomness. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0458 | The system shall calculate AHPR and GHPR when return series and trade count are sufficient. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0459 | The system shall calculate linear-regression correlation and linear-regression standard error for the equity curve. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0460 | The system shall calculate total trades, total deals, short trades and win percentage, long trades and win percentage, profit trades and percentage, and loss trades and percentage. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0461 | The system shall calculate largest profit trade, largest loss trade, average profit trade, and average loss trade. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0462 | The system shall calculate maximum consecutive wins, maximum consecutive losses, maximal consecutive profit, maximal consecutive loss, average consecutive wins, and average consecutive losses. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0463 | The system shall calculate balance drawdown absolute, equity drawdown absolute, balance drawdown maximal, equity drawdown maximal, balance drawdown relative, and equity drawdown relative. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0464 | Production-realistic reports shall attach confidence intervals to every material performance, risk, drawdown, cost, and execution-quality metric when Monte Carlo or bootstrap evidence is available. | Defer | Keep as a derived or later analysis artifact, not a Phase 1 canonical report requirement. | It is not needed for the minimal canonical run. |
| V2-SIM-REQ-0465 | Metrics without confidence intervals in production-realistic reports shall disclose why interval evidence is unavailable and whether the omission downgrades the result. | Defer | Keep as a derived or later analysis artifact, not a Phase 1 canonical report requirement. | It is not needed for the minimal canonical run. |
| V2-SIM-REQ-0466 | The system shall calculate liquidity metrics. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0467 | The system shall calculate execution-quality metrics. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0468 | The system shall calculate portfolio metrics. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0469 | The system shall include robustness metrics when Monte Carlo or walk-forward analysis is enabled. | Defer | Keep as a derived or later analysis artifact, not a Phase 1 canonical report requirement. | It is not needed for the minimal canonical run. |
| V2-SIM-REQ-0470 | Every report shall state whether the run used full production realism, MT5-parity settings, or research approximation settings. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0471 | The official report formats shall be JSON and Markdown. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0472 | HTML reports may be generated from the official JSON and Markdown artifacts. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0473 | CSV exports shall be supported for tabular report sections such as orders, deals, trades, positions, account snapshots, and diagnostics. | Modify | Delegate statistical/performance metric calculation to Analytics and include returned metrics in the report. | Broad analytics formulas do not belong in Simulation. |
| V2-SIM-REQ-0474 | Visual trade replay export shall be supported as a derived artifact from the canonical journal and report JSON. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0475 | Visual replay exports shall include candles or tick references, strategy signals, order events, fills, position state, equity or balance overlays, drawdown overlays, and annotations for rejections or halts. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0476 | Visual replay exports shall use a documented JSON schema suitable for charting libraries without becoming the canonical report artifact. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0477 | Notebook objects may consume official artifacts but shall not be a required production report format. | Defer | Keep as a derived or later analysis artifact, not a Phase 1 canonical report requirement. | It is not needed for the minimal canonical run. |
| V2-SIM-REQ-0478 | Report schema validation shall run before a report is marked complete. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0479 | The official JSON report shall be the canonical machine-readable report artifact. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0480 | The official Markdown report shall be the required human-review report artifact for Phase 1 CI and release evidence. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |
| V2-SIM-REQ-0481 | If JSON and human-readable report artifacts disagree, the run shall fail report validation until the derived artifact is regenerated from canonical JSON and journal data. | Add | Produce execution evidence and canonical JSON/Markdown reports; consume specialized analytics through an external contract. | These outputs are required to answer and audit a simulation run. |

### 1.29 Optimization and Walk-Forward

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0482 | The system shall support grid-search optimization. | Reject | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0483 | The system shall support random-search optimization. | Reject | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0484 | The system shall support Bayesian optimization. | Reject | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0485 | The system shall support genetic optimization. | Reject | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0486 | Optimization shall use the same canonical tick execution engine as normal backtests. | Modify | Expose deterministic single-run execution evidence for the Optimization domain; do not own search algorithms or job scheduling. | Simulation should supply canonical execution, not optimization orchestration. |
| V2-SIM-REQ-0487 | Walk-forward results shall separate in-sample and out-of-sample metrics. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0488 | Optimization shall reject parameter sets that fail minimum trade count. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0489 | Optimization shall reject parameter sets that fail data-quality checks. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0490 | Optimization shall reject parameter sets that fail robustness checks. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0491 | Optimization outputs shall include config hash, data hash, parameter hash, random seed, and objective function. | Modify | Expose deterministic single-run execution evidence for the Optimization domain; do not own search algorithms or job scheduling. | Simulation should supply canonical execution, not optimization orchestration. |
| V2-SIM-REQ-0492 | Large optimization jobs shall be split into deterministic work units keyed by strategy id, parameter hash, config hash, data hash, engine version, and schema version. | Modify | Expose deterministic single-run execution evidence for the Optimization domain; do not own search algorithms or job scheduling. | Simulation should supply canonical execution, not optimization orchestration. |
| V2-SIM-REQ-0493 | Parallel optimization workers shall run isolated engine instances and shall not share mutable account, order, journal, or strategy state. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0494 | Optimization caching shall reuse only completed work units whose provenance hash exactly matches the requested run. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0495 | Failed or diagnostic work units shall not poison the optimization cache. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0496 | Optimization result ranking shall be deterministic when objective scores tie. | Modify | Expose deterministic single-run execution evidence for the Optimization domain; do not own search algorithms or job scheduling. | Simulation should supply canonical execution, not optimization orchestration. |
| V2-SIM-REQ-0497 | Optimization jobs shall support resumable execution from persisted work-unit manifests. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0498 | Long-running optimization, walk-forward, and Monte Carlo jobs shall periodically checkpoint progress to disk in a restartable format. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0499 | A `ResumePolicy` shall define maximum checkpoint age, checkpoint compatibility rules, automatic resume eligibility, and restart-from-scratch behavior. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0500 | Optimization and walk-forward jobs shall decompose into independent deterministic work units executable on ephemeral stateless workers. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0501 | Distributed work units shall pull inputs from and write outputs to a shared versioned artifact store; local worker disk shall never be the sole source of truth for shared artifacts. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0502 | Worker loss, heartbeat expiry, or preemptible-instance termination shall requeue the affected work unit without marking the entire job `SIM_INTERNAL_ERROR`. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0503 | Requeued work units shall preserve deterministic provenance hashes and shall not duplicate completed journal or report artifacts. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0504 | Distributed schedulers shall detect poison-pill work units that repeatedly fail for the same work-unit hash. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0505 | Poison-pill detection shall quarantine the work unit, stop infinite requeue loops, emit an alert, and preserve failure artifacts for diagnosis. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0506 | Task queues and worker leases shall provide exactly-once effects or idempotent execution for journal writes, checkpoint commits, sidecar index updates, and artifact publication. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |
| V2-SIM-REQ-0507 | Distributed locks or compare-and-swap commits shall prevent duplicate journal sequences or duplicate checkpoint commits when workers restart mid-batch. | Defer | Place algorithm/search/scheduling behavior in Optimization; Simulation remains a deterministic execution dependency. | The proposed behavior belongs primarily to the Optimization domain or later service mode. |

### 1.30 Monte Carlo and Bootstrap

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0508 | The system shall support Monte Carlo analysis after a canonical journal exists. | Modify | Expose immutable journal/result inputs; Monte Carlo and bootstrap analysis belong to Analytics/Optimization. | Simulation should not own robustness-analysis algorithms. |
| V2-SIM-REQ-0509 | The system shall support bootstrap robustness analysis from the immutable journal. | Modify | Expose immutable journal/result inputs; Monte Carlo and bootstrap analysis belong to Analytics/Optimization. | Simulation should not own robustness-analysis algorithms. |
| V2-SIM-REQ-0510 | Monte Carlo analysis shall not replace the official backtest result. | Modify | Expose immutable journal/result inputs; Monte Carlo and bootstrap analysis belong to Analytics/Optimization. | Simulation should not own robustness-analysis algorithms. |
| V2-SIM-REQ-0511 | Monte Carlo outputs shall include confidence bands for drawdown. | Modify | Expose immutable journal/result inputs; Monte Carlo and bootstrap analysis belong to Analytics/Optimization. | Simulation should not own robustness-analysis algorithms. |
| V2-SIM-REQ-0512 | Monte Carlo outputs shall include confidence bands for net profit. | Modify | Expose immutable journal/result inputs; Monte Carlo and bootstrap analysis belong to Analytics/Optimization. | Simulation should not own robustness-analysis algorithms. |
| V2-SIM-REQ-0513 | Monte Carlo outputs shall include confidence bands for profit factor. | Modify | Expose immutable journal/result inputs; Monte Carlo and bootstrap analysis belong to Analytics/Optimization. | Simulation should not own robustness-analysis algorithms. |
| V2-SIM-REQ-0514 | Monte Carlo outputs shall include risk of ruin. | Modify | Expose immutable journal/result inputs; Monte Carlo and bootstrap analysis belong to Analytics/Optimization. | Simulation should not own robustness-analysis algorithms. |
| V2-SIM-REQ-0515 | Monte Carlo outputs shall include worst-case streaks. | Modify | Expose immutable journal/result inputs; Monte Carlo and bootstrap analysis belong to Analytics/Optimization. | Simulation should not own robustness-analysis algorithms. |

### 1.31 Performance Benchmarking

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0516 | The system shall benchmark tick generation speed. | Add | Add reproducible benchmark commands and record runtime/memory observations without premature hard gates. | Basic performance evidence is useful and proportionate. |
| V2-SIM-REQ-0517 | The system shall benchmark tick loop speed. | Add | Add reproducible benchmark commands and record runtime/memory observations without premature hard gates. | Basic performance evidence is useful and proportionate. |
| V2-SIM-REQ-0518 | The system shall benchmark memory usage. | Add | Add reproducible benchmark commands and record runtime/memory observations without premature hard gates. | Basic performance evidence is useful and proportionate. |
| V2-SIM-REQ-0519 | The system shall benchmark optimization throughput when optimization is enabled. | Add | Add reproducible benchmark commands and record runtime/memory observations without premature hard gates. | Basic performance evidence is useful and proportionate. |
| V2-SIM-REQ-0520 | Benchmark results shall be required before production promotion. | Add | Add reproducible benchmark commands and record runtime/memory observations without premature hard gates. | Basic performance evidence is useful and proportionate. |
| V2-SIM-REQ-0521 | Benchmark results shall be stored with release notes. | Open Decision | Approve benchmark fixtures, hardware profile, and blocking thresholds before making them release gates. | The source labels numeric targets provisional or promotion-specific. |
| V2-SIM-REQ-0522 | The production benchmark profile shall be `SIM_BENCHMARK_PROFILE_V1`: Python 3.12, 8 vCPU minimum, 32 GB RAM minimum, NVMe SSD, release build settings, no debugger, and no unrelated heavy background workload. | Open Decision | Approve benchmark fixtures, hardware profile, and blocking thresholds before making them release gates. | The source labels numeric targets provisional or promotion-specific. |
| V2-SIM-REQ-0523 | Benchmark manifests shall record OS, CPU model, logical CPU count, RAM, storage type, Python version, dependency lock hash, git commit, and benchmark dataset hash. | Add | Add reproducible benchmark commands and record runtime/memory observations without premature hard gates. | Basic performance evidence is useful and proportionate. |
| V2-SIM-REQ-0524 | The performance gate shall fail when median runtime regresses by more than 10 percent against the approved baseline and the absolute target is missed. | Open Decision | Approve benchmark fixtures, hardware profile, and blocking thresholds before making them release gates. | The source labels numeric targets provisional or promotion-specific. |
| V2-SIM-REQ-0525 | The memory gate shall fail when peak memory regresses by more than 15 percent against the approved baseline and the absolute memory target is missed. | Open Decision | Approve benchmark fixtures, hardware profile, and blocking thresholds before making them release gates. | The source labels numeric targets provisional or promotion-specific. |
| V2-SIM-REQ-0526 | Tick batching may accelerate pure mark-to-market updates. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |
| V2-SIM-REQ-0527 | Tick batching shall stop immediately at any tick that may trigger state transitions or compliance events. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |
| V2-SIM-REQ-0528 | Tick batching shall never reorder ticks. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |
| V2-SIM-REQ-0529 | Tick batching shall never suppress per-event accounting invariants. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |
| V2-SIM-REQ-0530 | Tick batching shall be permitted only between known pre-calculated boundary events. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |
| V2-SIM-REQ-0531 | Tick batching shall use active pending-order trigger prices, stop-loss prices, take-profit prices, expiration times, stopout thresholds, bar-open times, session boundaries, gap boundaries, swap rollover times, scheduled intent activations, strategy callback boundaries, and compliance boundaries to determine safe batch ranges. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |
| V2-SIM-REQ-0532 | Tick batching shall stop before the nearest active boundary that may cause a state transition. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |
| V2-SIM-REQ-0533 | Tick batching shall not evaluate or skip past a tick that may trigger a state change. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |
| V2-SIM-REQ-0534 | If active orders or open positions exist, batching shall proceed only up to the nearest known trigger boundary. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |
| V2-SIM-REQ-0535 | If no active orders or open positions exist, batching may proceed only up to the next bar open, session boundary, gap boundary, swap rollover boundary, scheduled intent activation, or strategy callback boundary. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |
| V2-SIM-REQ-0536 | Tick batching shall never infer safety from future bar high, low, close, or volume values unavailable at the current tick. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |
| V2-SIM-REQ-0537 | Tick-batching safety diagnostics shall be emitted when batching is enabled. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |
| V2-SIM-REQ-0538 | Phase 1 tick batching shall use a conservative boundary-interval proof model that batches only across intervals where all active trigger, session, rollover, strategy, and compliance boundaries are known before the batch starts. | Defer | Start with one-tick-at-a-time execution; add proven-safe batching only after correctness baselines exist. | Batching adds high correctness risk without a current performance baseline. |

### 1.32 Asset-Class Realism

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0539 | The system shall represent asset class in symbol metadata. | Add | Implement FX realism classification and explicit disclosures for the approved slice. | This directly supports the Phase 1 business question. |
| V2-SIM-REQ-0540 | The system shall support FX. | Add | Implement FX realism classification and explicit disclosures for the approved slice. | This directly supports the Phase 1 business question. |
| V2-SIM-REQ-0541 | The system shall support CFD. | Defer | Reserve metadata only; reject production-realistic execution for non-FX assets in Phase 1. | Other asset classes are expressly out of scope. |
| V2-SIM-REQ-0542 | The system shall support equity. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0543 | The system shall support ETF. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0544 | The system shall support future. | Defer | Reserve metadata only; reject production-realistic execution for non-FX assets in Phase 1. | Other asset classes are expressly out of scope. |
| V2-SIM-REQ-0545 | The system shall support perpetual swap. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0546 | The system shall support spot crypto. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0547 | The system shall support index instruments. | Defer | Reserve metadata only; reject production-realistic execution for non-FX assets in Phase 1. | Other asset classes are expressly out of scope. |
| V2-SIM-REQ-0548 | The system shall derive required realism modules from symbol metadata and simulation config. | Add | Implement FX realism classification and explicit disclosures for the approved slice. | This directly supports the Phase 1 business question. |
| V2-SIM-REQ-0549 | The system shall downgrade realism labels when required asset-class models are disabled. | Add | Implement FX realism classification and explicit disclosures for the approved slice. | This directly supports the Phase 1 business question. |
| V2-SIM-REQ-0550 | The system shall fail fast or explicitly record an approximation when required asset-class data is missing. | Defer | Reserve metadata only; reject production-realistic execution for non-FX assets in Phase 1. | Other asset classes are expressly out of scope. |
| V2-SIM-REQ-0551 | The system shall include asset-class realism decisions in the immutable journal and final report header. | Add | Implement FX realism classification and explicit disclosures for the approved slice. | This directly supports the Phase 1 business question. |
| V2-SIM-REQ-0552 | FX shall be the first asset class eligible for `production_realistic` promotion. | Add | Implement FX realism classification and explicit disclosures for the approved slice. | This directly supports the Phase 1 business question. |
| V2-SIM-REQ-0553 | FX `production_realistic` V1 classification shall require a documented checklist before Builder handoff. At minimum, the checklist shall evaluate data-quality pass status, approved broker profile, approved market-data authority manifest, tick model, spread model, slippage model, commission model, swap model, margin model, currency-conversion model, no-lookahead status, journal persistence status, replayability, and explicit realism downgrades. | Add | Implement FX realism classification and explicit disclosures for the approved slice. | This directly supports the Phase 1 business question. |
| V2-SIM-REQ-0554 | A run shall not receive `production_realistic` classification unless every required checklist item is true or explicitly marked not applicable by an approved owner decision recorded in the report. | Defer | Reserve metadata only; reject production-realistic execution for non-FX assets in Phase 1. | Other asset classes are expressly out of scope. |
| V2-SIM-REQ-0555 | Equity, ETF, futures, perpetual swap, spot crypto, CFD, and index instruments shall remain `research_approximation` or explicitly downgraded until their asset-class-specific data, cost, margin, and corporate-action or lifecycle models pass production gates. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0556 | FX `production_realistic` V1 shall explicitly exclude broker last-look behavior, broker bias, asymmetric slippage manipulation, news-event volatility-surface expansion, counterparty default risk, and broker solvency modelling. | Add | Implement FX realism classification and explicit disclosures for the approved slice. | This directly supports the Phase 1 business question. |
| V2-SIM-REQ-0557 | Reports using FX `production_realistic` V1 shall disclose these non-goals when they are material to interpretation. | Add | Implement FX realism classification and explicit disclosures for the approved slice. | This directly supports the Phase 1 business question. |
| V2-SIM-REQ-0558 | The first production FX slice shall cover deterministic tick execution, spreads, slippage, commission, swap, margin, market hours, multi-currency conversion, portfolio checks, journal integrity, and report schemas. | Add | Implement FX realism classification and explicit disclosures for the approved slice. | This directly supports the Phase 1 business question. |

### 1.33 Corporate Actions and Dividends

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0559 | The system shall support corporate-action treatment for production-realistic equity and ETF backtests. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0560 | The system shall support dividends. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0561 | The system shall support stock splits. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0562 | The system shall support reverse splits. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0563 | The system shall support mergers. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0564 | The system shall support spinoffs. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0565 | The system shall support delistings. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0566 | Dividends shall be applied on ex-date according to selected data policy. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0567 | Long positions shall receive eligible dividend cashflows. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0568 | Short positions shall pay applicable dividend cashflows. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0569 | Dividend cashflows shall be converted to account base currency. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0570 | Dividend events shall be recorded separately from trade PnL. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0571 | Reports shall disclose when dividend income is ignored. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0572 | Splits shall adjust open position volume and average price without changing economic value before fees or taxes. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0573 | Reverse-split fractional handling shall be explicitly configured. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0574 | Pending orders, SL, TP, and limit prices shall be adjusted or cancelled according to broker/config policy. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0575 | Split adjustment events shall be journaled with before/after volume, price, SL, TP, and pending-order state. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0576 | Delisting handling shall explicitly realize the configured final economic outcome instead of silently dropping the symbol. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0577 | Delisting outcomes shall support final exchange price, final OTC or pink-sheet price, cash merger consideration, liquidation value, or conservative total-loss treatment where appropriate. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0578 | Delisting losses, including possible negative 100 percent returns for equity holdings, shall be reflected in realized PnL, equity curve, drawdown, and reports. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0579 | Production-equity reports shall disclose unsupported corporate-action behavior. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0580 | Equity and ETF runs shall include a corporate-action quality report. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0581 | Cash dividends, stock splits, and reverse splits shall be the first supported corporate-action treatments for equity and ETF production realism. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0582 | Mergers, delistings, spinoffs, rights issues, symbol changes, and special distributions shall block production-realistic equity or ETF labels when they intersect the requested date range, holdings, or pending orders unless explicitly supported. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0583 | Research-mode handling of unsupported corporate actions shall disclose the unsupported action and the selected conservative approximation. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0584 | The system shall support configurable hard-to-borrow borrow fee rates for equity and ETF short positions. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0585 | Borrow fees shall be distinct from standard swap, dividends, commission, and trade PnL. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0586 | Borrow fees shall be applied daily or tick-by-tick according to configuration. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0587 | Borrow-fee cashflows shall be journaled separately from dividends, swap, commission, and trade PnL. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0588 | Borrow-fee cashflows shall convert to account base currency when the borrow-fee currency differs from account currency. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0589 | Reports shall disclose total borrow fees paid and the borrow-fee model status. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0590 | Production-realistic equity or ETF short backtests shall require borrow-fee treatment or shall disclose a realism downgrade or approximation. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0591 | The system shall support optional short-locate recall and forced buy-in modelling for equity and ETF short positions. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0592 | Recall models shall support deterministic configured recall events and seeded probabilistic recall rates by symbol, borrow status, and date. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0593 | Forced buy-ins shall close affected short positions at the first eligible market tick subject to configured latency, liquidity, fees, and market-halt rules. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0594 | Recall and forced-buy-in events shall be journaled separately from strategy-initiated exits. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |

### 1.34 Futures Rollover

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0595 | The system shall support futures contract metadata. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0596 | Futures contract metadata shall include root symbol, contract symbol, expiry, first notice date, last trade date, contract size, tick size, tick value, margin currency, and settlement currency. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0597 | The system shall support no futures rollover. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0598 | The system shall support continuous-adjusted rollover. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0599 | The system shall support calendar-spread rollover. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0600 | The system shall support physical close-and-reopen rollover. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0601 | Futures roll dates shall be deterministic and derived from contract metadata. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0602 | The roll engine shall decide whether to close/reopen, adjust the price series, or simulate calendar-spread execution. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0603 | Roll events shall be journaled with old contract, new contract, roll price, adjustment amount, realized roll PnL where applicable, and slippage/fees when simulated. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0604 | Reports shall separate trade PnL from roll yield where possible. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0605 | Continuous-adjusted data may support indicator continuity, but execution shall reference tradeable contract prices. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |

### 1.35 Perpetual Funding

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0606 | The system shall support disabled funding mode. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0607 | The system shall support fixed funding rate mode. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0608 | The system shall support historical funding rate mode. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0609 | The system shall support real-time tick funding rate mode. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0610 | Funding shall apply at exchange-defined funding timestamps. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0611 | Funding payment direction shall follow the configured exchange sign convention. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0612 | Funding cashflows shall remain distinct from swap and commission. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0613 | Funding shall convert to account base currency. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0614 | Reports shall disclose total funding paid or received. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0615 | Reports shall disclose net trading PnL excluding funding. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |

### 1.36 Multi-Currency Accounting

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0616 | The system shall support instruments whose profit currency, margin currency, commission currency, dividend currency, borrow-fee currency, funding currency, and account base currency differ. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0617 | The system shall support fixed-rate conversion. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0618 | The system shall support spot-at-event-time conversion. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0619 | The system shall support spot-at-bar-close conversion. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0620 | The system shall support real-time-tick conversion. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0621 | The accounting engine shall track native-currency and base-currency realized PnL. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0622 | The accounting engine shall track native-currency and base-currency unrealized PnL. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0623 | The accounting engine shall track native-currency and base-currency commissions and fees. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0624 | The accounting engine shall track native-currency and base-currency swap. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0625 | The accounting engine shall track native-currency and base-currency borrow fees. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0626 | The accounting engine shall track native-currency and base-currency dividend cashflows. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0627 | The accounting engine shall track native-currency and base-currency futures roll PnL. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0628 | The accounting engine shall track native-currency and base-currency perpetual funding. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0629 | The accounting engine shall track native-currency and base-currency margin. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0630 | The accounting engine shall track native-currency and base-currency cash balances. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0631 | The accounting engine shall track portfolio NAV in base currency. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0632 | Currency conversion rates shall come from a deterministic FX rate provider. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0633 | Direct currency pairs shall be preferred where available. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0634 | Inverse pairs may be used when enabled. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0635 | Cross-rate synthesis may be used when enabled and all legs are available. | Open Decision | Approve whether Phase 1 supports cross-rate synthesis; default to direct/inverse approved rates and fail closed otherwise. | The source itself leaves the active fixture decision pending. |
| V2-SIM-REQ-0636 | FX conversion precedence shall be direct pair first, inverse pair second when inverse conversion is enabled, and cross-rate synthesis third when cross-rate synthesis is enabled and all legs pass skew/staleness validation. | Open Decision | Approve whether Phase 1 supports cross-rate synthesis; default to direct/inverse approved rates and fail closed otherwise. | The source itself leaves the active fixture decision pending. |
| V2-SIM-REQ-0637 | If a higher-precedence rate exists but is stale, invalid, or checksum-mismatched, the fallback chain shall follow explicit configuration: either fail closed immediately or continue to the next enabled source with a journaled diagnostic. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0638 | Phase 1 shall document the exact fallback-chain setting and default before implementation; the default shall fail closed when no approved non-stale direct or enabled inverse rate is available unless the owner approves cross-rate synthesis for the active fixture. | Open Decision | Approve whether Phase 1 supports cross-rate synthesis; default to direct/inverse approved rates and fail closed otherwise. | The source itself leaves the active fixture decision pending. |
| V2-SIM-REQ-0639 | Stale FX rates shall fail or be explicitly recorded according to configuration. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0640 | Every conversion shall be journaled with rate, source, timestamp, and age. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0641 | Portfolio reports shall include currency exposure and currency PnL attribution. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0642 | FX conversion configuration shall expose `max_fx_rate_age_seconds` as the canonical maximum-rate-age field. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0643 | `stale_rate_tolerance_seconds` may be accepted only as a backward-compatible alias for `max_fx_rate_age_seconds`. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0644 | Maximum FX rate age shall be configurable by conversion context, including intraday tick conversion, bar-close conversion, daily-bar conversion, margin conversion, fee conversion, dividend conversion, funding conversion, and report-only conversion. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0645 | Intraday conversion shall default to a stricter maximum FX rate age than daily-bar conversion. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0646 | If a required conversion rate exceeds the configured maximum age, conversion shall fail closed with `SIM_FX_RATE_STALE` unless diagnostic mode explicitly overrides it. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0647 | FX stale-rate diagnostic overrides shall be journaled and disclosed in the report. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0648 | Cross-rate synthesis shall detect triangular arbitrage loops and circular paths in the FX provider graph. | Open Decision | Approve whether Phase 1 supports cross-rate synthesis; default to direct/inverse approved rates and fail closed otherwise. | The source itself leaves the active fixture decision pending. |
| V2-SIM-REQ-0649 | Cross-rate synthesis shall reject mathematically invalid conversion paths. | Open Decision | Approve whether Phase 1 supports cross-rate synthesis; default to direct/inverse approved rates and fail closed otherwise. | The source itself leaves the active fixture decision pending. |
| V2-SIM-REQ-0650 | Cross-rate synthesis shall reject highly skewed conversion paths when the synthesized rate differs from an available direct or inverse reference by more than the configured `max_cross_rate_skew_bps`. | Open Decision | Approve whether Phase 1 supports cross-rate synthesis; default to direct/inverse approved rates and fail closed otherwise. | The source itself leaves the active fixture decision pending. |
| V2-SIM-REQ-0651 | Phase 1 shall default `max_cross_rate_skew_bps` to 25 basis points for validation fixtures and production-candidate runs. | Open Decision | Approve whether Phase 1 supports cross-rate synthesis; default to direct/inverse approved rates and fail closed otherwise. | The source itself leaves the active fixture decision pending. |
| V2-SIM-REQ-0652 | Rejected cross-rate paths shall return or journal `SIM_FX_CROSS_RATE_REJECTED`. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |
| V2-SIM-REQ-0653 | Rejected cross-rate paths shall be journaled with failed currency graph, requested conversion pair, candidate path, computed rate, reference rate when available, skew, and rejection reason. | Add | Add deterministic FX conversion for required PnL, margin, fees, swap, and account reporting with staleness checks. | Multi-currency accounting is essential for FX realism. |

### 1.37 Benchmark Metrics

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0654 | The system shall support optional benchmark-relative reports. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0655 | The system shall align benchmark data to the same clock and currency as the strategy. | Modify | Simulation aligns and supplies benchmark-ready evidence; Analytics owns alpha/beta and other benchmark formulas. | Metric ownership belongs outside Simulation. |
| V2-SIM-REQ-0656 | The system shall calculate alpha when benchmark data is provided. | Modify | Simulation aligns and supplies benchmark-ready evidence; Analytics owns alpha/beta and other benchmark formulas. | Metric ownership belongs outside Simulation. |
| V2-SIM-REQ-0657 | The system shall calculate beta when benchmark data is provided. | Modify | Simulation aligns and supplies benchmark-ready evidence; Analytics owns alpha/beta and other benchmark formulas. | Metric ownership belongs outside Simulation. |
| V2-SIM-REQ-0658 | The system shall calculate information ratio when benchmark data is provided. | Modify | Simulation aligns and supplies benchmark-ready evidence; Analytics owns alpha/beta and other benchmark formulas. | Metric ownership belongs outside Simulation. |
| V2-SIM-REQ-0659 | The system shall calculate tracking error when benchmark data is provided. | Modify | Simulation aligns and supplies benchmark-ready evidence; Analytics owns alpha/beta and other benchmark formulas. | Metric ownership belongs outside Simulation. |
| V2-SIM-REQ-0660 | The system shall calculate benchmark-relative drawdown when benchmark data is provided. | Modify | Simulation aligns and supplies benchmark-ready evidence; Analytics owns alpha/beta and other benchmark formulas. | Metric ownership belongs outside Simulation. |
| V2-SIM-REQ-0661 | Reports shall clearly omit benchmark metrics when benchmark data is not provided. | Modify | Simulation aligns and supplies benchmark-ready evidence; Analytics owns alpha/beta and other benchmark formulas. | Metric ownership belongs outside Simulation. |

### 1.38 Order Chaining

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0662 | The system shall preserve parent-child order lineage for trade decomposition. | Add | Preserve lineage needed for execution audit and partial fills. | This directly supports replayability. |
| V2-SIM-REQ-0663 | The system shall preserve parent-child order lineage for partial fills. | Add | Preserve lineage needed for execution audit and partial fills. | This directly supports replayability. |
| V2-SIM-REQ-0664 | The system shall preserve parent-child order lineage for bracket orders. | Add | Preserve lineage needed for execution audit and partial fills. | This directly supports replayability. |
| V2-SIM-REQ-0665 | The system shall preserve parent-child order lineage for execution algorithms. | Add | Preserve lineage needed for execution audit and partial fills. | This directly supports replayability. |
| V2-SIM-REQ-0666 | The system shall store parent order id, child order ids, fill ids, and linkage metadata when order chaining is enabled. | Defer | Defer advanced bracket/execution-algorithm chaining until a workflow requires it. | No Phase 1 workflow requires the full chaining surface. |

### 1.39 Regulatory Constraints

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0667 | The system shall provide optional deterministic regulatory checks. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0668 | Regulatory checks may include pattern day trader checks. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0669 | Regulatory checks may include short-sale locate checks. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0670 | Regulatory checks may include position-limit checks. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0671 | Regulatory checks shall be fully journaled when enabled. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0672 | Disabled regulatory checks shall be disclosed for regulated asset-class reports. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0673 | The first regulatory engine scope shall be US equities and ETFs. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0674 | Initial US regulatory checks shall include pattern day trader disclosure, short-sale locate configuration, short-sale restriction support where data exists, and position-limit checks where configured. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0675 | Initial US regulatory checks shall explicitly support SEC Rule 201 alternative uptick-rule restrictions where required data is available. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0676 | The regulatory engine may support optional wash-sale detection and tax-awareness diagnostics for taxable account scenarios. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0677 | Wash-sale diagnostics shall flag loss sales followed by repurchases of substantially identical instruments within the configured window and shall disclose after-tax PnL impact only when tax modelling is enabled. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0678 | FX production-realistic promotion shall not require the regulatory engine, but reports shall disclose that regulatory checks were disabled or not applicable. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |

### 1.40 AI Tool Boundary

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0679 | Anything exported from a domain `__init__.py` and listed in `__all__` shall be treated as an official AI Tool. | Reject | Only explicit tool wrappers are agent-callable; protocol types and internal exports are not tools. | The blanket export rule would make safe package design harder and overexpose internals. |
| V2-SIM-REQ-0680 | Official AI Tools shall follow HaruQuant tool standards. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0681 | Official AI Tools shall include metadata. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0682 | Official AI Tools shall require or create request id. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0683 | Official AI Tools shall perform input validation. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0684 | Official AI Tools shall use structured logging. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0685 | Official AI Tools shall return deterministic error codes. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0686 | Official AI Tools shall avoid silent failures. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0687 | Official AI Tools shall use a standard return schema. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0688 | Internal engine services shall not be exported as agent-callable tools unless a deliberate wrapper is created. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0689 | Official AI Tool responses shall use an envelope containing `schema_version`, `request_id`, `status`, `result`, `error`, `warnings`, `metadata`, and `artifacts`. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0690 | `SimulationResult` shall include `schema_version`, `run_id`, `classification`, `started_at`, `completed_at`, `engine_version`, `config_hash`, `data_manifest_hash`, `broker_profile_id`, `artifact_manifest`, `summary_metrics`, `risk_metrics`, `cost_summary`, `realism_disclosure`, and `data_quality_summary`. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0691 | Failed runs shall return the same envelope with `status=failed`, deterministic error code, safe error message, and any completed diagnostic artifacts. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0692 | Official response schemas shall be versioned and backward-compatible within a major schema version. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0693 | Internal-only fields, secrets, raw credentials, and proprietary strategy source shall not appear in official AI Tool responses. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0694 | The `run_backtest` AI Tool shall not accept raw arbitrary Python strategy code as a string input. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0695 | The `run_backtest` AI Tool shall accept only registered strategy identifiers, validated strategy configuration schemas, or code explicitly vetted and sandboxed by the orchestration layer. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0696 | The `run_backtest` AI Tool shall reject raw strategy-code injection attempts before execution. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0697 | The `run_backtest` AI Tool shall return `SIM_ARBITRARY_CODE_REJECTED` when raw arbitrary strategy code is rejected. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0698 | The `run_backtest` AI Tool shall journal rejected strategy-injection attempts without logging unsafe code bodies in full. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |
| V2-SIM-REQ-0699 | Rejected strategy-input diagnostics shall include request id, strategy identifier when present, rejection reason, and deterministic error code. | Add | Add an explicit safe, versioned `run_backtest` tool boundary with deterministic envelopes and code-injection rejection. | This is the required public boundary. |

### 1.41 Release Phasing and Examples

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0700 | The first implementation slice shall be the Phase 1 FX canonical backtest slice. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0701 | Phase 1 shall implement `run_backtest`, `BacktestOrchestrator`, `EventDrivenExecutionEngine`, FX symbol metadata, tick generation, spread/slippage/commission/swap models, broker-profile fixtures, data-quality gates, deterministic journal storage, JSON and Markdown reports, schema validation, and replay tests. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0702 | Phase 1 shall exclude production-realistic labels for equity, ETF, futures, perpetual swap, spot crypto, CFD, index, option, and option-like instruments. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0703 | Options and option-like contracts shall remain out of scope beyond reserved enum or metadata mentions until an options-specific requirements document defines contract specs, Greeks, exercise/assignment, expiry, corporate actions, margin, pricing, and settlement. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0704 | Unsupported option or option-like instruments shall fail deterministically or run only in explicitly labelled research mode when a future research adapter exists. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0705 | Release readiness examples shall include one FX MT5-parity fixture run, one FX production-realistic single-symbol run, one FX multi-symbol portfolio run, one synthetic-tick research approximation run, one severe-data-quality blocked run, one deterministic replay run, and one JSON plus Markdown report pair. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0706 | Equity, futures, perpetual, and multi-currency examples shall be required before those asset classes are promoted to production-realistic status. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0707 | Implementation tickets and release manifests shall assign traceability ids such as `SIM-FR-001`, `SIM-NFR-001`, and `SIM-BR-001` to accepted requirements before implementation begins. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0708 | Implementation tickets and release manifests shall include priority, release phase, owner, acceptance criteria, and verification method for each accepted requirement. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.42 Model Governance and Validation

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0709 | Every production-candidate simulator model shall have a model inventory record. | Modify | Record model ids/versions/validation references in run evidence; governance approvals remain outside Simulation. | Simulation should consume governance decisions, not own the governance process. |
| V2-SIM-REQ-0710 | Model inventory records shall include model id, owner, purpose, approved use cases, prohibited use cases, asset-class scope, version, dependencies, validation status, materiality tier, known limitations, and review expiry. | Modify | Record model ids/versions/validation references in run evidence; governance approvals remain outside Simulation. | Simulation should consume governance decisions, not own the governance process. |
| V2-SIM-REQ-0711 | Simulator models shall include execution models, slippage models, liquidity models, spread models, sizing models, risk models, calibration models, strategy models, benchmark models, and data-adjustment models. | Modify | Record model ids/versions/validation references in run evidence; governance approvals remain outside Simulation. | Simulation should consume governance decisions, not own the governance process. |
| V2-SIM-REQ-0712 | Production promotion shall require independent validation or documented second-party review for material models. | Modify | Record model ids/versions/validation references in run evidence; governance approvals remain outside Simulation. | Simulation should consume governance decisions, not own the governance process. |
| V2-SIM-REQ-0713 | Validation shall cover conceptual soundness, implementation correctness, input-data suitability, outcome analysis, stress behavior, monitoring approach, and known limitations. | Modify | Record model ids/versions/validation references in run evidence; governance approvals remain outside Simulation. | Simulation should consume governance decisions, not own the governance process. |
| V2-SIM-REQ-0714 | Every model exception, override, accepted limitation, and temporary approval shall require owner, approver, rationale, expiry date, and audit record. | Modify | Record model ids/versions/validation references in run evidence; governance approvals remain outside Simulation. | Simulation should consume governance decisions, not own the governance process. |
| V2-SIM-REQ-0715 | Production models shall require periodic re-validation after material code, data, broker-profile, dependency, or calibration changes. | Modify | Record model ids/versions/validation references in run evidence; governance approvals remain outside Simulation. | Simulation should consume governance decisions, not own the governance process. |
| V2-SIM-REQ-0716 | Expired, unapproved, or materially changed model inventory records shall block production-realistic classification unless an explicit governance override is present. | Modify | Record model ids/versions/validation references in run evidence; governance approvals remain outside Simulation. | Simulation should consume governance decisions, not own the governance process. |
| V2-SIM-REQ-0717 | Model materiality shall be reassessed dynamically per run based on configured exposure, capital, instrument universe, strategy criticality, liquidity usage, and report distribution mode. | Modify | Record model ids/versions/validation references in run evidence; governance approvals remain outside Simulation. | Simulation should consume governance decisions, not own the governance process. |
| V2-SIM-REQ-0718 | Dynamic materiality reassessment shall be able to upgrade slippage, liquidity, sizing, risk, benchmark, and data-adjustment models to a stricter validation tier for a specific run. | Modify | Record model ids/versions/validation references in run evidence; governance approvals remain outside Simulation. | Simulation should consume governance decisions, not own the governance process. |
| V2-SIM-REQ-0719 | A dynamic materiality upgrade shall require the stricter validation evidence and sign-off associated with the upgraded tier before production promotion. | Modify | Record model ids/versions/validation references in run evidence; governance approvals remain outside Simulation. | Simulation should consume governance decisions, not own the governance process. |

### 1.43 Research Integrity and Overfitting Controls

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0720 | Strategy research runs shall record a research protocol manifest before optimization begins. | Modify | Record research-protocol and selection provenance supplied by Research/Optimization; do not own research policy. | The evidence matters, but the policy belongs elsewhere. |
| V2-SIM-REQ-0721 | The research protocol manifest shall include hypothesis, parameter search space, train/validation/test split, benchmark, objective function, minimum trade count, and promotion criteria. | Modify | Record research-protocol and selection provenance supplied by Research/Optimization; do not own research policy. | The evidence matters, but the policy belongs elsewhere. |
| V2-SIM-REQ-0722 | Time-series validation shall support walk-forward, anchored walk-forward, rolling walk-forward, purged cross-validation, embargo windows, and out-of-time validation. | Modify | Record research-protocol and selection provenance supplied by Research/Optimization; do not own research policy. | The evidence matters, but the policy belongs elsewhere. |
| V2-SIM-REQ-0723 | Optimization reports shall disclose total parameter combinations tested, rejected combinations, failed combinations, and final selected parameter lineage. | Modify | Record research-protocol and selection provenance supplied by Research/Optimization; do not own research policy. | The evidence matters, but the policy belongs elsewhere. |
| V2-SIM-REQ-0724 | Production promotion shall require configured out-of-sample degradation thresholds. | Modify | Record research-protocol and selection provenance supplied by Research/Optimization; do not own research policy. | The evidence matters, but the policy belongs elsewhere. |
| V2-SIM-REQ-0725 | Production promotion shall require sensitivity analysis around selected parameters. | Modify | Record research-protocol and selection provenance supplied by Research/Optimization; do not own research policy. | The evidence matters, but the policy belongs elsewhere. |
| V2-SIM-REQ-0726 | Production promotion shall require performance to remain acceptable under increased spread, increased slippage, reduced liquidity, delayed execution, missing-data, and gap-stress scenarios. | Modify | Record research-protocol and selection provenance supplied by Research/Optimization; do not own research policy. | The evidence matters, but the policy belongs elsewhere. |
| V2-SIM-REQ-0727 | Reports shall disclose whether a result is single-run, optimized, walk-forward selected, or post-hoc selected. | Modify | Record research-protocol and selection provenance supplied by Research/Optimization; do not own research policy. | The evidence matters, but the policy belongs elsewhere. |
| V2-SIM-REQ-0728 | Reports shall warn when the same dataset was used for strategy discovery, parameter selection, and final evaluation. | Modify | Record research-protocol and selection provenance supplied by Research/Optimization; do not own research policy. | The evidence matters, but the policy belongs elsewhere. |
| V2-SIM-REQ-0729 | Post-hoc selected strategies shall not be labelled production-realistic without explicit research-integrity approval. | Modify | Record research-protocol and selection provenance supplied by Research/Optimization; do not own research policy. | The evidence matters, but the policy belongs elsewhere. |

### 1.44 Execution Model Calibration

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0730 | Slippage, spread, market-impact, and liquidity models shall declare calibration data sources. | Modify | Consume immutable calibration references and disclose model status; calibration workflows live outside the engine. | This keeps execution evidence without adding a calibration platform. |
| V2-SIM-REQ-0731 | Calibration artifacts shall include symbol, venue or broker profile, date range, account type, order type, order size distribution, data checksum, calibration version, and calibration timestamp. | Modify | Consume immutable calibration references and disclose model status; calibration workflows live outside the engine. | This keeps execution evidence without adding a calibration platform. |
| V2-SIM-REQ-0732 | Production-realistic execution models shall define acceptable error bands against observed historical, paper, or live execution data where available. | Modify | Consume immutable calibration references and disclose model status; calibration workflows live outside the engine. | This keeps execution evidence without adding a calibration platform. |
| V2-SIM-REQ-0733 | Execution-model validation shall compare expected fill price, realized fill price, slippage distribution, rejection rate, partial-fill rate, and latency assumptions. | Modify | Consume immutable calibration references and disclose model status; calibration workflows live outside the engine. | This keeps execution evidence without adding a calibration platform. |
| V2-SIM-REQ-0734 | Reports shall disclose whether execution models are broker-calibrated, venue-calibrated, generic, synthetic, or uncalibrated. | Modify | Consume immutable calibration references and disclose model status; calibration workflows live outside the engine. | This keeps execution evidence without adding a calibration platform. |
| V2-SIM-REQ-0735 | Uncalibrated execution models shall downgrade realism classification or require explicit approval. | Modify | Consume immutable calibration references and disclose model status; calibration workflows live outside the engine. | This keeps execution evidence without adding a calibration platform. |
| V2-SIM-REQ-0736 | Calibration artifacts shall be immutable once attached to a production-candidate run. | Modify | Consume immutable calibration references and disclose model status; calibration workflows live outside the engine. | This keeps execution evidence without adding a calibration platform. |

### 1.45 Strategy Capacity and Scalability

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0737 | Reports shall include capacity diagnostics when liquidity or market-impact models are enabled. | Defer | Defer capacity modelling until liquidity/market-impact models and a production workflow are approved. | No Phase 1 workflow requires it. |
| V2-SIM-REQ-0738 | Capacity diagnostics shall estimate performance degradation across configured capital, order-size, and participation-rate levels. | Defer | Defer capacity modelling until liquidity/market-impact models and a production workflow are approved. | No Phase 1 workflow requires it. |
| V2-SIM-REQ-0739 | Capacity reports shall include turnover, average participation rate, maximum participation rate, liquidity utilization, slippage sensitivity, and market-impact sensitivity. | Defer | Defer capacity modelling until liquidity/market-impact models and a production workflow are approved. | No Phase 1 workflow requires it. |
| V2-SIM-REQ-0740 | Production promotion shall define maximum approved capital, maximum order size, maximum participation rate, and approved instrument universe. | Defer | Defer capacity modelling until liquidity/market-impact models and a production workflow are approved. | No Phase 1 workflow requires it. |
| V2-SIM-REQ-0741 | Capacity assumptions shall be journaled and included in the realism disclosure. | Defer | Defer capacity modelling until liquidity/market-impact models and a production workflow are approved. | No Phase 1 workflow requires it. |
| V2-SIM-REQ-0742 | Strategies that exceed approved capacity limits shall be blocked from production promotion or explicitly downgraded. | Defer | Defer capacity modelling until liquidity/market-impact models and a production workflow are approved. | No Phase 1 workflow requires it. |

### 1.46 Run Lifecycle and Idempotency

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0743 | Every official run shall use a deterministic lifecycle state machine: `created`, `validated`, `data_prepared`, `signals_built`, `ticks_built`, `executing`, `reporting`, `completed`, `failed`, and `cancelled`. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0744 | Retrying the same request id shall be idempotent unless explicitly configured to create a new run id. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0745 | A cancelled run shall produce a structured cancelled result, partial artifact manifest, final journal flush attempt, and cancellation diagnostic. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0746 | Resumed runs shall verify config hash, data manifest hash, engine version, journal sequence continuity, random-seed state, and checkpoint compatibility before continuing. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0747 | Stale, duplicated, or conflicting run ids shall fail with deterministic error codes. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |
| V2-SIM-REQ-0748 | Run lifecycle transitions shall be journaled with actor, request id, timestamp, previous state, next state, and transition reason. | Add | Implement the smallest deterministic Phase 1 behavior and map it to the focused capability. | No working V1 implementation satisfies this requirement. |

### 1.47 Third-Party Data and Vendor Governance

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0749 | Every external data source shall have a vendor or source inventory record. | Modify | Validate Data-owned source-manifest references and persist provenance hashes; vendor governance remains in Data/governance. | Simulation needs evidence, not vendor-policy ownership. |
| V2-SIM-REQ-0750 | Vendor records shall include provider, dataset, license scope, redistribution rights, retention rights, adjustment policy, timezone policy, revision policy, and support contact. | Modify | Validate Data-owned source-manifest references and persist provenance hashes; vendor governance remains in Data/governance. | Simulation needs evidence, not vendor-policy ownership. |
| V2-SIM-REQ-0751 | Production-realistic runs shall require point-in-time data snapshots or an explicit data-revision policy. | Modify | Validate Data-owned source-manifest references and persist provenance hashes; vendor governance remains in Data/governance. | Simulation needs evidence, not vendor-policy ownership. |
| V2-SIM-REQ-0752 | Data manifests shall record whether data is raw, adjusted, back-adjusted, survivorship-bias-free, point-in-time, revised, or vendor-restated. | Modify | Validate Data-owned source-manifest references and persist provenance hashes; vendor governance remains in Data/governance. | Simulation needs evidence, not vendor-policy ownership. |
| V2-SIM-REQ-0753 | Vendor data changes after a completed production run shall not mutate historical run artifacts. | Modify | Validate Data-owned source-manifest references and persist provenance hashes; vendor governance remains in Data/governance. | Simulation needs evidence, not vendor-policy ownership. |
| V2-SIM-REQ-0754 | Reports shall disclose material vendor-data limitations. | Modify | Validate Data-owned source-manifest references and persist provenance hashes; vendor governance remains in Data/governance. | Simulation needs evidence, not vendor-policy ownership. |
| V2-SIM-REQ-0755 | Data-source license or retention conflicts shall block external report export unless explicitly approved. | Modify | Validate Data-owned source-manifest references and persist provenance hashes; vendor governance remains in Data/governance. | Simulation needs evidence, not vendor-policy ownership. |

### 1.48 Production Promotion Manifest

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0756 | Every production promotion shall produce a `simulation_promotion_manifest.json`. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0757 | The promotion manifest shall include requirement ids, implementation tickets, test evidence, benchmark evidence, replay evidence, model-validation evidence, security evidence, known exceptions, approvers, approval timestamp, expiry, and release artifact hashes. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0758 | Promotion shall fail when any required evidence artifact is missing, expired, unverifiable, or hash-mismatched. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0759 | Promotion shall require explicit classification: `research_only`, `mt5_parity_candidate`, `production_fx_candidate`, or asset-class-specific production candidate. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |
| V2-SIM-REQ-0760 | Promotion manifests shall be retained with the release artifacts they approve. | Defer | Move to the Future Extensions Annex. | Not required for the FX canonical initial rebuild. |

### 2.1 Determinism and Reproducibility

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0761 | The same configuration, data, and seed shall produce the same tick stream. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0762 | The same configuration, data, and seed shall produce the same spread values. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0763 | The same configuration, data, and seed shall produce the same liquidity decisions. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0764 | The same configuration, data, and seed shall produce the same slippage values. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0765 | The same configuration, data, and seed shall produce the same trade intents. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0766 | The same configuration, data, and seed shall produce the same event-priority order. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0767 | The same configuration, data, and seed shall produce the same orders, deals, and positions. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0768 | The same configuration, data, and seed shall produce the same commission and swap events. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0769 | The same configuration, data, and seed shall produce the same portfolio state. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0770 | The same configuration, data, and seed shall produce the same journal. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0771 | The same configuration, data, and seed shall produce the same metrics. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0772 | Determinism guarantees shall be evaluated under the same pinned `requirements.txt` or lockfile, same approved dependency versions, same simulation schema version, and same Python minor version unless a cross-version reproducibility profile is explicitly certified. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0773 | When Python minor version, dependency lock hash, platform, or decimal/numeric backend differs from the certified profile, official results shall record an environment drift diagnostic and shall not be used for production promotion without compatibility evidence. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |

### 2.2 Auditability

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0774 | Every trade path shall be journaled from validation through sizing, liquidity, slippage, fills, fees, swap, accounting, and compliance checks. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0775 | Every shortcut shall be recorded in configuration, journal, and final report. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0776 | Event ordering shall be replayable. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0777 | Compliance records shall provide evidence of pre-trade checks and risk decisions. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0778 | Parent-child order lineage shall be auditable when order chaining is enabled. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |

### 2.3 Reliability

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0779 | The system shall not silently fail. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0780 | Controlled tool boundaries MUST return a deterministic `SIM_*` error code and safe redacted error envelope for all handled failures. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0781 | Unhandled exceptions at controlled tool boundaries MUST be mapped to `SIM_INTERNAL_ERROR`, logged at `ERROR` level with redacted context, and must not expose secrets, raw strategy code, credentials, or private payloads. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0782 | The system shall return deterministic error codes for rejections, skipped trades, invalid config, invalid data, validation failures, sizing failures, and execution failures. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0783 | The system shall log all failures. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0784 | The system shall stop the simulation on accounting invariant violations unless diagnostic mode is configured. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0785 | Severe data-quality failures shall block production runs unless diagnostic mode is configured. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0786 | Diagnostic mode shall never produce a `production_realistic` or `mt5_parity_oriented` classification after severe data-quality failure or accounting invariant violation. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0787 | Diagnostic mode may continue only far enough to emit bounded diagnostics, partial artifacts, failed invariant details, and safe remediation hints. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0788 | Diagnostic mode shall mark results `diagnostic_failed`, prevent optimization ranking, prevent benchmark promotion, and exclude the run from canonical performance comparisons. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0789 | Diagnostic mode shall require an explicit configuration flag, actor id, rationale, and audit record. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |

### 2.4 Performance

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0790 | The numeric performance values in this section are provisional engineering targets until a Phase 1 benchmark profile and pass/fail gates are approved. | Open Decision | Record non-blocking measurements until benchmark fixtures and pass/fail thresholds are approved. | The source explicitly says these values are provisional. |
| V2-SIM-REQ-0791 | Indicator and signal calculation for 10 years by 10 symbols of M1 bars should target less than 5 seconds after caching or preprocessing. | Open Decision | Record non-blocking measurements until benchmark fixtures and pass/fail thresholds are approved. | The source explicitly says these values are provisional. |
| V2-SIM-REQ-0792 | Python tick loop with no trade events should target at least 10,000 ticks per second. | Open Decision | Record non-blocking measurements until benchmark fixtures and pass/fail thresholds are approved. | The source explicitly says these values are provisional. |
| V2-SIM-REQ-0793 | Synthetic tick generation should target at least 100,000 generated ticks per second where possible. | Open Decision | Record non-blocking measurements until benchmark fixtures and pass/fail thresholds are approved. | The source explicitly says these values are provisional. |
| V2-SIM-REQ-0794 | Optimization batch of 10,000 parameter sets should target less than 30 minutes after parallel execution is enabled. | Open Decision | Record non-blocking measurements until benchmark fixtures and pass/fail thresholds are approved. | The source explicitly says these values are provisional. |
| V2-SIM-REQ-0795 | Common 10-symbol research runs should target less than 2 GB memory after chunking and caching. | Open Decision | Record non-blocking measurements until benchmark fixtures and pass/fail thresholds are approved. | The source explicitly says these values are provisional. |
| V2-SIM-REQ-0796 | Production promotion shall require recorded benchmark results. | Add | Add bounded performance measurement without compromising determinism. | Performance evidence is needed, but correctness remains primary. |
| V2-SIM-REQ-0797 | Production benchmark gates shall define benchmark dataset, hardware profile, dependency lock hash, measurement command, warmup behavior, sample count, pass/fail threshold, allowed variance, median runtime, and p95 runtime before the targets above are used as acceptance gates. | Add | Add bounded performance measurement without compromising determinism. | Performance evidence is needed, but correctness remains primary. |
| V2-SIM-REQ-0798 | Phase 1 Builder handoff shall either replace provisional `should target` values with approved `MUST meet` thresholds or explicitly mark them non-blocking until production promotion. | Open Decision | Record non-blocking measurements until benchmark fixtures and pass/fail thresholds are approved. | The source explicitly says these values are provisional. |
| V2-SIM-REQ-0799 | Phase 1 memory limits shall remain pending owner approval until the benchmark profile defines maximum resident memory, measurement command, reference hardware, dataset shape, and failure behavior. | Open Decision | Record non-blocking measurements until benchmark fixtures and pass/fail thresholds are approved. | The source explicitly says these values are provisional. |
| V2-SIM-REQ-0800 | Once approved, memory-limit breaches shall fail deterministically with `SIM_RESOURCE_QUOTA_EXCEEDED` before the run can claim production-realistic classification. | Add | Add bounded performance measurement without compromising determinism. | Performance evidence is needed, but correctness remains primary. |

### 2.5 Maintainability and Architecture

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0801 | The system shall follow a domain-driven architecture. | Modify | Use focused capability modules and stable contracts; avoid speculative extension layers. | The principle is valid but the proposed architecture must remain minimal. |
| V2-SIM-REQ-0802 | Simulation, indicators, and strategies shall remain in their target domains. | Add | Adopt import safety, domain separation, and explicit public-tool boundaries. | These are low-cost structural safeguards. |
| V2-SIM-REQ-0803 | Internal engine services shall remain separate from official AI Tool wrappers. | Add | Adopt import safety, domain separation, and explicit public-tool boundaries. | These are low-cost structural safeguards. |
| V2-SIM-REQ-0804 | Simple four-tick OHLC generation shall remain separate from MQL5-style synthetic tick generation. | Add | Adopt import safety, domain separation, and explicit public-tool boundaries. | These are low-cost structural safeguards. |
| V2-SIM-REQ-0805 | Optional enterprise features shall have extension points without forcing a breaking redesign of the core engine. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0806 | This domain document may be split into smaller requirement files after Phase 1 boundaries are implemented, provided traceability to this baseline is preserved. | Add | Adopt import safety, domain separation, and explicit public-tool boundaries. | These are low-cost structural safeguards. |
| V2-SIM-REQ-0807 | Any split requirements file shall preserve requirement ids, release phase, acceptance criteria, and verification mapping. | Add | Adopt import safety, domain separation, and explicit public-tool boundaries. | These are low-cost structural safeguards. |
| V2-SIM-REQ-0808 | Public simulation modules shall expose only approved AI Tool wrappers and stable protocol types; internal execution, accounting, journal, data-quality, and reporting services shall remain non-agent-callable and shall be protected by import-boundary tests. | Add | Adopt import safety, domain separation, and explicit public-tool boundaries. | These are low-cost structural safeguards. |
| V2-SIM-REQ-0809 | Importing public simulation modules shall not start workers, open network connections, read secrets, write artifacts, register global mutable state, access market data, contact brokers, or launch background schedulers. | Add | Adopt import safety, domain separation, and explicit public-tool boundaries. | These are low-cost structural safeguards. |

### 2.6 Compatibility

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0810 | The simulator shall reproduce important MT5 Strategy Tester execution semantics. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0811 | MT5-parity tests shall compare supported behavior against controlled MT5 Strategy Tester scenarios. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0812 | The simulator shall support live/simulation parity through an MT5-style `SimTrader` protocol. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0813 | MT5 parity comparisons shall require exact match for order count, deal count, position lifecycle count, side, symbol, order type, fill policy, and deterministic event order. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0814 | MT5 parity comparisons shall require execution timestamps to match the fixture tick timestamp for the same eligible tick. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0815 | MT5 parity price comparisons shall tolerate at most one half of the symbol tick size, unless the approved broker fixture documents a stricter tolerance. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0816 | MT5 parity money comparisons shall tolerate at most the larger of one account-currency cent or 0.01 percent of the compared value for realized PnL, balance, equity, margin, commission, and swap. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0817 | MT5 parity shall fail when a difference is explained only by an undocumented broker rule, missing symbol metadata, or non-deterministic rounding. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0818 | Public response schemas shall remain backward-compatible within a major schema version, and breaking changes shall require a new major schema version. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |

### 2.7 Data Integrity

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0819 | Required data-quality gates shall run before calculations and execution. | Modify | Simulation validates the Data-owned immutable input contract and execution-specific integrity; Data owns source quality and bias metadata. | Preserves the boundary. |
| V2-SIM-REQ-0820 | Data checks shall be deterministic. | Modify | Simulation validates the Data-owned immutable input contract and execution-specific integrity; Data owns source quality and bias metadata. | Preserves the boundary. |
| V2-SIM-REQ-0821 | History-quality metadata shall be exposed. | Modify | Simulation validates the Data-owned immutable input contract and execution-specific integrity; Data owns source quality and bias metadata. | Preserves the boundary. |
| V2-SIM-REQ-0822 | Data checks shall include survivorship-bias flags where relevant. | Modify | Simulation validates the Data-owned immutable input contract and execution-specific integrity; Data owns source quality and bias metadata. | Preserves the boundary. |

### 2.8 Precision and Rounding

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0823 | Internal simulation math shall use `Decimal` or equivalent fixed-precision decimal arithmetic for prices, points, fees, FX conversions, margins, cashflows, and account balances. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0824 | Floating-point types may be used for vectorized indicator research only when the result is not used directly for official accounting or official fill prices. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0825 | Tradable prices shall be normalized to the symbol tick size. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0826 | Conservative price rounding shall default to adverse rounding: buy-side executable prices round up to the next valid tick and sell-side executable prices round down to the next valid tick when exact normalization is required. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0827 | Point calculations shall preserve decimal precision internally and shall be rounded only at configured reporting or validation boundaries. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0828 | Commission, fees, swap, dividends, funding, realized PnL, and cash ledger entries shall round at each cashflow boundary to the relevant currency precision using the broker profile rule or `ROUND_HALF_UP` when no broker-specific rule exists. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0829 | FX conversions shall store source rate precision, conversion timestamp, and converted cashflow rounded to the account currency precision at the accounting boundary. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0830 | Fractional shares and fractional contract quantities shall be allowed only when symbol metadata declares a valid fractional volume step. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |
| V2-SIM-REQ-0831 | Position sizing shall default to floor-to-step volume rounding, while final fill prices and account cashflows shall follow the execution and accounting rounding rules above. | Add | Adopt as a Phase 1 quality attribute or invariant. | Required for trustworthy canonical simulation. |

### 2.9 Observability and Operations

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0832 | The simulator shall emit run-level telemetry for every official run. | Add | Emit basic run/stage timing and diagnostic metadata through the existing observability boundary. | Lightweight telemetry supports operability. |
| V2-SIM-REQ-0833 | Telemetry shall include stage duration, tick generation rate, tick loop rate, memory high-water mark, journal flush latency, journal backlog, data-quality failure counts, rejection counts, fill counts, and report-generation duration. | Add | Emit basic run/stage timing and diagnostic metadata through the existing observability boundary. | Lightweight telemetry supports operability. |
| V2-SIM-REQ-0834 | Production service mode shall expose health checks for data access, artifact storage, journal backend, sidecar index, secrets provider, and worker capacity. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0835 | Production service mode shall define SLOs for run startup latency, successful completion rate, journal durability, artifact availability, and report-generation latency. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0836 | Alerting shall cover journal persistence failures, schema validation failures, repeated accounting invariant failures, abnormal rejection spikes, data-provider failures, and performance regressions. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0837 | Operational runbooks shall cover failed runs, corrupted sidecar index, journal replay recovery, data-source outage, artifact restore, stuck worker, and rollback after bad release. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0838 | Production service mode shall enforce per-user, per-tenant, or per-request resource quotas. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0839 | Resource quotas shall include maximum concurrent runs, maximum wall-clock seconds per run, maximum temporary storage bytes, maximum queued runs, and maximum worker count where applicable. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0840 | Quota violations shall fail fast with `SIM_RESOURCE_QUOTA_EXCEEDED`. | Add | Emit basic run/stage timing and diagnostic metadata through the existing observability boundary. | Lightweight telemetry supports operability. |
| V2-SIM-REQ-0841 | Production service mode shall queue `run_backtest` requests when workers are saturated and return a run id with `queued` status. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0842 | Queueing shall enforce maximum queue length, maximum queue age, cancellation support, and deterministic rejection when limits are exceeded. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0843 | The scheduler shall persist queued, running, completed, failed, and cancelled states outside worker memory. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0844 | The complete resolved configuration for a production run shall be serialized into an immutable run-configuration artifact stored alongside results. | Add | Emit basic run/stage timing and diagnostic metadata through the existing observability boundary. | Lightweight telemetry supports operability. |
| V2-SIM-REQ-0845 | The immutable run-configuration artifact shall include data authority manifest versions, broker profile versions, strategy version, engine version, dependency lock hash, resource policy, and effective runtime flags. | Add | Emit basic run/stage timing and diagnostic metadata through the existing observability boundary. | Lightweight telemetry supports operability. |
| V2-SIM-REQ-0846 | Production run-configuration artifacts shall be signed or checksum-verified and shall be the single source of truth for replay. | Add | Emit basic run/stage timing and diagnostic metadata through the existing observability boundary. | Lightweight telemetry supports operability. |
| V2-SIM-REQ-0847 | Before a production run starts, the system shall compute and record an environment diagnostic hash covering dependency versions, selected system libraries, relevant environment variables, container image digest where applicable, and benchmark profile id. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0848 | The system shall raise `SIM_ENVIRONMENT_DRIFT_WARNING` when the environment diagnostic hash differs from the certified benchmark profile environment. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0849 | Every major pipeline stage shall emit an OpenTelemetry-compatible trace span, including validation, data preparation, signal generation, tick generation, execution, reporting, and artifact persistence. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0850 | Trace and log context shall propagate run id, request id, strategy id, config hash, data manifest hash, and engine version. | Add | Emit basic run/stage timing and diagnostic metadata through the existing observability boundary. | Lightweight telemetry supports operability. |
| V2-SIM-REQ-0851 | The simulator shall emit business-level time-series metrics suitable for dashboards, including run status counts, lookahead violation counts, execution latency, data-quality failure counts, persistence failure counts, queue depth, and quota rejection counts. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0852 | Alerting shall include trend or predictive rules for persistence failures, data-provider failures, queue saturation, and SLO burn rate where the monitoring platform supports them. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0853 | Production service mode shall define maximum request payload size, maximum resolved configuration size, maximum artifact path length, maximum diagnostic payload size, maximum run duration, maximum queue wait, and maximum retry count before implementation. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |
| V2-SIM-REQ-0854 | Production service mode shall support synthetic transaction monitoring through a scheduled canonical simulation probe. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0855 | Synthetic transaction probes shall alert when the canonical simulation fails, produces non-deterministic output, violates expected metrics tolerance, or cannot produce required artifacts. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0856 | Major engine releases shall support canary analysis by running a controlled subset of production requests through old and new engine versions and comparing results for configured statistical equivalence. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0857 | Canary divergence shall block promotion or trigger rollback without changing the primary user-facing result for the request. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0858 | Optional service failures such as warm-cache outage or SQLite sidecar index outage may degrade to slower fallback behavior for non-production runs when configured. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0859 | Production runs shall fail closed or require explicit diagnostic override when optional service degradation would weaken durability, replayability, auditability, or report correctness. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0860 | SQLite sidecar fallback shall use a full canonical JSONL scan and shall disclose the slower degraded mode in diagnostics. | Defer | Keep basic structured run telemetry in Phase 1; defer production service operations and platform monitoring. | These are service/platform concerns beyond the local canonical engine. |

### 8.1 Confirmed Security-Related Requirements

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0861 | Official AI Tool exports shall require metadata. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0862 | Official AI Tool exports shall require or create request id. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0863 | Official AI Tool exports shall validate inputs. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0864 | Official AI Tool exports shall use structured logging. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0865 | Official AI Tool exports shall return deterministic error codes. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0866 | Official AI Tool exports shall avoid silent failures. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0867 | Official AI Tool exports shall use a standard return schema. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0868 | Official AI Tool exports shall provide safe errors. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0869 | Internal engine services shall not be agent-callable unless wrapped deliberately. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0870 | Strategies shall not directly mutate official account, order, deal, position, margin, equity, or journal state. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0871 | The immutable journal shall preserve audit evidence. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0872 | Compliance records shall be created for accepted and rejected trade requests. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0873 | Pre-trade checks and risk-check evidence shall be recorded. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0874 | Parent-child order lineage shall be preserved where enabled for auditability. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0875 | Local trusted CLI or notebook usage may run without interactive authentication only when the process uses local filesystem permissions and does not expose a network listener. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0876 | Any network, multi-user, agent-orchestrated, or externally accessible `run_backtest` surface shall require authenticated actor identity. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0877 | External tool access shall enforce role-based authorization with at least `simulation.viewer`, `simulation.runner`, and `simulation.admin` roles. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0878 | `simulation.viewer` may read authorized reports and metadata but shall not launch runs or read protected journals. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0879 | `simulation.runner` may launch runs only for authorized strategy ids, data scopes, and artifact roots. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0880 | `simulation.admin` may manage approved broker profiles, data-authority manifests, retention policies, and benchmark baselines. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0881 | Every official run shall record actor id, auth context, role, request id, and authorization decision in audit metadata. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0882 | Strategy files, market data paths, broker profiles, and artifact destinations shall be resolved through approved registries or allowlisted roots, not arbitrary user-supplied filesystem paths. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0883 | External data-provider or broker credentials shall be read only from approved secrets providers or environment bindings and shall never be accepted as plain request payload fields. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0884 | Externally accessible simulator tools shall not be enabled until threat model, data-governance review, RBAC configuration, redaction policy, retention policy, and protected-artifact policy are approved. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0885 | The `run_backtest` AI Tool shall reject raw arbitrary Python strategy code strings before execution. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0886 | The `run_backtest` AI Tool shall require registered strategy identifiers or validated strategy configuration schemas. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0887 | The orchestration layer shall explicitly vet and sandbox any code-based strategy path before it can be executed. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0888 | The tool wrapper shall prevent arbitrary code execution through strategy input. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0889 | The tool wrapper shall prevent unregistered or unapproved strategy modules from being invoked. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0890 | The strategy registry shall be an explicit allowlist of approved strategy ids, module paths, version hashes, configuration schemas, and permitted execution modes. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0891 | Sandbox policy shall define allowed imports, denied imports, filesystem access, network access, subprocess access, environment-variable access, timeouts, memory limits, and prohibited operations before any code-based strategy path is enabled. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0892 | Code-based strategy execution approval shall require `simulation.admin` approval, strategy owner approval, sandbox profile id, vetting artifact hash, and recorded approval expiry. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0893 | Rejected code-injection attempts shall be logged with safe redaction. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0894 | Security-relevant rejections shall include deterministic error codes. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |

### 8.2 Data Governance, Redaction, and Retention

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0895 | Logs, reports, and journals may include run id, request id, actor id or pseudonymous actor id, strategy id, strategy version, symbol, timeframe, non-secret configuration, checksums, aggregate metrics, diagnostics, and artifact references. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0896 | Logs, reports, and journals shall not include API keys, tokens, passwords, private keys, full broker credentials, raw personal identifiers, payment data, unrestricted account identifiers, proprietary strategy source code, or raw proprietary market data payloads unless an explicit protected-artifact policy allows it. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0897 | Sensitive identifiers shall be redacted, hashed, or pseudonymized before appearing in standard logs or reports. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0898 | Production-candidate and validation journals, reports, and benchmark metadata shall default to a seven-year retention tier. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0899 | Research runs shall default to a 180-day retention tier. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0900 | Diagnostic failure logs shall default to a 90-day retention tier unless linked to a production-candidate incident. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0901 | Benchmark metadata attached to a release shall be retained for at least three years or the lifetime of the release line, whichever is longer. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0902 | Retention tier, deletion eligibility, and legal-hold status shall be stored in the artifact manifest. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0903 | Artifact export shall include checksums for reports, journals, tables, and benchmark files. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0904 | Protected artifacts shall be readable only by authorized roles and approved service identities. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0905 | Protected journals, artifact manifests, report bundles, and replay evidence shall define encryption-at-rest requirements before any externally accessible or production-candidate simulator surface is enabled. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0906 | Encryption-at-rest requirements shall define owning module, approved key source, key rotation expectations, failure behavior when encryption is unavailable, metadata redaction, and compatibility with checksum/signature verification. | Defer | Apply when an externally accessible or production-candidate service is approved; keep local safe defaults now. | The initial rebuild is a local FX engine, not a multi-tenant service. |
| V2-SIM-REQ-0907 | Phase 1 local-only research artifacts may remain unencrypted only when explicitly classified as local research, stored outside protected artifact roots, and excluded from production-candidate evidence. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |

### 8.3 Secure SDLC and Supply Chain

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0908 | Production releases shall require pinned dependency lockfiles. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0909 | Production releases shall generate an SBOM. | Modify | Treat as project/release gates outside Simulation; record evidence references in artifacts when available. | These are cross-cutting SDLC controls, not simulator behavior. |
| V2-SIM-REQ-0910 | Production releases shall pass dependency vulnerability scanning. | Modify | Treat as project/release gates outside Simulation; record evidence references in artifacts when available. | These are cross-cutting SDLC controls, not simulator behavior. |
| V2-SIM-REQ-0911 | Production releases shall pass secret scanning. | Modify | Treat as project/release gates outside Simulation; record evidence references in artifacts when available. | These are cross-cutting SDLC controls, not simulator behavior. |
| V2-SIM-REQ-0912 | Production releases shall pass static security analysis for public modules and official AI Tool wrappers. | Modify | Treat as project/release gates outside Simulation; record evidence references in artifacts when available. | These are cross-cutting SDLC controls, not simulator behavior. |
| V2-SIM-REQ-0913 | Production artifacts shall record git commit, dependency lock hash, container image digest when applicable, build timestamp, builder identity, and release signature. | Modify | Treat as project/release gates outside Simulation; record evidence references in artifacts when available. | These are cross-cutting SDLC controls, not simulator behavior. |
| V2-SIM-REQ-0914 | Official release artifacts shall be signed or checksum-verified before deployment. | Add | Add explicit safe tool validation, redaction, no-live-side-effects, and immutable audit evidence. | These are proportionate security requirements for the public tool. |
| V2-SIM-REQ-0915 | Third-party market-data adapters, broker-profile loaders, and optimization plugins shall be treated as supply-chain dependencies with approval status and version hashes. | Modify | Treat as project/release gates outside Simulation; record evidence references in artifacts when available. | These are cross-cutting SDLC controls, not simulator behavior. |

### Error Handling Expectations

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0916 | Every rejection shall return a deterministic error code. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0917 | Every skipped trade shall return a deterministic error code. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0918 | Every invalid configuration shall return a deterministic error code. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0919 | Every invalid data condition shall return a deterministic error code. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0920 | Every validation failure shall return a deterministic error code. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0921 | Every sizing failure shall return a deterministic error code. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0922 | Every execution failure shall return a deterministic error code. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0923 | Every failure shall be logged. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0924 | Severe data-quality failure shall block production runs unless diagnostic mode is explicitly enabled. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0925 | Accounting invariant violation shall stop the simulation unless diagnostic mode is explicitly enabled. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0926 | Unsupported fill policies shall be rejected before matching. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0927 | Missing required model data shall fail fast or be explicitly recorded as an approximation. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0928 | Stale FX conversion rates shall fail or be explicitly recorded according to configuration. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0929 | Safe errors shall be provided by the exported tool wrapper. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0930 | The system shall support the documented `SIM_*` error-code taxonomy. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0931 | The system shall return `SIM_PERSISTENCE_FAILED` when the journal cannot be written, flushed, fsynced, committed, indexed, or otherwise persisted. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0932 | The system shall stop production runs on `SIM_PERSISTENCE_FAILED`. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0933 | The system shall return `SIM_ARBITRARY_CODE_REJECTED` when raw arbitrary strategy code is passed to `run_backtest`. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0934 | The system shall return `SIM_FX_RATE_STALE` when a required FX conversion rate exceeds configured maximum age. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0935 | The system shall journal `SIM_IOC_REMAINDER_CANCELLED` when an IOC order remainder is cancelled after a valid partial fill. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0936 | `SIM_IOC_REMAINDER_CANCELLED` shall be classified as a non-fatal diagnostic code. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0937 | The system shall return or journal `SIM_FX_CROSS_RATE_REJECTED` when FX cross-rate synthesis is rejected due to invalid, circular, or skewed conversion paths. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0938 | The system shall return `SIM_RUN_ID_CONFLICT` when a run id or request id conflicts with an existing incompatible run. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0939 | The system shall return `SIM_CHECKPOINT_INCOMPATIBLE` when a resumed run fails checkpoint compatibility validation. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0940 | The system shall return `SIM_MODEL_GOVERNANCE_EXPIRED` when a required model inventory record or approval is expired. | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-0941 | The system shall return `SIM_RESEARCH_PROTOCOL_MISSING` when a production-candidate optimized strategy lacks the required research protocol manifest. | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-0942 | The system shall return `SIM_CALIBRATION_REQUIRED` when calibrated execution evidence is required but missing, expired, or invalid. | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-0943 | The system shall return `SIM_VENDOR_DATA_POLICY_VIOLATION` when data license, retention, revision, or point-in-time requirements are violated. | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-0944 | The system shall return `SIM_PROMOTION_EVIDENCE_MISSING` when a production promotion manifest lacks required evidence. | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-0945 | The system shall return or journal `SIM_DATA_PARTIAL` when partial data is quarantined according to `PartialDataPolicy`. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0946 | The system shall return or journal `SIM_DATA_STALE` when stale data is used under an explicit stale-data policy. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0947 | The system shall return `SIM_RESOURCE_QUOTA_EXCEEDED` when a request exceeds configured resource quotas. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0948 | The system shall return `SIM_QUEUE_LIMIT_EXCEEDED` when scheduler queue limits are exceeded. | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-0949 | The system shall journal `SIM_ENVIRONMENT_DRIFT_WARNING` when runtime environment differs from the certified benchmark profile. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0950 | The system shall return `SIM_WORKER_LOST_REQUEUED` as a non-fatal diagnostic when a lost worker causes a work unit to be requeued. | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-0951 | The system shall return `SIM_CANARY_DIVERGENCE` when canary comparison exceeds configured divergence tolerance. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0952 | The system shall return `SIM_FEATURE_LOOKAHEAD_DETECTED` when feature-store or alternative-data availability violates point-in-time rules. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0953 | The system shall return or journal `SIM_MARKET_HALT_ACTIVE` when trading is blocked or deferred by a halt or limit-up/limit-down state. | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-0954 | The system shall return or journal `SIM_KILL_SWITCH_TRIGGERED` when portfolio kill-switch policy blocks or alters trading. | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-0955 | The system shall return or journal `SIM_POISON_WORK_UNIT_QUARANTINED` when a repeated-failure work unit is quarantined. | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-0956 | The system shall return or journal `SIM_OPTIONAL_SERVICE_DEGRADED` when a non-production run falls back after optional cache or sidecar service failure. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-0957 | The system shall not log unsafe raw strategy code bodies in full when rejecting arbitrary-code input. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0958 | Strategy-input rejection diagnostics shall include request id, strategy identifier when present, rejection reason, and deterministic error code. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0959 | Persistence-failure diagnostics shall include journal backend, run id, failed operation, and last committed sequence number. | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |

### Confirmed Error and Diagnostic Codes

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-0960 | `SIM_INVALID_CONFIG` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0961 | `SIM_INVALID_DATE_RANGE` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0962 | `SIM_MISSING_SYMBOL` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0963 | `SIM_UNSUPPORTED_TICK_MODEL` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0964 | `SIM_UNSUPPORTED_SPREAD_MODEL` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0965 | `SIM_UNSUPPORTED_LIQUIDITY_MODEL` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0966 | `SIM_UNSUPPORTED_SLIPPAGE_MODEL` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0967 | `SIM_UNSUPPORTED_COMMISSION_MODEL` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0968 | `SIM_UNSUPPORTED_SWAP_MODEL` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0969 | `SIM_DATA_EMPTY` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0970 | `SIM_DATA_MISSING_COLUMN` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0971 | `SIM_DATA_DUPLICATE_TIMESTAMP` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0972 | `SIM_DATA_NON_MONOTONIC_TIME` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0973 | `SIM_DATA_NEGATIVE_SPREAD` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0974 | `SIM_DATA_INVALID_OHLC` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0975 | `SIM_DATA_PRICE_OUTLIER` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0976 | `SIM_DATA_QUALITY_FAILED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0977 | `SIM_LOOKAHEAD_DETECTED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0978 | `SIM_INVALID_VOLUME` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0979 | `SIM_VOLUME_BELOW_MIN` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0980 | `SIM_VOLUME_ABOVE_MAX` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0981 | `SIM_VOLUME_STEP_MISMATCH` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0982 | `SIM_INVALID_STOPS_LEVEL` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0983 | `SIM_FREEZE_LEVEL_VIOLATION` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0984 | `SIM_INSUFFICIENT_MARGIN` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0985 | `SIM_PORTFOLIO_RISK_REJECTED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0986 | `SIM_CORRELATION_LIMIT_EXCEEDED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0987 | `SIM_CONCENTRATION_LIMIT_EXCEEDED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0988 | `SIM_MARKET_CLOSED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0989 | `SIM_GAP_HANDLING_REJECTED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0990 | `SIM_INVALID_PRICE` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0991 | `SIM_SLIPPAGE_EXCEEDED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0992 | `SIM_LIQUIDITY_UNAVAILABLE` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0993 | `SIM_PARTIAL_FILL_REMAINDER` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0994 | `SIM_UNSUPPORTED_FILL_POLICY` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0995 | `SIM_LIMIT_QUEUE_NOT_FILLED` | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-0996 | `SIM_PENDING_ORDER_EXPIRED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0997 | `SIM_POSITION_NOT_FOUND` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0998 | `SIM_ORDER_NOT_FOUND` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-0999 | `SIM_SIZING_FAILED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1000 | `SIM_SIZING_REQUIRES_STOP_LOSS` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1001 | `SIM_SIZING_INVALID_ATR` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1002 | `SIM_SIZING_INVALID_KELLY_INPUTS` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1003 | `SIM_SYNTHETIC_TICK_GENERATION_FAILED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1004 | `SIM_PERSISTENCE_FAILED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1005 | `SIM_ARBITRARY_CODE_REJECTED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1006 | `SIM_SPREAD_MISSING` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1007 | `SIM_COMMISSION_CALCULATION_FAILED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1008 | `SIM_SWAP_CALCULATION_FAILED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1009 | `SIM_FX_RATE_STALE` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1010 | `SIM_FX_CROSS_RATE_REJECTED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1011 | `SIM_IOC_REMAINDER_CANCELLED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1012 | `SIM_DATA_PARTIAL` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1013 | `SIM_DATA_STALE` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1014 | `SIM_RESOURCE_QUOTA_EXCEEDED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1015 | `SIM_QUEUE_LIMIT_EXCEEDED` | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-1016 | `SIM_ENVIRONMENT_DRIFT_WARNING` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1017 | `SIM_WORKER_LOST_REQUEUED` | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-1018 | `SIM_CANARY_DIVERGENCE` | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1019 | `SIM_FEATURE_LOOKAHEAD_DETECTED` | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-1020 | `SIM_MARKET_HALT_ACTIVE` | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-1021 | `SIM_KILL_SWITCH_TRIGGERED` | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-1022 | `SIM_POISON_WORK_UNIT_QUARANTINED` | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-1023 | `SIM_OPTIONAL_SERVICE_DEGRADED` | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1024 | `SIM_RUN_ID_CONFLICT` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1025 | `SIM_CHECKPOINT_INCOMPATIBLE` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1026 | `SIM_MODEL_GOVERNANCE_EXPIRED` | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-1027 | `SIM_RESEARCH_PROTOCOL_MISSING` | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-1028 | `SIM_CALIBRATION_REQUIRED` | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-1029 | `SIM_VENDOR_DATA_POLICY_VIOLATION` | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-1030 | `SIM_PROMOTION_EVIDENCE_MISSING` | Defer | Reserve only if the deferred capability is later promoted; do not implement a dead code path now. | The triggering behavior is outside Phase 1. |
| V2-SIM-REQ-1031 | `SIM_EVENT_PRIORITY_CONFLICT` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1032 | `SIM_ACCOUNT_INVARIANT_BROKEN` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1033 | `SIM_PERFORMANCE_GATE_FAILED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1034 | `SIM_MONTE_CARLO_FAILED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1035 | `SIM_OPTIMIZATION_FAILED` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |
| V2-SIM-REQ-1036 | `SIM_INTERNAL_ERROR` | Add | Include in the versioned Phase 1 `SIM_*` taxonomy when mapped to an accepted behavior and verification test. | Deterministic safe failures are essential. |

### Phase 1 Edge and Error Matrix

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1037 | Invalid date range. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1038 | Missing symbol. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1039 | Unsupported tick model. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1040 | Unsupported spread model. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1041 | Unsupported liquidity model. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1042 | Unsupported slippage model. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1043 | Unsupported commission model. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1044 | Unsupported swap model. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1045 | Empty data. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1046 | Missing required data columns. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1047 | Duplicate timestamps. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1048 | Non-monotonic timestamps. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1049 | Negative spread. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1050 | Missing spread. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1051 | Zero or negative prices. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1052 | Invalid OHLC bars. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1053 | Price outliers. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1054 | Missing bars beyond threshold. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1055 | Tick volume less than or equal to zero. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1056 | Synthetic tick generation with tick volume equal to 1. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1057 | Synthetic tick generation with tick volume equal to 2. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1058 | Synthetic tick generation with tick volume equal to 3. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1059 | Synthetic tick generation with tick volume greater than 3. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1060 | Generated ticks exceeding OHLC bounds. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1061 | Current-bar lookahead detected. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1062 | Invalid volume. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1063 | Volume below minimum. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1064 | Volume above maximum. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1065 | Volume step mismatch. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1066 | Invalid stop-loss or take-profit direction. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1067 | Stops-level violation. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1068 | Freeze-level violation. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1069 | Insufficient margin. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1070 | Portfolio-risk rejection. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1071 | Correlation limit exceeded. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1072 | Concentration limit exceeded. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1073 | Market closed. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1074 | Market order submitted outside session. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1075 | Weekend or session gap. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1076 | Gap through stop loss. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1077 | Gap through take profit. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1078 | Ambiguous same-gap SL/TP hit. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1079 | Same-tick SL/TP conflict. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1080 | Stopout and strategy intent on same tick. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1081 | Pending order expiration and trigger on same tick. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1082 | Unsupported fill policy. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1083 | Insufficient liquidity. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1084 | Partial-fill remainder. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1085 | Limit order touched but queue not filled. | Defer | Move this verification to the Future Extensions Annex. | Its target capability is outside Phase 1. |
| V2-SIM-REQ-1086 | Slippage cap exceeded. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1087 | Position not found. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1088 | Order not found. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1089 | Sizing requires stop loss. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1090 | Invalid ATR sizing input. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1091 | Invalid Kelly sizing input. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1092 | Commission calculation failure. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1093 | Swap calculation failure. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1094 | Event-priority conflict. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1095 | Accounting invariant violation. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1096 | Monte Carlo failure. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1097 | Optimization failure. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1098 | Missing corporate-action data when required. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1099 | Unsupported merger, spinoff, or delisting behavior. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1100 | Reverse split fractional quantity handling. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1101 | Missing futures contract chain when required. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1102 | Continuous-adjusted indicator values used for non-tradeable execution prices. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1103 | Missing perpetual funding rate when required. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1104 | Missing, stale, or unusable FX conversion rate. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1105 | Disabled regulatory checks for regulated asset-class reports. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1106 | Synthetic tick generation resumes from checkpoint mid-run. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1107 | Synthetic tick generation is parallelized by symbol. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1108 | Synthetic tick generation is parallelized by date chunk. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1109 | Synthetic tick generation processes bars out of chronological order. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1110 | Optimization run produces too many journal events for memory. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1111 | Walk-forward run produces too many journal events for memory. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1112 | Monte Carlo run attempts to materialize all journals in memory. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1113 | Journal append-to-disk write fails. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1114 | Journal backend becomes unavailable mid-run. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1115 | Journal write succeeds but flush or commit fails. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1116 | SQLite sidecar index transaction fails. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1117 | Raw Python strategy code is supplied to `run_backtest`. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1118 | Strategy identifier does not exist in registry. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1119 | Strategy identifier resolves to an unapproved module. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1120 | Sandbox or vetting metadata is missing for code-based strategy execution. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1121 | Tick batching approaches active stop loss. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1122 | Tick batching approaches active take profit. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1123 | Tick batching approaches pending-order trigger. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1124 | Tick batching approaches order expiration. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1125 | Tick batching approaches stopout threshold. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1126 | Tick batching approaches bar-open signal boundary. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1127 | Tick batching approaches session boundary. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1128 | Tick batching approaches gap boundary. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1129 | Tick batching approaches swap rollover. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1130 | Tick batching approaches scheduled strategy callback. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1131 | Tick batching approaches compliance boundary. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1132 | IOC order partially fills and cancels remainder. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1133 | FX rate is present but stale. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1134 | FX stale-rate diagnostic override is enabled. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1135 | FX cross-rate synthesis creates a circular path. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1136 | FX cross-rate synthesis produces a skewed or invalid conversion rate. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1137 | Equity short position spans a borrow-fee accrual boundary. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1138 | Borrow-fee data is missing for hard-to-borrow equity. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1139 | Borrow-fee currency differs from account currency. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1140 | Malformed request payload. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1141 | Unknown request field. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1142 | Invalid enum casing. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1143 | Missing required request field. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1144 | Request payload exceeds configured size limit. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1145 | Timezone-naive timestamp. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1146 | Date range crosses a DST or session-boundary ambiguity. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1147 | Broker-profile timezone rules are missing for a local session calendar. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1148 | Spring-forward local session time gap cannot be mapped to UTC. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1149 | Fall-back local session duplicate maps to multiple possible UTC instants. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1150 | Unauthorized actor attempts to launch a run. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1151 | Authorized actor lacks access to requested strategy id, data scope, broker profile, journal, or artifact root. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1152 | Artifact path attempts directory traversal or resolves outside allowlisted roots. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1153 | Secrets, tokens, broker credentials, authorization headers, or provider credentials are supplied in request payload fields. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1154 | Data manifest checksum mismatch. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1155 | Broker profile manifest is unavailable or checksum-mismatched. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1156 | Market-data authority manifest is unavailable, expired, or checksum-mismatched. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1157 | Artifact store is unavailable before run start. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1158 | Filesystem permission is denied for journal, sidecar index, report, or artifact root. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1159 | Disk becomes full during journal append, report generation, sidecar index write, or artifact manifest write. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1160 | Canonical journal exists but the SQLite sidecar index is corrupted. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1161 | Canonical journal hash chain or sequence validation fails. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1162 | Duplicate request id is submitted concurrently. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1163 | Duplicate request id is replayed with incompatible material fields. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1164 | External dependency timeout occurs during data manifest, broker profile, artifact store, secrets-provider, scheduler, worker heartbeat, or optional service access. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1165 | Concurrent read of `MarketDataAuthorityManifest` by multiple optimization workers. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1166 | Corrupted artifact manifest is encountered during replay or report generation. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1167 | Protected journal access is denied to a viewer or unauthorized service account. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |

### Phase 1 Test Suite

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1168 | `run_backtest` contract tests for success, failed, cancelled, queued where supported, and diagnostic-failed envelopes. | Defer | Move this verification to the Future Extensions Annex. | Its target capability is outside Phase 1. |
| V2-SIM-REQ-1169 | Request validation tests for required fields, unknown fields, malformed payloads, invalid enum casing, invalid date range, missing symbol, oversized payload, path traversal, and secrets in payload fields. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1170 | Registered strategy reference tests proving raw Python strategy-code strings are rejected before import or execution. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1171 | Data authority tests proving `MarketDataAuthorityManifest` presence, checksum, point-in-time status, and authorization are validated before execution. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1172 | Broker profile fixture tests for approved FX symbol metadata, precision, volume constraints, spread, swap, margin, sessions, and hash stability. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1173 | Tick execution tests for canonical bid/ask tick order, signal timing, previous-closed-bar behavior, and no vectorized official fills. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1174 | Synthetic tick determinism tests for per-bar seed derivation under sequential, chunked, out-of-order, and checkpoint-resumed processing. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1175 | Spread, slippage, commission, swap, margin, and accounting golden tests for the approved FX fixture set. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1176 | Gap-handling tests for rejection, fill-at-open, fill-with-slippage, and ambiguous SL/TP conservative outcome. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1177 | FX conversion tests for direct, inverse, stale, and rejected cross-rate paths according to approved Phase 1 settings. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1178 | Journal persistence tests for append-only JSONL, SQLite sidecar indexing, hash-chain/sequence validation, replay, and fail-closed persistence errors. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1179 | Fault-injection tests for disk-full during journal append, disk-full during report generation, flush failure, fsync failure, SQLite sidecar transaction failure, and artifact manifest write failure. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1180 | Fault-injection tests shall verify `SIM_PERSISTENCE_FAILED` is returned, the run halts cleanly, the last committed JSONL sequence remains recoverable, and corrupted partial artifacts are not promoted. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1181 | Timezone/DST tests proving broker-profile timezone rules map local sessions to UTC and reject unresolved spring-forward gaps or fall-back duplicate ambiguity before execution. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1182 | Concurrent manifest-read tests proving immutable `MarketDataAuthorityManifest` reads are thread-safe for multiple workers and conflicting manifest versions are rejected deterministically. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1183 | Report tests for canonical JSON report, required Markdown report, realism disclosure, data-quality summary, cost summary, and artifact manifest. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1184 | No-live-side-effect tests proving Simulation cannot call live broker mutation paths. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1185 | Import-time safety tests proving public Simulation imports perform no network, broker, filesystem write, worker, scheduler, or secret-read side effects. | Defer | Move this verification to the Future Extensions Annex. | Its target capability is outside Phase 1. |
| V2-SIM-REQ-1186 | Requirement-to-test traceability report for all accepted Phase 1 requirements. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |

### 9.0 Contract, Traceability, and Import-Safety Gates

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1187 | Contract tests shall verify `run_backtest` success envelopes include `schema_version`, `request_id`, `status`, `result`, `error`, `warnings`, `metadata`, and `artifacts`. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1188 | Contract tests shall verify failed, queued, cancelled, and diagnostic-failed responses preserve the same envelope shape and include deterministic `SIM_*` error codes where applicable. | Defer | Move this verification to the Future Extensions Annex. | Its target capability is outside Phase 1. |
| V2-SIM-REQ-1189 | Contract tests shall verify unknown fields, malformed payloads, invalid enum casing, missing required fields, timezone-naive dates, oversized payloads, and path traversal attempts. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1190 | Contract tests shall verify public schema backward compatibility within a major schema version. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1191 | Traceability tests shall verify every accepted implementation requirement has `requirement_id`, `phase`, `priority`, `acceptance_criteria`, `verification_method`, and at least one mapped verification gate. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1192 | Traceability tests shall verify no `future`, `enterprise`, or asset-class-expansion requirement is marked blocking for Phase 1 without owner approval. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1193 | Usage examples shall run as executable documentation tests and assert exact success or failure envelope shape. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1194 | Usage examples shall include canonical FX backtest, severe data-quality blocked run, optimization with streaming journal persistence, and raw Python strategy-code rejection. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1195 | Import-time tests shall verify public module import performs no filesystem writes, network access, worker startup, secret reads, market-data access, broker access, or long-running initialization. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1196 | Boundary tests shall verify Simulation does not call live broker execution paths and does not mutate strategy-owned state except through approved callbacks or returned diagnostics. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1197 | Security tests shall verify unauthenticated network or agent-orchestrated access is rejected, each RBAC role is enforced, secrets in payloads are rejected and redacted, and rejected raw strategy code is not executed or logged in full. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |

### 9.1 Unit and Integration Test Areas

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1198 | Config tests shall cover invalid dates, invalid tick model, invalid spread model, invalid liquidity model, invalid fee/swap config, and missing symbol. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1199 | Data-quality tests shall cover missing columns, invalid OHLC, duplicate timestamps, non-monotonic time, negative spreads, price outliers, and missing bars. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1200 | Partial-data tests shall cover symbol-day quarantine, stale-data fallback, stale-data age limits, whole-run failure, and production-realism downgrade behavior. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1201 | Signal-timing tests shall cover previous-close-only behavior, shifted signals, no current-bar leakage, and first tick of new bar activation. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1202 | Tick-factory tests shall cover timeframe ticks, M1 ticks, real ticks, synthetic ticks, sequence order, and bar-open flags. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1203 | Synthetic-tick tests shall cover volume 1, volume 2, volume 3, volume greater than 3, support points, determinism, bounds, and MQL5-style behavior. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1204 | Synthetic-tick tests shall verify that per-bar seed derivation produces identical ticks for full sequential runs, chunked runs, out-of-order bar processing, and checkpoint-resumed runs. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1205 | Synthetic-tick tests shall verify that different symbols and different bar-open timestamps produce independent deterministic synthetic tick streams. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1206 | Spread tests shall cover native, fixed, variable, missing spread, negative spread, and deterministic random spread. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1207 | Market-calendar and gap tests shall cover market-closed rejection, session open, weekend gap, gap-through SL, gap-through TP, and SL/TP ambiguity. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1208 | Market-halt tests shall cover market-wide halts, symbol halts, limit-up/limit-down states, halted order rejection or deferral, and resumed trading. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1209 | Event-priority tests shall cover same-tick SL/TP conflict, stopout priority, expiration before trigger, and deterministic ordering. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1210 | Position-sizing tests shall cover all sizing modes, invalid inputs, volume normalization, and margin failure. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1211 | Broker-rule tests shall cover supported fill policies, max pending orders, max positions, hedging/netting rules, and stopout thresholds. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1212 | Portfolio-risk tests shall cover exposure, concentration, correlation, portfolio margin, and multi-symbol margin aggregation. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1213 | Kill-switch tests shall cover drawdown, loss, exposure, margin, volatility, and error-triggered trading halt behavior. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1214 | Liquidity tests shall cover infinite liquidity, volume-dependent liquidity, order-book walking, insufficient liquidity, partial fills, and market impact. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1215 | Slippage tests shall cover fixed, spread-relative, volatility-based, volume-dependent, cap exceeded, and deterministic random slippage. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1216 | Liquidity and slippage tests shall verify that liquidity constraints are evaluated before slippage and that slippage applies only to actually filled volume. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1217 | Latency tests shall cover fixed latency, distribution latency, component latency, delayed eligibility, and latency interaction with missed fills. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1218 | Execution-quality tests shall verify that liquidity shortfall is distinguished from slippage cost. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1219 | Fee and commission tests shall cover per-lot, per-trade, percent-notional, tiered, maker/taker, min/max commission, and currency conversion. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1220 | Pass-through fee tests shall cover regulatory, exchange, clearing, transaction, activity, rebate, SEC Section 31, FINRA TAF, and maker/taker fee attribution where configured. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1221 | Swap tests shall cover daily rollover, triple-swap day, long/short swap, and disabled-swap disclosure. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1222 | Validation tests shall cover volume, stops, freeze, price, margin, portfolio, max positions/orders, and unsupported fill policy. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1223 | Matching tests shall cover market order, pending trigger, stop-limit, SL/TP, gap, partial fill, and order-book fill. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1224 | Advanced-order tests shall cover trailing stops, pegged orders, cancel-replace behavior, queue-priority effects, and deterministic repricing. | Defer | Move this verification to the Future Extensions Annex. | Its target capability is outside Phase 1. |
| V2-SIM-REQ-1225 | Accounting tests shall cover equity, margin, free margin, margin level, realized/floating PnL, commission, swap, and stopout. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1226 | Strategy tests shall cover EMA trend intents, martingale recovery, decomposition child orders, and partial-fill handling. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1227 | Model-governance tests shall cover model inventory validation, expired approvals, missing validation evidence, and accepted model exceptions. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1228 | Dynamic-materiality tests shall cover run-level materiality upgrades from exposure, capital, liquidity usage, instrument universe, and external distribution mode. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1229 | Research-integrity tests shall cover missing protocol manifests, post-hoc selection disclosure, out-of-sample degradation thresholds, and parameter-sensitivity evidence. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1230 | Execution-calibration tests shall cover missing calibration artifacts, stale calibration artifacts, calibration error-band failures, and uncalibrated realism downgrades. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1231 | Capacity tests shall cover capital scaling diagnostics, participation-rate limits, approved-capacity violations, and capacity disclosure. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1232 | Run-lifecycle tests shall cover idempotent retries, duplicate run ids, cancellation artifacts, checkpoint compatibility, and lifecycle transition journaling. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1233 | Reporting tests shall verify metrics are reproducible from the journal and include realism disclosure, cost diagnostics, and portfolio diagnostics. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1234 | Monte Carlo tests shall cover bootstrap reproducibility, confidence interval outputs, and failure handling. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1235 | Optimization tests shall cover grid/random runs, walk-forward IS/OOS split, overfit rejection, and deterministic parameter ranking. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1236 | Optimization-cache tests shall cover provenance hash hits, provenance hash misses, failed work-unit exclusion, resumable manifests, and isolated worker state. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1237 | Journal persistence tests shall cover streaming append behavior, journal replay from append-only storage, SQLite sidecar indexing, and report generation from persisted journals. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1238 | Journal persistence tests shall verify optimization, walk-forward, and Monte Carlo runs do not retain all journals in memory. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1239 | Journal persistence tests shall verify journal write, flush, fsync, sidecar transaction, and commit failures return `SIM_PERSISTENCE_FAILED`. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1240 | Journal persistence tests shall verify last committed journal sequence is recoverable after persistence failure. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1241 | Checkpoint and resume tests shall cover checkpoint age limits, checkpoint compatibility, OOM-style restart, worker loss, requeue behavior, and duplicate artifact prevention. | Defer | Move this verification to the Future Extensions Annex. | Its target capability is outside Phase 1. |
| V2-SIM-REQ-1242 | Performance tests shall cover tick generation benchmark, tick loop benchmark, memory benchmark, and optimization benchmark. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1243 | Performance tests shall include memory profiles for optimization, walk-forward, and Monte Carlo runs with streaming journal persistence enabled. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1244 | Tick-batching tests shall verify batching stops before active stop loss, active take profit, pending-order trigger, order expiration, stopout threshold, bar-open signal boundary, scheduled strategy callback, market session boundary, gap boundary, swap rollover boundary, and compliance boundary. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1245 | Tick-batching tests shall verify batching does not use future bar high, low, close, or volume to prove safety. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1246 | Performance-gate tests shall cover runtime regression threshold, memory regression threshold, benchmark manifest fields, and benchmark-profile validation. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1247 | Corporate-action tests shall cover dividend cashflow, split adjustment, reverse split, merger/delisting policy, adjusted/unadjusted price modes, and journal disclosure. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1248 | Delisting tests shall cover final exchange price, OTC price, cash consideration, liquidation value, total-loss treatment, and prevention of silent symbol dropping. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1249 | Short-recall tests shall cover deterministic recall events, seeded probabilistic recall, forced buy-ins, market-halt interaction, liquidity, fees, and journal attribution. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1250 | Futures-rollover tests shall cover contract expiry, roll date selection, continuous adjustment, calendar-spread roll, roll PnL attribution, and missing contract-chain failure. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1251 | Perpetual-funding tests shall cover funding interval, long/short funding direction, funding currency conversion, and missing funding-rate behavior. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1252 | Multi-currency-accounting tests shall cover realized PnL conversion, floating PnL conversion, margin conversion, fee/swap/dividend/funding conversion, and stale FX-rate rejection. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1253 | FX staleness tests shall verify stale rates return `SIM_FX_RATE_STALE`, diagnostic overrides require explicit configuration, and stale-rate overrides are journaled and disclosed. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1254 | FX cross-rate tests shall verify circular paths, mathematically invalid rates, and skewed rates outside configured tolerance return or journal `SIM_FX_CROSS_RATE_REJECTED`. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1255 | Benchmark tests shall cover benchmark alignment, currency conversion, alpha, beta, information ratio, tracking error, and benchmark-relative drawdown. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1256 | Order-chaining tests shall cover parent-child lineage, partial-fill child links, decomposition remainder, and bracket/OCO chain integrity. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1257 | Regulatory-constraint tests shall cover PDT rule, short-sale locate, position limits, and disabled-regulatory disclosure. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1258 | Regulatory-constraint tests shall cover SEC Rule 201 alternative uptick-rule restrictions when required data is available. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1259 | Wash-sale tests shall cover optional taxable-account diagnostics, configured windows, substantially identical instrument mapping, and after-tax disclosure when enabled. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1260 | Replay tests shall verify same seed, config, and data produce identical output. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1261 | Broker-profile tests shall cover `mt5_demo_reference_fx_v1` metadata, symbol spec hashes, session rules, swap rules, margin rules, and fixture provenance. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1262 | Rounding tests shall cover tick-size price normalization, adverse rounding, currency cashflow rounding, FX conversion rounding, point precision, and fractional volume steps. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1263 | Schema tests shall cover `SimulationResult`, official AI Tool response envelopes, report JSON, report Markdown metadata, artifact manifests, and backward-compatible schema versioning. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1264 | Security tests shall cover local trusted mode, external authentication requirement, RBAC authorization, allowlisted strategy/data/artifact roots, secret rejection, and safe errors. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1265 | Secure-SDLC tests shall cover dependency lock validation, SBOM generation, vulnerability scan evidence, secret scan evidence, release artifact checksums, and release signatures where enabled. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1266 | Service-operations tests shall cover resource quotas, queue backpressure, queued run status, queue limit rejection, cancellation, environment drift warnings, synthetic transaction probes, and canary divergence handling. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1267 | Chaos and fault-injection tests shall simulate disk-full, permission-denied, journal flush failure, sidecar transaction failure, artifact-store outage, and worker heartbeat loss with deterministic error envelopes and no silent artifact promotion. | Defer | Move this verification to the Future Extensions Annex. | Its target capability is outside Phase 1. |
| V2-SIM-REQ-1268 | Observability tests shall cover trace context propagation, required pipeline spans, business metrics export, SLO burn-rate alert inputs, and predictive alert rule configuration where supported. | Defer | Move this verification to the Future Extensions Annex. | Its target capability is outside Phase 1. |
| V2-SIM-REQ-1269 | Data-lineage tests shall verify lineage from deal and PnL events back to generated ticks, support points, M1 bars, normalized rows, raw vendor files, source manifests, and checksums where applicable. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1270 | Distributed-worker tests shall cover deterministic work-unit decomposition, stateless worker execution, shared artifact-store usage, cache checksum validation, worker heartbeat expiry, and preemptible-worker requeue. | Defer | Move this verification to the Future Extensions Annex. | Its target capability is outside Phase 1. |
| V2-SIM-REQ-1271 | Distributed-worker tests shall cover poison-pill work-unit quarantine, idempotent journal writes, distributed-lock or compare-and-swap commits, and duplicate checkpoint prevention. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1272 | Optional-service degradation tests shall cover warm-cache failure, SQLite sidecar outage, JSONL scan fallback, non-production degraded diagnostics, and production fail-closed behavior. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1273 | Feature-store tests shall cover point-in-time retrieval, availability timestamps, publication lag, microsecond decision timestamps, and feature lookahead rejection. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1274 | Alternative-data tests shall cover irregular event times, delayed publication, ingestion timestamps, as-of alignment, lag policy, embargo policy, and no-lookahead behavior. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1275 | Debug-replay tests shall cover pause by timestamp, journal sequence, event, bar boundary, strategy callback, and error condition with deterministic resume. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1276 | Visual-replay-export tests shall cover schema validation, signals, fills, order events, equity overlays, drawdown overlays, halt annotations, and derivation from canonical journal artifacts. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1277 | Report-confidence-interval tests shall verify material production-realistic metrics include confidence intervals or explicit omission disclosure and downgrade behavior. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1278 | Vendor-governance tests shall cover vendor inventory records, license conflicts, point-in-time snapshot requirements, vendor restatement policy, and immutable historical artifacts. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1279 | Promotion-manifest tests shall cover required evidence artifacts, expired approvals, hash mismatches, missing classification, and manifest retention. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1280 | Retention and redaction tests shall cover retention tiers, legal-hold metadata, artifact checksums, disallowed secret fields, pseudonymized actors, and protected artifact access. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1281 | AI Tool strategy security tests shall verify `run_backtest` rejects raw arbitrary Python strategy code, returns `SIM_ARBITRARY_CODE_REJECTED`, does not execute rejected code, and does not log rejected code in full. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1282 | AI Tool strategy security tests shall verify registered strategy identifiers succeed when schemas are valid, unregistered strategy identifiers are rejected, unapproved modules are rejected, and invalid strategy configuration schemas are rejected. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1283 | IOC remainder tests shall verify partial-fill remainder cancellation journals `SIM_IOC_REMAINDER_CANCELLED`, does not fail a valid partial-fill simulation, and appears in execution-quality diagnostics. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1284 | Borrow-fee tests shall verify equity and ETF short borrow fees accrue daily and tick-by-tick when configured, remain distinct from swap and dividends, convert to account base currency, and appear in reports. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |

### 9.2 Production Hardening Gates

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1285 | Determinism gate shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1286 | Accounting gate shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1287 | Execution realism gate shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1288 | Portfolio risk gate shall pass for multi-symbol runs. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1289 | MT5 parity gate shall pass within documented tolerance for supported semantics. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1290 | Performance gate shall pass before production promotion. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1291 | Model-governance gate shall pass before production promotion. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1292 | Research-integrity gate shall pass before production promotion. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1293 | Execution-calibration gate shall pass before production-realistic promotion when calibrated execution models are required. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1294 | Supply-chain gate shall pass before production release. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1295 | CI gate shall pass before production merge. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |

### 9.3 CI Requirements

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1296 | `ruff` shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1297 | `black` shall pass. | Open Decision | Use the project-wide formatter/linter policy selected during cross-domain alignment. | Tooling policy is not established by the two source documents. |
| V2-SIM-REQ-1298 | `mypy` shall pass for public modules. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1299 | `pytest` shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1300 | Test coverage shall be at least 80%. | Add | Require at least 80% coverage for the accepted Phase 1 package. | This is explicit and measurable. |
| V2-SIM-REQ-1301 | No official tool shall be exported without metadata/schema tests. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1302 | Deterministic replay tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1303 | Synthetic tick tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1304 | Accounting invariant tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1305 | Liquidity and partial-fill tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1306 | Event-priority tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1307 | Portfolio-risk tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1308 | Swap and gap tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1309 | Data-quality tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1310 | Response schema and artifact manifest tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1311 | Broker-profile fixture tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1312 | Rounding and precision tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1313 | Security, redaction, and retention tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1314 | Optimization cache and resumability tests shall pass when optimization is enabled. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1315 | Per-bar synthetic tick seed tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1316 | Streaming journal persistence and failure tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1317 | AI Tool strategy-injection rejection tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1318 | Tick-batching boundary proof tests shall pass when tick batching is enabled. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1319 | IOC remainder diagnostic tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1320 | FX staleness and cross-rate rejection tests shall pass. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1321 | Borrow-fee tests shall pass before equity or ETF short-selling runs are production-promoted. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1322 | Model-governance, research-integrity, run-lifecycle, vendor-governance, and promotion-manifest tests shall pass before production promotion workflows are enabled. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1323 | Dependency lock, SBOM, vulnerability scan, secret scan, static security analysis, and artifact checksum checks shall pass before production release workflows are enabled. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1324 | Service-mode CI shall include resource-quota, queue, tracing, business-metric, synthetic-probe, canary, data-lineage, checkpoint-resume, and distributed-worker tests before production service deployment. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |

### 6.3 Usage Examples

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1325 | Successful canonical FX backtest using a registered strategy id and approved data/broker manifests. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1326 | Failed request that validates `SIM_INVALID_DATE_RANGE` before data access. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1327 | Failed request that validates `SIM_ARBITRARY_CODE_REJECTED` before strategy import or execution. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1328 | Severe data-quality blocked run that returns `diagnostic_failed` and does not claim `production_realistic` or `mt5_parity_oriented`. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1329 | `diagnostic_failed` envelope example showing bounded diagnostics, warnings, safe error details, artifacts, and non-promotable classification. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1330 | `queued` envelope example showing run id, queue position or bounded queue metadata where available, retry/cancellation metadata, warnings, and no completed result. | Defer | Move this verification to the Future Extensions Annex. | Its target capability is outside Phase 1. |

### Example 1 — Canonical FX backtest request

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1331 | The tool validates config, data quality, strategy registry, broker profile, and market-data authority requirements. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1332 | Signals are converted to timestamped `TradeIntent` objects. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1333 | Official fills are produced only by the canonical tick loop. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1334 | The result includes a `SimulationResult`, journal artifact, JSON report, Markdown report, artifact manifest, metrics, and realism disclosure. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |

### Example 2 — Severe data-quality blocked run

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1335 | Severe missing bars, duplicate timestamps, negative spreads, invalid OHLC bars, or lookahead-sensitive feature data block production runs. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1336 | The response returns a deterministic `SIM_*` error code, bounded diagnostics, and any safe partial artifacts. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1337 | The run is not labelled `production_realistic` or `mt5_parity_oriented` after severe data-quality failure. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |

### Example 3 — Optimization with streaming journal persistence

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1338 | Optimization uses the same canonical tick execution engine as normal backtests. | Defer | Retain as a later test obligation when its capability is promoted. | The underlying behavior is deferred or belongs to another domain. |
| V2-SIM-REQ-1339 | Work units are deterministic and resumable. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1340 | Journals are streamed to disk instead of held fully in memory. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |
| V2-SIM-REQ-1341 | Ranking is deterministic when objective scores tie. | Add | Add a verification gate for the corresponding accepted Phase 1 behavior. | The core simulator currently lacks runnable implementation evidence. |

### Requirement Metadata And Traceability

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1342 | Before Builder handoff, every accepted requirement shall include `requirement_id`, `release_phase`, `priority`, `owner`, `status`, `acceptance_criteria`, `dependencies`, and `verification_method`. | Add | Use this as the release-scope and traceability gate for the accepted reconciliation decisions. | The V2 document is too broad to hand directly to a builder. |
| V2-SIM-REQ-1343 | Requirement IDs shall use stable prefixes such as `SIM-FR`, `SIM-NFR`, `SIM-SEC`, `SIM-EDGE`, `SIM-TEST`, `SIM-BR`, and `SIM-DOC`. | Add | Use this as the release-scope and traceability gate for the accepted reconciliation decisions. | The V2 document is too broad to hand directly to a builder. |
| V2-SIM-REQ-1344 | The test plan shall include a requirements-to-tests traceability matrix mapping every accepted requirement ID to one or more unit, integration, contract, replay, security, performance, CI, benchmark, or documented manual verification gates. | Add | Use this as the release-scope and traceability gate for the accepted reconciliation decisions. | The V2 document is too broad to hand directly to a builder. |
| V2-SIM-REQ-1345 | A generated traceability report shall fail CI when an accepted implementation requirement lacks mapped verification or when a future requirement is marked blocking for Phase 1 without owner approval. | Add | Use this as the release-scope and traceability gate for the accepted reconciliation decisions. | The V2 document is too broad to hand directly to a builder. |
| V2-SIM-REQ-1346 | External contracts required for implementation shall be attached or summarized in this file before Builder handoff, including strategy outputs, indicator manifests, data manifests, broker profiles, market-data authority manifests, and the active source-of-truth baseline. | Modify | Narrow to the approved capability set and exact contracts from this reconciliation. | The broad baseline must be reduced before implementation. |

### Phase 1 Builder Slice

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1347 | The first Builder-ready implementation scope shall be limited to the FX canonical backtest slice unless another phase slice is explicitly approved in `docs/ROADMAP.md`. | Modify | Narrow to the approved capability set and exact contracts from this reconciliation. | The broad baseline must be reduced before implementation. |
| V2-SIM-REQ-1348 | Phase 1 shall include only `run_backtest`, deterministic tick execution, approved FX symbol metadata, broker-profile fixtures, registered strategy references with validated configuration, data-quality gates, tick generation, spread/slippage/commission/swap models, journal persistence, JSON reports, Markdown reports, schema validation, replay tests, and no-live-side-effect guarantees. | Add | Use this as the release-scope and traceability gate for the accepted reconciliation decisions. | The V2 document is too broad to hand directly to a builder. |
| V2-SIM-REQ-1349 | Phase 1 shall exclude equity/ETF corporate actions, borrow-fee production realism, forced buy-ins, delisting, US regulatory engines, futures rollover production realism, perpetual funding production realism, feature-store integration, alternative-data integration, distributed workers, poison-pill work-unit quarantine, canary analysis, synthetic transaction monitoring, external report distribution, and production promotion workflows unless separately approved. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1350 | Phase 1 may preserve future enum values or metadata fields only when they are inert, documented as non-goals, and covered by deterministic unsupported-scope behavior. | Add | Use this as the release-scope and traceability gate for the accepted reconciliation decisions. | The V2 document is too broad to hand directly to a builder. |
| V2-SIM-REQ-1351 | Any Phase 1 code or schema introduced to accommodate future scope shall be inert by default, guarded by an explicit feature flag or scope tag, and fully tested for deterministic unsupported-scope rejection. | Add | Use this as the release-scope and traceability gate for the accepted reconciliation decisions. | The V2 document is too broad to hand directly to a builder. |

### Phase 1 Specification Gate

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1352 | `Phase 1 Specification`: FX canonical backtest requirements, exact API contracts, exact acceptance criteria, Phase 1 edge/error matrix, Phase 1 test suite, and Phase 1 traceability matrix. | Add | Use this as the release-scope and traceability gate for the accepted reconciliation decisions. | The V2 document is too broad to hand directly to a builder. |
| V2-SIM-REQ-1353 | `Future Extensions Annex`: future asset classes, enterprise service mode, distributed workers, regulatory engines, feature-store/alternative-data integrations, canary/synthetic monitoring, external report distribution, and production-promotion automation. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1354 | Shared requirement IDs may appear in both tiers only when the Phase 1 requirement has a precise in-scope behavior and the annex references deferred extensions without changing the Phase 1 contract. | Add | Use this as the release-scope and traceability gate for the accepted reconciliation decisions. | The V2 document is too broad to hand directly to a builder. |

### Business Rules

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1355 | The engine is the single source of truth for orders, deals, positions, pending orders, account state, balance, equity, margin, free margin, margin level, realized PnL, floating PnL, commission, swap, trade history, audit journal, and execution timestamps. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1356 | Strategies may maintain decision state but shall not mutate official trading state. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1357 | All official backtests must execute through a tick loop. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1358 | Vectorized processing is allowed only for indicator and signal generation. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1359 | Bar-open trading must use previous closed-bar data by default. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1360 | Production realism shortcuts must be explicitly configured. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1361 | Production realism shortcuts must be disclosed in the report. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1362 | A shortcut shall never be silently assumed. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1363 | A simulation must declare asset-class realism requirements for selected instruments. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1364 | A run shall not be labelled production-realistic unless required asset-class models are enabled or proven unnecessary. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1365 | Equities and ETFs require corporate-action treatment for production-realistic classification. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1366 | Futures require contract metadata, expiry, rollover policy, margin model, and roll-adjustment disclosure for production-realistic classification. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1367 | Perpetual swaps require funding-rate treatment, funding timestamps, funding currency, and exchange-fee model for production-realistic classification. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1368 | Multi-currency strategies require base-currency conversion for realized PnL, floating PnL, margin, commission, swap, dividends, funding, and cash balances. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1369 | Benchmark-relative reports require benchmark data aligned to the same clock and currency as the strategy. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1370 | A required model may be disabled only if the report records the disablement and downgrades the realism label where relevant. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1371 | Optimization must use the canonical tick-execution engine. | Defer | Apply when the Optimization/robustness workflow is promoted. | Not needed for the initial single-run simulator. |
| V2-SIM-REQ-1372 | Monte Carlo analysis must not replace the official backtest result. | Defer | Apply when the Optimization/robustness workflow is promoted. | Not needed for the initial single-run simulator. |
| V2-SIM-REQ-1373 | Balance may change only from closed realized PnL, commission, fee, swap, borrow-fee, dividend, funding, and configured cashflow events. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1374 | Risk rejections must be journaled. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1375 | Production merge requires CI gates to pass with coverage at least 80%. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1376 | A global random seed alone shall not be sufficient for synthetic tick generation in production mode. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1377 | Synthetic tick randomness shall be locally reproducible per symbol and per bar. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1378 | Streaming journal persistence shall be mandatory for optimization, walk-forward, and Monte Carlo production runs. | Defer | Apply when the Optimization/robustness workflow is promoted. | Not needed for the initial single-run simulator. |
| V2-SIM-REQ-1379 | Production runs shall fail closed when journal persistence fails. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1380 | `run_backtest` shall not execute arbitrary user-provided Python code strings. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1381 | Strategy execution shall occur only through registered strategies, validated schemas, or explicitly sandboxed and vetted orchestration paths. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1382 | Tick batching shall be allowed only where the engine can prove no state transition or compliance event can occur before the next boundary. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1383 | A batched range shall never skip a possible execution, risk, accounting, session, rollover, or compliance event. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1384 | `IOC` remainder cancellation shall be a journaled diagnostic, not a silent side effect. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1385 | FX conversion shall fail closed when rate age exceeds the configured maximum unless diagnostic override is explicitly enabled. | Merge | Fold into the corresponding final capability invariant. | This repeats earlier functional or non-functional requirements. |
| V2-SIM-REQ-1386 | Equity and ETF short production-realistic runs shall include borrow-fee treatment or disclose downgrade or approximation. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |

### 4.1 Inputs

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1387 | `SimulationConfig` with strategy settings, symbols, timeframe, start date, end date, execution mode, tick model, data modelling mode, spread model, signal timing, sizing mode, initial deposit, leverage, margin mode, slippage configuration, optimization configuration, visual mode, progress reporting, terminal verbosity, and random seed. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1388 | Execution-realism configuration for liquidity, slippage, latency, commission, pass-through fees, swap, borrow fees, recall risk, market hours, market halts, gap handling, broker rules, portfolio risk, kill switches, data quality, corporate actions, futures rollover, perpetual funding, currency conversion, benchmark, and regulatory checks. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1389 | Feature-store configuration for point-in-time feature retrieval when machine-learning features are used. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1390 | Alternative-data configuration for source timing, publication delay, ingestion delay, as-of alignment, lag policy, and embargo policy when non-price data is used. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1391 | `PartialDataPolicy` for incomplete provider files, partial symbol-day data, stale-data fallback, quarantine behavior, and fail-fast behavior. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1392 | `ResumePolicy` for checkpoint age, checkpoint compatibility, automatic resume eligibility, and restart behavior. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1393 | Resource quota configuration for concurrent runs, wall-clock time, temporary storage, queued runs, and worker limits. | Defer | Keep in the Future Extensions Annex or owning platform domain. | Outside the Phase 1 FX canonical slice. |
| V2-SIM-REQ-1394 | Scheduler configuration for queue backend, queue limits, worker heartbeat timeout, retry policy, cancellation behavior, and preemptible-worker handling. | Defer | Keep in the Future Extensions Annex or owning platform domain. | Outside the Phase 1 FX canonical slice. |
| V2-SIM-REQ-1395 | Poison-pill policy for repeated work-unit failure thresholds, quarantine behavior, alert routing, and diagnostic artifact retention. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1396 | Observability configuration for tracing, metrics export, SLO thresholds, synthetic probes, canary analysis, and alert routing. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1397 | Market data from a provider. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1398 | OHLCV bar data. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1399 | M1 OHLCV data when M1 or synthetic tick generation is used. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1400 | Real bid/ask tick data when real-tick mode is used. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1401 | Spread data when native spread mode is used. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1402 | Symbol specifications including point, tick size, tick value, contract size, volume min/max/step, asset class, currencies, sessions, and broker constraints. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1403 | Registered strategy identifier and validated strategy configuration. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1404 | Code-based strategy execution metadata only when referenced by an approved registry entry with sandbox profile id, vetting artifact hash, approval metadata, and explicit orchestration-layer permission. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1405 | Indicator specifications. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1406 | Optional order-book depth data. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1407 | Optional feature-store data and point-in-time feature manifests. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1408 | Optional alternative data such as sentiment, fundamentals, news, options flow, and external signals. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1409 | Optional market-halt and limit-up/limit-down data. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1410 | Optional corporate-action data. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1411 | Optional futures contract-chain data. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1412 | Optional perpetual funding-rate data. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1413 | Optional FX conversion-rate data. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1414 | Optional benchmark data. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1415 | Optional optimization configuration. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1416 | Optional Monte Carlo configuration. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1417 | Required `MarketDataAuthorityManifest` for production-realistic runs. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1418 | Required broker profile manifest for MT5-parity and production-realistic FX runs. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1419 | Immutable run-configuration artifact for production runs. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1420 | Required artifact retention tier for every official run. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1421 | Required `global_seed` for deterministic synthetic tick generation. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1422 | Derived `symbol_hash` for per-symbol synthetic tick seed derivation. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1423 | `bar_open_timestamp` for per-bar synthetic tick seed derivation. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1424 | Journal persistence configuration for streaming append-to-disk storage. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1425 | Journal backend selection with Phase 1 support for canonical JSONL and SQLite sidecar index. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1426 | Registered strategy identifier or validated strategy configuration for `run_backtest`. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1427 | Sandbox and vetting metadata only when code-based strategy execution is explicitly permitted by the orchestration layer. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1428 | Tick-batching boundary metadata derived from active orders, positions, session boundaries, gap boundaries, rollover boundaries, compliance boundaries, and scheduled strategy events. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1429 | Equity and ETF borrow-fee configuration for short-selling runs. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1430 | `max_fx_rate_age_seconds` or equivalent context-specific FX stale-rate tolerance configuration. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1431 | `max_cross_rate_skew_bps` for cross-rate synthesis validation. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |

### 4.2 Outputs

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1432 | Structured `SimulationResult`. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1433 | Immutable journal. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1434 | Orders history. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1435 | Deals history. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1436 | Trade list. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1437 | Partial-fill history. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1438 | Position lifecycle history. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1439 | Account snapshots. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1440 | Equity curve. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1441 | Balance curve. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1442 | Margin curve. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1443 | Exposure curve. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1444 | Data-quality report. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1445 | Corporate-action quality report for equity/ETF runs. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1446 | Liquidity diagnostics. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1447 | Slippage diagnostics. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1448 | Commission, fee, swap, and borrow-fee summary. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1449 | Funding summary for perpetual swap runs. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1450 | Futures roll events and roll PnL attribution for futures runs. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1451 | Multi-currency cash ledgers and currency exposure report. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1452 | Portfolio-risk summary. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1453 | Realism-disclosure summary. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1454 | Benchmark-relative metrics when benchmark data is provided. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1455 | Monte Carlo confidence bands when enabled. | Defer | Provide only the canonical single-run boundary in Phase 1; owning domains add later inputs/outputs. | This input/output belongs to deferred analysis or service workflows. |
| V2-SIM-REQ-1456 | Walk-forward in-sample and out-of-sample metrics when enabled. | Defer | Provide only the canonical single-run boundary in Phase 1; owning domains add later inputs/outputs. | This input/output belongs to deferred analysis or service workflows. |
| V2-SIM-REQ-1457 | Optimization result set with hashes, random seed, and objective function. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1458 | Structured error result with deterministic error code on failure. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1459 | Artifact manifest containing paths, media types, schema versions, hashes, sizes, retention tier, and created timestamps. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1460 | Per-bar synthetic tick seed derivation metadata or replay metadata. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1461 | Journal persistence backend and durability metadata. | Merge | Include in the corresponding accepted contract capability; do not create a separate subsystem requirement. | This duplicates functional/API requirements already reconciled. |
| V2-SIM-REQ-1462 | Immutable run-configuration artifact and checksum or signature. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1463 | Environment diagnostic hash and environment drift warning when applicable. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1464 | Queue, scheduler, worker, quota, and checkpoint metadata for service-mode runs. | Defer | Keep in the Future Extensions Annex or owning platform domain. | Outside the Phase 1 FX canonical slice. |
| V2-SIM-REQ-1465 | Data-lineage graph or lineage artifact references for audited data points. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1466 | OpenTelemetry trace identifiers and business-metric export metadata when observability is enabled. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1467 | Canary comparison results and synthetic transaction probe results when production monitoring is enabled. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1468 | Latency diagnostics when execution latency modelling is enabled. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1469 | Market-halt, limit-up/limit-down, kill-switch, trailing-stop, pegged-order, cancel-replace, recall, forced-buy-in, wash-sale, and alternative-uptick-rule diagnostics when applicable. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1470 | Feature-store and alternative-data alignment diagnostics when ML or non-price data is used. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1471 | Visual trade replay export artifact when requested. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1472 | Step-through replay metadata when debugger mode is used. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1473 | Persistence-failure diagnostics when journal writes, flushes, fsyncs, sidecar transactions, or commits fail. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1474 | Rejected strategy-injection diagnostics. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1475 | Tick-batching safety diagnostics when batching is enabled. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1476 | IOC remainder cancellation diagnostics. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1477 | Borrow-fee totals and borrow-fee cashflow history for equity and ETF short runs. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1478 | FX stale-rate override disclosures. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |
| V2-SIM-REQ-1479 | Rejected FX cross-rate synthesis diagnostics. | Modify | Keep only fields required by the approved FX workflow and external contracts. | The proposed aggregate input/output set is broader than Phase 1. |

### User Roles and System Actors

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1480 | User, agent, CLI, or notebook shall be able to invoke the `run_backtest` tool wrapper. | Modify | Keep the actor/boundary intent without requiring the named classes or a network service. | Actors are useful; implementation prescriptions are not authoritative. |
| V2-SIM-REQ-1481 | Strategy developer shall provide vectorized or event-driven strategy logic. | Modify | Keep the actor/boundary intent without requiring the named classes or a network service. | Actors are useful; implementation prescriptions are not authoritative. |
| V2-SIM-REQ-1482 | Vectorized signal strategy shall compute indicators, generate signals, and convert signals to trade intents. | Modify | Keep the actor/boundary intent without requiring the named classes or a network service. | Actors are useful; implementation prescriptions are not authoritative. |
| V2-SIM-REQ-1483 | Event strategy shall respond to initialization, bar-open, tick, and trade-transaction events. | Modify | Keep the actor/boundary intent without requiring the named classes or a network service. | Actors are useful; implementation prescriptions are not authoritative. |
| V2-SIM-REQ-1484 | The `run_backtest` tool wrapper shall be the official user-facing tool boundary. | Modify | Keep the actor/boundary intent without requiring the named classes or a network service. | Actors are useful; implementation prescriptions are not authoritative. |
| V2-SIM-REQ-1485 | The `BacktestOrchestrator` shall coordinate validation, data quality, signal construction, tick construction, execution, metrics, and reporting. | Modify | Keep the actor/boundary intent without requiring the named classes or a network service. | Actors are useful; implementation prescriptions are not authoritative. |
| V2-SIM-REQ-1486 | The `EventDrivenExecutionEngine` shall own canonical execution. | Modify | Keep the actor/boundary intent without requiring the named classes or a network service. | Actors are useful; implementation prescriptions are not authoritative. |
| V2-SIM-REQ-1487 | The `SimTrader` shall expose MT5-style trading methods to strategies through controlled interfaces. | Modify | Keep the actor/boundary intent without requiring the named classes or a network service. | Actors are useful; implementation prescriptions are not authoritative. |
| V2-SIM-REQ-1488 | Internal engines shall provide data quality, tick generation, spread, market calendar, gaps, event priority, liquidity, slippage, matching, fees, swap, broker rules, portfolio, accounting, compliance, metrics, optimization, Monte Carlo, and performance services. | Reject | Do not create a service/class per noun; implement focused modules only where behavior is accepted. | This is an implementation inventory, not a necessary behavior. |
| V2-SIM-REQ-1489 | The immutable journal shall act as the audit and replay source. | Modify | Keep the actor/boundary intent without requiring the named classes or a network service. | Actors are useful; implementation prescriptions are not authoritative. |

### 10.1 Report Documentation

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1490 | Every report shall disclose tick model. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1491 | Every report shall disclose spread model. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1492 | Every report shall disclose liquidity model. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1493 | Every report shall disclose slippage model. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1494 | Every report shall disclose commission model. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1495 | Every report shall disclose swap model. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1496 | Every report shall disclose market-hours and gap policy. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1497 | Every report shall disclose margin model. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1498 | Every report shall disclose portfolio-risk model. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1499 | Every report shall disclose corporate-action model. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1500 | Every report shall disclose futures-rollover model. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1501 | Every report shall disclose perpetual-funding model. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1502 | Every report shall disclose currency-conversion model. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1503 | Every report shall disclose benchmark model. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1504 | Every report shall disclose regulatory-constraint model. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1505 | Every report shall disclose data-quality status. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1506 | Every report shall disclose the run classification: `production_realistic`, asset-class-specific production-realistic label, `mt5_parity_oriented`, or `research_approximation`. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1507 | Every report shall disclose disabled required models and any realism-label downgrade. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1508 | Equity reports shall disclose corporate-action adjustment method. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1509 | Futures reports shall disclose rollover policy and roll PnL attribution where possible. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1510 | Perpetual reports shall disclose total funding paid/received and net trading PnL excluding funding. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1511 | Multi-currency reports shall reconcile native and base-currency ledgers. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1512 | Reports shall disclose journal storage backend, durability mode, and sidecar index usage. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1513 | Reports shall disclose IOC remainder cancellation diagnostics. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1514 | Reports shall disclose total borrow fees paid for equity and ETF short runs. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1515 | Reports shall disclose FX stale-rate diagnostic overrides. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1516 | Reports shall disclose rejected FX cross-rate synthesis diagnostics when they affect a run. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1517 | Reports shall disclose tick-batching safety diagnostics when batching is enabled. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1518 | Reports shall disclose model inventory ids, validation status, material model exceptions, and approval expiry for production-candidate runs. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1519 | Reports shall disclose research protocol id, selection method, optimization status, out-of-sample degradation, and parameter-sensitivity status when strategy research or optimization influenced the result. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1520 | Reports shall disclose execution-model calibration status and whether execution models are broker-calibrated, venue-calibrated, generic, synthetic, or uncalibrated. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1521 | Reports shall disclose execution latency model, latency assumptions, and latency diagnostics when latency modelling is enabled. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1522 | Reports shall disclose capacity diagnostics and approved capacity limits when liquidity or market-impact models are enabled. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1523 | Reports shall disclose market-halt, limit-up/limit-down, portfolio kill-switch, trailing-stop, pegged-order, and cancel-replace behavior when encountered. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1524 | Reports shall disclose pass-through regulatory and exchange fees separately from broker commission when configured. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1525 | Equity and ETF reports shall disclose delisting treatment, recall-risk model, forced buy-ins, and borrow availability assumptions when applicable. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1526 | Regulated asset reports shall disclose SEC Rule 201, wash-sale diagnostics, and disabled tax-aware or regulatory modules where applicable. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1527 | ML or alternative-data reports shall disclose feature-store point-in-time status, alternative-data alignment policies, lag assumptions, and rejected feature lookahead diagnostics. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1528 | Reports shall disclose vendor-data limitations, data revision policy, and point-in-time snapshot status when external data sources are used. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1529 | Reports shall disclose partial-data handling decisions, quarantined symbol-date ranges, stale-data fallback usage, and any resulting realism downgrade. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1530 | Reports shall disclose metric confidence intervals for material production-realistic metrics or explicitly disclose why intervals are unavailable. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1531 | Reports shall disclose immutable run-configuration artifact id, environment diagnostic hash, and environment drift warnings when applicable. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1532 | Reports shall disclose queue wait time, execution worker id, retry count, resume source, and checkpoint id for service-mode runs. | Defer | Keep in the Future Extensions Annex or owning platform domain. | Outside the Phase 1 FX canonical slice. |
| V2-SIM-REQ-1533 | Reports shall disclose canary comparison and synthetic transaction probe evidence when used for release or service-health validation. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1534 | Reports shall disclose FX `production_realistic` V1 non-goals where material. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1535 | Reports shall declare distribution mode: `internal_research`, `internal_production_review`, `client_facing`, `investor_facing`, or `public`. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1536 | Client-facing, investor-facing, or public reports shall include hypothetical-performance disclosures when results are simulated. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1537 | External reports shall disclose major assumptions, limitations, model simplifications, data limitations, fees and costs treatment, optimization status, and whether live trading evidence exists. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1538 | External report generation shall support a compliance approval workflow before export. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1539 | External reports shall prevent unsupported performance claims and shall include configured legal or compliance disclaimers. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |

### 10.2 Journal Documentation

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1540 | The journal shall document configuration hash and data checksum. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1541 | The journal shall document model choices used in the run. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1542 | The journal shall document every state transition and rejection. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1543 | The journal shall document every compliance record. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1544 | The journal shall document currency conversion rate, source, timestamp, and age for every conversion. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1545 | The journal shall document asset-class realism decisions. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1546 | The journal shall document per-bar synthetic tick seed derivation metadata when generated ticks are used. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1547 | The journal shall document persistence backend, durability mode, flush policy, sidecar index configuration, and last committed sequence. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1548 | The journal shall document strategy-input rejection attempts without logging unsafe code bodies in full. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1549 | The journal shall document IOC remainder cancellations as non-fatal diagnostics. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1550 | The journal shall document borrow-fee accruals separately from dividends, swap, commission, and trade PnL. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1551 | The journal shall document FX stale-rate overrides and rejected cross-rate synthesis paths. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1552 | The journal shall document model inventory ids, model validation evidence ids, governance overrides, and model exception expiry. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1553 | The journal shall document research protocol manifest id, selected-parameter lineage, and out-of-sample validation evidence. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1554 | The journal shall document execution-calibration artifact ids and calibration status for execution realism models. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1555 | The journal shall document latency model id, latency components, delayed eligibility time, and latency-affected fill decisions. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1556 | The journal shall document capacity assumptions, approved limits, and capacity-limit violations. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1557 | The journal shall document market halts, limit-up/limit-down states, kill-switch triggers, trailing-stop updates, pegged-order repricing, and cancel-replace operations. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1558 | The journal shall document delisting outcomes, recall events, forced buy-ins, pass-through regulatory fees, exchange fees, SEC Rule 201 checks, and wash-sale diagnostics when applicable. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1559 | The journal shall document feature-store retrieval timestamps, feature availability timestamps, alternative-data as-of alignment, and rejected feature lookahead events. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1560 | The journal shall document run lifecycle transitions, idempotency decisions, cancellations, and checkpoint compatibility checks. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1561 | The journal shall document vendor/source inventory ids, point-in-time snapshot ids, and material vendor-data limitations. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1562 | The journal shall document immutable run-configuration artifact id, environment diagnostic hash, and environment drift warnings. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1563 | The journal shall document resource quota checks, queue transitions, worker assignment, worker heartbeat loss, requeue decisions, retry attempts, and resume checkpoints. | Defer | Keep in the Future Extensions Annex or owning platform domain. | Outside the Phase 1 FX canonical slice. |
| V2-SIM-REQ-1564 | The journal shall document poison-pill work-unit quarantine, idempotent write decisions, distributed-lock ownership, compare-and-swap commit outcomes, and optional service degradation events. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1565 | The journal shall document partial-data policy decisions, quarantined symbol-date ranges, stale-data use, and stale-data age. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1566 | The journal shall document data-lineage artifact ids for fill-price, mark-to-market, and PnL events. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1567 | The journal shall document trace ids, span ids, synthetic transaction probe ids, and canary comparison ids when applicable. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |

### 10.3 Developer and Release Documentation

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1568 | Benchmark results shall be stored with release notes before production promotion. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1569 | Usage examples shall run end-to-end. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1570 | Optional enterprise feature contracts shall be defined early to avoid breaking redesign. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1571 | External synthetic tick algorithm reference shall be documented as MQL5 Article #75. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1572 | Release notes shall reference the applicable `simulation_promotion_manifest.json`. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1573 | Release documentation shall include model-validation, research-integrity, calibration, security, and benchmark evidence links for production promotions. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |

### 10.4 Production Documentation

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1574 | Documentation shall include a formal user guide for interpreting realism labels. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1575 | Documentation shall include a configuration reference for every config class and enum. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1576 | Documentation shall include a migration guide if earlier simulator versions exist. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1577 | Documentation shall include report examples for FX, equity, futures, perpetual, and multi-currency portfolios before those scopes are production-promoted. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1578 | Documentation shall include a schema reference for `SimulationResult`, official AI Tool envelopes, journal events, report JSON, artifact manifests, broker profiles, and market-data authority manifests. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1579 | Documentation shall include a threat model and data-governance guide before any externally accessible simulator tool is enabled. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1580 | Documentation shall include retention, redaction, and protected-artifact operating procedures. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1581 | Documentation shall describe per-bar synthetic tick seed derivation, including SHA-256 inputs, `global_seed`, `symbol_hash`, UTC `bar_open_timestamp`, and replay metadata. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1582 | Documentation shall describe checkpoint and replay behavior for synthetic tick generation. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1583 | Documentation shall describe streaming journal persistence requirements, supported journal storage backends, SQLite sidecar indexing, fsync-per-batch durability, and maximum in-memory journal buffer limits. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1584 | Documentation shall describe memory-safety constraints for optimization, walk-forward, and Monte Carlo runs. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1585 | Documentation shall state that raw arbitrary Python strategy code is not accepted by `run_backtest`. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1586 | Documentation shall describe approved strategy input modes, strategy registry behavior, and sandbox/vetting requirements if code-based strategy execution is ever enabled. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1587 | Documentation shall describe tick-batching safety boundaries and the Phase 1 boundary-interval proof model. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1588 | Documentation shall describe IOC remainder cancellation diagnostics. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1589 | Documentation shall describe FX stale-rate behavior, `max_fx_rate_age_seconds`, diagnostic overrides, and report disclosures. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1590 | Documentation shall describe FX cross-rate synthesis rejection behavior and `max_cross_rate_skew_bps`. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1591 | Documentation shall describe equity and ETF short borrow-fee behavior. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1592 | Documentation shall describe added error and diagnostic codes. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1593 | Documentation shall describe Phase 1 defaults for MT5 parity tolerance, JSONL journal storage, SQLite sidecar indexing, canonical JSON report format, and required Markdown report format. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1594 | Documentation shall include model-governance and model-inventory operating procedures. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1595 | Documentation shall include dynamic model materiality assessment rules and evidence requirements. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1596 | Documentation shall include research-integrity, optimization, and overfitting-control operating procedures. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1597 | Documentation shall include execution-model calibration requirements and calibration artifact schemas. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1598 | Documentation shall include execution latency modelling, latency component definitions, and latency diagnostic interpretation. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1599 | Documentation shall include strategy-capacity diagnostics and production capacity approval procedures. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1600 | Documentation shall include run lifecycle, idempotency, cancellation, checkpoint, and resume behavior. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1601 | Documentation shall include observability metrics, alerting expectations, SLOs, and operational runbooks. | Defer | Keep in the Future Extensions Annex or owning platform domain. | Outside the Phase 1 FX canonical slice. |
| V2-SIM-REQ-1602 | Documentation shall include resource quota, scheduler queue, worker heartbeat, checkpoint/resume, preemptible-worker, and backpressure operating procedures. | Defer | Keep in the Future Extensions Annex or owning platform domain. | Outside the Phase 1 FX canonical slice. |
| V2-SIM-REQ-1603 | Documentation shall include immutable run-configuration, environment drift detection, and benchmark-profile certification procedures. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1604 | Documentation shall include OpenTelemetry tracing, business metrics, predictive alerting, synthetic transaction monitoring, and canary analysis procedures. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1605 | Documentation shall include end-to-end data-lineage graph schema and audit query examples. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1606 | Documentation shall include warm data cache behavior, TTL rules, `DataManifestHash` keys, and checksum validation requirements. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1607 | Documentation shall include confidence interval methodology for reported metrics and downgrade behavior when intervals are unavailable. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1608 | Documentation shall include market-halt, limit-up/limit-down, portfolio kill-switch, trailing-stop, pegged-order, and cancel-replace semantics. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1609 | Documentation shall include pass-through regulatory and exchange fee models, including US equity examples for SEC Section 31 and FINRA TAF where supported. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1610 | Documentation shall include delisting, survivorship-bias, recall-risk, forced-buy-in, borrow-fee, SEC Rule 201, and optional wash-sale diagnostic behavior. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1611 | Documentation shall include feature-store point-in-time retrieval, alternative-data as-of alignment, publication lag, ingestion lag, and no-lookahead rules. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1612 | Documentation shall include poison-pill work-unit quarantine, idempotent queue semantics, distributed locks, compare-and-swap commits, and optional-service degradation behavior. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1613 | Documentation shall include deterministic step-through replay and visual trade replay export schema. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1614 | Documentation shall include FX `production_realistic` V1 non-goals and scope limitations. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1615 | Documentation shall include secure-SDLC and software supply-chain procedures, including SBOM, dependency scanning, secret scanning, release signing, and artifact checksum verification. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1616 | Documentation shall include third-party data and vendor-governance procedures. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |
| V2-SIM-REQ-1617 | Documentation shall include external-report distribution modes, hypothetical-performance disclosures, compliance approval workflow, and unsupported-claim controls. | Modify | Reference external evidence when available; detailed operating procedures remain in the owning domain. | Simulation should disclose evidence, not own cross-domain governance manuals. |
| V2-SIM-REQ-1618 | Documentation shall include the schema and approval workflow for `simulation_promotion_manifest.json`. | Merge | Generate documentation from the accepted contracts, journal schema, report schema, and Phase 1 defaults. | This is documentation of already accepted behavior. |

### Assumptions

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1619 | The attached Hardened Draft v1.6 specification is the active source of truth. | Open Decision | Confirm or attach the referenced contracts before Builder handoff. | The source explicitly records missing authority/evidence. |
| V2-SIM-REQ-1620 | Pending: the referenced Hardened Draft v1.6 specification, strategy contracts, indicator contracts, data contracts, broker-profile manifests, and market-data authority manifests must be attached or summarized before Builder handoff. | Open Decision | Confirm or attach the referenced contracts before Builder handoff. | The source explicitly records missing authority/evidence. |
| V2-SIM-REQ-1621 | The requirements are domain-wide supporting requirements under `docs/source-requirements/`, not a sprint-specific implementation ticket. | Keep | Retain as a planning assumption unless contradicted by cross-domain alignment. | It establishes the intended domain direction. |
| V2-SIM-REQ-1622 | The simulator is intended for Python implementation. | Keep | Retain as a planning assumption unless contradicted by cross-domain alignment. | It establishes the intended domain direction. |
| V2-SIM-REQ-1623 | The simulation module is intended to live under `app/services/simulation/`. | Keep | Use `app/services/simulation/` as the canonical package path. | This resolves the V1 `simulator`/`simulation` naming conflict. |
| V2-SIM-REQ-1624 | Indicator implementation requirements live in `docs/source-requirements/03-indicator.md`. | Keep | Retain as a planning assumption unless contradicted by cross-domain alignment. | It establishes the intended domain direction. |
| V2-SIM-REQ-1625 | Strategy implementation requirements live in `docs/source-requirements/04-strategy.md`. | Keep | Retain as a planning assumption unless contradicted by cross-domain alignment. | It establishes the intended domain direction. |
| V2-SIM-REQ-1626 | The simulator targets deterministic backtesting and simulation, not live order execution against a broker. | Keep | Retain as a planning assumption unless contradicted by cross-domain alignment. | It establishes the intended domain direction. |
| V2-SIM-REQ-1627 | MT5 Strategy Tester semantics are an inspiration and parity target for selected controlled cases, not necessarily a guarantee of exact MT5 behavior for every broker-specific case. | Keep | Retain as a planning assumption unless contradicted by cross-domain alignment. | It establishes the intended domain direction. |
| V2-SIM-REQ-1628 | Tick execution is the canonical production mode. | Keep | Retain as a planning assumption unless contradicted by cross-domain alignment. | It establishes the intended domain direction. |
| V2-SIM-REQ-1629 | Vectorized processing is acceptable only for indicators and signal generation. | Keep | Retain as a planning assumption unless contradicted by cross-domain alignment. | It establishes the intended domain direction. |
| V2-SIM-REQ-1630 | Asset-class production realism depends on enabled models and available data. | Keep | Retain as a planning assumption unless contradicted by cross-domain alignment. | It establishes the intended domain direction. |
| V2-SIM-REQ-1631 | Reports and journals are required artifacts, not optional diagnostics. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1632 | Optional enterprise features may be disabled initially, but their contracts should be defined to avoid breaking redesign. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |

### Future Improvements

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| V2-SIM-REQ-1633 | Future improvements shall contain only deferred optional enhancements and shall not contain mandatory business rules, required inputs, required outputs, or production gates. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1634 | Each future improvement shall include rationale, non-goal status for the current phase, promotion trigger, affected requirement sections, and required owner decision before promotion. | Keep | Use the Deferred Scope Register as the Phase 1 source of truth. | Prevents future scope from becoming blocking work. |
| V2-SIM-REQ-1635 | Deferred enterprise and future-scope areas include non-FX production-realistic asset-class expansion, regulatory engines, feature-store integration, alternative-data integration, distributed workers, canary analysis, synthetic transaction monitoring, external-report distribution workflows, and production-promotion automation unless explicitly approved for the active release phase. | Defer | Future Extensions Annex; deterministic unsupported-scope response in Phase 1. | Outside the approved FX initial rebuild. |
| V2-SIM-REQ-1636 | The Deferred Scope Register in the Phase 1 Builder Slice section shall be the single source of truth for Simulation deferred-scope status during Phase 1 handoff preparation. | Keep | Use the Deferred Scope Register as the Phase 1 source of truth. | Prevents future scope from becoming blocking work. |

## 7. Workflow Reconciliation
| Final workflow ID | Workflow | Scope | V1 status | V2 proposal | Decision | Final boundary and outcome |
|---|---|---|---|---|---|---|
| WF-SIM-001 | Official FX backtest | Cross-domain | V1 `V1-WF-SIMULATOR-001` broken | V2 canonical `run_backtest` pipeline | Replace | Registered strategy + approved data/broker references → Simulation validates, builds canonical ticks, executes, accounts, journals, reports → versioned result and artifacts. |
| WF-SIM-002 | Simulation Trader operations inside a run | Cross-domain | V1 `V1-WF-SIMULATOR-002` conditionally broken | V2 SimTrader protocol | Replace | Approved strategy intent/query → simulated Trader contract → engine-owned state mutation/read-only snapshot → journaled response; no live adapter calls. |
| WF-SIM-003 | Optimization candidate execution | Cross-domain | V1 `V1-WF-SIMULATOR-003` mock-only | V2 optimization/search/workers | Replace | Optimization-owned candidate/config → canonical Simulation single-run execution → immutable result/provenance → Optimization-owned ranking/checkpointing. |
| WF-SIM-004 | Severe data-quality blocked run | Cross-domain | Missing | V2 data-quality and diagnostic-failed flow | Add | Data-owned manifest and normalized data → Simulation validation gate → no execution on severe failure → deterministic failed/diagnostic-failed envelope and bounded artifacts. |
| WF-SIM-005 | Deterministic replay | Internal | Missing | V2 immutable journal and replay | Add | Canonical journal + matching config/data/engine hashes → sequence/hash validation → deterministic state reconstruction/result comparison. |
| WF-SIM-006 | Registered-strategy security rejection | Cross-domain | Missing | V2 arbitrary-code rejection | Add | Unregistered/raw code input → tool validation before import/execution → `SIM_ARBITRARY_CODE_REJECTED` + redacted journal diagnostic. |
| WF-SIM-007 | Non-canonical fast research run | Internal | Historical bar-simulator intent only | V2 FAST_RESEARCH | Add | Approved research request → explicitly approximate execution path → non-canonical result with mandatory disclosure and no promotion/official-fill claims. |
| WF-SIM-008 | Asynchronous queued service run | Cross-domain | Missing | V2 queued/service-mode lifecycle | Defer | Excluded from initial rebuild; later platform scheduler → Simulation run contract → persisted lifecycle/result. |

### `WF-SIM-001` — Official FX Backtest

**Scope:** Cross-domain

**V1 behaviour:**

```text
Direct legacy test/example import → missing `app.services.simulator` → workflow stops.
```

**V2 proposal:**

```text
Tool validation → approved strategy/data/broker references → canonical tick construction → execution/accounting → immutable journal → reports.
```

**Final decision:**

```text
Replace the V1 workflow with the canonical `run_backtest` workflow.
```

**Reason:**

The V1 route is not operational; V2 supplies the minimum domain purpose when narrowed to the FX slice.

### `WF-SIM-002` — Simulation Trader Operations

**Scope:** Cross-domain

**V1 behaviour:**

```text
Trading service resolves `active_broker=simulator` → dynamic import of missing package → conditional failure.
```

**V2 proposal:**

```text
Strategy uses simulated Trader semantics backed by engine-owned orders, deals, positions, and account state.
```

**Final decision:**

```text
Replace global broker selection with an explicit Simulation-owned implementation of a shared contract, subject to the cross-domain open decision.
```

**Reason:**

This preserves strategy compatibility without allowing Simulation to import live adapters or masquerade as a globally active broker.

### `WF-SIM-003` — Optimization Candidate Execution

**Scope:** Cross-domain

**V1 behaviour:**

```text
Optimization tests inject fake simulator modules; no real simulator executes.
```

**V2 proposal:**

```text
Optimization requests deterministic canonical runs and receives immutable result/provenance evidence.
```

**Final decision:**

```text
Replace mock-only integration; Simulation does not own search algorithms, worker scheduling, ranking, or Monte Carlo.
```

**Reason:**

This is the smallest useful cross-domain contract and removes duplicate ownership.

### `WF-SIM-004` — Severe Data-Quality Block

**Scope:** Cross-domain

**V1 behaviour:**

```text
No V1 workflow.
```

**V2 proposal:**

```text
Manifest/input validation detects severe invalid data before execution and emits bounded diagnostic artifacts.
```

**Final decision:**

```text
Add.
```

**Reason:**

Production or canonical claims are impossible without a deterministic gate.

### `WF-SIM-005` — Deterministic Replay

**Scope:** Internal

**V1 behaviour:**

```text
No V1 workflow.
```

**V2 proposal:**

```text
Validate journal sequence/hash/config/data/engine identity and reconstruct state/results deterministically.
```

**Final decision:**

```text
Add.
```

**Reason:**

Replay is the required proof that journal evidence is canonical.

### `WF-SIM-006` — Registered-Strategy Security Rejection

**Scope:** Cross-domain

**V1 behaviour:**

```text
No V1 workflow.
```

**V2 proposal:**

```text
Reject raw code or unapproved strategy references before import/execution and record a redacted diagnostic.
```

**Final decision:**

```text
Add.
```

**Reason:**

The official tool boundary must not become an arbitrary-code execution surface.

### `WF-SIM-007` — Fast Research Approximation

**Scope:** Internal

**V1 behaviour:**

```text
Historical bar-simulator intent only; current implementation absent.
```

**V2 proposal:**

```text
Explicitly non-canonical approximation with mandatory classification and no official fill/promotion claims.
```

**Final decision:**

```text
Add as optional and isolated.
```

**Reason:**

Preserves research usefulness without weakening the canonical path.

### `WF-SIM-008` — Asynchronous Service Run

**Scope:** Cross-domain

**V1 behaviour:**

```text
No V1 workflow.
```

**V2 proposal:**

```text
Queue, workers, quotas, cancellation, health checks, and persisted service lifecycle.
```

**Final decision:**

```text
Defer.
```

**Reason:**

It is platform scope and not required to establish a correct local engine.

## 8. Recommended Minimal Capability Structure
```text
app/services/simulation/
├── run/          # Official tool contract, orchestration, permissions, lifecycle
├── timeline/     # Signal timing, tick construction, no-lookahead
├── execution/    # Matching, order lifecycle, engine state, simulated Trader
├── accounting/   # Volume normalization, costs, margin, PnL, FX conversion
├── validation/   # Config, manifest, data, broker-rule, and execution validation
├── journal/      # Append-only evidence, persistence, replay, idempotency
└── reporting/    # SimulationResult, JSON/Markdown reports, artifact manifest
```

This is capability-level structure only. Exact files, classes, functions, schemas, and exports are intentionally deferred to the domain README and Builder-ready specification.

| Module | Capability | Source | Main decision |
|---|---|---|---|
| `run/` | Official tool contracts, orchestration, permissions, lifecycle | V2 plus V1 workflow intent | Add / Modify |
| `timeline/` | Signal timing, canonical tick construction, no-lookahead | Both | Modify |
| `execution/` | Engine state, matching, fill policy, gaps, SimTrader | Both | Modify / Add |
| `accounting/` | Volume normalization, margin, costs, PnL, FX conversion | V2 | Add |
| `validation/` | Config, manifest, input, broker-rule, and execution validation | V2 | Add |
| `journal/` | Append-only events, persistence, replay, idempotency evidence | V2 | Add |
| `reporting/` | SimulationResult, canonical JSON/Markdown, artifact manifest, analytics integration | Both | Modify / Add |

## 9. Reuse and Migration Plan
| Priority | Existing V1 item | Migration action | Target capability | Validation required |
|---:|---|---|---|---|
| 1 | Legacy package identity `app.services.simulator` | Remove after caller confirmation | `CAP-SIM-001` | Search external deployments/local modules; map all repository imports. |
| 2 | V1 simulator tests and usage example | Refactor | `CAP-SIM-001`–`011` | Convert to approved contract/golden/replay tests; prove clean-checkout execution. |
| 3 | Broker-router simulator branch | Replace | `CAP-SIM-005` | Cross-domain decision on Trader protocol; no live-side-effect integration test. |
| 4 | Referenced `SimulatorConfig` contract | Refactor | `CAP-SIM-001`, `006` | Approve exact request fields, defaults, enums, unknown-field behavior, limits, and error mapping. |
| 5 | Referenced `TradeSimulator.run()` behavior | Replace | `CAP-SIM-002`–`004` | Canonical FX fixture, no-lookahead, fill, gap, and deterministic replay tests. |
| 6 | Referenced result fields | Refactor | `CAP-SIM-006`–`008` | Schema compatibility mapping and Analytics contract confirmation. |
| 7 | Optimization simulator mocks | Remove after replacement | `CAP-SIM-013` | Real cross-domain integration test using canonical Simulation runner. |
| 8 | Historical deleted deterministic simulator | Remove | None | Preserve only reconciled behavior in tests/specs; no code restoration. |
| 9 | All accepted Phase 1 V2 behavior | New | All final capabilities | Traceability IDs, acceptance criteria, and mapped tests before Builder handoff. |

## 10. Simplifications from V2
| V2 proposal | Problem | Simplified final direction |
|---|---|---|
| One class/service per V2 noun (`BacktestOrchestrator`, many model services, compliance service, performance service) | Would create architecture before behavior is proven. | Use one public `run_backtest` function; retain stateful classes only for execution state and simulated Trader lifecycle. |
| `models/` file for every spread/slippage/liquidity/fee/swap/margin concept | Fragmentation without confirmed independent lifecycle. | Keep model configuration and pure calculations with their owning capability; split only when file cohesion/size requires it. |
| All exports in `__all__` become AI tools | Would expose protocol types and internals accidentally. | Register only deliberate tool wrappers as agent-callable. |
| Simulation owns grid/random/Bayesian/genetic optimization and Monte Carlo | Duplicates Optimization/Analytics ownership. | Simulation supplies deterministic single-run execution and provenance only. |
| Simulation calculates the full analytics metric catalog | Duplicates Analytics and couples engine to reporting formulas. | Simulation emits canonical execution/accounting evidence and consumes Analytics results. |
| Simulation owns broad data quality, caches, data lineage DAGs, and vendor governance | Duplicates Data ownership. | Validate Data-owned immutable manifests and execution-critical input conditions. |
| Simulation owns portfolio risk policy, VaR, correlation, concentration, and governance decisions | Duplicates Risk ownership. | Apply and journal a supplied simulation risk profile/decision contract; maintain only execution/accounting state. |
| Mandatory JSONL plus SQLite sidecar index in the first slice | Adds dual persistence and failure modes before query demand is measured. | JSONL hash-chained canonical journal first; sidecar index deferred or optional after profiling. |
| Distributed workers, queueing, quotas, poison work units, canaries, and synthetic probes | Transforms a simulator rebuild into a platform project. | Defer service mode; build a deterministic local single-run engine first. |
| Full multi-asset realism, regulatory engines, corporate actions, futures, perpetuals, and options | Contradicts the declared FX Phase 1 boundary. | Reserve metadata and deterministic unsupported-scope responses; implement only after separate promotion decisions. |
| Tick batching in Phase 1 | Optimization risks skipping execution/accounting boundaries. | Start one tick at a time; add only after correctness and benchmark evidence. |
| Separate compliance-record subsystem | Duplicates journal and governance layers. | Use typed accepted/rejected validation and risk-decision journal events. |
| Visual/debug replay, external reports, and notebook outputs as core artifacts | Expands canonical artifact surface. | Keep JSON, Markdown, journal, and manifest canonical; derive visual/debug outputs later. |

## 11. Open Decisions
| Status | Decision required | Evidence available | Options | Affected capabilities |
|---|---|---|---|---|
| Open — cross-domain | Who owns the shared Trader protocol and how Simulation/Trading select implementations? | V1 has a broken broker-router branch; V2 requires shared semantics without live imports. | Shared contracts domain; Trading-owned protocol; Simulation-owned protocol with external compatibility tests. | `CAP-SIM-005`, `WF-SIM-002` |
| Open — cross-domain | Exact Strategy/Indicator/Data inbound schemas and registry/manifest references | V2 marks these contracts pending; V1 has only stale direct imports. | Attach approved contracts; define minimal adapters; defer affected behavior. | `CAP-SIM-001`, `003`, `009`, `010` |
| Open — cross-domain | Risk/sizing ownership between Strategy, Risk, and Simulation | V2 centralizes final volume and portfolio checks in Simulation but states external risk policy is not owned here. | Simulation normalizes supplied volume; Simulation applies Risk decision; shared sizing contract. | `CAP-SIM-006` |
| Open — cross-domain | Analytics ownership and the exact report/metric boundary | V1 expected metrics; V2 embeds a large metric catalog in Simulation. | Analytics computes all performance metrics; Simulation computes only accounting/execution totals; hybrid contract. | `CAP-SIM-008` |
| Open — domain | Exact `SimulationBacktestRequestV1`, envelope statuses, limits, and artifact-root rules | V2 scaffold is explicitly pending and includes service-mode statuses. | Synchronous Phase 1 only; include cancelled; include queued later. | `CAP-SIM-001`, `002` |
| Open — domain | Phase 1 tick-model set and controlled MT5 parity fixture | V2 proposes four tick models and a named fixture but no attached broker/data contracts. | M1 + real ticks; add synthetic research; include timeframe approximation. | `CAP-SIM-003`, `004` |
| Open — domain | Whether RETURN orders, order modify/delete, and cancel-replace are Phase 1 | V2 protocol table marks modification/deletion deferred unless approved. | FOK/IOC only; add RETURN; add full MT5 subset. | `CAP-SIM-004`, `005` |
| Open — domain | Journal durability defaults and whether SQLite sidecar indexing is mandatory | V2 prescribes JSONL + SQLite and batch/fsync limits without measured need. | JSONL only; optional sidecar; mandatory sidecar. | `CAP-SIM-007` |
| Open — cross-domain | FX conversion provider contract and cross-rate synthesis support | V2 leaves fallback-chain approval pending. | Direct only; direct+inverse; permit validated cross synthesis. | `CAP-SIM-006` |
| Open — project-wide | Approved formatter/linter/type-check/coverage CI policy | V2 requires both Ruff and Black but the two source documents do not establish project-wide tooling authority. | Use project standard; keep both; choose one formatter. | `CAP-SIM-011` |
| Open — project-wide | Blocking performance and memory thresholds | V2 numeric targets are explicitly provisional. | Non-blocking baseline; approve fixed gates before build; gate only promotion. | `CAP-SIM-011` |
| Open — cross-domain | Migration deadline for stale `app.services.simulator` imports and `active_broker=simulator` | V1 audit confirms missing package and stale callers. | Immediate removal; compatibility shim; staged caller migration. | `CAP-SIM-001`, `005`, `013` |

Cross-domain and project-wide items above must be copied to the top-level system Open Decisions section and resolved through the applicable ADR during pipeline step 05. This reconciliation does not modify the top-level system document.

Deferrals that change system shape—service-mode scheduling, distributed workers, future asset classes, regulatory engines, feature/alternative-data integration, external distribution, and production-promotion automation—must remain visible in the top-level Deferred Capabilities section.

## 12. Inputs for the Final Domain README
### Approved capabilities

* `CAP-SIM-001` — Official simulation tool and versioned contracts
* `CAP-SIM-002` — Run validation, orchestration, and lifecycle
* `CAP-SIM-003` — Signal timing, tick construction, and no-lookahead
* `CAP-SIM-004` — Canonical FX execution, matching, and realism
* `CAP-SIM-005` — Simulated Trader interface and authoritative execution state
* `CAP-SIM-006` — Sizing application, accounting, costs, margin, and FX conversion
* `CAP-SIM-007` — Immutable journal, replay, persistence, and run idempotency
* `CAP-SIM-008` — Canonical reports, artifacts, and analytics boundary
* `CAP-SIM-009` — Inbound data authority and simulation-specific quality gate
* `CAP-SIM-010` — Strategy and indicator integration boundary
* `CAP-SIM-011` — Determinism, precision, reliability, security, and verification
* `CAP-SIM-012` — Explicit non-canonical fast research mode
* `CAP-SIM-013` — Optimization and robustness execution boundary

### Approved workflows

* `WF-SIM-001` — Official FX backtest
* `WF-SIM-002` — Simulation Trader operations inside a run
* `WF-SIM-003` — Optimization candidate execution
* `WF-SIM-004` — Severe data-quality blocked run
* `WF-SIM-005` — Deterministic replay
* `WF-SIM-006` — Registered-strategy security rejection
* `WF-SIM-007` — Non-canonical fast research run

### V1 behaviours to preserve

* Deterministic repeatability as an explicit objective from `V1-CAP-SIMULATOR-009`.
* Previous-period/no-lookahead strategy behavior from `V1-CAP-SIMULATOR-003`.
* Pending, protective, and time-based execution intent from `V1-CAP-SIMULATOR-004`, narrowed to approved Phase 1 order types.
* Point-in-time multi-timeframe visibility intent from `V1-CAP-SIMULATOR-005`.
* Structured trades, equity, and serialized-result intent from `V1-CAP-SIMULATOR-006`.
* Broker-neutral shared strategy semantics from `V1-CAP-SIMULATOR-007`, implemented only through the simulated side of an approved Trader contract.

### V1 behaviours to modify

* Replace bar-based official execution with canonical bid/ask tick execution.
* Replace the missing `SimulatorConfig` with versioned request/config schemas.
* Replace `TradeSimulator.run()` with the official `run_backtest` boundary and internal stateful engine.
* Replace the global simulator broker branch with explicit simulation-scoped Trader binding.
* Replace embedded/assumed analytics with an Analytics contract.
* Replace optimization mocks with a real canonical single-run integration.

### V1 behaviours to remove

* The absent legacy package identity `app.services.simulator`, after external-caller verification.
* Deleted `app/services/NEW/simulator` implementation artifacts.
* Stale tests/examples that import missing modules, after equivalent canonical tests exist.
* Optimization `sys.modules` simulator mocks, after real integration exists.
* Any claim that `active_broker=simulator` is supported before a real contract-backed provider exists.

### V2 behaviours to add

* Explicit safe `run_backtest` tool and versioned envelopes.
* Canonical FX tick timeline, no-lookahead enforcement, and supported tick models.
* Deterministic matching, costs, margin, accounting, and selected MT5-parity semantics.
* Engine-owned orders, deals, positions, pending orders, account state, and read-only snapshots.
* Data/strategy/broker manifest validation and severe-failure gate.
* Immutable streaming journal, replay, lifecycle, and request idempotency.
* Canonical SimulationResult, JSON report, Markdown report, and artifact manifest.
* Fixed-precision accounting, deterministic SIM_* errors, import safety, and no-live-side-effects.
* Traceable Phase 1 contract, golden, replay, persistence-failure, and boundary tests.

### V2 proposals to reject or defer

* Optimization search algorithms and robustness-analysis ownership in Simulation.
* Full analytics formula ownership in Simulation.
* Data-platform caches, vendor governance, and complete lineage ownership in Simulation.
* Risk-policy, VaR, correlation, concentration, and approval ownership in Simulation.
* Blanket rule that every `__all__` export is an AI tool.
* Mandatory SQLite sidecar before demonstrated query/performance need.
* Tick batching before correctness and benchmark proof.
* Distributed workers, queues, quotas, poison work units, canaries, and synthetic probes.
* Corporate actions, borrow fees, futures rollover, perpetual funding, options, regulatory engines, feature stores, and alternative data.
* Visual/debug replay, external report distribution, and production-promotion automation in the initial rebuild.

### Required open decisions before README completion

* Shared Trader protocol ownership and selection.
* Exact Strategy, Indicator, Data, broker-profile, and manifest contracts.
* Risk/sizing and Analytics boundaries.
* Exact Phase 1 request/envelope schemas and status set.
* Exact Phase 1 tick models and MT5 parity fixture.
* Phase 1 order modification/RETURN/cancel-replace scope.
* Journal durability and optional sidecar policy.
* FX conversion provider and cross-rate policy.
* Project-wide CI tooling policy and approved performance gates.
* Legacy `simulator` caller migration deadline.

## 13. Final Reconciliation Checklist
* [x] every V1 capability received a disposition.
* [x] every V2 requirement received a disposition.
* [x] every V1 workflow was reconciled.
* [x] every proposed V2 workflow was reconciled.
* [x] confirmed working V1 behaviour was not discarded without reason.
* [x] unused V1 behaviour was not preserved without reason.
* [x] V2 implementation complexity was not accepted automatically.
* [x] the proposed direction follows the four-level minimal structure.
* [x] capabilities suspected to belong to another domain are flagged.
* [x] unresolved conflicts are listed under Open Decisions.
* [x] cross-domain open decisions and system-shape deferrals are marked for top-level escalation.
* [x] no code was changed.
* [x] neither source document was modified.
* [x] the output is sufficient to write the final domain README after open contract decisions are resolved.

**Disposition count check:** 1636 total = Add 841, Defer 423, Keep 22, Merge 143, Modify 171, Open Decision 27, Reject 9.

## Evidence Not Available

* Exact approved Strategy, Indicator, Data, Trader, broker-profile, market-data-authority, artifact, and Analytics contracts.
* Top-level system ownership decisions, ADRs, roadmap promotion decisions, and deferred-capability register.
* An approved MT5 parity fixture and broker/data manifest.
* Owner-approved public schemas, performance thresholds, memory gates, durability settings, and CI tooling policy.
* Runtime/deployment evidence showing whether external callers still depend on `app.services.simulator` or `active_broker=simulator`.
