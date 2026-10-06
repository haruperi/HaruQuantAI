# P10 — Optimizer: parameter search, sequential modes, walk-forward and matrix

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P06,P08,P09.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 10 tasks; current archive allocations and resource/integration tasks only.

# 10.1 FEAT-OPTIMIZER-APP-OPTIMIZER - AppOptimizer.jar

## 1. Objective

- **Goal:** Mount the Optimizer workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppOptimizer/AppOptimizer.jar`; 1 raw class entries; SHA-256 `bde1b68ded4bd092c9bfa5554be07dc02a0dcc0f026db8f26f5026e6cf3c6872`.
- **Inspected reference:** [AppOptimizer.md](../../sqx/Optimizer/AppOptimizer.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppOptimizer/AppOptimizer.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppOptimizer/AppOptimizer.jar" com.strategyquant.plugin.App.impl.Optimizer.OptimizerAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Optimizer/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppOptimizer`; `SQX_145_REFERENCE_ROOT/internal/web/OPTIMIZER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppOptimizer/module.js`.
- **Existing UI connection:** Optimizer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Optimizer/optimizerClient.ts`; wire selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Optimizer/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Optimizer/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Optimizer/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Optimizer/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_app_optimizer.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_app_optimizer.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Optimizer/optimizerClient.ts`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerProgress.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/WalkForwardMatrixView.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-optimizer-app-optimizer.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the Optimizer workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-OPTIMIZER-APP-OPTIMIZER-OPTIMIZER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.Optimizer.OptimizerAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-OPTIMIZER-APP-OPTIMIZER-OPTIMIZER-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.Optimizer.OptimizerAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-OPTIMIZER-APP-OPTIMIZER-OPTIMIZER-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.Optimizer.OptimizerAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_app_optimizer.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-optimizer-app-optimizer.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Optimizer for FEAT-OPTIMIZER-APP-OPTIMIZER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 10.2 FEAT-OPTIMIZER-FITNESS-METHOD-WF-RESULT - FitnessMethodWFResult.jar

## 1. Objective

