# Phase 10 — Compute

**Feature group:** F10. **Tasks:** 3. **Status:** proposed; 0 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Place trusted jobs locally with explicit measured capacity limits. This phase owns the compute capability group. Use the shared host and existing domain operations; settings, execution and presentation belong to the same capability.

**Dependencies:** Qualified H03/H07/H08/H10 and an executable domain operation. Remote execution is optional for local research and training.

**Delivery:** M08. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/plugins/research/compute`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P14](../V1/phase-14-grid-compute.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Local | 10.1 | Capacity/placement/worker limits reuse host scheduling |
| Remote | 10.2 | Enrollment/compatibility, messages, admission/leases/heartbeats, result publication and cancellation |
| Recovery/UI | 10.3 | Grid Control/Test, lost workers, late/duplicate attempt fencing, deterministic seeds/order and cleanup |
| Wire compatibility | 10.2 | HaruQuantAI workers only; SQX Java-node protocol compatibility requires its own adopted requirement |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F10 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Retained UI files to audit/connect: [ui/app/workspace/GridControl/GridControlWorkspace.tsx](../../../ui/app/workspace/GridControl/GridControlWorkspace.tsx), [ui/app/workspace/GridTest/GridTestWorkspace.tsx](../../../ui/app/workspace/GridTest/GridTestWorkspace.tsx). Preserve existing layouts and meaningful controls.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 10.1 Local capacity and job placement

## 1. Objective

Place trusted jobs locally with explicit measured capacity limits.

## 2. Research and donors

P14 grid/job consumers and existing host jobs; local execution remains useful without remote workers.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/compute/local_capacity.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_10/test_local_capacity.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Reuse H03 capacity/settings and H07 scheduling instead of installing another coordinator.
- [ ] **Step 2:** Define per-operation CPU/memory admission and process concurrency with fair bounded queues.
- [ ] **Step 3:** Expose actual placement/capacity and deterministic seed partitioning; keep custom/untrusted code under separate isolation.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_10/test_local_capacity.py --no-cov`.

**Independent cases:** Capacity unavailable/overcommit, queue saturation, concurrent cancellations and identical result lineage under different worker counts.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 10.2 Remote workers, protocol, admission and leases

## 1. Objective

Extend the existing coordinator with authenticated versioned remote workers.

## 2. Research and donors

P14 Grid Control/Test/JMS/JGroups consumers; HaruQuantAI protocol does not claim SQX Java-node interoperability.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/compute/protocol.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/research/compute/workers.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_10/test_protocol.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Define enrollment/compatibility, trusted capabilities, validated job messages, artifact transfers and permissions.
- [ ] **Step 2:** Use bounded HTTP/events, admission/leases/heartbeats, attempt IDs and checksummed publication.
- [ ] **Step 3:** Define retry/loss/cancel policy; reject arbitrary executable-object payloads and late/duplicate attempts.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_10/test_protocol.py --no-cov`.

**Independent cases:** Incompatible versions, enrollment denial, expired lease, worker loss, duplicate/late output, corrupted transfer, cancel and cleanup.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 10.3 Grid Control/Test, recovery and local/remote equivalence

## 1. Objective

Connect grid operations and qualify deterministic local/remote equivalence.

## 2. Research and donors

P14 integration and shared H07/H08 lifecycle; remote deployment needs its own approved authenticated/TLS plan.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/compute/integration.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_10/test_integration.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Wire GridControl/GridTest inventory/status/placement/test controls to real worker capabilities.
- [ ] **Step 2:** Run the same qualified domain specs locally and remotely with stable seeds and aggregate order.
- [ ] **Step 3:** Verify loss/restart/cancel removes leases/subscriptions/staging while preserving retained results and explicit interrupted jobs.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_10/test_integration.py --no-cov`.

**Independent cases:** Isolated coordinator/two-worker journey, deterministic output comparison, slow/disconnected workers and retry fencing; measure resource bounds.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [ ] All 3 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [ ] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [ ] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [ ] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.

A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.
