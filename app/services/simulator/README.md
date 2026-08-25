# Simulator

> **Package:** `app/services/simulator/`
> **Status:** `Missing`
> **Last updated:** `2026-08-25`
> **Domain ID:** `D-SIM`
> **Specification version:** `1.2-execution-parity`

> This README is the domain package's **single source of truth** for Simulator boundaries, feature IDs/statuses, functional requirements, domain-local workflows, semantic contract ownership, persistence, implementation sequence, and acceptance evidence.
> Update this document before modifying or adding Simulator code.
> Cross-domain execution ownership follows [`docs/EXECUTION_PARITY.md`](../../../docs/EXECUTION_PARITY.md): Simulator is the deterministic `SIM`/`PAPER` execution authority for the one Trading-owned business execution lifecycle. It does not implement a second canonical trading lifecycle.

---

## Code-Aligned Implementation Convention

`PROJECT.md` owns system scope, cross-domain behavior, system NFRs, dependency direction, and release gates. `ARCHITECTURE.md` owns universal package/runtime constraints. `EXECUTION_PARITY.md` owns the unified Runtime Risk -> Trading -> execution-authority relationship. This README remains the authoritative Simulator target registry.

Implementation uses the repository's feature substrate: each feature lives directly at `app/services/simulator/<feature>/`, is discovered through `haruquantai.features`, and declares one immutable `FeatureSpec` in `manifest.py`. Every implemented feature also contains runtime-validated `README.md`, pure `__init__.py`, strict `config.py`, lifecycle `feature.py`, and focused implementation modules. Cross-feature and cross-domain collaboration uses exact versioned capabilities through `FeatureContext`/`FeatureScope`; private implementation imports are prohibited.

Feature-level automated tests live at `tests/services/simulator/<feature>/`. Usage examples belong to each feature's designated primary domain-logic module. The code-backed procedure is the [Feature Implementation Pipeline](../../../docs/dev/feature_implementation_pipeline.md).

---

## 1. Purpose and Boundary

### Purpose

Simulator provides deterministic historical/replay execution and forward paper execution mechanics, reproducible run/result orchestration, engine/precision profiles, event scheduling, matching, spread/slippage/cost modeling, checkpointing, perturbation, distribution, Stockpicker simulation, and differential/parity evidence.

For execution-parity runs the path is:

```text
Strategy intent
  -> Runtime Risk
  -> Trading canonical lifecycle
  -> Simulator execution-authority capability
  -> Simulator authority-side matching/fills/snapshots
  -> Trading canonical receipt/order/deal/position evidence
  -> Simulator committed result
  -> Analytics
```

The authority changes by route. The business trading lifecycle does not.

### Owns

- `FEAT-SIM-CONFIGURE_ENGINE` — Run Manifest and Engine Profile.
- `FEAT-SIM-MODEL_PRECISION` — Precision Models.
- `FEAT-SIM-SIMULATE_ORDERS` — Simulator Authority Matching and State Evidence.
- `FEAT-SIM-CALCULATE_COSTS` — Execution Cost Models and Sizing Conformance Evidence.
- `FEAT-SIM-MANAGE_EXITS` — Authority-Side Exit/ATM Mechanics, Schedules, and Segments.
- `FEAT-SIM-RUN_INDICATORS` — Indicator Runtime.
- `FEAT-SIM-COMMIT_RESULTS` — Result Commit, Checkpointing, and Job Control.
- `FEAT-SIM-CACHE_EVALUATIONS` — Evaluation Cache.
- `FEAT-SIM-PERTURB_INPUTS` — Perturbation Hooks.
- `FEAT-SIM-DISTRIBUTE_EVALUATIONS` — Distributed Evaluation.
- `FEAT-SIM-SIMULATE_STOCKPICKERS` — Stockpicker Simulation.
- `FEAT-SIM-CALCULATE_PROFILES` — Volume Profile and TPO Indicators.
- Deterministic scheduler/time authority for `SIM` and configured `PAPER` execution.
- Intrabar paths, order-trigger/matching mechanics, simulated liquidity/partial-fill behavior, spread, slippage, commission, financing/swap, and target-runtime semantic emulation.
- Simulator authority-side pending-order/fill/position snapshots required to return truthful execution-authority evidence to Trading.
- Reproducible result projections, checkpoints, first-divergence/parity evidence, and simulation-specific artifacts.

### Does not own

- Strategy authoring or signal generation; Strategy owns them.
- Executable sizing/admission, approval tokens, capacity, or kill-switch authority; Runtime Risk owns them for parity execution.
- Canonical application operation/order/deal/position lifecycle, idempotency policy, protection ownership, receipt classification, or reconciliation policy; Trading owns them.
- Broker/provider transport, credentials, or demo/live authority state; Broker Connectivity owns them.
- Catalogue instrument/rule/cost definitions or Data source preparation.
- Analytics metrics, Research search policy, Portfolio construction, Interfaces, or UI behavior.
- A parallel “simulation trading” business state machine.

### Deletion boundary

Deleting `app/services/simulator/` makes `SIM`/Simulator-backed `PAPER`, native simulation, runtime indicator evaluation, and new simulation-result production unavailable. Broker-backed `DEMO`/`LIVE` Trading remains healthy when its own dependencies exist. Strategies, data, Trading contracts/state, and existing committed results remain manageable. The kernel and unrelated domains remain healthy.

### Execution-authority invariant

Simulator accepts only a Trading-approved executable request through a public versioned capability boundary. It cannot create or enlarge executable quantity, bypass Runtime Risk, or construct canonical Trading order/deal/position state directly.

Simulator may maintain authority-local state needed for matching. That state is evidence, not the application business ledger.

---

## 1.1 Shared Contracts

Simulator semantically owns the contracts listed here; physical definitions live in `app/contracts/simulator/` and generated wire schemas under `app/contracts/simulator/wire/`. This reconciliation deliberately preserves the existing 23-record v1 planning surface while clarifying ownership. Record names are not permission to duplicate Trading business authority.

