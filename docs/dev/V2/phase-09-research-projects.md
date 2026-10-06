# Phase 9 — Research projects

**Feature group:** F09. **Tasks:** 4. **Status:** proposed; 0 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Represent reusable projects with a finite state machine and owned task lifecycle. This phase owns the research projects capability group. Use the shared host and existing domain operations; settings, execution and presentation belong to the same capability.

**Dependencies:** H07/H09 and only the capabilities selected by each task. F11/F10/external adapters are not blanket project prerequisites.

**Delivery:** M06; domain breadth as selected. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/plugins/research/projects`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P13](../V1/phase-13-custom-projects-tasks.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Project lifecycle | 9.1 | Settings/resources/databanks/results, notes, clone/start/stop and bounded branches/repetitions/go-to |
| Domain tasks | 9.2 | Build, optimize, retest/automatic retest, portfolio/automatic portfolio, neural training, mass config, custom analysis/filtering, updates and databank statistics |
| Utility tasks | 9.3 | Wait, go-to, stop-and-start, load/save files, notes, clear databanks/delete files, notification/mail and external scripts; settings/task pairs share one operation |
| Conditions | 9.4 | Cycle count, go-to activated, go-to evaluated, result count, elapsed runtime; equality, evaluation points and disabled behavior |
| Q workflow | 9.2/9.4 | Reusable discovery/build/testing workflow with actual domain output lineage and bounded authority |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F09 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Retained UI files to audit/connect: [ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx](../../../ui/app/workspace/CustomProjects/CustomProjectsWorkspace.tsx). Preserve existing layouts and meaningful controls.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 9.1 Project documents, tasks and bounded state machine

## 1. Objective

Represent reusable projects with a finite state machine and owned task lifecycle.

## 2. Research and donors

P13 TaskManager/ServletProject/Projects/settings resources; do not restrict supported projects to DAGs.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/projects/documents.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/research/projects/runner.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_09/test_documents.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define versioned task nodes/settings, branches/go-to targets, notes and result/databank/resource references.
- [ ] **Step 2:** Specify cloned/start/stop/disabled task transitions and finite step/cycle/runtime budgets.
- [ ] **Step 3:** Run sequential nodes first, then bounded branches/repetitions; delegate execution and children to H07.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_09/test_documents.py --no-cov`.

**Independent cases:** Independent state traces, invalid targets, zero-task project, clone isolation, budget exhaustion and no unbounded loop; go-to semantics remain representable.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 9.2 Domain task adapters and mass configuration

## 1. Objective

Delegate every domain task and mass configuration to its existing owner.

## 2. Research and donors

P13 domain/task-settings pairs and Q research workflow; no direct sibling business imports or ad-hoc SQL.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/projects/task_adapters.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/research/projects/mass_configuration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_09/test_task_adapters.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Provide build, optimize, retest/automatic retest, portfolio/automatic portfolio and neural-training adapters using their existing schemas.
- [ ] **Step 2:** Add custom analysis, filtering, data update and databank statistics through owner operations.
- [ ] **Step 3:** Validate mass configuration across all selected targets before applying the specified transactional/rollback policy; retain Q discovery/build/testing workflow lineage.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_09/test_task_adapters.py --no-cov`.

**Independent cases:** Missing selected capability blocks its node only; test configuration incompatibility, mass-update conflict/rollback, owned child counts and actual result propagation.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 9.3 Utility, file, notification and external-script tasks

## 1. Objective

Provide utility and external-effect tasks with explicit lifecycle and authority.

## 2. Research and donors

P13 full utility Settings/Task pairs plus mail/process consumers; document accepted MIME/file/script contracts.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/projects/utility_tasks.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_09/test_utility_tasks.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Implement notes, wait, go-to, stop-and-start, load/save files and report/statistics tasks using owned resources/jobs.
- [ ] **Step 2:** Resolve clear-databank/delete-file targets exactly; preserve unrelated artifacts and reject unauthorized destructive actions.
- [ ] **Step 3:** Adapt notification/mail and external scripts with scoped authorization, credentials, timeout/rate/output policies and enforceable execution controls.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_09/test_utility_tasks.py --no-cov`.

**Independent cases:** Independent wait/deadline, safe file round trip, path escape, unauthorized delete/clear/mail/script, timeout and partial-failure cases; no side-effect authority from project start alone.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 9.4 Conditions, recovery and connected project qualification

## 1. Objective

Qualify all conditions, recovery and connected Custom Projects behavior.

## 2. Research and donors

P13 all five conditions and integration gate; missing neural/grid adapters must not block unrelated projects.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/projects/conditions.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/research/projects/integration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_09/test_conditions.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define cycle count, go-to activated/evaluated, result-count and elapsed-runtime evaluation points/equality and disabled behavior.
- [ ] **Step 2:** Persist checkpoints and reconcile child-job outcomes on cancellation, stop/start and restart without duplicate external effects.
- [ ] **Step 3:** Connect Custom Projects/Task Manager settings, logs, resources/databanks/results and Q-callable workflow.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_09/test_conditions.py --no-cov`.

**Independent cases:** Independent condition/counter/equality/loop traces and real-host build -> retest -> portfolio project; failed/cancelled/recovered nodes and side-effect denial preserved.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [ ] All 4 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [ ] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [ ] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [ ] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.

A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.
