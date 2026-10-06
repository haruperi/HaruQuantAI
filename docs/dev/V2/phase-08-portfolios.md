# Phase 8 — Portfolios

**Feature group:** F08. **Tasks:** 4. **Status:** proposed; 0 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Retain manual portfolio membership and weights against immutable result revisions. This phase owns the portfolios capability group. Use the shared host and existing domain operations; settings, execution and presentation belong to the same capability.

**Dependencies:** Qualified F05 inputs and H07/H08/H09; F04 when reexecution is required. Manual portfolios do not depend on Builder.

**Delivery:** M06. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/plugins/portfolio`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P12](../V1/phase-12-portfolio-workflows.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Manual composition | 8.1/8.2 | Members/weights/version references, correlation, aggregate accounting/exposure and saved revisions |
| Automatic methods | 8.3 | Construction/search, existing-portfolio fitness, selection objectives and finite budgets |
| Workspaces | 8.4 | Composer/Master, charts/logs, member selection and databank moveToPC/moveToPM actions |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F08 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Retained UI files to audit/connect: [ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx](../../../ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx), [ui/app/workspace/PortfolioMaster/PortfolioMasterWorkspace.tsx](../../../ui/app/workspace/PortfolioMaster/PortfolioMasterWorkspace.tsx). Preserve existing layouts and meaningful controls.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 8.1 Portfolio membership, weights and revisions

## 1. Objective

Retain manual portfolio membership and weights against immutable result revisions.

## 2. Research and donors

P12 Composer/Master membership/settings and retained databank portfolio actions.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/portfolio/documents.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_08/test_documents.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define member/result IDs, weights, currency/capital policy, ownership and revision conflicts.
- [ ] **Step 2:** Implement add/remove/clone/save with compatibility checks and explicit missing-member states.
- [ ] **Step 3:** Preserve historical member versions instead of following mutable strategy pointers.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_08/test_documents.py --no-cov`.

**Independent cases:** Duplicate members, invalid weights, mixed/incompatible producers, revision conflict and reload after producer removal.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 8.2 Aggregate accounting, exposures and correlations

## 1. Objective

Evaluate portfolio equity, exposures and correlations with explicit capital semantics.

## 2. Research and donors

P12 portfolio accounting/correlation consumers; summing equity curves is not automatically shared-capital simulation.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/portfolio/evaluation.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_08/test_evaluation.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Choose independent/weighted/shared-capital accounting and time/currency alignment for each accepted evaluation mode.
- [ ] **Step 2:** Reuse F05 correlation/metrics; use F04 when shared-capital reexecution is required.
- [ ] **Step 3:** Publish reconciled aggregate outputs and distinguish missing samples from zero return.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_08/test_evaluation.py --no-cov`.

**Independent cases:** Independent weight/equity/exposure vectors, calendar alignment, currency/cost basis, zero variance and simultaneous capital-constrained positions.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 8.3 Automatic construction, selection and search

## 1. Objective

Search and rank portfolios through the same qualified evaluator.

## 2. Research and donors

P12 automatic portfolio and existing-portfolio fitness methods.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/portfolio/search.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_08/test_search.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define candidate membership/weight bounds, existing-portfolio fitness, selection objective/ties and finite search budget.
- [ ] **Step 2:** Generate valid candidates and call the manual evaluator rather than another simulation stack.
- [ ] **Step 3:** Retain accepted/rejected candidate lineage and reproduce seed/aggregation order independently of timing.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_08/test_search.py --no-cov`.

**Independent cases:** Small independent optimal-set/weight cases, impossible constraints, duplicate members, missing inputs, tie order and bounded cancellation.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 8.4 Composer/Master workflows and independent qualification

## 1. Objective

Connect manual and automatic Portfolio Composer/Master workflows.

## 2. Research and donors

P12 integration and retained moveToPC/moveToPM consumers.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/portfolio/integration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_08/test_integration.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Wire member selection, weights, settings, chart/logs, search progress and databank moves to owned operations.
- [ ] **Step 2:** Demonstrate manual composition first, then search/save/reload without requiring Builder or every robustness method.
- [ ] **Step 3:** Verify errors, cancellation/reconnect and retained revisions across removal.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_08/test_integration.py --no-cov`.

**Independent cases:** Real-host membership -> evaluate -> compare -> search -> retain journey with independent aggregate accounting and unavailable inputs.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [ ] All 4 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [ ] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [ ] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [ ] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.

A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.