Rows labelled `FEAT-* capability surface` are semantic bundles, not literal runtime capability keys.

| Status | Contract | Version | Counterparty | Reconciled purpose |
|---|---|---|---|---|
| Missing | `FEAT-SIM-CONFIGURE_ENGINE` capability surface | `v1` | Trading, Catalogue, Data, Research, Strategy, Workspace | Run manifest, pinned behavior providers, engine profile, scheduler/event semantics. |
| Missing | `FEAT-SIM-MODEL_PRECISION` capability surface | `v1` | Trading, Catalogue, Data, Research, Strategy | Deterministic precision/intrabar/spread source semantics. |
| Missing | `FEAT-SIM-SIMULATE_ORDERS` capability surface | `v1` | Trading, Research, Strategy, Workspace | Simulator authority matching, pending state, fills, snapshots, checkpoints, and comparison evidence. |
| Missing | `FEAT-SIM-CALCULATE_COSTS` capability surface | `v1` | Trading, Runtime Risk, Catalogue, Research | Cost/fill-price mechanics plus sizing-conformance evidence; never executable sizing authority. |
| Missing | `FEAT-SIM-MANAGE_EXITS` capability surface | `v1` | Trading, Strategy, Research | Authority-side execution of Trading-owned protection/exit intent under pinned engine semantics. |
| Missing | `FEAT-SIM-RUN_INDICATORS` capability surface | `v1` | Strategy, Research | Deterministic indicator runtime state. |
| Missing | `FEAT-SIM-COMMIT_RESULTS` capability surface | `v1` | Trading, Analytics, Research, Workspace | Reconciled result commit/checkpoint/control and first-divergence evidence. |
| Missing | `FEAT-SIM-CACHE_EVALUATIONS` capability surface | `v1` | Research | Semantic evaluation cache. |
| Missing | `FEAT-SIM-PERTURB_INPUTS` capability surface | `v1` | Research | Deterministic perturbation hooks. |
| Missing | `FEAT-SIM-DISTRIBUTE_EVALUATIONS` capability surface | `v1` | Research, Workspace | Distributed deterministic evaluation. |
| Missing | `FEAT-SIM-SIMULATE_STOCKPICKERS` capability surface | `v1` | Trading, Research, Catalogue, Data | Stockpicker execution-authority simulation. |
| Missing | `FEAT-SIM-CALCULATE_PROFILES` capability surface | `v1` | Data, Strategy, Research | Deterministic Volume Profile/TPO calculation. |

### Cross-domain capability dependencies

For parity execution, the relevant Simulator feature manifests require public capabilities from Trading and Runtime Risk as dictated by their exact feature behavior. This package never imports Trading/Risk implementation modules. Runtime callbacks/events do not reverse package-import direction.

The package also consumes Catalogue/Data/Strategy/Workspace capabilities as specified by the FRs below. Research may consume Simulator but is not a prerequisite of baseline simulation.

### Ratified v1 public records (23)

Deterministic identity rule: run/result/authority-evidence identities are pinned by content hashes and monotonic simulation sequence. Repeated runs on one manifest and seed set emit identical canonical artifacts and equivalent Trading evidence.

| # | Record | Exact wire fields / invariant | Reconciled semantic role |
|---|---|---|---|
| R1 | `RunManifest` | Existing v1 fields: manifest/job/capability snapshot, behavior providers, engine/profile, strategy/settings/data/catalogue/block versions, seed streams, environment, segments, artifacts, state, hash. | Pins every material simulation and authority-semantic input, including the Trading/Risk capability providers used for execution parity. |
| R2 | `EngineProfileVersion` | Existing v1 target runtime, timing, path/gap/fill, position, rounding, session, collision, cost, capability matrix, hash. | Declares Simulator authority semantics; does not redefine Trading business states. |
| R3 | `PrecisionModel` | Existing selected-timeframe/M1/tick precision, intrabar path, spread and missing-side policy. | Authority market-path/fill input semantics. |
| R4 | `SimulationRequest` | Existing request, strategy/profile/settings/data/seed/idempotency/priority fields. | Requests a simulation job; executable order actions produced by the run still traverse Risk -> Trading -> Simulator authority. |
| R5 | `SimulationRunRef` | Existing run/job/manifest/state/progress fields. | Simulation job lifecycle, distinct from Trading operation lifecycle. |
| R6 | `SimulationEvent` | Existing monotonic event envelope. | Simulator scheduler/authority/result event evidence. Trading maintains its own canonical causal execution events. |
| R7 | `SimOrder` | Existing authority order fields/state. | **Simulator authority-side order/matching evidence only.** It cannot be exposed as a competing canonical `TradingOrder`. |
| R8 | `SimFill` | Existing fill sequence/time/price/spread/slippage/source-event fields. | **Simulator authority fill evidence** returned to Trading; canonical accepted execution becomes Trading-owned deal/evidence. |
| R9 | `SimPosition` | Existing authority position/result/size/P&L fields. | **Simulator authority snapshot/result evidence** used for reconciliation; canonical application position remains Trading-owned. |
| R10 | `SimTrade` | Existing result/position/segment/open-close/P&L/cost/MAE/MFE fields. | **Simulation result projection** derived from reconciled canonical execution plus Simulator authority details; not a mutable business order ledger. |
| R11 | `SizingDecision` | Existing method/computed/normalized/rejection/order fields. | **Simulator sizing-conformance/calculation trace only.** For parity execution, `normalized_size` must equal the current Runtime Risk-approved executable quantity; the record cannot approve, increase, or substitute size. |
| R12 | `CostBreakdown` | Existing price/spread/slippage/commission/swap/conversion/net fields; exact reconciliation. | Simulator execution-cost/result evidence. |
| R13 | `ExitSchedule` | Existing exit kind/level/activation/collision/considered-condition fields. | Authority-side schedule used to execute Trading-owned protection/exit semantics under the pinned engine profile. |
| R14 | `ResultSegment` | Existing half-open segment fields/policies. | Result partition/admission window evidence; does not replace Trading/Risk admission. |
| R15 | `IndicatorRuntimeSpec` | Existing indicator/version/chart/warmup/missing/state-scope fields. | Deterministic simulation indicator runtime. |
| R16 | `SimulationResult` | Existing strategy/manifest/state/completion/metric and artifact refs/times/hash. | Committed simulation result after Trading/authority/result reconciliation. |
| R17 | `ResultCommitReceipt` | Existing reconciliation/schema/checksum/commit fields. | Atomic result-commit evidence. |
| R18 | `EvaluationCacheKey` | Existing strategy/engine/data/partition/cost/metric/seed hashes. | Cache identity must include all material execution-authority/Trading/Risk semantics through the pinned manifests/provider hashes. |
| R19 | `PerturbationSpec` | Existing cost/data/parameter/execution-delay/trade-sequence perturbation fields. | Research perturbation of Simulator authority/input behavior, never silent mutation of Trading/Risk policy. |
| R20 | `DistributedEvaluationPlan` | Existing manifest/partitions/worker requirements/locality fields. | Distribution plan preserving identical canonical Trading/Simulator results. |
| R21 | `StockpickerSimulationSpec` | Existing universe/ranking/rebalance/allocation/cost/delisting/missing/timing fields. | Stockpicker simulation profile whose executable actions still use the common Risk/Trading path. |
| R22 | `VolumeProfileResult` | Existing Data source/session/value-area/POC/bins/incomplete/hash fields. | Deterministic indicator/result evidence. |
| R23 | `TpoProfileResult` | Existing source/session/POC/TPO/incomplete/hash fields. | Deterministic indicator/result evidence. |

