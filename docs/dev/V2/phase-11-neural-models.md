# Phase 11 — Neural models

**Feature group:** F11. **Tasks:** 3. **Status:** proposed; 0 complete.

[Checklist](implementation_checklist.md) · [V2 index](README.md) · [Delivery milestones](delivery-plan.md)

## Objective and boundary

Prepare temporal training inputs with retained preprocessing and no leakage. This phase owns the neural models capability group. Use the shared host and existing domain operations; settings, execution and presentation belong to the same capability.

**Dependencies:** F02 plus local H07/H08/H09. F03/F04 for model consumption; remote compute is optional.

**Delivery:** M08. Phase numbers identify scope, not a requirement to finish every earlier feature before starting this one. Deliver the smallest connected operation first; pending matrix rows remain full-product obligations.

**Ownership:** proposed semantic owner `app/plugins/research/neural`; workspace composition remains in `app/workspace/<workspace>`, and the host owns storage, jobs, resource custody and route mounting. No sibling business imports or plugin SQL. Package/module names below are proposed targets to audit and ratify per task, not newly registered contracts.

## Research and authority

Read [V1 P15](../V1/phase-15-neural-network.md), the [legacy task map](legacy-task-map.csv), [scope coverage](coverage-map.md), [current inventory](../evidence/p00-inventory.json) and [evidence procedure](../evidence/README.md). The V1 files retain exact archive/resource locators, fingerprints, consumed symbols and source limitations; use the relevant rows instead of recrawling unrelated archives. The sole donor is `SQX_145_REFERENCE_ROOT` (145-dev1). Hash and inspect the selected consumed bodies/resources before deciding defaults or numerical behavior. Signatures and UI labels alone do not establish semantics.

The root [AGENTS.md](../../../AGENTS.md), [architecture](../../ARCHITECTURE.md) and approved P01 contracts remain authoritative. For each implementation slice: audit current source, create an exact-path canonical plan, get owner approval, implement, verify and write a walkthrough. Missing source behavior requires explicit disposition; no copied proprietary implementation or invented SQX parity.

## Scope and acceptance matrix

Each row is a mandatory acceptance set inside its numbered tasks, not another feature/plugin backlog. Mark a task complete only when all of its promised rows are qualified.

| Acceptance set | Tasks | Retained behavior |
| --- | --- | --- |
| Inputs | 11.1 | Feature/target selection, scaling, temporal splits and no future leakage |
| Training | 11.2 | Qualified architecture/settings/backend, seeded budgets, validation/held-out metrics and honest progress |
| Models | 11.3 | Safe compatible retention/versioning, identical preprocessing on reload/inference and strategy/project integration |

## Shared proposed changes and verification rules

- Audit/Create the owning domain README when absent; update it after each accepted capability. Reconcile actual FEAT/FR/DEC identities there; F11 and task numbers are planning labels.
- Compose domain capabilities in the selected workspace with typed attachment; public requests use the host transport. Reuse earlier qualified schemas/services instead of copying modules to satisfy a file list.
- Every proposed Python module follows the canonical module template, explicitly typed APIs and observable FR logs. Test success, failure, cancellation and redaction; never use silent exceptions.
- Proposed tests below are future commands, **not reported passes**. They use isolated stores/resources. Run scoped tests while editing, then required quality/coverage gates for the actual approved runtime scope.
- Retained UI files to audit/connect: [ui/app/workspace/NeuralNetwork/NeuralNetworkTrainer.tsx](../../../ui/app/workspace/NeuralNetwork/NeuralNetworkTrainer.tsx). Preserve existing layouts and meaningful controls.
- After actual UI changes run `npm --prefix ui run typecheck`, `npm --prefix ui run test` and `npm --prefix ui run build`. Fixture-only UI regressions do not replace real backend/UI acceptance.

# 11.1 Training features, targets, preprocessing and temporal splits

## 1. Objective

Prepare temporal training inputs with retained preprocessing and no leakage.

## 2. Research and donors

