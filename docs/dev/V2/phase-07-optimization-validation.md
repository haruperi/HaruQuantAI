# Phase 7 — Optimization and validation

**Feature group:** F07. **Tasks:** 7. **Status:** proposed; 0 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Run explicit parameter experiments through the shared simulator. This phase owns the optimization and validation capability group. Use the shared host and existing domain operations; settings, execution and presentation belong to the same capability.

**Dependencies:** F04/F05, compatible F02 market/precision data and H07/H09. A saved strategy can be optimized without Builder.

**Delivery:** M05. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/plugins/optimization`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P10](../V1/phase-10-optimizer-walk-forward.md), [V1 P11](../V1/phase-11-retester-robustness.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Optimization | 7.1/7.2 | Simple parameter search, sequential passes, profiles and system-parameter permutations; shared robustness wrappers |
| Walk-forward | 7.3 | Partition/optimization/aggregation and matrix views; no in/out-of-sample leakage |
| Monte Carlo | 7.4/7.5 | Retained-trade manipulation and input-perturbation/resimulation remain separate methods |
| Other checks | 7.6 | Additional markets, higher precision and What-If with individual availability and threshold semantics |
| Chains/UI | 7.7 | What-to-retest, automatic-retest data/chains, cross-check settings, automatic/manual tasks, robustness reports and both workspaces |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F07 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Retained UI files to audit/connect: [ui/app/workspace/Optimizer/OptimizerWorkspace.tsx](../../../ui/app/workspace/Optimizer/OptimizerWorkspace.tsx), [ui/app/workspace/Retester/RetesterWorkspace.tsx](../../../ui/app/workspace/Retester/RetesterWorkspace.tsx). Preserve existing layouts and meaningful controls.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 7.1 Experiment specifications and parameter search

## 1. Objective

Run explicit parameter experiments through the shared simulator.

## 2. Research and donors

P10 simple optimization/settings/results and P11 retest selection consumers.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/optimization/experiments.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/optimization/parameter_search.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_07/test_experiments.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define ranges, inclusive endpoints, enumeration order, objectives/ties, run budgets and selected saved strategy/data revisions.
- [ ] **Step 2:** Generate typed scenario specs for F04 and retain every outcome/rejection with F05-compatible lineage.
- [ ] **Step 3:** Connect basic Optimizer settings/progress/results without a separate backtest engine.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_07/test_experiments.py --no-cov`.

**Independent cases:** Independent grid/endpoints/order/optimum vectors, empty/invalid ranges, nonfinite objective, ties and deterministic bounded cancellation.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 7.2 Sequential search, profiles and parameter permutations

## 1. Objective

Support sequential search, profiles and system-parameter permutations distinctly.

## 2. Research and donors

P10 methods plus P11 SequentialOptimization and OptProfileSysParamPermutation cross-checks.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/optimization/search_methods.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_07/test_search_methods.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Recover sequential pass order/stop criteria and parameter interaction rules.
- [ ] **Step 2:** Define profile sampling and permutation space, output projections and reproducible budgets.
- [ ] **Step 3:** Expose these methods to Optimizer and their corresponding robustness adapters through one method interface.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_07/test_search_methods.py --no-cov`.

**Independent cases:** Independent sequential interaction/pass-budget, profile sample/order and permutation-count vectors; missing parameters, ties and threshold equality.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 7.3 Walk-forward optimization, aggregation and matrices

## 1. Objective

Optimize and aggregate walk-forward windows without leakage.

## 2. Research and donors

P10/P11 WalkForwardOptimization/Matrix contracts; an ordinary split is not the complete matrix method.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/optimization/walk_forward.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_07/test_walk_forward.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Specify anchored/rolling boundaries, training/test windows, parameter selection and matrix axes.
- [ ] **Step 2:** Optimize only in-sample; replay selected settings on untouched out-of-sample data.
- [ ] **Step 3:** Aggregate overlapping/nonoverlapping windows according to explicit accounting and retain every window/matrix cell lineage.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_07/test_walk_forward.py --no-cov`.

**Independent cases:** Independent boundary/window/matrix vectors, insufficient history, leakage sentinels, overlap accounting and empty/failed cells.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 7.4 Monte Carlo trade manipulation

## 1. Objective

Manipulate retained trades for Monte Carlo with its own scenario semantics.

## 2. Research and donors

P11 MonteCarloManipulation; keep separate from input perturbation/retest.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/optimization/monte_carlo_trades.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_07/test_monte_carlo_trades.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Recover trade sampling/reordering/skipping/cost perturbations, replacement, seeds and iteration budgets.
- [ ] **Step 2:** Apply scenarios to immutable trade inputs without pretending to resimulate strategy signals.
- [ ] **Step 3:** Publish distributions/quantiles and accepted robustness thresholds with exact denominator/tie rules.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_07/test_monte_carlo_trades.py --no-cov`.

**Independent cases:** Independent tiny-trade permutations/sampling/quantile vectors, empty input, replacement, skipped-trade counts, threshold equality and deterministic seeds.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 7.5 Monte Carlo input perturbation and retest

## 1. Objective

Perturb simulation inputs and rerun strategies for Monte Carlo retest.

## 2. Research and donors

P11 MonteCarloRetest and selected engine/data perturbation consumers.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/optimization/monte_carlo_retest.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_07/test_monte_carlo_retest.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define each accepted parameter/data/execution perturbation and its units/distribution/correlation.
- [ ] **Step 2:** Build scenario F04 specs and preserve seed/input revisions and parent-child lineage.
- [ ] **Step 3:** Aggregate actual rerun outcomes with bounds and explicit failures; do not substitute shuffled trades.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_07/test_monte_carlo_retest.py --no-cov`.

**Independent cases:** Independent perturbation vectors, invalid scenario ranges, repeatable reruns, cancelled chains and failure/threshold aggregation.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 7.6 Additional-market, higher-precision and What-If checks

## 1. Objective

Run additional-market, higher-precision and What-If checks under explicit availability.

## 2. Research and donors

P11 AdditionalMarkets/HigherPrecision/WhatIf and F02/F04 compatibility records.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/optimization/retest_scenarios.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_07/test_retest_scenarios.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Map saved strategy settings onto compatible additional-market datasets without silent symbol/unit changes.
- [ ] **Step 2:** Require qualified higher-precision data and execution profile before admitting that check.
- [ ] **Step 3:** Apply each What-If trade/scenario rule with documented denominators and retained modified/result lineage.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_07/test_retest_scenarios.py --no-cov`.

**Independent cases:** Independent cross-market mapping, precision-dependent fill and What-If exclusion vectors; missing dataset/profile, unsupported scenario and equality boundaries.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 7.7 Cross-check chains, thresholds and connected qualification

## 1. Objective

Compose automatic/manual retest chains and connect actual robustness reports.

## 2. Research and donors

P10/P11 integration, SettingsAutomaticRetest resources and ResultsRobustnessTests.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/optimization/chains.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/optimization/integration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_07/test_chains.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define what-to-retest, automatic-retest data, ordered cross-check configuration, acceptance thresholds and stop/failure policy.
- [ ] **Step 2:** Adapt each named method above as owned child jobs with retained settings/output, reusing Builder/Project consumers.
- [ ] **Step 3:** Connect Optimizer/Retester settings/results and robustness actions; save/reload/reconnect with visible unavailable/partial outcomes.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_07/test_chains.py --no-cov`.

**Independent cases:** Independent chain/threshold vectors and real-host manual/automatic retest journeys; cancellation/failure recovery and each robustness matrix row accepted individually.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [ ] All 7 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [ ] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [ ] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [ ] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.

A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.