Cross-owner records are referenced, never copied: Trading executable/canonical execution contracts, Risk decisions/sizing authority, `UniverseRef` (Catalogue), Data bindings/profile sources, Strategy definitions, Analytics metric values, Workspace job/lease records.

### Ratified v1 capabilities and operation envelopes

The existing capability IDs remain stable. Their semantics are reconciled as follows:

1. `simulator.configure-engine@1` — defines/lists pinned authority engine profiles.
2. `simulator.model-precision@1` — defines/validates deterministic market-path inputs.
3. `simulator.simulate-orders@1` — drives run control and **Simulator authority matching/state evidence**; it receives only admitted Trading execution work for business mutations.
4. `simulator.calculate-costs@1` — applies spread/slippage/commission/swap and may calculate sizing evidence for conformance, but cannot replace Runtime Risk-approved executable quantity.
5. `simulator.manage-exits@1` — performs authority-side trigger/collision/fill mechanics for Trading-owned protections/exits.
6. `simulator.run-indicators@1` — deterministic indicator runtime.
7. `simulator.commit-results@1` — validates/commits reconciled results and checkpoints.
8. `simulator.cache-evaluations@1` — semantic cache.
9. `simulator.calculate-profiles@1` — experimental Volume Profile/TPO.
10. `simulator.perturb-inputs@1` — deterministic perturbation definitions.
11. `simulator.distribute-evaluations@1` — distributed deterministic plan/progress.
12. `simulator.simulate-stockpickers@1` — Stockpicker simulation using the same execution-parity boundary.

`SimulatorFailure` remains the domain failure envelope. Missing Trading/Risk capability required by a parity run returns `CAPABILITY_UNAVAILABLE`; the Simulator does not fall back to its own business lifecycle.

### Persisted State Ownership

| Status | State / Store | Ownership rule |
|---|---|---|
| Missing | `run_manifests`, `results`, `result_segments` | Canonical Simulator run/result state. |
| Missing | `orders`, `fills`, `positions` | Simulator **authority-side** matching/reconciliation evidence only; not canonical Trading business state. |
| Missing | `trades` | Simulator result projection derived from reconciled execution; not a second mutable trading ledger. |

Other domains access this state only through public Simulator capabilities.

---

## 2. Final Package Structure and Feature Independence

```text
simulator/
├── README.md
├── __init__.py
├── run_manifest_engine_profile/    # FEAT-SIM-CONFIGURE_ENGINE
├── precision_models/               # FEAT-SIM-MODEL_PRECISION
├── order_position_lifecycle/       # FEAT-SIM-SIMULATE_ORDERS (authority matching/state evidence)
├── sizing_trading_costs/           # FEAT-SIM-CALCULATE_COSTS
├── exit_schedule_atm/              # FEAT-SIM-MANAGE_EXITS
├── indicator_runtime/              # FEAT-SIM-RUN_INDICATORS
├── result_commit_job_control/      # FEAT-SIM-COMMIT_RESULTS
├── evaluation_cache/               # FEAT-SIM-CACHE_EVALUATIONS
├── perturbation_hooks/             # FEAT-SIM-PERTURB_INPUTS
├── distributed_evaluation/         # FEAT-SIM-DISTRIBUTE_EVALUATIONS
├── stockpicker_simulation/         # FEAT-SIM-SIMULATE_STOCKPICKERS
└── volume_profile_tpo/             # FEAT-SIM-CALCULATE_PROFILES
```

Each feature folder contains mandatory `README.md`, pure `__init__.py`, `manifest.py`, `config.py`, `feature.py`, and its focused responsibility module. Feature modules do not import one another's private files. Runtime dependencies resolve through exact capability keys obtained from `FeatureContext`.

The feature IDs, module folders, and FR IDs are retained unchanged by the execution-parity reconciliation. Only ownership semantics that previously duplicated Risk/Trading are corrected.

---

## 3. Workflows

