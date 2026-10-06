# Phase 6 — Strategy generation

**Feature group:** F06. **Tasks:** 4. **Status:** proposed; 0 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Generate valid random strategies under explicit finite search constraints. This phase owns the strategy generation capability group. Use the shared host and existing domain operations; settings, execution and presentation belong to the same capability.

**Dependencies:** F03/F04/F05 and H07. F07 is required only for enabled automatic retest.

**Delivery:** M04. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/plugins/research/generation`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P09](../V1/phase-09-builder-generation.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Candidate methods | 6.1/6.2 | Random generation; genetic populations/selection/crossover/mutation/elitism; what-to-build and parts-to-improve |
| Fitness | 6.3 | Objectives/direction/ties, filters, seed and ancestry, accepted/rejected lineage |
| Builder | 6.4 | Settings/progress/dashboard/engine panels, finite stop budgets, automatic-retest hooks, actual databank outputs |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F06 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Retained UI files to audit/connect: [ui/app/workspace/Builder/BuilderWorkspace.tsx](../../../ui/app/workspace/Builder/BuilderWorkspace.tsx). Preserve existing layouts and meaningful controls.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 6.1 Constrained random candidate generation

## 1. Objective

Generate valid random strategies under explicit finite search constraints.

## 2. Research and donors

P09 what-to-build/generation settings and random search consumers.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/generation/random_search.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_06/test_random_search.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define what-to-build/parts-to-improve, eligible block/parameter constraints, seed distribution and stop budgets.
- [ ] **Step 2:** Generate F03 documents from qualified catalog entries and reject invalid candidates before F04 execution.
- [ ] **Step 3:** Retain parent/configuration/seed lineage and bounded attempts for reproducibility.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_06/test_random_search.py --no-cov`.

**Independent cases:** Independent sampling/constraint vectors, impossible search space, invalid block, finite attempt limit and deterministic candidate lineage; same numeric seed does not prove Java random-stream parity.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 6.2 Genetic generation and strategy improvement

## 1. Objective

Implement genetic generation and improvement as a method over the same candidates.

## 2. Research and donors

P09 genetic options/Watchmaker/math consumers; preserve method semantics without recreating the frameworks.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/generation/genetic.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_06/test_genetic.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Specify population initialization, selection, crossover, mutation, elitism and replacement/tie policies.
- [ ] **Step 2:** Validate offspring with F03, evaluate with F04 and retain ancestry/generation metadata.
- [ ] **Step 3:** Support improvement of selected parts without mutating the retained parent revision.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_06/test_genetic.py --no-cov`.

**Independent cases:** Small independent population/selection/mutation/crossover cases, invalid offspring, duplicate candidates, elitism ties and generation-budget termination.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 6.3 Fitness, ranking, filters and candidate lineage

## 1. Objective

Rank candidates using qualified metrics, filtering and transparent lineage.

## 2. Research and donors

P09 ranking/fitness/results consumers and F05 metrics.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/generation/fitness.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_06/test_fitness.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define objective direction, multiobjective policy, filters, ties and missing/nonfinite scores.
- [ ] **Step 2:** Call F05 metrics on immutable run outputs and publish accepted candidates to databanks.
- [ ] **Step 3:** Retain rejected reason, evaluation specification, seed and parent lineage; keep ranking independent of worker completion timing.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_06/test_fitness.py --no-cov`.

**Independent cases:** Hand-computed score/rank/filter cases, equality, NaN/missing scores, deterministic ties and reordered worker results.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 6.4 Builder jobs, automatic retest and connected acceptance

## 1. Objective

Connect Builder progress and automatic retest to real bounded search jobs.

## 2. Research and donors

P09 Builder integration and AutomaticRetest hooks; ordinary optimization does not require Builder.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/generation/integration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_06/test_integration.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Wire Builder settings, dashboard, engine/progress and candidate results through H07/F05.
- [ ] **Step 2:** Invoke F07 only when automatic retest is enabled, with owned child jobs and explicit unavailable state.
- [ ] **Step 3:** Demonstrate random then genetic/improvement runs, cancellation, stop limits and saved results across reconnect.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_06/test_integration.py --no-cov`.

**Independent cases:** Real-host Builder journey, child/result counts, cancelled generation, retest failure, finite termination and reload of actual candidates/configuration.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [ ] All 4 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [ ] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [ ] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [ ] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.

A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.
