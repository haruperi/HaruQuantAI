# P15 — Neural Network Trainer and model resource lifecycle

- **Source:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P03,P05,P06,P08,P14.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 3 tasks; current archive allocations and resource/integration tasks only.

# 15.1 FEAT-NEURAL-APP-NEURAL-NETWORK - AppNeuralNetwork.jar

## 1. Objective

- **Goal:** Implement the named neural training/model resource capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Train, persist and consume qualified neural model resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppNeuralNetwork/AppNeuralNetwork.jar`; 1 raw class entries; SHA-256 `a9b596747d3b2f47afb2c9a949331708a6c9edf3930316dba1adfab76ffc9256`.
- **Inspected reference:** [AppNeuralNetwork.md](sqx/NeuralNetworkTrainer/AppNeuralNetwork.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppNeuralNetwork/AppNeuralNetwork.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppNeuralNetwork/AppNeuralNetwork.jar" com.strategyquant.plugin.App.impl.NeuralNetwork.NeuralNetworkAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/NeuralNetwork/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppNeuralNetwork`; `SQX_145_REFERENCE_ROOT/internal/web/NEURALNETWORK`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskNeuralNetworkTrainer`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppNeuralNetwork/module.js`.
- **Existing UI connection:** Neural Network; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/NeuralNetwork/NeuralNetworkTrainer.tsx`; wire dataset/training selection, server training job and saved model resource.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

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

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/NeuralNetwork/NeuralNetworkTrainer.tsx`
  - Display dataset/training selection, server training job and saved model resource from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/NeuralNetwork/neuralNetStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/NeuralNetwork/neuralClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-neural-app-neural-network.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-neural-network-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named neural training/model resource capability; verify feature scaling, seed/split policy, model version and finite inference.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/training selection, server training job and saved model resource to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-NEURAL-APP-NEURAL-NETWORK-NEURAL-NETWORK-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.NeuralNetwork.NeuralNetworkAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-NEURAL-APP-NEURAL-NETWORK-NEURAL-NETWORK-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.NeuralNetwork.NeuralNetworkAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-NEURAL-APP-NEURAL-NETWORK-NEURAL-NETWORK-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.NeuralNetwork.NeuralNetworkAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_neural_app_neural_network.py --no-cov`; expect feature scaling, seed/split policy, model version and finite inference; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture feature scaling, seed/split policy, model version and finite inference and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-neural-app-neural-network.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-neural-network-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Neural Network for FEAT-NEURAL-APP-NEURAL-NETWORK; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 15.2 FEAT-NEURAL-TASK-NEURAL-NETWORK-TRAINER - TaskNeuralNetworkTrainer.jar

## 1. Objective

- **Goal:** Implement the named neural training/model resource capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Train, persist and consume qualified neural model resources.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskNeuralNetworkTrainer/TaskNeuralNetworkTrainer.jar`; 1 raw class entries; SHA-256 `ae6ec1406158b23fc416b4e4d3d8e053ae128894aa4ac0c25cb12067920569e5`.
- **Inspected reference:** [TaskNeuralNetworkTrainer.md](sqx/NeuralNetworkTrainer/TaskNeuralNetworkTrainer.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskNeuralNetworkTrainer/TaskNeuralNetworkTrainer.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskNeuralNetworkTrainer/TaskNeuralNetworkTrainer.jar" com.strategyquant.plugin.Task.impl.NeuralNetworkTrainer.NeuralNetworkTrainerTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/NeuralNetwork/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Neural training task; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskNeuralNetworkTrainer`; `SQX_145_REFERENCE_ROOT/internal/web/NEURALNETWORK`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/NEURALNETWORK/layout/LayoutCtrl.js`.
- **Existing UI connection:** Neural Network; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/NeuralNetwork/NeuralNetworkTrainer.tsx`; wire dataset/training selection, server training job and saved model resource.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

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

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/NeuralNetwork/NeuralNetworkTrainer.tsx`
  - Display dataset/training selection, server training job and saved model resource from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/NeuralNetwork/neuralNetStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/NeuralNetwork/neuralClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-neural-task-neural-network-trainer.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-neural-network-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named neural training/model resource capability; verify feature scaling, seed/split policy, model version and finite inference.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/training selection, server training job and saved model resource to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-NEURAL-TASK-NEURAL-NETWORK-TRAINER-NEURAL-NETWORK-TRAINER-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.NeuralNetworkTrainer.NeuralNetworkTrainerTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-NEURAL-TASK-NEURAL-NETWORK-TRAINER-NEURAL-NETWORK-TRAINER-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.NeuralNetworkTrainer.NeuralNetworkTrainerTask.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-NEURAL-TASK-NEURAL-NETWORK-TRAINER-NEURAL-NETWORK-TRAINER-TASK-GET-NAME` → `com.strategyquant.plugin.Task.impl.NeuralNetworkTrainer.NeuralNetworkTrainerTask.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_neural_task_neural_network_trainer.py --no-cov`; expect feature scaling, seed/split policy, model version and finite inference; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture feature scaling, seed/split policy, model version and finite inference and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-neural-task-neural-network-trainer.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-neural-network-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Neural Network for FEAT-NEURAL-TASK-NEURAL-NETWORK-TRAINER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 15.3 P15 integration — Train, persist and consume qualified neural model resources

## 1. Objective

- **Goal:** Train, persist and consume qualified neural model resources.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`, P15; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/NeuralNetwork/NeuralNetworkTrainer.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/NeuralNetwork/neuralNet.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/NEURALNETWORK`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskNeuralNetworkTrainer`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/NEURALNETWORK/layout/LayoutCtrl.js`.
- **Existing UI connection:** Neural Network; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/NeuralNetwork/NeuralNetworkTrainer.tsx`; wire dataset/training selection, server training job and saved model resource.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

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

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/NeuralNetwork/neuralNetStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/NeuralNetwork/neuralClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/task-15-3.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Recover training inputs, feature scaling, architecture, targets, split rules and seeded initialization.
- [ ] **Step 3:** Implement training/inference jobs, progress and versioned model artifacts under owned resources.
- [ ] **Step 4:** Connect NeuralNetwork controls to real metrics and permit only qualified models in strategy execution.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/training selection, server training job and saved model resource to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_neural_network_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/NeuralNetwork/neuralNet.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-neural-network-backend.spec.ts`. Assert fixed-seed training, no split leakage, model save/reload and inference vectors; reject invalid features, unsupported model version, nonfinite loss and interrupted training.
- **Manual / Browser Verification:** Train a small fixture model; inspect real loss; save/reload it; compare predictions; reject an incompatible model artifact.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-15-3.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-neural-network-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Neural Network for 15.3; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