| Status | Workflow ID | Workflow | Reconciled boundary | Requirement sequence |
|---|---|---|---|---|
| Missing | `WF-SIM-001` | Run Manifest and Engine Profile | Admit/pin a run and its Trading/Risk/authority behavior providers; prepare deterministic scheduler. | `FR-SIM-BUILD_RUN_MANIFEST` -> `FR-SIM-PIN_RUN_INPUTS` -> `FR-SIM-PROCESS_EVENT_STREAM` -> `FR-SIM-ENFORCE_CLOSED_INPUTS` -> `FR-SIM-DEFINE_ENGINE_SEMANTICS` -> `FR-SIM-VERSION_ENGINE_PROFILES` |
| Missing | `WF-SIM-002` | Precision Models | Build deterministic authority market path/precision evidence. | `FR-SIM-MODEL_INTRABAR_PATH` -> `FR-SIM-SIMULATE_FROM_M1` -> `FR-SIM-APPLY_CUSTOM_SPREAD` -> `FR-SIM-APPLY_RECORDED_SPREAD` |
| Missing | `WF-SIM-003` | Authority Order Matching and State | Receive Trading-approved work, match/process it, return authority fill/order/position evidence. | `FR-SIM-JOURNAL_SIMULATION_EVENTS` -> `FR-SIM-VALIDATE_MARKET_ORDERS` -> `FR-SIM-PROCESS_PENDING_ORDERS` -> `FR-SIM-PROCESS_STOP_LIMITS` -> `FR-SIM-MODEL_POSITION_ACCOUNTING` -> `FR-SIM-TRACK_ENTRY_IDENTITIES` |
| Missing | `WF-SIM-004` | Sizing Conformance and Trading Costs | Verify Risk-approved quantity and apply Simulator execution-cost mechanics. | `FR-SIM-CALCULATE_POSITION_SIZE` -> `FR-SIM-REJECT_INVALID_SIZE` -> `FR-SIM-APPLY_SPREAD` -> `FR-SIM-APPLY_SLIPPAGE` -> `FR-SIM-APPLY_COMMISSION` -> `FR-SIM-APPLY_SWAP_FINANCING` -> `FR-SIM-RECONCILE_TRADING_COSTS` |
| Missing | `WF-SIM-005` | Exits, Schedules, Segments, and ATM | Execute authority-side triggers/fills for Trading-owned protection/exit intent and result segments. | `FR-SIM-APPLY_STOP_TARGET` -> `FR-SIM-APPLY_DYNAMIC_EXITS` -> `FR-SIM-RESOLVE_EXIT_COLLISIONS` -> `FR-SIM-ENFORCE_TRADING_SCHEDULE` -> `FR-SIM-DEFINE_RESULT_SEGMENTS` -> `FR-SIM-ENFORCE_TRADE_RESTRICTIONS` -> `FR-SIM-EXECUTE_ATM_STATE` -> `FR-SIM-ALLOCATE_PARTIAL_EXITS` -> `FR-SIM-GENERATE_ATM_SCENARIOS` |
| Missing | `WF-SIM-006` | Indicator Runtime | Isolate/warm deterministic indicator state. | `FR-SIM-ISOLATE_INDICATOR_STATE` |
| Missing | `WF-SIM-007` | Result Commit and Job Control | Reconcile canonical Trading execution with Simulator authority/result artifacts before commit; checkpoint/control/compare. | `FR-SIM-COMMIT_SIMULATION_RESULT` -> `FR-SIM-CHECKPOINT_SIMULATION` -> `FR-SIM-PRESERVE_PARTIAL_RESULTS` -> `FR-SIM-COMPARE_EXECUTION_RESULTS` -> `FR-SIM-STREAM_BATCH_PROGRESS` |
| Missing | `WF-SIM-008` | Evaluation Cache | Cache by complete semantic identity including Trading/Risk/authority provider pins. | `FR-SIM-CACHE_EVALUATIONS` |
| Missing | `WF-SIM-009` | Perturbation Hooks | Define deterministic research perturbations without changing baseline execution policy. | `FR-SIM-PERTURB_SIMULATION` |
| Missing | `WF-SIM-010` | Distributed Evaluation | Preserve canonical results independent of worker scheduling/locality. | `FR-SIM-DISTRIBUTE_SIMULATION` |
| Missing | `WF-SIM-011` | Stockpicker Simulation | Run historical-universe ranking and execution through the unified Trading path. | `FR-SIM-SIMULATE_STOCKPICKER` -> `FR-SIM-DEFINE_STOCKPICKER_TIMING` -> `FR-SIM-ENFORCE_DAILY_STOCKPICKER` |
| Missing | `WF-SIM-012` | Volume Profile and TPO | Calculate deterministic profile indicators from validated Data sources. | `FR-SIM-CALCULATE_VOLUME_PROFILES` |

### End-to-end parity workflow

A `SimulationRequest` may create/pin a run before individual trade actions exist. Once a Strategy action becomes executable, Simulator must not bypass the common path:

```text
Simulation scheduler produces observable Strategy event
  -> Strategy emits intent
  -> Runtime Risk evaluates/sizes/admit or NO_TRADE
  -> Trading creates canonical logical operation and applies common gates
  -> Trading dispatches to Simulator authority capability
  -> Simulator matches and returns authority receipt/fill/snapshot evidence
  -> Trading classifies/reconciles and updates canonical state
  -> Simulator records result projections/checkpoint state
```

Missing required Risk/Trading capability stops the executable path with a structured capability failure; it never silently switches to a legacy private simulation lifecycle.

---

## 4. Composable Feature Specifications

Implement these sections in order. `Depends` describes product/acceptance sequencing; runtime dependencies are exact versioned capability keys declared by `FeatureSpec`.

### 4.1 `FEAT-SIM-CONFIGURE_ENGINE` — Run Manifest and Engine Profile

**Module:** `run_manifest_engine_profile/`
**Responsibility file:** `run_manifest_engine_profile.py`
**Purpose:** Admit runs, pin every semantic input/provider, order events, and select deterministic target semantics.
**Deletion:** New simulations are unavailable; existing manifests/results remain inspectable.

