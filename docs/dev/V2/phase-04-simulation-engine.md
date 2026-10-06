# Phase 4 — Simulation

**Feature group:** F04. **Tasks:** 7. **Status:** proposed; 0 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Execute a validated immutable run specification in explicit chronological order. This phase owns the simulation capability group. Use the shared host and existing domain operations; settings, execution and presentation belong to the same capability.

**Dependencies:** Qualified F02 data, F03 strategy/blocks and F01 jobs/resources. Each profile/precision has its own evidence gate.

**Delivery:** M03 and M07. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/plugins/simulator`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P06](../V1/phase-06-simulation-engine.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Execution | 4.1/4.2 | Deterministic chronological evaluation, order/fill/trade lifecycle, same-bar/gap precedence and platform profiles |
| Management/accounting | 4.3/4.4 | All consumed advanced trade/money-management methods, spread/slippage/commission, cost timing, precision and account ledger |
| Precision/selection | 4.5 | Multi-series clocks, actual higher-precision input/events, stock universe/ranking/rebalance and capital/exposure |
| NinjaTrader profile | 4.2/4.7 | Separate missing-engine-body and independent native trace gate; export templates alone do not qualify simulation |
| Shared operation | 4.6/4.7 | Builder/Optimizer/Retester/Projects use the same engine; actual trades/equity reach retained result views |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F04 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Backend consumers are the retained simulation/run views in Builder, Optimizer, Retester and Results. Verify the operation through its actual connected consumer; do not invent an engine screen.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 4.1 Run specification and chronological execution

## 1. Objective

Execute a validated immutable run specification in explicit chronological order.

## 2. Research and donors

P06 strategy evaluation consumers and missing core engine bodies; unsupported SQX semantics need explicit evidence or target decisions.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/simulator/specifications.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/simulator/engine.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_04/test_specifications.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Resolve strategy/block/data versions, execution profile, dates, precision, seed and costs before admission.
- [ ] **Step 2:** Define event clock, warm-up, missing-data behavior and evaluation order; keep order/account state sequential.
- [ ] **Step 3:** Emit trace and typed run outputs for all consumers through one engine.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_04/test_specifications.py --no-cov`.

**Independent cases:** Hand-auditable event sequences, first/last boundaries, look-ahead prevention, missing warm-up, deterministic replay and incompatible inputs.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 4.2 Orders, fills and platform execution profiles

## 1. Objective

Model orders, fills and platform profiles with documented precedence.

## 2. Research and donors

P06 NinjaTrader engine research and execution options; templates cannot substitute for missing engine-body evidence.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/simulator/execution.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/simulator/orders.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_04/test_execution.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Specify market/limit/stop behavior, pending/cancel/reject transitions and price availability.
- [ ] **Step 2:** Define same-bar entry/stop/target precedence, gaps, partial fills and bar-close/tick distinctions per accepted profile.
- [ ] **Step 3:** Keep NinjaTrader engine qualification separate from code generation; publish unavailable profiles until independent traces exist.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_04/test_execution.py --no-cov`.

**Independent cases:** Independent long/short gap/limit/stop and same-bar conflict traces; pending cancellation, rejected orders and profile incompatibility.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 4.3 Position management, risk and money sizing

## 1. Objective

Apply position, risk, sizing and advanced trade management through owned rules.

## 2. Research and donors

P06 AdvancedTM/MoneyManagement/Options and accepted strategy actions; names alone do not establish defaults.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/simulator/management.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/simulator/sizing.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_04/test_management.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Specify retained entry/exit, trailing/break-even, stop/target, pyramiding and position-limit methods from consumed settings.
- [ ] **Step 2:** Define money-management sizing, capital/exposure, lot steps and rejection policy.
- [ ] **Step 3:** Apply management at documented event points and retain chosen settings with each run.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_04/test_management.py --no-cov`.

**Independent cases:** Independent sizing, leverage/capital/lot-rounding, trailing/break-even timing and overlapping-position vectors for every accepted method.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 4.4 Costs, ledger and equity accounting

## 1. Objective

Reconcile every trade, cash movement and equity value in one ledger.

## 2. Research and donors

P06 accounting consumers and P08 expected result fields; no duplicated UI metric arithmetic.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/simulator/accounting.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_04/test_accounting.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define commission, spread, slippage, financing/currency conversion where consumed, tick rounding and cost timing.
- [ ] **Step 2:** Record fills, realized/unrealized P&L, cash, exposure and equity using specified precision/order.
- [ ] **Step 3:** Publish immutable trades and account ledger with reconciliation invariants used by F05/F08.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_04/test_accounting.py --no-cov`.

**Independent cases:** Independent balances after each event, long/short costs, rounding ties, currency conversion, zero/negative capital and closed/open-trade reconciliation.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 4.5 Precision, multi-series and stock-selection behavior

## 1. Objective

Expand precision, multi-series and stock-selection behavior only with qualified inputs.

## 2. Research and donors

P06 execution options and P08 SP/stock-picker consumers; higher precision requires real data and event semantics.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/simulator/alignment.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/simulator/stock_selection.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_04/test_alignment.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Specify bar/tick/higher-precision input contracts, timestamp alignment and stale/missing secondary series.
- [ ] **Step 2:** Define stock universe, ranking ties, rebalance timing and shared capital/exposure behavior.
- [ ] **Step 3:** Enumerate each retained platform/precision combination and reject missing data or unsupported profiles.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_04/test_alignment.py --no-cov`.

**Independent cases:** Independent multi-series clock alignment, no future samples, precision-dependent fills, universe changes, rebalance timing and constrained-capital vectors.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 4.6 Bounded run jobs, caches and performance

## 1. Objective

Run bounded simulations with reusable trusted execution and measured acceleration.

## 2. Research and donors

P06 integration and shared Builder/Optimizer/Retester/Project consumption.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/simulator/run_jobs.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/simulator/cache.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_04/test_run_jobs.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Adapt the engine to H07 specs, chunk/checkpoint cancellation and H08 publication without separate engines per workspace.
- [ ] **Step 2:** Cache only version-keyed reusable work with bounds; profile before vectorizing/accelerating kernels.
- [ ] **Step 3:** Keep attempt outputs private until successful publication; preserve explicit interrupted/failed runs and retry lineage.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_04/test_run_jobs.py --no-cov`.

**Independent cases:** Compare cached/uncached and local-worker results; cancel at checkpoints, crash workers, reject late output, bound memory and clean unpublished artifacts.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 4.7 Independent numerical and connected backtest qualification

## 1. Objective

Qualify independent numerical outcomes and the connected backtest journey.

## 2. Research and donors

P06 integration gate and P18 numerical/reference qualification.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/simulator/integration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_04/test_integration.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Create independent small data/strategy fixtures with hand-derived fills, costs, ledger and expected traces.
- [ ] **Step 2:** Compare accepted donor/platform behavior where available, retaining precise profile/version limits.
- [ ] **Step 3:** Connect run settings/progress/trades/equity to real jobs and demonstrate reload/reconnect/failure.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_04/test_integration.py --no-cov`.

**Independent cases:** Import -> author -> run -> inspect/export through an isolated real host; independent accounting checks and denied/unavailable/cancelled states; no blanket parity.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [ ] All 7 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [ ] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [ ] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [ ] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.

A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.