P15 neural settings/training data consumers; missing donor algorithms constrain parity.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/neural/training_data.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_11/test_training_data.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Specify features/targets/lookback/horizon, units, missing-data policy and immutable dataset versions.
- [ ] **Step 2:** Split training/validation/test by explicit time boundaries before fitting scaling/preprocessing.
- [ ] **Step 3:** Retain feature order/scalers and independent input lineage for later inference.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_11/test_training_data.py --no-cov`.

**Independent cases:** Independent feature/target/scaling/split vectors, future-data sentinels, empty/invalid samples and missing inputs.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 11.2 Bounded training, backend qualification and metrics

## 1. Objective

Train through a bounded backend adapter with honest metrics and reproducibility.

## 2. Research and donors

P15 training/model body evidence; no prebuilt distributed training platform.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/neural/training.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_11/test_training.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Recover accepted architecture/loss/optimizer/seed/stop semantics and qualify the smallest backend against Python 3.14 before dependency approval.
- [ ] **Step 2:** Use H07 local jobs for training progress/cancel; retain validation/held-out metrics and actual model artifacts.
- [ ] **Step 3:** Expose unavailable backend/settings and numerical failures without synthetic success; remote/GPU remains optional.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_11/test_training.py --no-cov`.

**Independent cases:** Small independent training cases, bounded seed/stop behavior, nonfinite loss, validation leakage, cancel/resource limits and missing backend.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

# 11.3 Model revisions, inference and connected acceptance

## 1. Objective

Retain compatible model revisions and use identical preprocessing during inference.

## 2. Research and donors

P15 integration and selected strategy/project model consumers; cancelled training is incomplete.

Use the phase sources and legacy CSV to recover exact donor entries/fingerprints. Write independent input/output expectations before translation. Record missing bodies, target decisions and compatibility limits in source-bound evidence.

## 3. File Changes

- **Create (proposed):** `app/plugins/research/neural/models.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `app/plugins/research/neural/inference.py` — owned implementation of the operations below; reuse an earlier qualified module when appropriate.
- **Create (proposed):** `tests/unit/v2/phase_11/test_models.py` — independent contract, failure and FR-log cases for this task.
- **Audit/compose:** the owning README and applicable workspace/client listed above; choose exact existing files in the task plan. Host services remain the only job/resource/persistence authority.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Store model/backend/schema/feature/scaler versions and safe artifact format through H08/H09.
- [ ] **Step 2:** Validate reload/inference compatibility and expose model references to F03/F04/project adapters.
- [ ] **Step 3:** Connect NeuralNetwork training/result/selection controls to actual jobs, metrics and inference.
- [ ] **Acceptance:** implement the independent tests below; retain evidence, owned lifecycle and observable errors in the connected consumer before checking this task.

## 5. Verification and Testing

**Future automated command:** `uv run pytest tests/unit/v2/phase_11/test_models.py --no-cov`.

**Independent cases:** Saved/reloaded inference equivalence, feature order/schema mismatch, missing/corrupt model, incompatible backend and real-host train -> retain -> use journey.

**Connected acceptance:** use an isolated real host and temporary resources through the declared workspace/consumer. Verify genuine job/resource IDs, visible unavailable/denied/failure states, cancellation and retained lineage after reconnect/reload. Capture expected versus actual results; do not report fixture outputs as runtime behavior.

## Phase completion gate

- [ ] All 3 numbered tasks and all specialist matrix rows are accepted under their own approved plans.
- [ ] Independent behavioral/numerical/format evidence supports each claimed compatibility scope; missing donor/provider/platform behavior remains explicitly unresolved.
- [ ] Actual backend/UI journey, failures, cancellation, restart/reconnect and scoped removal preserve retained outputs and unrelated work.
- [ ] Owning READMEs, task evidence and the master checklist agree; required Ruff/mypy/tests/coverage and applicable UI gates pass for implemented source.

A milestone subset is usable progress. Whole-product release also requires the [shared release gate](implementation_checklist.md#shared-release-gate). No checkbox is completed by publishing this plan.