- **Goal:** Compute the named fitness objective from qualified result inputs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodWFResult/FitnessMethodWFResult.jar`; 3 raw class entries; SHA-256 `9d652f7e6ef5d6631969668b6d2c50efa4244504eca0ab3d452e341e7c33546f`.
- **Inspected reference:** [FitnessMethodWFResult.md](../../sqx/Shared/FitnessMethodWFResult.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodWFResult/FitnessMethodWFResult.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodWFResult/FitnessMethodWFResult.jar" com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/optimization/FitnessMethodWFResult/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodWFResult`; `SQX_145_REFERENCE_ROOT/internal/web/OPTIMIZER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/OPTIMIZER/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization/OptimizationService.js`.
- **Existing UI connection:** Optimizer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Optimizer/optimizerClient.ts`; wire selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/optimization/FitnessMethodWFResult/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/FitnessMethodWFResult/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/FitnessMethodWFResult/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/FitnessMethodWFResult/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_fitness_method_wf_result.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_fitness_method_wf_result.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Optimizer/optimizerClient.ts`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerProgress.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/WalkForwardMatrixView.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-optimizer-fitness-method-wf-result.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Compute the named fitness objective from qualified result inputs; verify objective direction, ties, missing metrics and nonfinite scores.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-OPTIMIZER-FITNESS-METHOD-WF-RESULT-FITNESS-METHOD-WFRESULT-CONTRACT` → `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-OPTIMIZER-FITNESS-METHOD-WF-RESULT-FITNESS-METHOD-WFRESULT-GET-PRODUCT` → `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-OPTIMIZER-FITNESS-METHOD-WF-RESULT-FITNESS-METHOD-WFRESULT-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_fitness_method_wf_result.py --no-cov`; expect objective direction, ties, missing metrics and nonfinite scores; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture objective direction, ties, missing metrics and nonfinite scores and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-optimizer-fitness-method-wf-result.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Optimizer for FEAT-OPTIMIZER-FITNESS-METHOD-WF-RESULT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 10.3 FEAT-OPTIMIZER-RESULTS-OPTIMIZATION-PROFILE - ResultsOptimizationProfile.jar

## 1. Objective

- **Goal:** Implement parameter profile/permutation sampling and projections.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile/ResultsOptimizationProfile.jar`; 12 raw class entries; SHA-256 `03f223f91b4aa45a3172fa39d409194f91741df7ac045d1625c9dbdb5c68fc0d`.
- **Inspected reference:** [ResultsOptimizationProfile.md](../../sqx/Results/ResultsOptimizationProfile.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile/ResultsOptimizationProfile.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile/ResultsOptimizationProfile.jar" com.strategyquant.plugin.Results.impl.OptimizationProfile.OptimizationProfileServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/optimization/ResultsOptimizationProfile/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile`; `SQX_145_REFERENCE_ROOT/internal/web/OPTIMIZER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile/OptimizationProfileService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile/directives/manageviews/ManageViewsService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile/OptimizationProfileCtrl.js`.
- **Existing UI connection:** Optimizer; exact retained source-map `ui/app/plugins/optimization/ResultsOptimizationProfile/source-map.json`. Target `ui/app/plugins/optimization/ResultsOptimizationProfile/OptimizationProfileCtrl.ts`; wire selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/optimization/ResultsOptimizationProfile/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsOptimizationProfile/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsOptimizationProfile/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsOptimizationProfile/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_results_optimization_profile.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_results_optimization_profile.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/optimization/ResultsOptimizationProfile/OptimizationProfileCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/optimization/ResultsOptimizationProfile/optimizationProfile.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/optimization/ResultsOptimizationProfile/module.ts`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/optimizerClient.ts`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerProgress.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/WalkForwardMatrixView.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Create:** `ui/app/plugins/optimization/ResultsOptimizationProfile/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-optimizer-results-optimization-profile.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement parameter profile/permutation sampling and projections; verify range endpoints, enumeration order and matrix/result reconciliation.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-OPTIMIZER-RESULTS-OPTIMIZATION-PROFILE-OPTIMIZATION-PROFILE-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.OptimizationProfile.OptimizationProfileServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-OPTIMIZER-RESULTS-OPTIMIZATION-PROFILE-OPTIMIZATION-PROFILE-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.OptimizationProfile.OptimizationProfileServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-OPTIMIZER-RESULTS-OPTIMIZATION-PROFILE-OPTIMIZATION-PROFILE-SERVLET-ON-PRINT` → `com.strategyquant.plugin.Results.impl.OptimizationProfile.OptimizationProfileServlet.onPrint(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_results_optimization_profile.py --no-cov`; expect range endpoints, enumeration order and matrix/result reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture range endpoints, enumeration order and matrix/result reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-optimizer-results-optimization-profile.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Optimizer for FEAT-OPTIMIZER-RESULTS-OPTIMIZATION-PROFILE; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 10.4 FEAT-OPTIMIZER-RESULTS-PROFILE-CHART - ResultsProfileChart.jar

## 1. Objective

- **Goal:** Project the named result series with verified metrics and sampling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/ResultsProfileChart.jar`; 2 raw class entries; SHA-256 `e68533b22cc2d8d670723f4ffd023cfe2099a44e75abb81ae8e209350ddd9b0f`.
- **Inspected reference:** [ResultsProfileChart.md](../../sqx/Results/ResultsProfileChart.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/ResultsProfileChart.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/ResultsProfileChart.jar" com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/optimization/ResultsProfileChart/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsProfileChart`; `SQX_145_REFERENCE_ROOT/internal/web/OPTIMIZER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/ProfileChartService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/ProfileChartCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/profileChart.html`.
- **Existing UI connection:** Optimizer; exact retained source-map `ui/app/plugins/project/ResultsProfileChart/source-map.json`. Target `ui/app/plugins/project/ResultsProfileChart/ProfileChartCtrl.ts`; wire selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/optimization/ResultsProfileChart/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsProfileChart/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsProfileChart/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsProfileChart/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_results_profile_chart.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_results_profile_chart.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsProfileChart/ProfileChartCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsProfileChart/profileChart.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ResultsProfileChart/module.ts`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/optimizerClient.ts`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerProgress.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/WalkForwardMatrixView.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsProfileChart/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-optimizer-results-profile-chart.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project the named result series with verified metrics and sampling; verify units, timestamp alignment, missing samples and reconciled source totals.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-OPTIMIZER-RESULTS-PROFILE-CHART-PROFILE-CHART-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-OPTIMIZER-RESULTS-PROFILE-CHART-PROFILE-CHART-SERVLET-DO-GET` → `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet.doGet(Ljakarta/servlet/http/HttpServletRequest;Ljakarta/servlet/http/HttpServletResponse;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-OPTIMIZER-RESULTS-PROFILE-CHART-PROFILE-CHART-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_results_profile_chart.py --no-cov`; expect units, timestamp alignment, missing samples and reconciled source totals; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture units, timestamp alignment, missing samples and reconciled source totals and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-optimizer-results-profile-chart.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Optimizer for FEAT-OPTIMIZER-RESULTS-PROFILE-CHART; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 10.5 FEAT-OPTIMIZER-RESULTS-SEQUENTIAL-OPTIMIZATION - ResultsSequentialOptimization.jar

## 1. Objective

- **Goal:** Implement sequential parameter-search ordering and result retention.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSequentialOptimization/ResultsSequentialOptimization.jar`; 2 raw class entries; SHA-256 `7d5039a1c9d0868b8ed2e64913b46a0329bd79f8bc01d4546e899a7a26c6ee7e`.
- **Inspected reference:** [ResultsSequentialOptimization.md](../../sqx/Results/ResultsSequentialOptimization.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSequentialOptimization/ResultsSequentialOptimization.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSequentialOptimization/ResultsSequentialOptimization.jar" com.strategyquant.plugin.Results.impl.SequentialOptimization.SequentialOptimizationServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/optimization/ResultsSequentialOptimization/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSequentialOptimization`; `SQX_145_REFERENCE_ROOT/internal/web/OPTIMIZER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSequentialOptimization/ResultsSequentialOptimizationCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSequentialOptimization/directives/ChainParamChartCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSequentialOptimization/sequentialOptimization.html`.
- **Existing UI connection:** Optimizer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Optimizer/optimizerClient.ts`; wire selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/optimization/ResultsSequentialOptimization/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsSequentialOptimization/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsSequentialOptimization/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsSequentialOptimization/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_results_sequential_optimization.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_results_sequential_optimization.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Optimizer/optimizerClient.ts`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerProgress.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/WalkForwardMatrixView.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-optimizer-results-sequential-optimization.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement sequential parameter-search ordering and result retention; verify candidate dependencies, repeated passes, stopping and score ordering.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-OPTIMIZER-RESULTS-SEQUENTIAL-OPTIMIZATION-SEQUENTIAL-OPTIMIZATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.SequentialOptimization.SequentialOptimizationServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-OPTIMIZER-RESULTS-SEQUENTIAL-OPTIMIZATION-SEQUENTIAL-OPTIMIZATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.SequentialOptimization.SequentialOptimizationServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-OPTIMIZER-RESULTS-SEQUENTIAL-OPTIMIZATION-SEQUENTIAL-OPTIMIZATION-SERVLET-ON-PRINT` → `com.strategyquant.plugin.Results.impl.SequentialOptimization.SequentialOptimizationServlet.onPrint(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_results_sequential_optimization.py --no-cov`; expect candidate dependencies, repeated passes, stopping and score ordering; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture candidate dependencies, repeated passes, stopping and score ordering and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-optimizer-results-sequential-optimization.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Optimizer for FEAT-OPTIMIZER-RESULTS-SEQUENTIAL-OPTIMIZATION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 10.6 FEAT-OPTIMIZER-RESULTS-SYS-PARAM-PERMUTATION - ResultsSysParamPermutation.jar

## 1. Objective

- **Goal:** Implement parameter profile/permutation sampling and projections.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSysParamPermutation/ResultsSysParamPermutation.jar`; 2 raw class entries; SHA-256 `a93d9519154a9761ea6226b14b7997c2e75418bb9c9cf899d11d5e077549fc8c`.
- **Inspected reference:** [ResultsSysParamPermutation.md](../../sqx/Results/ResultsSysParamPermutation.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSysParamPermutation/ResultsSysParamPermutation.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSysParamPermutation/ResultsSysParamPermutation.jar" com.strategyquant.plugin.Results.impl.SysParamPermutation.SysParamPermutationServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/optimization/ResultsSysParamPermutation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSysParamPermutation`; `SQX_145_REFERENCE_ROOT/internal/web/OPTIMIZER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSysParamPermutation/services/SysParamPermutationService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSysParamPermutation/controllers/SysParamPermutationCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsSysParamPermutation/directives/SPPPanelCtrl.js`.
- **Existing UI connection:** Optimizer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Optimizer/optimizerClient.ts`; wire selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/optimization/ResultsSysParamPermutation/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsSysParamPermutation/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsSysParamPermutation/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsSysParamPermutation/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_results_sys_param_permutation.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_results_sys_param_permutation.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Optimizer/optimizerClient.ts`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerProgress.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/WalkForwardMatrixView.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-optimizer-results-sys-param-permutation.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement parameter profile/permutation sampling and projections; verify range endpoints, enumeration order and matrix/result reconciliation.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-OPTIMIZER-RESULTS-SYS-PARAM-PERMUTATION-SYS-PARAM-PERMUTATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.SysParamPermutation.SysParamPermutationServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-OPTIMIZER-RESULTS-SYS-PARAM-PERMUTATION-SYS-PARAM-PERMUTATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.SysParamPermutation.SysParamPermutationServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-OPTIMIZER-RESULTS-SYS-PARAM-PERMUTATION-SYS-PARAM-PERMUTATION-SERVLET-LOAD-LAST-SETTINGS` → `com.strategyquant.plugin.Results.impl.SysParamPermutation.SysParamPermutationServlet.loadLastSettings()Lorg/json/JSONObject;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_results_sys_param_permutation.py --no-cov`; expect range endpoints, enumeration order and matrix/result reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture range endpoints, enumeration order and matrix/result reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-optimizer-results-sys-param-permutation.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Optimizer for FEAT-OPTIMIZER-RESULTS-SYS-PARAM-PERMUTATION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 10.7 FEAT-OPTIMIZER-RESULTS-WALK-FORWARD - ResultsWalkForward.jar

## 1. Objective

- **Goal:** Implement the named walk-forward partition/result contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/ResultsWalkForward.jar`; 5 raw class entries; SHA-256 `f35a0ece39d090656ace5996fadc12ae1c0ddfd028952054f2b8c6ddf801964a`.
- **Inspected reference:** [ResultsWalkForward.md](../../sqx/Results/ResultsWalkForward.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/ResultsWalkForward.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/ResultsWalkForward.jar" com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/optimization/ResultsWalkForward/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsWalkForward`; `SQX_145_REFERENCE_ROOT/internal/web/OPTIMIZER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/WFResultsService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/WFResultsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/directives/manageviews/ManageViewsCtrlWF.js`.
- **Existing UI connection:** Optimizer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Optimizer/optimizerClient.ts`; wire selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/optimization/ResultsWalkForward/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsWalkForward/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsWalkForward/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsWalkForward/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_results_walk_forward.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_results_walk_forward.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Optimizer/optimizerClient.ts`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerProgress.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/WalkForwardMatrixView.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-optimizer-results-walk-forward.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named walk-forward partition/result contract; verify in/out-of-sample boundaries, leakage rejection, aggregation and tie rules.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-OPTIMIZER-RESULTS-WALK-FORWARD-WALK-FORWARD-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-OPTIMIZER-RESULTS-WALK-FORWARD-WALK-FORWARD-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-OPTIMIZER-RESULTS-WALK-FORWARD-WALK-FORWARD-SERVLET-ON-EXPORT` → `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet.onExport(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_results_walk_forward.py --no-cov`; expect in/out-of-sample boundaries, leakage rejection, aggregation and tie rules; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture in/out-of-sample boundaries, leakage rejection, aggregation and tie rules and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-optimizer-results-walk-forward.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Optimizer for FEAT-OPTIMIZER-RESULTS-WALK-FORWARD; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 10.8 FEAT-OPTIMIZER-SETTINGS-OPTIMIZATION - SettingsOptimization.jar

## 1. Objective

- **Goal:** Implement validated Optimization settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization/SettingsOptimization.jar`; 2 raw class entries; SHA-256 `396caaa71a8de45400cba27e8aa6810341088c077a56be9b0411adff13a9ea05`.
- **Inspected reference:** [SettingsOptimization.md](../../sqx/Shared/SettingsOptimization.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization/SettingsOptimization.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization/SettingsOptimization.jar" com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/optimization/SettingsOptimization/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization`; `SQX_145_REFERENCE_ROOT/internal/web/OPTIMIZER`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization/OptimizationService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization/OptimizationCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization/views/autoPresetPopup.html`.
- **Existing UI connection:** Optimizer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Optimizer/optimizerClient.ts`; wire selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/optimization/SettingsOptimization/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/SettingsOptimization/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/SettingsOptimization/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/SettingsOptimization/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_settings_optimization.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_settings_optimization.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Optimizer/optimizerClient.ts`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerProgress.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/WalkForwardMatrixView.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-optimizer-settings-optimization.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated Optimization settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-OPTIMIZER-SETTINGS-OPTIMIZATION-OPTIMIZATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-OPTIMIZER-SETTINGS-OPTIMIZATION-OPTIMIZATION-SERVLET-GET-INSTANCE` → `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet.getInstance()Lcom/strategyquant/plugin/Settings/impl/Optimization/OptimizationServlet;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-OPTIMIZER-SETTINGS-OPTIMIZATION-OPTIMIZATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_settings_optimization.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-optimizer-settings-optimization.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Optimizer for FEAT-OPTIMIZER-SETTINGS-OPTIMIZATION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 10.9 FEAT-OPTIMIZER-TASK-OPTIMIZE - TaskOptimize.jar

## 1. Objective

- **Goal:** Execute Optimize through an owned typed task capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskOptimize/TaskOptimize.jar`; 10 raw class entries; SHA-256 `026673159e7365b15e877ecd9123bf4187f49218d4db3855a6c0fed6a3735bc5`.
- **Inspected reference:** [TaskOptimize.md](../../sqx/Optimizer/TaskOptimize.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskOptimize/TaskOptimize.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskOptimize/TaskOptimize.jar" com.strategyquant.plugin.Task.impl.Optimize.OptimizeTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/optimization/TaskOptimize/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskOptimize`; `SQX_145_REFERENCE_ROOT/internal/web/OPTIMIZER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskOptimize/simpleSettings/SimpleOptimizeSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskOptimize/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskOptimize/module.js`.
- **Existing UI connection:** Optimizer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Optimizer/optimizerClient.ts`; wire selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/optimization/TaskOptimize/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/TaskOptimize/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/TaskOptimize/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/TaskOptimize/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_task_optimize.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_task_optimize.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Optimizer/optimizerClient.ts`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerProgress.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/WalkForwardMatrixView.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-optimizer-task-optimize.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute Optimize through an owned typed task capability; verify input handles, start/stop/clone transitions, failure status and retained outputs.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-OPTIMIZER-TASK-OPTIMIZE-OPTIMIZE-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.Optimize.OptimizeTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-OPTIMIZER-TASK-OPTIMIZE-OPTIMIZE-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.Optimize.OptimizeTask.getType()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-OPTIMIZER-TASK-OPTIMIZE-OPTIMIZE-TASK-GET-NAME` → `com.strategyquant.plugin.Task.impl.Optimize.OptimizeTask.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_task_optimize.py --no-cov`; expect input handles, start/stop/clone transitions, failure status and retained outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture input handles, start/stop/clone transitions, failure status and retained outputs and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-optimizer-task-optimize.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Optimizer for FEAT-OPTIMIZER-TASK-OPTIMIZE; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 10.10 P10 integration — Optimize strategy parameters and calculate walk-forward/profile results

## 1. Objective

- **Goal:** Optimize strategy parameters and calculate walk-forward/profile results.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P10; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/Optimizer/optimizerModes.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/OPTIMIZER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/OPTIMIZER/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptimization/OptimizationService.js`.
- **Existing UI connection:** Optimizer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Optimizer/optimizerClient.ts`; wire selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Optimizer/workspace.py` (proposed earlier in FEAT-OPTIMIZER-APP-OPTIMIZER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/Optimizer/routes.py` (proposed earlier in FEAT-OPTIMIZER-APP-OPTIMIZER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/optimization/search.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/optimization/parameters.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/optimization/walk_forward.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/optimization/matrix.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Modify:** `ui/app/workspace/Optimizer/optimizerClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/workspace/Optimizer/README.md` (proposed earlier in FEAT-OPTIMIZER-APP-OPTIMIZER)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_optimizer_walk_forward_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Optimizer/OptimizerProgress.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Optimizer/WalkForwardMatrixView.tsx`
  - Display selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/task-10-10.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify parameter ranges, candidate order, objective/ties, sequential rules and WF partitions.
- [ ] **Step 3:** Implement simple/sequential/profile/matrix search with isolated in/out-of-sample windows.
- [ ] **Step 4:** Connect Optimizer settings, progress and result projections to real reusable runs.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/settings execution, optimization/WF jobs and actual profile/matrix outputs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_optimizer_walk_forward_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/Optimizer/optimizerModes.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`. Assert candidate enumeration, objective ordering, WF window boundaries and matrix reconciliation; reject empty range, invalid partition, data leakage, tied score and cancellation.
- **Manual / Browser Verification:** Run a small parameter grid; inspect each candidate; run a WF matrix; confirm out-of-sample rows and repeatability.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-10-10.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Optimizer for 10.11; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