| Status | Requirement ID | Pri | Reconciled responsibility | Acceptance / failure |
|---|---|---:|---|---|
| Missing | `FR-SIM-BUILD_RUN_MANIFEST` | P0 | Atomically create immutable run manifest and durable queued job only after all inputs and required execution-parity capability bindings validate. | Same idempotency key returns original job; missing Risk/Trading provider required by the selected run profile does not create a bypass run. |
| Missing | `FR-SIM-PIN_RUN_INPUTS` | P0 | Pin engine/profile, Strategy version/hash, settings/hash, Data/Catalogue/block versions, seeds, and all material Trading/Risk/authority behavior-provider versions/hashes. | Manifest comparison reports every material semantic difference. |
| Missing | `FR-SIM-PROCESS_EVENT_STREAM` | P0 | Process a deterministic ordered simulation event stream and drive Strategy/Risk/Trading/authority interactions at their declared event phases. | Same manifest produces identical authority and canonical Trading/result evidence. |
| Missing | `FR-SIM-ENFORCE_CLOSED_INPUTS` | P0 | Expose only closed/observable data under the documented timestamp/chart-ordinal rules. | Simultaneous/missing-bar fixtures prove no future leakage. |
| Missing | `FR-SIM-DEFINE_ENGINE_SEMANTICS` | P0 | Declare signal evaluation, order activation, same-bar/gap/fill priority, authority position model, rounding, sessions, collisions, and cost policy. | A run cannot start with an unspecified required authority semantic. |
| Missing | `FR-SIM-VERSION_ENGINE_PROFILES` | P0 | Provide separately versioned semantic profiles for advertised target runtimes and parity targets. | Profile-specific golden/differential tests pass before advertisement. |

### 4.2 `FEAT-SIM-MODEL_PRECISION` — Precision Models

**Module:** `precision_models/`
**Responsibility file:** `precision_models.py`
**Purpose:** Provide deterministic market-path/price-side evidence to the Simulator authority.

| Status | Requirement ID | Pri | Reconciled responsibility | Acceptance / failure |
|---|---|---:|---|---|
| Missing | `FR-SIM-MODEL_INTRABAR_PATH` | P0 | `SELECTED_TIMEFRAME` constructs deterministic intrabar events from OHLC using the normative path policy. | Bull/bear/doji/gap/collision fixtures identify exact event order. |
| Missing | `FR-SIM-SIMULATE_FROM_M1` | P0 | `M1_SIMULATION` uses ordered underlying M1 bars and the same per-M1 path policy. | Higher-timeframe result reconciles to underlying event stream; missing coverage follows policy. |
| Missing | `FR-SIM-APPLY_CUSTOM_SPREAD` | P0 | Custom-spread real-tick mode uses canonical bid and derives ask only as explicitly configured. | Bid/ask authority fills match fixtures. |
| Missing | `FR-SIM-APPLY_RECORDED_SPREAD` | P0 | Recorded-spread mode uses recorded bid/ask and rejects a missing required side. | Ask is never synthesized in recorded mode. |

### 4.3 `FEAT-SIM-SIMULATE_ORDERS` — Simulator Authority Matching and State Evidence

**Module:** `order_position_lifecycle/`
**Responsibility file:** `order_position_lifecycle.py`
**Purpose:** Execute Simulator authority matching for Trading-approved requests and expose truthful authority state. It does not create canonical Trading orders or positions independently.
**Deletion:** `SIM`/Simulator-backed `PAPER` execution authority is unavailable; Broker-backed Trading remains independent.

| Status | Requirement ID | Pri | Reconciled responsibility | Acceptance / failure |
|---|---|---:|---|---|
| Missing | `FR-SIM-JOURNAL_SIMULATION_EVENTS` | P0 | Record scheduler/authority signals, order receptions, fills, cancellations, stop updates, forced exits, and errors as typed monotonic Simulator events linked to Trading operation/evidence identities. | First-divergence tooling identifies earliest authority mismatch without parsing logs. |
| Missing | `FR-SIM-VALIDATE_MARKET_ORDERS` | P0 | Validate **authority-side** order compatibility: Risk-approved quantity equality, session/time window, instrument/venue constraints, target-engine capability, and matching prerequisites. | It never performs a second business Risk admission; any quantity mismatch or unsupported authority semantic rejects before fill. |
| Missing | `FR-SIM-PROCESS_PENDING_ORDERS` | P0 | Process stop/limit eligibility and fills according to pinned path/gap/slippage/partial-fill/TIF rules. | No fill occurs before eligibility or above Trading-requested/Risk-approved quantity. |
| Missing | `FR-SIM-PROCESS_STOP_LIMITS` | P0 | Maintain distinct authority trigger and limit phases for stop-limit requests. | Trigger without eligible limit remains pending and both phases are evidence-visible. |
| Missing | `FR-SIM-MODEL_POSITION_ACCOUNTING` | P0 | Maintain the selected Simulator authority hedged/netted/one-position model needed for matching, fills, P/L, and snapshots. | Authority snapshots reconcile to fills; canonical application position remains Trading-owned. |
| Missing | `FR-SIM-TRACK_ENTRY_IDENTITIES` | P0 | Preserve stable authority entry/order identities, independent quantities, and protection linkage required for Trading reconciliation. | Scaling fixtures reconcile entries/exits/costs and never silently merge identities. |

### 4.4 `FEAT-SIM-CALCULATE_COSTS` — Execution Cost Models and Sizing Conformance

**Module:** `sizing_trading_costs/`
**Responsibility file:** `sizing_trading_costs.py`
**Purpose:** Apply deterministic execution-cost models and prove that Simulator never changes executable size approved by Runtime Risk.
**Deletion:** Runs requiring missing cost behavior are rejected; no zero-cost fallback is inferred.

