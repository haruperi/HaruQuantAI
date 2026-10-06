# P11 — Retester, robustness checks, Monte Carlo and What-If

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P06,P08,P10.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 18 tasks; current archive allocations and resource/integration tasks only.

# 11.1 FEAT-ROBUSTNESS-APP-RETESTER - AppRetester.jar

## 1. Objective

- **Goal:** Mount the Retester workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppRetester/AppRetester.jar`; 1 raw class entries; SHA-256 `d79488d54448b70198336bcca5fd597d983a8ea108ae2d329ff8bef815bb964f`.
- **Inspected reference:** [AppRetester.md](../../sqx/Retester/AppRetester.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppRetester/AppRetester.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppRetester/AppRetester.jar" com.strategyquant.plugin.App.impl.Retester.RetesterAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Retester/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppRetester`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppRetester/module.js`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Retester/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_app_retester.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_app_retester.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-app-retester.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the Retester workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-APP-RETESTER-RETESTER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.Retester.RetesterAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-APP-RETESTER-RETESTER-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.Retester.RetesterAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-APP-RETESTER-RETESTER-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.Retester.RetesterAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_app_retester.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-app-retester.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-APP-RETESTER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.2 FEAT-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-MANIPULATION - CrossCheckMonteCarloManipulation.jar

## 1. Objective

- **Goal:** Implement the named Monte Carlo perturbation/retest check.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/CrossCheckMonteCarloManipulation.jar`; 2 raw class entries; SHA-256 `9e1b43294ccf3a6fa2e9fbda63a6e1d2089982050dc3f31267793e16425e6688`.
- **Inspected reference:** [CrossCheckMonteCarloManipulation.md](../../sqx/Shared/CrossCheckMonteCarloManipulation.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/CrossCheckMonteCarloManipulation.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/CrossCheckMonteCarloManipulation.jar" com.strategyquant.plugin.CrossCheck.impl.MonteCarloManipulation.MonteCarloManipulationServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/cross_checks/CrossCheckMonteCarloManipulation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/MonteCarloManipulationService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/FitnessFunction/MCManipulationFitnessService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/MonteCarloManipulationCtrl.js`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/cross_checks/CrossCheckMonteCarloManipulation/check.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckMonteCarloManipulation/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckMonteCarloManipulation/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_cross_check_monte_carlo_manipulation.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_cross_check_monte_carlo_manipulation.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-cross-check-monte-carlo-manipulation.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named Monte Carlo perturbation/retest check; verify seeded sampling, replacement rules, thresholds and rejected scenarios.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-MANIPULATION-MONTE-CARLO-MANIPULATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.MonteCarloManipulation.MonteCarloManipulationServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-MANIPULATION-MONTE-CARLO-MANIPULATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.CrossCheck.impl.MonteCarloManipulation.MonteCarloManipulationServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-MANIPULATION-MONTE-CARLO-MANIPULATION-SERVLET-ON-LIST` → `com.strategyquant.plugin.CrossCheck.impl.MonteCarloManipulation.MonteCarloManipulationServlet.onList(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_cross_check_monte_carlo_manipulation.py --no-cov`; expect seeded sampling, replacement rules, thresholds and rejected scenarios; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture seeded sampling, replacement rules, thresholds and rejected scenarios and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-cross-check-monte-carlo-manipulation.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-MANIPULATION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.3 FEAT-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-RETEST - CrossCheckMonteCarloRetest.jar

## 1. Objective

- **Goal:** Implement the named Monte Carlo perturbation/retest check.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/CrossCheckMonteCarloRetest.jar`; 7 raw class entries; SHA-256 `e2f5937574171309bcfb4dc9ada19eff0195f767383e614187b06a71a941c43b`.
- **Inspected reference:** [CrossCheckMonteCarloRetest.md](../../sqx/Shared/CrossCheckMonteCarloRetest.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/CrossCheckMonteCarloRetest.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/CrossCheckMonteCarloRetest.jar" com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest.MonteCarloRetestServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/cross_checks/CrossCheckMonteCarloRetest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/MonteCarloRetestService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/FitnessFunction/MCRetestFitnessService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/MonteCarloRetestCtrl.js`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/cross_checks/CrossCheckMonteCarloRetest/check.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckMonteCarloRetest/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckMonteCarloRetest/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_cross_check_monte_carlo_retest.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_cross_check_monte_carlo_retest.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-cross-check-monte-carlo-retest.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named Monte Carlo perturbation/retest check; verify seeded sampling, replacement rules, thresholds and rejected scenarios.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-RETEST-MONTE-CARLO-RETEST-SERVLET-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest.MonteCarloRetestServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-RETEST-MONTE-CARLO-RETEST-SERVLET-EXECUTE` → `com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest.MonteCarloRetestServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-RETEST-MONTE-CARLO-RETEST-SERVLET-ON-LIST` → `com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest.MonteCarloRetestServlet.onList()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_cross_check_monte_carlo_retest.py --no-cov`; expect seeded sampling, replacement rules, thresholds and rejected scenarios; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture seeded sampling, replacement rules, thresholds and rejected scenarios and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-cross-check-monte-carlo-retest.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-RETEST; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.4 FEAT-ROBUSTNESS-CROSS-CHECK-OPT-PROFILE-SYS-PARAM-PERMUTATION - CrossCheckOptProfileSysParamPermutation.jar

## 1. Objective

- **Goal:** Implement parameter profile/permutation sampling and projections.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/CrossCheckOptProfileSysParamPermutation.jar`; 2 raw class entries; SHA-256 `c4e99b61351649ea64d8ea64d88a719336b0a249edd7ae3d28a34b097080d6da`.
- **Inspected reference:** [CrossCheckOptProfileSysParamPermutation.md](../../sqx/Shared/CrossCheckOptProfileSysParamPermutation.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/CrossCheckOptProfileSysParamPermutation.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/CrossCheckOptProfileSysParamPermutation.jar" com.strategyquant.plugin.CrossCheck.impl.OptProfileSysParamPermutation.OptProfileSysParamPermutationServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/cross_checks/CrossCheckOptProfileSysParamPermutation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/OptProfileSysParamPermutationService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/OptProfileSysParamPermutationCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/filtering.html`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/cross_checks/CrossCheckOptProfileSysParamPermutation/check.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckOptProfileSysParamPermutation/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckOptProfileSysParamPermutation/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_cross_check_opt_profile_sys_param_permutation.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_cross_check_opt_profile_sys_param_permutation.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-cross-check-opt-profile-sys-param-permutation.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement parameter profile/permutation sampling and projections; verify range endpoints, enumeration order and matrix/result reconciliation.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-CROSS-CHECK-OPT-PROFILE-SYS-PARAM-PERMUTATION-OPT-PROFILE-SYS-PARAM-PERMUTATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.OptProfileSysParamPermutation.OptProfileSysParamPermutationServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-CROSS-CHECK-OPT-PROFILE-SYS-PARAM-PERMUTATION-OPT-PROFILE-SYS-PARAM-PERMUTATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.CrossCheck.impl.OptProfileSysParamPermutation.OptProfileSysParamPermutationServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-CROSS-CHECK-OPT-PROFILE-SYS-PARAM-PERMUTATION-OPT-PROFILE-SYS-PARAM-PERMUTATION-SERVLET-ON-GET-DEFAULT-SPPCONDITIONS` → `com.strategyquant.plugin.CrossCheck.impl.OptProfileSysParamPermutation.OptProfileSysParamPermutationServlet.onGetDefaultSPPConditions()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_cross_check_opt_profile_sys_param_permutation.py --no-cov`; expect range endpoints, enumeration order and matrix/result reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture range endpoints, enumeration order and matrix/result reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-cross-check-opt-profile-sys-param-permutation.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-CROSS-CHECK-OPT-PROFILE-SYS-PARAM-PERMUTATION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.5 FEAT-ROBUSTNESS-CROSS-CHECK-RETEST-ON-ADDITIONAL-MARKETS - CrossCheckRetestOnAdditionalMarkets.jar

## 1. Objective

- **Goal:** Retest saved strategies on explicitly selected additional-market datasets.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/CrossCheckRetestOnAdditionalMarkets.jar`; 4 raw class entries; SHA-256 `d351ae03bb2e4c695dcb4a3abb3ca223a8777ae850deb2572c8eb30934d4ddaa`.
- **Inspected reference:** [CrossCheckRetestOnAdditionalMarkets.md](../../sqx/Shared/CrossCheckRetestOnAdditionalMarkets.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/CrossCheckRetestOnAdditionalMarkets.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/CrossCheckRetestOnAdditionalMarkets.jar" com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/cross_checks/CrossCheckRetestOnAdditionalMarkets/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/RetestOnAdditionalMarketsService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/FitnessFunction/PortfolioFitnessService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/RetestOnAdditionalMarketsCtrl.js`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/cross_checks/CrossCheckRetestOnAdditionalMarkets/check.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckRetestOnAdditionalMarkets/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckRetestOnAdditionalMarkets/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_cross_check_retest_on_additional_markets.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_cross_check_retest_on_additional_markets.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-cross-check-retest-on-additional-markets.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Retest saved strategies on explicitly selected additional-market datasets; verify symbol/data selection, missing market and aggregate check decisions.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-CROSS-CHECK-RETEST-ON-ADDITIONAL-MARKETS-RETEST-ON-ADDITIONAL-MARKETS-SERVLET-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-CROSS-CHECK-RETEST-ON-ADDITIONAL-MARKETS-RETEST-ON-ADDITIONAL-MARKETS-SERVLET-EXECUTE` → `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-CROSS-CHECK-RETEST-ON-ADDITIONAL-MARKETS-RETEST-ON-ADDITIONAL-MARKETS-SERVLET-ON-LIST` → `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet.onList()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_cross_check_retest_on_additional_markets.py --no-cov`; expect symbol/data selection, missing market and aggregate check decisions; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol/data selection, missing market and aggregate check decisions and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-cross-check-retest-on-additional-markets.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-CROSS-CHECK-RETEST-ON-ADDITIONAL-MARKETS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.6 FEAT-ROBUSTNESS-CROSS-CHECK-RETEST-WITH-HIGHER-PRECISION - CrossCheckRetestWithHigherPrecision.jar

## 1. Objective

- **Goal:** Retest with a qualified higher-precision data/execution model.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/CrossCheckRetestWithHigherPrecision.jar`; 4 raw class entries; SHA-256 `a62e26f3efe6e7a087cc78203c49d038a1e90c96ed69037bcec70d01f73eb5ec`.
- **Inspected reference:** [CrossCheckRetestWithHigherPrecision.md](../../sqx/Shared/CrossCheckRetestWithHigherPrecision.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/CrossCheckRetestWithHigherPrecision.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/CrossCheckRetestWithHigherPrecision.jar" com.strategyquant.plugin.CrossCheck.impl.RetestWithHigherPrecision.RetestWithHigherPrecisionServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/cross_checks/CrossCheckRetestWithHigherPrecision/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/RetestWithHigherPrecisionService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/FitnessFunction/CCHigherPrecisionService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/RetestWithHigherPrecisionCtrl.js`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/cross_checks/CrossCheckRetestWithHigherPrecision/check.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckRetestWithHigherPrecision/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckRetestWithHigherPrecision/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_cross_check_retest_with_higher_precision.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_cross_check_retest_with_higher_precision.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-cross-check-retest-with-higher-precision.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Retest with a qualified higher-precision data/execution model; verify precision availability, event alignment and result comparison.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-CROSS-CHECK-RETEST-WITH-HIGHER-PRECISION-RETEST-WITH-HIGHER-PRECISION-SERVLET-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.RetestWithHigherPrecision.RetestWithHigherPrecisionServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-CROSS-CHECK-RETEST-WITH-HIGHER-PRECISION-RETEST-WITH-HIGHER-PRECISION-SERVLET-EXECUTE` → `com.strategyquant.plugin.CrossCheck.impl.RetestWithHigherPrecision.RetestWithHigherPrecisionServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-CROSS-CHECK-RETEST-WITH-HIGHER-PRECISION-RETEST-WITH-HIGHER-PRECISION-SERVLET-ON-LIST` → `com.strategyquant.plugin.CrossCheck.impl.RetestWithHigherPrecision.RetestWithHigherPrecisionServlet.onList()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_cross_check_retest_with_higher_precision.py --no-cov`; expect precision availability, event alignment and result comparison; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture precision availability, event alignment and result comparison and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-cross-check-retest-with-higher-precision.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-CROSS-CHECK-RETEST-WITH-HIGHER-PRECISION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.7 FEAT-ROBUSTNESS-CROSS-CHECK-SEQUENTIAL-OPTIMIZATION - CrossCheckSequentialOptimization.jar

## 1. Objective

- **Goal:** Implement sequential parameter-search ordering and result retention.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/CrossCheckSequentialOptimization.jar`; 2 raw class entries; SHA-256 `d1b45af45898fbb7c875b9b670a5d423eac1386ad13953be08c7dabcfc93cec0`.
- **Inspected reference:** [CrossCheckSequentialOptimization.md](../../sqx/Shared/CrossCheckSequentialOptimization.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/CrossCheckSequentialOptimization.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/CrossCheckSequentialOptimization.jar" com.strategyquant.plugin.CrossCheck.impl.SequentialOptimization.SequentialOptimization`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/cross_checks/CrossCheckSequentialOptimization/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/SequentialOptimizationService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/SequentialOptimizationCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/filtering.html`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/cross_checks/CrossCheckSequentialOptimization/check.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckSequentialOptimization/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckSequentialOptimization/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_cross_check_sequential_optimization.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_cross_check_sequential_optimization.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-cross-check-sequential-optimization.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement sequential parameter-search ordering and result retention; verify candidate dependencies, repeated passes, stopping and score ordering.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-CROSS-CHECK-SEQUENTIAL-OPTIMIZATION-SEQUENTIAL-OPTIMIZATION-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.SequentialOptimization.SequentialOptimization`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-CROSS-CHECK-SEQUENTIAL-OPTIMIZATION-SEQUENTIAL-OPTIMIZATION-GET-NAME` → `com.strategyquant.plugin.CrossCheck.impl.SequentialOptimization.SequentialOptimization.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-CROSS-CHECK-SEQUENTIAL-OPTIMIZATION-SEQUENTIAL-OPTIMIZATION-GET-SHORT-NAME` → `com.strategyquant.plugin.CrossCheck.impl.SequentialOptimization.SequentialOptimization.getShortName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_cross_check_sequential_optimization.py --no-cov`; expect candidate dependencies, repeated passes, stopping and score ordering; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture candidate dependencies, repeated passes, stopping and score ordering and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-cross-check-sequential-optimization.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-CROSS-CHECK-SEQUENTIAL-OPTIMIZATION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.8 FEAT-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-MATRIX - CrossCheckWalkForwardMatrix.jar

## 1. Objective

- **Goal:** Implement the named walk-forward partition/result contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/CrossCheckWalkForwardMatrix.jar`; 1 raw class entries; SHA-256 `f007a6c8f3edeee29044a0c357cd51a1a60768b4daa06d621fd1508789543c1a`.
- **Inspected reference:** [CrossCheckWalkForwardMatrix.md](../../sqx/Shared/CrossCheckWalkForwardMatrix.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/CrossCheckWalkForwardMatrix.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/CrossCheckWalkForwardMatrix.jar" com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/cross_checks/CrossCheckWalkForwardMatrix/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/WalkForwardMatrixService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/WalkForwardMatrixCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/filtering.html`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/cross_checks/CrossCheckWalkForwardMatrix/check.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckWalkForwardMatrix/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckWalkForwardMatrix/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_cross_check_walk_forward_matrix.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_cross_check_walk_forward_matrix.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-cross-check-walk-forward-matrix.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named walk-forward partition/result contract; verify in/out-of-sample boundaries, leakage rejection, aggregation and tie rules.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-MATRIX-WALK-FORWARD-MATRIX-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-MATRIX-WALK-FORWARD-MATRIX-GET-NAME` → `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-MATRIX-WALK-FORWARD-MATRIX-GET-SHORT-NAME` → `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix.getShortName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_cross_check_walk_forward_matrix.py --no-cov`; expect in/out-of-sample boundaries, leakage rejection, aggregation and tie rules; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture in/out-of-sample boundaries, leakage rejection, aggregation and tie rules and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-cross-check-walk-forward-matrix.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-MATRIX; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.9 FEAT-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-OPTIMIZATION - CrossCheckWalkForwardOptimization.jar

## 1. Objective

- **Goal:** Implement the named walk-forward partition/result contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/CrossCheckWalkForwardOptimization.jar`; 1 raw class entries; SHA-256 `4408fcd694f4289b606b4a72443e9df2c1212287fe7ce371257d288e4f9df6f4`.
- **Inspected reference:** [CrossCheckWalkForwardOptimization.md](../../sqx/Shared/CrossCheckWalkForwardOptimization.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/CrossCheckWalkForwardOptimization.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/CrossCheckWalkForwardOptimization.jar" com.strategyquant.plugin.CrossCheck.impl.WalkForwardOptimization.WalkForwardOptimization`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/cross_checks/CrossCheckWalkForwardOptimization/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/WalkForwardOptimizationService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/WalkForwardOptimizationCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/filtering.html`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/cross_checks/CrossCheckWalkForwardOptimization/check.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckWalkForwardOptimization/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckWalkForwardOptimization/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_cross_check_walk_forward_optimization.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_cross_check_walk_forward_optimization.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-cross-check-walk-forward-optimization.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named walk-forward partition/result contract; verify in/out-of-sample boundaries, leakage rejection, aggregation and tie rules.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-OPTIMIZATION-WALK-FORWARD-OPTIMIZATION-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.WalkForwardOptimization.WalkForwardOptimization`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-OPTIMIZATION-WALK-FORWARD-OPTIMIZATION-GET-NAME` → `com.strategyquant.plugin.CrossCheck.impl.WalkForwardOptimization.WalkForwardOptimization.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-OPTIMIZATION-WALK-FORWARD-OPTIMIZATION-GET-SHORT-NAME` → `com.strategyquant.plugin.CrossCheck.impl.WalkForwardOptimization.WalkForwardOptimization.getShortName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_cross_check_walk_forward_optimization.py --no-cov`; expect in/out-of-sample boundaries, leakage rejection, aggregation and tie rules; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture in/out-of-sample boundaries, leakage rejection, aggregation and tie rules and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-cross-check-walk-forward-optimization.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-OPTIMIZATION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.10 FEAT-ROBUSTNESS-CROSS-CHECK-WHAT-IF - CrossCheckWhatIf.jar

## 1. Objective

- **Goal:** Apply configured What-If scenarios to qualified result inputs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/CrossCheckWhatIf.jar`; 2 raw class entries; SHA-256 `21b7eef300135c7899bd4d235582a036ba9a9b0ad436d6fa3de533fddc1d1820`.
- **Inspected reference:** [CrossCheckWhatIf.md](../../sqx/Shared/CrossCheckWhatIf.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/CrossCheckWhatIf.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/CrossCheckWhatIf.jar" com.strategyquant.plugin.CrossCheck.impl.WhatIf.WhatIfServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/cross_checks/CrossCheckWhatIf/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/WhatIfService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/WhatIfCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/settings.html`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/cross_checks/CrossCheckWhatIf/check.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckWhatIf/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/CrossCheckWhatIf/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_cross_check_what_if.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_cross_check_what_if.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-cross-check-what-if.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Apply configured What-If scenarios to qualified result inputs; verify scenario composition, excluded trades and denominator/totals reconciliation.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-CROSS-CHECK-WHAT-IF-WHAT-IF-SERVLET-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.WhatIf.WhatIfServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-CROSS-CHECK-WHAT-IF-WHAT-IF-SERVLET-EXECUTE` → `com.strategyquant.plugin.CrossCheck.impl.WhatIf.WhatIfServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-CROSS-CHECK-WHAT-IF-WHAT-IF-SERVLET-ON-LIST` → `com.strategyquant.plugin.CrossCheck.impl.WhatIf.WhatIfServlet.onList(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_cross_check_what_if.py --no-cov`; expect scenario composition, excluded trades and denominator/totals reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture scenario composition, excluded trades and denominator/totals reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-cross-check-what-if.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-CROSS-CHECK-WHAT-IF; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.11 FEAT-ROBUSTNESS-RESULTS-ROBUSTNESS-TESTS - ResultsRobustnessTests.jar

## 1. Objective

- **Goal:** Implement authoritative RobustnessTests result projections/actions.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/ResultsRobustnessTests.jar`; 7 raw class entries; SHA-256 `c82ecb7d211e28b40b5e635ddde834bf09f67f54514b85d5997bf97e2f5aad4f`.
- **Inspected reference:** [ResultsRobustnessTests.md](../../sqx/Results/ResultsRobustnessTests.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/ResultsRobustnessTests.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/ResultsRobustnessTests.jar" com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/results/ResultsRobustnessTests/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness result projection and diagnostics; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/services/RTService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/directives/manageviews/ManageViewsService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/RobustnessTestsResultsCtrl.js`.
- **Existing UI connection:** Retester; exact retained source-map `ui/app/plugins/project/ResultsRobustnessTests/source-map.json`. Target `ui/app/plugins/project/ResultsRobustnessTests/RobustnessTestsResultsCtrl.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/results/ResultsRobustnessTests/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsRobustnessTests/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/results/ResultsRobustnessTests/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_results_robustness_tests.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_results_robustness_tests.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsRobustnessTests/RobustnessTestsResultsCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsRobustnessTests/robustnessTests.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ResultsRobustnessTests/directives/robustnessAnalysis/robustnessAnalysis.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsRobustnessTests/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-results-robustness-tests.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement authoritative RobustnessTests result projections/actions; verify metric provenance, result identity, empty/error state and stored-value reconciliation.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-RESULTS-ROBUSTNESS-TESTS-ROBUSTNESS-TESTS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-RESULTS-ROBUSTNESS-TESTS-ROBUSTNESS-TESTS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-RESULTS-ROBUSTNESS-TESTS-ROBUSTNESS-TESTS-SERVLET-ON-GET-METHODS` → `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet.onGetMethods(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_results_robustness_tests.py --no-cov`; expect metric provenance, result identity, empty/error state and stored-value reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture metric provenance, result identity, empty/error state and stored-value reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-results-robustness-tests.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-RESULTS-ROBUSTNESS-TESTS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.12 FEAT-ROBUSTNESS-SETTINGS-AUTO-RETEST-DATA - SettingsAutoRetestData.jar

## 1. Objective

- **Goal:** Implement validated AutoRetestData settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/SettingsAutoRetestData.jar`; 1 raw class entries; SHA-256 `f2f6bd48ea64be3a858502972b50b5b5770847fba1432f201663c109478ef7ff`.
- **Inspected reference:** [SettingsAutoRetestData.md](../../sqx/Shared/SettingsAutoRetestData.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/SettingsAutoRetestData.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/SettingsAutoRetestData.jar" com.strategyquant.plugin.Settings.impl.AutoRetestData.CustomDataSettingsPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Retester/SettingsAutoRetestData/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Retest/automatic-retest project/task configuration and results; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/AutoRetestDataService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/AutoRetestDataCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/views/autoRetestData.html`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Retester/SettingsAutoRetestData/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/SettingsAutoRetestData/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/SettingsAutoRetestData/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/SettingsAutoRetestData/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_settings_auto_retest_data.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_settings_auto_retest_data.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-settings-auto-retest-data.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated AutoRetestData settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-SETTINGS-AUTO-RETEST-DATA-CUSTOM-DATA-SETTINGS-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.AutoRetestData.CustomDataSettingsPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-SETTINGS-AUTO-RETEST-DATA-CUSTOM-DATA-SETTINGS-PLUGIN-GET-HANDLER` → `com.strategyquant.plugin.Settings.impl.AutoRetestData.CustomDataSettingsPlugin.getHandler()Lorg/eclipse/jetty/server/Handler;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-SETTINGS-AUTO-RETEST-DATA-CUSTOM-DATA-SETTINGS-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.AutoRetestData.CustomDataSettingsPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_settings_auto_retest_data.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-settings-auto-retest-data.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-SETTINGS-AUTO-RETEST-DATA; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.13 FEAT-ROBUSTNESS-SETTINGS-CROSS-CHECKS - SettingsCrossChecks.jar

## 1. Objective

- **Goal:** Implement validated CrossChecks settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/SettingsCrossChecks.jar`; 2 raw class entries; SHA-256 `12ed3ab90da9476cdd55e57d00d67ef8f913a0af4963abe3a54070c03dc3515e`.
- **Inspected reference:** [SettingsCrossChecks.md](../../sqx/Shared/SettingsCrossChecks.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/SettingsCrossChecks.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/SettingsCrossChecks.jar" com.strategyquant.plugin.Settings.impl.CrossChecks.CrossChecksServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/cross_checks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness method selection and configuration; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossCheckAcceptanceSettingsService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossChecksService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossCheckAcceptanceSettingsCtrl.js`.
- **Existing UI connection:** Retester; exact retained source-map `ui/app/plugins/project/SettingsCrossChecks/source-map.json`. Target `ui/app/plugins/project/SettingsCrossChecks/CrossChecksCtrl.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/cross_checks/catalog.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/cross_checks/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_settings_cross_checks.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_settings_cross_checks.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/SettingsCrossChecks/CrossChecksCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/SettingsCrossChecks/crossCheckSettingsDialog.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/SettingsCrossChecks/crossChecks.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/SettingsCrossChecks/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-settings-cross-checks.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated CrossChecks settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-SETTINGS-CROSS-CHECKS-CROSS-CHECKS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.CrossChecks.CrossChecksServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-SETTINGS-CROSS-CHECKS-CROSS-CHECKS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.CrossChecks.CrossChecksServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-SETTINGS-CROSS-CHECKS-CROSS-CHECKS-SERVLET-LIST` → `com.strategyquant.plugin.Settings.impl.CrossChecks.CrossChecksServlet.list()Lorg/json/JSONArray;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_settings_cross_checks.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-settings-cross-checks.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-SETTINGS-CROSS-CHECKS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.14 FEAT-ROBUSTNESS-SETTINGS-WHAT-TO-RETEST - SettingsWhatToRetest.jar

## 1. Objective

- **Goal:** Implement validated WhatToRetest settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/SettingsWhatToRetest.jar`; 1 raw class entries; SHA-256 `e2ccf9f12713cf7a759c7502ef666e060b5fa69273a7e53508dbf02e415c6e14`.
- **Inspected reference:** [SettingsWhatToRetest.md](../../sqx/Shared/SettingsWhatToRetest.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/SettingsWhatToRetest.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/SettingsWhatToRetest.jar" com.strategyquant.plugin.Settings.impl.WhatToRetest.SettingsWhatToRetestPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Retester/SettingsWhatToRetest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Retest/automatic-retest project/task configuration and results; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/SettingsWhatToRetestService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/SettingsWhatToRetestCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/whatToRetest.html`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Retester/SettingsWhatToRetest/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/SettingsWhatToRetest/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/SettingsWhatToRetest/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/SettingsWhatToRetest/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_settings_what_to_retest.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_settings_what_to_retest.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-settings-what-to-retest.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated WhatToRetest settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-SETTINGS-WHAT-TO-RETEST-SETTINGS-WHAT-TO-RETEST-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.WhatToRetest.SettingsWhatToRetestPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-SETTINGS-WHAT-TO-RETEST-SETTINGS-WHAT-TO-RETEST-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.WhatToRetest.SettingsWhatToRetestPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-SETTINGS-WHAT-TO-RETEST-SETTINGS-WHAT-TO-RETEST-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.WhatToRetest.SettingsWhatToRetestPlugin.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_settings_what_to_retest.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-settings-what-to-retest.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-SETTINGS-WHAT-TO-RETEST; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.15 FEAT-ROBUSTNESS-TASK-AUTOMATIC-RETEST - TaskAutomaticRetest.jar

## 1. Objective

- **Goal:** Run owned retest chains against immutable strategy/run inputs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/TaskAutomaticRetest.jar`; 6 raw class entries; SHA-256 `be3c69292d3dd949a7324a7527d105ea1320c7b02493ee6be00b1cc013ac73b1`.
- **Inspected reference:** [TaskAutomaticRetest.md](../../sqx/Retester/TaskAutomaticRetest.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/TaskAutomaticRetest.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/TaskAutomaticRetest.jar" com.strategyquant.plugin.Task.impl.AutomaticRetest.AutomaticRetestTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Retester/TaskAutomaticRetest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Retest/automatic-retest project/task configuration and results; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/TaskAutoRetestService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/simpleSettings/SimpleAutoRetestSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/simpleSettings/simpleSettings.html`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Retester/TaskAutomaticRetest/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/TaskAutomaticRetest/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/TaskAutomaticRetest/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/TaskAutomaticRetest/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_task_automatic_retest.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_task_automatic_retest.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-task-automatic-retest.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Run owned retest chains against immutable strategy/run inputs; verify child-job ownership, threshold evaluation, cancellation and result retention.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-TASK-AUTOMATIC-RETEST-AUTOMATIC-RETEST-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.AutomaticRetest.AutomaticRetestTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-TASK-AUTOMATIC-RETEST-AUTOMATIC-RETEST-TASK-BEFORE-START` → `com.strategyquant.plugin.Task.impl.AutomaticRetest.AutomaticRetestTask.beforeStart()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-TASK-AUTOMATIC-RETEST-AUTOMATIC-RETEST-TASK-RECOGNIZE-CUSTOM-ANALYSIS-METHOD` → `com.strategyquant.plugin.Task.impl.AutomaticRetest.AutomaticRetestTask.recognizeCustomAnalysisMethod()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_task_automatic_retest.py --no-cov`; expect child-job ownership, threshold evaluation, cancellation and result retention; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture child-job ownership, threshold evaluation, cancellation and result retention and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-task-automatic-retest.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-TASK-AUTOMATIC-RETEST; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.16 FEAT-ROBUSTNESS-TASK-RETEST - TaskRetest.jar

## 1. Objective

- **Goal:** Run owned retest chains against immutable strategy/run inputs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskRetest/TaskRetest.jar`; 4 raw class entries; SHA-256 `a7957f8d46aa6b01be420af5970a63fed5b8ac9600beac6af95a28eab5cb5437`.
- **Inspected reference:** [TaskRetest.md](../../sqx/Retester/TaskRetest.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskRetest/TaskRetest.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskRetest/TaskRetest.jar" com.strategyquant.plugin.Task.impl.Retest.RetestTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Retester/TaskRetest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Retest/automatic-retest project/task configuration and results; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskRetest`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskRetest/simpleSettings/SimpleRetestSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskRetest/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskRetest/module.js`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Retester/TaskRetest/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/TaskRetest/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/TaskRetest/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/TaskRetest/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_task_retest.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_task_retest.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-task-retest.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Run owned retest chains against immutable strategy/run inputs; verify child-job ownership, threshold evaluation, cancellation and result retention.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-ROBUSTNESS-TASK-RETEST-RETEST-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.Retest.RetestTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-ROBUSTNESS-TASK-RETEST-RETEST-TASK-BEFORE-START` → `com.strategyquant.plugin.Task.impl.Retest.RetestTask.beforeStart()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-ROBUSTNESS-TASK-RETEST-RETEST-TASK-RECOGNIZE-CUSTOM-ANALYSIS-METHOD` → `com.strategyquant.plugin.Task.impl.Retest.RetestTask.recognizeCustomAnalysisMethod()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_task_retest.py --no-cov`; expect child-job ownership, threshold evaluation, cancellation and result retention; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture child-job ownership, threshold evaluation, cancellation and result retention and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-task-retest.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-TASK-RETEST; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.17 FEAT-UI-SETTINGS-AUTOMATIC-RETEST - SettingsAutomaticRetest resource contribution

## 1. Objective

- **Goal:** Qualify and connect SettingsAutomaticRetest without assuming a missing backend JAR.
- **Context / Problem Solved:** SettingsAutomaticRetest is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest`; narrow source: `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest/module.js`.
- **FR:** `FR-UI-SETTINGS-AUTOMATIC-RETEST-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/Retester/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest`; `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest/SettingsAutomaticRetestCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest/automaticRetest.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest/module.js`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Retester/resource_contributions.py`
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/workspace/Retester/README.md` (proposed earlier in FEAT-ROBUSTNESS-APP-RETESTER)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_settings_automatic_retest.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-settings-automatic-retest.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-SETTINGS-AUTOMATIC-RETEST-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_settings_automatic_retest.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Retest one saved strategy with a fixed seed; inspect scenario inputs and thresholds; cancel a check and verify consistent status. Inspect the SettingsAutomaticRetest contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-settings-automatic-retest.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-UI-SETTINGS-AUTOMATIC-RETEST; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 11.18 P11 integration — Run reproducible robustness checks and publish actual retest outcomes

## 1. Objective

- **Goal:** Run reproducible robustness checks and publish actual retest outcomes.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P11; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/Retester/retesterWorkflow.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/RETESTER/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossCheckAcceptanceSettingsService.js`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Retester/workspace.py` (proposed earlier in FEAT-ROBUSTNESS-APP-RETESTER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/Retester/routes.py` (proposed earlier in FEAT-ROBUSTNESS-APP-RETESTER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/robustness/monte_carlo.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/robustness/what_if.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/robustness/runner.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/workspace/Retester/README.md` (proposed earlier in FEAT-ROBUSTNESS-APP-RETESTER)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_retester_robustness_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/task-11-18.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify each cross-check's perturbation, seed, sampling, precision and pass/fail rules.
- [ ] **Step 3:** Implement Monte Carlo manipulation/retest, additional markets, What-If and optimizer-backed checks.
- [ ] **Step 4:** Connect Retester and automatic-retest jobs to stored input/results and real progress.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_retester_robustness_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/Retester/retesterWorkflow.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-retester-robustness-backend.spec.ts`. Assert fixed-seed perturbations, cross-check thresholds and additional-market retests; reject missing market, unsupported precision, invalid scenario and interrupted child job.
- **Manual / Browser Verification:** Retest one saved strategy with a fixed seed; inspect scenario inputs and thresholds; cancel a check and verify consistent status.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-11-18.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for 11.19; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
