# P15 — Neural Network Trainer and model resource lifecycle

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P03,P05,P06,P08,P14.
- **Scope:** 2 JAR feature tasks, 0 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.

# AppNeuralNetwork.jar — FEAT-NEURAL-APP-NEURAL-NETWORK

## 1. Objective

- **Goal:** Implement the named neural training/model resource capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Train, persist and consume qualified neural model resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppNeuralNetwork/AppNeuralNetwork.jar`; 1 class declarations; SHA-256 `f20b8d1412bed668ef1b39a3cf1fc5e418b20ee433c65bc021f6afd0a7a2169e`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/NeuralNetworkTrainer/AppNeuralNetwork.md`; roadmap allocation `FEAT-NEURAL-APP-NEURAL-NETWORK`.
- **Owner:** `app/workspace/NeuralNetwork/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppNeuralNetwork/AppNeuralNetwork.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppNeuralNetwork/AppNeuralNetwork.jar" com.strategyquant.plugin.App.impl.NeuralNetwork.NeuralNetworkAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/workspace/NeuralNetwork/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/NeuralNetwork/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/NeuralNetwork/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/NeuralNetwork/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_neural_app_neural_network.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/neural_app_neural_network.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named neural training/model resource capability; verify feature scaling, seed/split policy, model version and finite inference.
- [ ] **Step 4:** `FR-NEURAL-APP-NEURAL-NETWORK-NEURAL-NETWORK-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.NeuralNetwork.NeuralNetworkAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-NEURAL-APP-NEURAL-NETWORK-NEURAL-NETWORK-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.NeuralNetwork.NeuralNetworkAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-NEURAL-APP-NEURAL-NETWORK-NEURAL-NETWORK-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.NeuralNetwork.NeuralNetworkAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_neural_app_neural_network.py --no-cov`; expect feature scaling, seed/split policy, model version and finite inference; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture feature scaling, seed/split policy, model version and finite inference and visible failures.

# TaskNeuralNetworkTrainer.jar — FEAT-NEURAL-TASK-NEURAL-NETWORK-TRAINER

## 1. Objective

- **Goal:** Implement the named neural training/model resource capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Train, persist and consume qualified neural model resources.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskNeuralNetworkTrainer/TaskNeuralNetworkTrainer.jar`; 1 class declarations; SHA-256 `86b5b1a68f20fc9cf2025ce903bfc09f69a7b49b647af061387efd9bc743ae64`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/NeuralNetworkTrainer/TaskNeuralNetworkTrainer.md`; roadmap allocation `FEAT-NEURAL-TASK-NEURAL-NETWORK-TRAINER`.
- **Owner:** `app/workspace/NeuralNetwork/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Neural training task; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskNeuralNetworkTrainer/TaskNeuralNetworkTrainer.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskNeuralNetworkTrainer/TaskNeuralNetworkTrainer.jar" com.strategyquant.plugin.Task.impl.NeuralNetworkTrainer.NeuralNetworkTrainerTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/workspace/NeuralNetwork/training.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/NeuralNetwork/contracts.py` (proposed earlier in FEAT-NEURAL-APP-NEURAL-NETWORK)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/NeuralNetwork/README.md` (proposed earlier in FEAT-NEURAL-APP-NEURAL-NETWORK)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_neural_task_neural_network_trainer.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/neural_task_neural_network_trainer.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named neural training/model resource capability; verify feature scaling, seed/split policy, model version and finite inference.
- [ ] **Step 4:** `FR-NEURAL-TASK-NEURAL-NETWORK-TRAINER-NEURAL-NETWORK-TRAINER-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.NeuralNetworkTrainer.NeuralNetworkTrainerTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-NEURAL-TASK-NEURAL-NETWORK-TRAINER-NEURAL-NETWORK-TRAINER-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.NeuralNetworkTrainer.NeuralNetworkTrainerTask.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-NEURAL-TASK-NEURAL-NETWORK-TRAINER-NEURAL-NETWORK-TRAINER-TASK-CLONE` → `com.strategyquant.plugin.Task.impl.NeuralNetworkTrainer.NeuralNetworkTrainerTask.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_neural_task_neural_network_trainer.py --no-cov`; expect feature scaling, seed/split policy, model version and finite inference; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture feature scaling, seed/split policy, model version and finite inference and visible failures.

# P15 integration — Train, persist and consume qualified neural model resources

## 1. Objective

- **Goal:** Train, persist and consume qualified neural model resources.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P15; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/NeuralNetwork/NeuralNetworkTrainer.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/NeuralNetwork/neuralNet.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

## 3. File Changes

- **Modify:** `app/workspace/NeuralNetwork/workspace.py` (proposed earlier in FEAT-NEURAL-APP-NEURAL-NETWORK)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/NeuralNetwork/training.py` (proposed earlier in FEAT-NEURAL-TASK-NEURAL-NETWORK-TRAINER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/NeuralNetwork/contracts.py` (proposed earlier in FEAT-NEURAL-APP-NEURAL-NETWORK)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/NeuralNetwork/routes.py` (proposed earlier in FEAT-NEURAL-APP-NEURAL-NETWORK)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/models/artifacts.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/models/inference.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/NeuralNetwork/NeuralNetworkTrainer.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/NeuralNetwork/neuralNetworkClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/workspace/NeuralNetwork/README.md` (proposed earlier in FEAT-NEURAL-APP-NEURAL-NETWORK)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_neural_network_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-neural-network-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Recover training inputs, feature scaling, architecture, targets, split rules and seeded initialization.
- [ ] **Step 3:** Implement training/inference jobs, progress and versioned model artifacts under owned resources.
- [ ] **Step 4:** Connect NeuralNetwork controls to real metrics and permit only qualified models in strategy execution.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_neural_network_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/NeuralNetwork/neuralNet.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-neural-network-backend.spec.ts`. Assert fixed-seed training, no split leakage, model save/reload and inference vectors; reject invalid features, unsupported model version, nonfinite loss and interrupted training.
- **Manual / Browser Verification:** Train a small fixture model; inspect real loss; save/reload it; compare predictions; reject an incompatible model artifact.

## Phase completion gate

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