| Status | Requirement ID | Pri | Reconciled responsibility | Acceptance / failure |
|---|---|---:|---|---|
| Missing | `FR-SIM-CALCULATE_POSITION_SIZE` | P0 | Calculate the versioned historical sizing formula as **conformance evidence** and compare it with the Runtime Risk sizing/approval used by the Trading request. For parity execution, the executable quantity is the Risk-approved quantity. | Exact method fixtures reconcile; mismatch is reported/rejected and Simulator cannot replace or increase approved quantity. |
| Missing | `FR-SIM-REJECT_INVALID_SIZE` | P0 | Reject authority execution when the Trading-approved quantity violates instrument authority constraints or required sizing evidence is inconsistent. | No implicit minimum-size trade and no Simulator-side resizing. |
| Missing | `FR-SIM-APPLY_SPREAD` | P0 | Apply spread on the correct executable side under selected precision/profile. | Long/short entry/exit fixtures reconcile. |
| Missing | `FR-SIM-APPLY_SLIPPAGE` | P0 | Apply named/versioned slippage and record pre-slippage price, slippage, final price, and seed where applicable. | Seeded random slippage reproduces identically. |
| Missing | `FR-SIM-APPLY_COMMISSION` | P0 | Apply the declared commission model with explicit timing/currency. | Component charges reconcile exactly. |
| Missing | `FR-SIM-APPLY_SWAP_FINANCING` | P0 | Apply side-specific financing using pinned rollover/day-count/multiplier/conversion semantics. | Triple-swap/calendar fixtures reconcile. |
| Missing | `FR-SIM-RECONCILE_TRADING_COSTS` | P0 | Persist/reconcile each authority cost component from gross to net P/L. | Price P/L + spread + slippage + commission + swap + conversion equals net result under exact currency rules. |

`SizingDecision` is retained as a Simulator-local calculation/conformance record. It is not a `RiskDecision`, approval token, or permission to execute.

### 4.5 `FEAT-SIM-MANAGE_EXITS` — Authority-Side Exits, Schedules, Segments, and ATM

**Module:** `exit_schedule_atm/`
**Responsibility file:** `exit_schedule_atm.py`
**Purpose:** Execute deterministic authority mechanics for Trading-owned protections/exits and Simulator result segmentation.

| Status | Requirement ID | Pri | Reconciled responsibility | Acceptance / failure |
|---|---|---:|---|---|
| Missing | `FR-SIM-APPLY_STOP_TARGET` | P0 | Match stop-loss/profit-target requests using every supported distance/expression and authority price rule. | Long/short levels/fills obey pinned engine semantics and never alter Trading protection ownership. |
| Missing | `FR-SIM-APPLY_DYNAMIC_EXITS` | P1 | Execute trailing, breakeven, bars/rule/EOD/Friday authority triggers. | Distinct close reasons and deterministic precedence are evidenced. |
| Missing | `FR-SIM-RESOLVE_EXIT_COLLISIONS` | P0 | Resolve same-event authority collisions using versioned path/priority policy and record all considered conditions. | Collision fixtures explain winner and alternatives. |
| Missing | `FR-SIM-ENFORCE_TRADING_SCHEDULE` | P1 | Apply configured simulation trading/session schedule using configured timezone. | Machine timezone cannot alter result. |
| Missing | `FR-SIM-DEFINE_RESULT_SEGMENTS` | P0 | Define explicit half-open IS/validation/OOS/no-trade result ranges. | Boundary event belongs to exactly one non-FULL segment. |
| Missing | `FR-SIM-ENFORCE_TRADE_RESTRICTIONS` | P0 | Enforce result no-trade intervals for new/scale-in exposure while management/exits remain active. | Retain/cancel policy is journalled; the restriction is not a substitute for Risk admission. |
| Missing | `FR-SIM-EXECUTE_ATM_STATE` | P1 | Execute ATM authority state machine, splits, levels, transitions, protection, and cancellation under pinned semantics. | Gap/collision/expiry/rounding fixtures pass. |
| Missing | `FR-SIM-ALLOCATE_PARTIAL_EXITS` | P1 | Allocate authority fill quantity/cost/P&L/residual protection deterministically and feed resulting execution evidence back to Trading. | Canonical Trading quantity and Simulator result projections reconcile exactly. |
| Missing | `FR-SIM-GENERATE_ATM_SCENARIOS` | P1 | Generate the seven documented ATM scenarios deterministically from pinned configuration/seed. | Invalid combination fails admission and scenario selection reproduces. |

### 4.6 `FEAT-SIM-RUN_INDICATORS` — Indicator Runtime

**Module:** `indicator_runtime/`
**Responsibility file:** `indicator_runtime.py`

| Status | Requirement ID | Pri | Responsibility | Acceptance / failure |
|---|---|---:|---|---|
| Missing | `FR-SIM-ISOLATE_INDICATOR_STATE` | P0 | Isolate indicator state per Strategy instance/chart with declared warm-up and missing-value policy. | Parallel strategies cannot mutate each other's state; insufficient warm-up blocks or returns declared nulls. |

### 4.7 `FEAT-SIM-COMMIT_RESULTS` — Result Commit, Checkpointing, and Job Control

**Module:** `result_commit_job_control/`
**Responsibility file:** `result_commit_job_control.py`

| Status | Requirement ID | Pri | Reconciled responsibility | Acceptance / failure |
|---|---|---:|---|---|
| Missing | `FR-SIM-COMMIT_SIMULATION_RESULT` | P0 | Commit a result only after Simulator artifacts **and canonical Trading execution evidence** reconcile, schemas validate, and checksums pass. | Forced reconciliation/validation failure publishes no selectable complete result. |
| Missing | `FR-SIM-CHECKPOINT_SIMULATION` | P0 | Checkpoint only at declared safe scheduler/authority/Trading boundaries; resume after last committed work without duplicate logical operation/fill. | Pause/resume output equals uninterrupted deterministic output. |
| Missing | `FR-SIM-PRESERVE_PARTIAL_RESULTS` | P0 | Preserve stop/cancel outputs as explicitly incomplete artifacts without promoting them. | UI/Research cannot treat incomplete result as complete. |
| Missing | `FR-SIM-COMPARE_EXECUTION_RESULTS` | P0 | Align canonical Trading execution plus Simulator authority evidence with a reference target and report earliest event/time/type/side/price/size/cost/close mismatch. | A one-tick injected mismatch produces one first-divergence record/context. |
| Missing | `FR-SIM-STREAM_BATCH_PROGRESS` | P1 | Emit bounded intermediate summaries without committing partial final results. | Worker loss follows checkpoint policy. |

### 4.8 `FEAT-SIM-CACHE_EVALUATIONS` — Evaluation Cache

**Module:** `evaluation_cache/`
**Responsibility file:** `evaluation_cache.py`

| Status | Requirement ID | Pri | Responsibility | Acceptance / failure |
|---|---|---:|---|---|
| Missing | `FR-SIM-CACHE_EVALUATIONS` | P0 | Cache results by normalized Strategy, engine, Data, partition, cost, metric hook, seed, and material Trading/Risk/authority provider identity. | Any semantic input/provider change causes a miss. |

### 4.9 `FEAT-SIM-PERTURB_INPUTS` — Perturbation Hooks

**Module:** `perturbation_hooks/`
**Responsibility file:** `perturbation_hooks.py`

| Status | Requirement ID | Pri | Responsibility | Acceptance / failure |
|---|---|---:|---|---|
| Missing | `FR-SIM-PERTURB_SIMULATION` | P0 | Expose deterministic perturbations for costs, Data, parameters, execution delay, and trade sequence without changing baseline Trading/Risk semantics. | Zero perturbation hashes to baseline result. |

### 4.10 `FEAT-SIM-DISTRIBUTE_EVALUATIONS` — Distributed Evaluation

**Module:** `distributed_evaluation/`
**Responsibility file:** `distributed_evaluation.py`

| Status | Requirement ID | Pri | Responsibility | Acceptance / failure |
|---|---|---:|---|---|
| Missing | `FR-SIM-DISTRIBUTE_SIMULATION` | P1 | Preserve semantics independent of worker identity, locale, scheduling, or locality, including canonical Trading execution evidence. | Local/remote golden runs produce identical canonical artifacts. |

### 4.11 `FEAT-SIM-SIMULATE_STOCKPICKERS` — Stockpicker Simulation

**Module:** `stockpicker_simulation/`
**Responsibility file:** `stockpicker_simulation.py`

| Status | Requirement ID | Pri | Reconciled responsibility | Acceptance / failure |
|---|---|---:|---|---|
| Missing | `FR-SIM-SIMULATE_STOCKPICKER` | P1 | Evaluate versioned universe/ranking/rebalance/allocation/cost/delisting policy; executable constituent actions use common Runtime Risk -> Trading -> Simulator authority path. | Rotation fixtures reconcile constituents, canonical fills, cash, and equity. |
| Missing | `FR-SIM-DEFINE_STOCKPICKER_TIMING` | P0 | Define BEFORE_OPEN/ON_OPEN/ON_CLOSE visible-data frontier and execution timing. | Sentinel future values cannot alter ranking/orders. |
| Missing | `FR-SIM-ENFORCE_DAILY_STOCKPICKER` | P0 | Enforce daily-only pessimistic ambiguity and next-session protection rules where configured. | Same-day stop/target/gap/protection fixtures record the conservative rule used. |

### 4.12 `FEAT-SIM-CALCULATE_PROFILES` — Volume Profile and TPO Indicators

**Module:** `volume_profile_tpo/`
**Responsibility file:** `volume_profile_tpo.py`

| Status | Requirement ID | Pri | Responsibility | Acceptance / failure |
|---|---|---:|---|---|
| Missing | `FR-SIM-CALCULATE_VOLUME_PROFILES` | P1 | Calculate separate deterministic Volume Profile/TPO indicators from Data-owned validated sources. | Profile fixture passes before Strategy nodes can consume the indicator. |

---

## 5. Package-Wide Requirements and Architecture Invariants

### Persistence

The domain-owned table namespace is `simulator_`. Canonical Simulator entities are run manifests, results, result segments, and authority/result evidence. `orders`, `fills`, and `positions` are explicitly Simulator-authority scoped; `trades` are result projections. Trading owns the canonical business execution projections.

Only Simulator writes Simulator tables. Other domains use public capabilities. Simulator never writes Trading/Risk/Broker tables directly.

### Shared configuration

Feature configuration is strict TOML under `[features.FEAT-*].config`; accepted keys match the owning `FeatureSpec.config_keys`/`config.py`. Provider choice belongs in `[providers]`. No missing authority, risk, cost, precision, or execution policy receives a hidden default.

### Non-functional requirements

- Pinned deterministic inputs/time/providers produce byte-identical canonical Simulator artifacts and Trading execution evidence.
- No business mutation bypasses Runtime Risk/Trading in parity mode.
- Simulator never increases or substitutes Risk-approved executable quantity.
- The common Trading business state machine is not copied into Simulator.
- Authority-local order/fill/position structures are explicitly scoped and cannot be consumed as canonical Trading state without Trading reconciliation.
- Missing Trading/Risk capability required by a run fails closed; no legacy fallback.
- Physical removal of Simulator withdraws only Simulator-backed execution and simulation capabilities.
- All standard project determinism, durability, performance, isolation, observability, compatibility, lifecycle, replacement, leak, and exact-removal requirements apply.

---

## 6. Open Decisions

None. Any behavior not specified here, in `EXECUTION_PARITY.md`, or in the normative project/architecture contracts is unsupported and must fail capability validation rather than be guessed.

---

## 7. Tests and Definition of Done

### Required verification

- Every one of the 45 `FR-SIM-*` rows above has focused automated verification and a named executable usage scenario.
- `SIM` and `PAPER` authority integrations accept only Trading-approved requests.
- A Simulator authority cannot construct canonical Trading order/deal/position state directly.
- A Simulator authority cannot increase, replace, or independently approve Runtime Risk quantity.
- Equivalent route-applicable `SIM`, `PAPER`, `DEMO`, and `LIVE` scenarios prove the same Trading business/risk gate categories and ordering, with explicit route-specific safety/transport/time deltas only.
- Same manifest/seed/provider versions reproduce identical Simulator authority evidence and canonical Trading results.
- Partial fill, pending, stop-limit, hedging/netting, gap, collision, spread, slippage, commission, swap, checkpoint, event-gap, and first-divergence fixtures pass.
- Result commit fails when canonical Trading execution and Simulator result artifacts do not reconcile.
- Local/distributed equivalence passes.
- Feature disable/re-enable, physical removal, failed activation/cleanup, replacement, and leak tests pass.
- Removing Trading/Risk required by the selected execution-parity profile yields structured unavailability; no private fallback path appears.

### Commands

```bash
uv run ruff check app/services/simulator
uv run ruff format --check app/services/simulator
uv run mypy app/services/simulator
uv run pytest tests/services/simulator/<feature>/
uv run pytest tests/simulator --cov=app/services/simulator --cov-fail-under=80
```

### Package completion checklist

- [ ] Actual package tree matches Section 2.
- [ ] All 12 features and all 45 Simulator FRs are `Implemented` with executable evidence.
- [ ] Every public capability, dependency, effect, error, state owner, and contract is documented.
- [ ] Trading/Risk execution-parity integration and authority-removal tests pass.
- [ ] No duplicated canonical Trading or Runtime Risk business logic exists.
- [ ] Determinism, durability, performance, isolation, observability, compatibility, lifecycle, leak, and removal gates pass.
- [ ] No unresolved decision affects implementation.

---

## 8. Change Process

```text
1. Update this README first.
2. Update affected owned/consumed contracts and system workflows.
3. Preserve the one-Trading-lifecycle execution-parity invariant.
4. Resolve or record any decision that would otherwise require guessing.
5. Update the relevant FR, failure behavior, dependency, feature manifest, configuration, and evidence plan.
6. Implement the smallest change through public capability boundaries.
7. Execute usage, unit, integration, parity, deletion, and fault tests.
8. Mark Implemented only after every applicable gate passes.
```

Any proposal that gives Simulator its own executable sizing authority or canonical business order/deal/position lifecycle is an architecture regression unless `docs/EXECUTION_PARITY.md` is explicitly superseded.

---

## 9. Normative Simulator Authority Semantics

The stable `§18`/`§23` concepts from the consolidated specification remain binding. They describe **Simulator authority mechanics** and result calculations, not ownership of the application Trading lifecycle.

### §18.1 Event pipeline and authority ledger

For each instrument timestamp, Simulator processes deterministic market ingestion, clock/session advancement, scheduled financing, authority-order expiry, pre-existing trigger matching, authority fills/costs, trade callbacks, indicator/mark updates, Strategy evaluation, Trading-approved action dispatch, result/account updates, and immutable simulation-event journaling in the configured order. An action created at a later phase cannot participate in an earlier phase. Equal timestamps use canonical instrument/strategy ordering.

Financial result calculations use double-entry/reconciled evidence. Every simulated fill, fee, financing, deposit/withdrawal fixture, and conversion carries an identity/effective time. Missing required currency conversion makes valuation unavailable and prevents the Risk/Trading path from authorizing a quantity that depends on that valuation.

### §18.2 Intrabar path, triggers, gaps, and fills

Selected-timeframe deterministic path:

- `close >= open`: `open -> low -> high -> close`;
- `close < open`: `open -> high -> low -> close`.

Segments are monotonic. Triggers on one segment process in travel order; equal-price authority triggers use creation sequence except protective exits precede entries and stop loss precedes profit target under the selected profile. Tick mode uses `(timestamp, source_sequence)`. Recorded bid/ask is used directly; synthetic side construction is permitted only by the explicitly selected non-recorded spread profile.

Market/stop/limit/stop-limit, gap, spread, adverse slippage, rounding, price-band, partial-fill, TIF, validity-bar, and rejection mechanics follow the pinned `EngineProfileVersion`/`PrecisionModel`. Authority fills may never exceed the Trading-requested/Risk-approved quantity.

### §18.3 Authority position identity and matching

Supported authority position models are hedged, netted, and one-position-per-direction semantics as declared by the engine profile. Entry/order identities remain stable, close allocation is deterministic, and gross P/L/margin/notional calculations use pinned instrument/FX semantics.

These are Simulator authority mechanics. `SimPosition` is evidence; `TradingPositionProjection` is the canonical application projection after reconciliation.

### §18.4 Costs and financing

Commission models, spread treatment, swap/financing, rollover multipliers, currency conversion, and component journaling remain explicit and versioned. Spread represented in bid/ask is never charged a second time. Each component must reconcile gross P/L to net P/L exactly under declared currency tolerance/rules.

### §18.5 Sizing catalogue

The historical sizing catalogue remains available for deterministic calculation/conformance fixtures (`FixedSize`, fixed amount, balance/equity risk percent, ATR risk, stock/crypto/picker sizing, Martingale, and future versioned methods).

**Authority rule:** for a parity execution, this catalogue does not grant executable size. Runtime Risk produces the executable approval/maximum size. Simulator may calculate the expected historical sizing value and must compare it with the Risk-approved request; mismatch fails the run/action or produces explicit conformance evidence according to the selected profile. No hidden fallback to fixed/minimum size exists.

### §18.6 Protective exits and trading options

Stop/target/trailing/breakeven/time/rule/EOD/Friday trigger and schedule mechanics remain Simulator authority responsibilities. Trading owns protection identity, authorization, and canonical lifecycle. Simulator receives the approved protection/action and applies the pinned price/time/collision mechanics without silently widening, replacing, or re-owning it.

### §18.7 ATM authority state machine

The seven built-in ATM split scenarios and deterministic leg/level mechanics remain supported as Simulator authority execution behavior. Quantity allocation uses the exact Trading-approved filled/residual quantity and returns authority fill/protection evidence to Trading. Global/protective collisions cannot create duplicate canonical close operations.

### §18.8 Stockpicker timing

`BEFORE_OPEN`, `ON_OPEN`, and `ON_CLOSE` define exact visible-data frontiers and execution timing. The daily profile uses pessimistic ambiguity rules where configured. Ranking/allocation proposes actions; executable constituent orders still traverse Runtime Risk and Trading before Simulator matches them.

### §23 Golden parity fixtures

The existing intrabar/gap/order-identity/position-mode, cost/currency/margin/sizing, and ATM split/state golden examples remain required. Their expected Simulator fills/results are reconciled with the canonical Trading operation/deal/position evidence rather than tested as a separate business ledger.
