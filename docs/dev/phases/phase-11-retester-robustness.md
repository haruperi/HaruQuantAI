# P11 — Retester, robustness checks, Monte Carlo and What-If

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P06,P08,P10.
- **Scope:** 17 JAR feature tasks, 1 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.

# 11.1 FEAT-ROBUSTNESS-APP-RETESTER - AppRetester.jar

## 1. Objective

- **Goal:** Mount the Retester workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppRetester/AppRetester.jar`; 1 class declarations; SHA-256 `f92947a7e0740396fd214099f8a3746a0b187b64183bf2ac73af29c12d91c5ec`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Retester/AppRetester.md`; roadmap allocation `FEAT-ROBUSTNESS-APP-RETESTER`.
- **Owner:** `app/workspace/Retester/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppRetester/AppRetester.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppRetester/AppRetester.jar" com.strategyquant.plugin.App.impl.Retester.RetesterAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/AppRetester`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/AppRetester/module.js`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-APP-RETESTER-RETESTER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.Retester.RetesterAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-APP-RETESTER-RETESTER-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.Retester.RetesterAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-ROBUSTNESS-APP-RETESTER-RETESTER-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.Retester.RetesterAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/CrossCheckMonteCarloManipulation.jar`; 2 class declarations; SHA-256 `90124230d9193aca301b0bd01e80d7954664977d79795e7c211418995b409155`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/CrossCheckMonteCarloManipulation.md`; roadmap allocation `FEAT-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-MANIPULATION`.
- **Owner:** `app/plugins/cross_checks/CrossCheckMonteCarloManipulation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/CrossCheckMonteCarloManipulation.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/CrossCheckMonteCarloManipulation.jar" com.strategyquant.plugin.CrossCheck.impl.MonteCarloManipulation.MonteCarloManipulationServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/MonteCarloManipulationService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/FitnessFunction/MCManipulationFitnessService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/MonteCarloManipulationCtrl.js`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-MANIPULATION-MONTE-CARLO-MANIPULATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.MonteCarloManipulation.MonteCarloManipulationServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-MANIPULATION-MONTE-CARLO-MANIPULATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.CrossCheck.impl.MonteCarloManipulation.MonteCarloManipulationServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/CrossCheckMonteCarloRetest.jar`; 7 class declarations; SHA-256 `94fa7d1ee09ca5daa6031e4c3149b0cfb46aa36938df0e1d792423eccaa500ca`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/CrossCheckMonteCarloRetest.md`; roadmap allocation `FEAT-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-RETEST`.
- **Owner:** `app/plugins/cross_checks/CrossCheckMonteCarloRetest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/CrossCheckMonteCarloRetest.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/CrossCheckMonteCarloRetest.jar" com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest.MonteCarloRetestServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/MonteCarloRetestService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/FitnessFunction/MCRetestFitnessService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/MonteCarloRetestCtrl.js`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-RETEST-MONTE-CARLO-RETEST-SERVLET-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest.MonteCarloRetestServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-CROSS-CHECK-MONTE-CARLO-RETEST-MONTE-CARLO-RETEST-SERVLET-EXECUTE` → `com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest.MonteCarloRetestServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/CrossCheckOptProfileSysParamPermutation.jar`; 2 class declarations; SHA-256 `0989ee5ab3d156aee9c8be77d8cdbd095a99999af61753c8c134e5eba36b0b1a`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/CrossCheckOptProfileSysParamPermutation.md`; roadmap allocation `FEAT-ROBUSTNESS-CROSS-CHECK-OPT-PROFILE-SYS-PARAM-PERMUTATION`.
- **Owner:** `app/plugins/cross_checks/CrossCheckOptProfileSysParamPermutation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/CrossCheckOptProfileSysParamPermutation.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/CrossCheckOptProfileSysParamPermutation.jar" com.strategyquant.plugin.CrossCheck.impl.OptProfileSysParamPermutation.OptProfileSysParamPermutationServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/OptProfileSysParamPermutationService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/OptProfileSysParamPermutationCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/filtering.html`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-CROSS-CHECK-OPT-PROFILE-SYS-PARAM-PERMUTATION-OPT-PROFILE-SYS-PARAM-PERMUTATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.OptProfileSysParamPermutation.OptProfileSysParamPermutationServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-CROSS-CHECK-OPT-PROFILE-SYS-PARAM-PERMUTATION-OPT-PROFILE-SYS-PARAM-PERMUTATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.CrossCheck.impl.OptProfileSysParamPermutation.OptProfileSysParamPermutationServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/CrossCheckRetestOnAdditionalMarkets.jar`; 4 class declarations; SHA-256 `531c66823aef77bd1f04b344a9f5e1da9de842bbd17926d3844a91cfcc200e25`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/CrossCheckRetestOnAdditionalMarkets.md`; roadmap allocation `FEAT-ROBUSTNESS-CROSS-CHECK-RETEST-ON-ADDITIONAL-MARKETS`.
- **Owner:** `app/plugins/cross_checks/CrossCheckRetestOnAdditionalMarkets/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/CrossCheckRetestOnAdditionalMarkets.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/CrossCheckRetestOnAdditionalMarkets.jar" com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/RetestOnAdditionalMarketsService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/FitnessFunction/PortfolioFitnessService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/RetestOnAdditionalMarketsCtrl.js`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-CROSS-CHECK-RETEST-ON-ADDITIONAL-MARKETS-RETEST-ON-ADDITIONAL-MARKETS-SERVLET-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-CROSS-CHECK-RETEST-ON-ADDITIONAL-MARKETS-RETEST-ON-ADDITIONAL-MARKETS-SERVLET-EXECUTE` → `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets.RetestOnAdditionalMarketsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/CrossCheckRetestWithHigherPrecision.jar`; 4 class declarations; SHA-256 `bb44c67411968855e01e99a9e00a8245d686f223929c38d7ea95c75972aac388`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/CrossCheckRetestWithHigherPrecision.md`; roadmap allocation `FEAT-ROBUSTNESS-CROSS-CHECK-RETEST-WITH-HIGHER-PRECISION`.
- **Owner:** `app/plugins/cross_checks/CrossCheckRetestWithHigherPrecision/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/CrossCheckRetestWithHigherPrecision.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/CrossCheckRetestWithHigherPrecision.jar" com.strategyquant.plugin.CrossCheck.impl.RetestWithHigherPrecision.RetestWithHigherPrecisionServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/RetestWithHigherPrecisionService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/FitnessFunction/CCHigherPrecisionService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/RetestWithHigherPrecisionCtrl.js`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-CROSS-CHECK-RETEST-WITH-HIGHER-PRECISION-RETEST-WITH-HIGHER-PRECISION-SERVLET-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.RetestWithHigherPrecision.RetestWithHigherPrecisionServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-CROSS-CHECK-RETEST-WITH-HIGHER-PRECISION-RETEST-WITH-HIGHER-PRECISION-SERVLET-EXECUTE` → `com.strategyquant.plugin.CrossCheck.impl.RetestWithHigherPrecision.RetestWithHigherPrecisionServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/CrossCheckSequentialOptimization.jar`; 2 class declarations; SHA-256 `8afb96fe06d9378832563bab6068636ef807cf0c32122949191271c1a2548537`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/CrossCheckSequentialOptimization.md`; roadmap allocation `FEAT-ROBUSTNESS-CROSS-CHECK-SEQUENTIAL-OPTIMIZATION`.
- **Owner:** `app/plugins/cross_checks/CrossCheckSequentialOptimization/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/CrossCheckSequentialOptimization.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/CrossCheckSequentialOptimization.jar" com.strategyquant.plugin.CrossCheck.impl.SequentialOptimization.SequentialOptimization`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/SequentialOptimizationService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/SequentialOptimizationCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/filtering.html`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-CROSS-CHECK-SEQUENTIAL-OPTIMIZATION-SEQUENTIAL-OPTIMIZATION-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.SequentialOptimization.SequentialOptimization`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-CROSS-CHECK-SEQUENTIAL-OPTIMIZATION-SEQUENTIAL-OPTIMIZATION-GET-SHORT-NAME` → `com.strategyquant.plugin.CrossCheck.impl.SequentialOptimization.SequentialOptimization.getShortName`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-ROBUSTNESS-CROSS-CHECK-SEQUENTIAL-OPTIMIZATION-SEQUENTIAL-OPTIMIZATION-GET-SETTING-NAME` → `com.strategyquant.plugin.CrossCheck.impl.SequentialOptimization.SequentialOptimization.getSettingName`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/CrossCheckWalkForwardMatrix.jar`; 1 class declarations; SHA-256 `5022a6b0988f531f575ce94a1372c6f01274a9e619e60ea8392feac34ee1cee3`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/CrossCheckWalkForwardMatrix.md`; roadmap allocation `FEAT-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-MATRIX`.
- **Owner:** `app/plugins/cross_checks/CrossCheckWalkForwardMatrix/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/CrossCheckWalkForwardMatrix.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/CrossCheckWalkForwardMatrix.jar" com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/WalkForwardMatrixService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/WalkForwardMatrixCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/filtering.html`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-MATRIX-WALK-FORWARD-MATRIX-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-MATRIX-WALK-FORWARD-MATRIX-GET-SHORT-NAME` → `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix.getShortName`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-MATRIX-WALK-FORWARD-MATRIX-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix.WalkForwardMatrix.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/CrossCheckWalkForwardOptimization.jar`; 1 class declarations; SHA-256 `760b5d0b261914e97225bb7f58fe2f76bacf3f30cf7b13152e26635aa0cdf06e`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/CrossCheckWalkForwardOptimization.md`; roadmap allocation `FEAT-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-OPTIMIZATION`.
- **Owner:** `app/plugins/cross_checks/CrossCheckWalkForwardOptimization/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/CrossCheckWalkForwardOptimization.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/CrossCheckWalkForwardOptimization.jar" com.strategyquant.plugin.CrossCheck.impl.WalkForwardOptimization.WalkForwardOptimization`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/WalkForwardOptimizationService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/WalkForwardOptimizationCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/filtering.html`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-OPTIMIZATION-WALK-FORWARD-OPTIMIZATION-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.WalkForwardOptimization.WalkForwardOptimization`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-OPTIMIZATION-WALK-FORWARD-OPTIMIZATION-GET-SHORT-NAME` → `com.strategyquant.plugin.CrossCheck.impl.WalkForwardOptimization.WalkForwardOptimization.getShortName`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-ROBUSTNESS-CROSS-CHECK-WALK-FORWARD-OPTIMIZATION-WALK-FORWARD-OPTIMIZATION-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.CrossCheck.impl.WalkForwardOptimization.WalkForwardOptimization.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/CrossCheckWhatIf.jar`; 2 class declarations; SHA-256 `fbde3b92796f43ec8a077d20b2c8b6986653c72b9b2f925ddd5e37da509e1d73`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/CrossCheckWhatIf.md`; roadmap allocation `FEAT-ROBUSTNESS-CROSS-CHECK-WHAT-IF`.
- **Owner:** `app/plugins/cross_checks/CrossCheckWhatIf/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness check registration and execution, consuming P06/P10 algorithms; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/CrossCheckWhatIf.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/CrossCheckWhatIf.jar" com.strategyquant.plugin.CrossCheck.impl.WhatIf.WhatIfServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/WhatIfService.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/WhatIfCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/settings.html`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-CROSS-CHECK-WHAT-IF-WHAT-IF-SERVLET-CONTRACT` → `com.strategyquant.plugin.CrossCheck.impl.WhatIf.WhatIfServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-CROSS-CHECK-WHAT-IF-WHAT-IF-SERVLET-EXECUTE` → `com.strategyquant.plugin.CrossCheck.impl.WhatIf.WhatIfServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_cross_check_what_if.py --no-cov`; expect scenario composition, excluded trades and denominator/totals reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture scenario composition, excluded trades and denominator/totals reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-cross-check-what-if.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-CROSS-CHECK-WHAT-IF; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 11.11 FEAT-ROBUSTNESS-PROJECT-RETESTER - ProjectRetester.jar

## 1. Objective

- **Goal:** Implement Retester project capabilities with owned lifecycle.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectRetester/ProjectRetester.jar`; 0 class declarations; SHA-256 `df42d7e4a97ed687ce1e935533f337994ace0edf6db0955ef6b6c63852c68ba1`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ProjectRetester.md`; roadmap allocation `FEAT-ROBUSTNESS-PROJECT-RETESTER`.
- **Owner:** `app/workspace/Retester/ProjectRetester/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Retest/automatic-retest project/task configuration and results; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ProjectRetester/ProjectRetester.jar"`; inspect manifest/resources and target runtime requirements.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectRetester`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/web/RETESTER/layout/LayoutCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossCheckAcceptanceSettingsService.js`.
- **Existing UI connection:** Retester; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Retester/retesterClient.ts`; wire selected strategy/check configuration, retest jobs and actual robustness results.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Retester/ProjectRetester/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/ProjectRetester/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/ProjectRetester/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Retester/ProjectRetester/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_robustness_project_retester.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/robustness_project_retester.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Retester/retesterClient.ts`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterWorkspace.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Retester/RetesterProgress.tsx`
  - Display selected strategy/check configuration, retest jobs and actual robustness results from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-robustness-project-retester.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-retester-robustness-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement Retester project capabilities with owned lifecycle; verify project revisions, input/output contracts, failed transitions and cancellation.
- [ ] **Step 4:** `FR-ROBUSTNESS-PROJECT-RETESTER-RESOURCE-CONTRIBUTION` → `No compiled class entries; inspect registration/resources`: Verify the resource/manifest contract.
- [ ] **Step 5:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 7:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 8:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_project_retester.py --no-cov`; expect project revisions, input/output contracts, failed transitions and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture project revisions, input/output contracts, failed transitions and cancellation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-project-retester.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-PROJECT-RETESTER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 11.12 FEAT-ROBUSTNESS-RESULTS-ROBUSTNESS-TESTS - ResultsRobustnessTests.jar

## 1. Objective

- **Goal:** Implement authoritative RobustnessTests result projections/actions.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/ResultsRobustnessTests.jar`; 7 class declarations; SHA-256 `ca78fea41989e25555b43f2042b775befbe015807c5bc3de4b8416e3909bc0d9`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsRobustnessTests.md`; roadmap allocation `FEAT-ROBUSTNESS-RESULTS-ROBUSTNESS-TESTS`.
- **Owner:** `app/plugins/results/ResultsRobustnessTests/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness result projection and diagnostics; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/ResultsRobustnessTests.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/ResultsRobustnessTests.jar" com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/services/RTService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/directives/manageviews/ManageViewsService.js`; `SQX_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/RobustnessTestsResultsCtrl.js`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-RESULTS-ROBUSTNESS-TESTS-ROBUSTNESS-TESTS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-RESULTS-ROBUSTNESS-TESTS-ROBUSTNESS-TESTS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_results_robustness_tests.py --no-cov`; expect metric provenance, result identity, empty/error state and stored-value reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture metric provenance, result identity, empty/error state and stored-value reconciliation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-results-robustness-tests.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-RESULTS-ROBUSTNESS-TESTS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 11.13 FEAT-ROBUSTNESS-SETTINGS-AUTO-RETEST-DATA - SettingsAutoRetestData.jar

## 1. Objective

- **Goal:** Implement validated AutoRetestData settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/SettingsAutoRetestData.jar`; 1 class declarations; SHA-256 `387f7c85e9267a282607dbcffb8c880ddf0715b65577cd692e5656b8d6541f79`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsAutoRetestData.md`; roadmap allocation `FEAT-ROBUSTNESS-SETTINGS-AUTO-RETEST-DATA`.
- **Owner:** `app/workspace/Retester/SettingsAutoRetestData/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Retest/automatic-retest project/task configuration and results; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/SettingsAutoRetestData.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/SettingsAutoRetestData.jar" com.strategyquant.plugin.Settings.impl.AutoRetestData.CustomDataSettingsPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/AutoRetestDataService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/AutoRetestDataCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/views/autoRetestData.html`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-SETTINGS-AUTO-RETEST-DATA-CUSTOM-DATA-SETTINGS-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.AutoRetestData.CustomDataSettingsPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-SETTINGS-AUTO-RETEST-DATA-CUSTOM-DATA-SETTINGS-PLUGIN-GET-HANDLER` → `com.strategyquant.plugin.Settings.impl.AutoRetestData.CustomDataSettingsPlugin.getHandler`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-ROBUSTNESS-SETTINGS-AUTO-RETEST-DATA-CUSTOM-DATA-SETTINGS-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.AutoRetestData.CustomDataSettingsPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_settings_auto_retest_data.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-settings-auto-retest-data.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-SETTINGS-AUTO-RETEST-DATA; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 11.14 FEAT-ROBUSTNESS-SETTINGS-CROSS-CHECKS - SettingsCrossChecks.jar

## 1. Objective

- **Goal:** Implement validated CrossChecks settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/SettingsCrossChecks.jar`; 2 class declarations; SHA-256 `090d0d2f0a10bbbdb3b25602651594239b72033aa3e2588779040f6977faa51e`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsCrossChecks.md`; roadmap allocation `FEAT-ROBUSTNESS-SETTINGS-CROSS-CHECKS`.
- **Owner:** `app/plugins/cross_checks/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Robustness method selection and configuration; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/SettingsCrossChecks.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/SettingsCrossChecks.jar" com.strategyquant.plugin.Settings.impl.CrossChecks.CrossChecksServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossCheckAcceptanceSettingsService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossChecksService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossCheckAcceptanceSettingsCtrl.js`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-SETTINGS-CROSS-CHECKS-CROSS-CHECKS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.CrossChecks.CrossChecksServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-SETTINGS-CROSS-CHECKS-CROSS-CHECKS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.CrossChecks.CrossChecksServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-ROBUSTNESS-SETTINGS-CROSS-CHECKS-CROSS-CHECKS-SERVLET-LIST` → `com.strategyquant.plugin.Settings.impl.CrossChecks.CrossChecksServlet.list`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_settings_cross_checks.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-settings-cross-checks.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-SETTINGS-CROSS-CHECKS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 11.15 FEAT-ROBUSTNESS-SETTINGS-WHAT-TO-RETEST - SettingsWhatToRetest.jar

## 1. Objective

- **Goal:** Implement validated WhatToRetest settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/SettingsWhatToRetest.jar`; 1 class declarations; SHA-256 `76253f516c5db8bb347893ee33df1b1b40ac96f31fd520fe814cd827a79f8794`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsWhatToRetest.md`; roadmap allocation `FEAT-ROBUSTNESS-SETTINGS-WHAT-TO-RETEST`.
- **Owner:** `app/workspace/Retester/SettingsWhatToRetest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Retest/automatic-retest project/task configuration and results; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/SettingsWhatToRetest.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/SettingsWhatToRetest.jar" com.strategyquant.plugin.Settings.impl.WhatToRetest.SettingsWhatToRetestPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/SettingsWhatToRetestService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/SettingsWhatToRetestCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/whatToRetest.html`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-SETTINGS-WHAT-TO-RETEST-SETTINGS-WHAT-TO-RETEST-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.WhatToRetest.SettingsWhatToRetestPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-SETTINGS-WHAT-TO-RETEST-SETTINGS-WHAT-TO-RETEST-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.WhatToRetest.SettingsWhatToRetestPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-ROBUSTNESS-SETTINGS-WHAT-TO-RETEST-SETTINGS-WHAT-TO-RETEST-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.WhatToRetest.SettingsWhatToRetestPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_settings_what_to_retest.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-settings-what-to-retest.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-SETTINGS-WHAT-TO-RETEST; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 11.16 FEAT-ROBUSTNESS-TASK-AUTOMATIC-RETEST - TaskAutomaticRetest.jar

## 1. Objective

- **Goal:** Run owned retest chains against immutable strategy/run inputs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/TaskAutomaticRetest.jar`; 6 class declarations; SHA-256 `55b8703b11756d6bb17a27464d96d35e78f4f7513b299a63d4c11027bdda5db8`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Retester/TaskAutomaticRetest.md`; roadmap allocation `FEAT-ROBUSTNESS-TASK-AUTOMATIC-RETEST`.
- **Owner:** `app/workspace/Retester/TaskAutomaticRetest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Retest/automatic-retest project/task configuration and results; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/TaskAutomaticRetest.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/TaskAutomaticRetest.jar" com.strategyquant.plugin.Task.impl.AutomaticRetest.AutomaticRetestTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/TaskAutoRetestService.js`; `SQX_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/simpleSettings/SimpleAutoRetestSettingsCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/TaskAutomaticRetest/simpleSettings/simpleSettings.html`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-TASK-AUTOMATIC-RETEST-AUTOMATIC-RETEST-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.AutomaticRetest.AutomaticRetestTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-TASK-AUTOMATIC-RETEST-AUTOMATIC-RETEST-TASK-BEFORE-START` → `com.strategyquant.plugin.Task.impl.AutomaticRetest.AutomaticRetestTask.beforeStart`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-ROBUSTNESS-TASK-AUTOMATIC-RETEST-AUTOMATIC-RETEST-TASK-START` → `com.strategyquant.plugin.Task.impl.AutomaticRetest.AutomaticRetestTask.start`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_task_automatic_retest.py --no-cov`; expect child-job ownership, threshold evaluation, cancellation and result retention; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture child-job ownership, threshold evaluation, cancellation and result retention and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-task-automatic-retest.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-TASK-AUTOMATIC-RETEST; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 11.17 FEAT-ROBUSTNESS-TASK-RETEST - TaskRetest.jar

## 1. Objective

- **Goal:** Run owned retest chains against immutable strategy/run inputs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Run reproducible robustness checks and publish actual retest outcomes.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskRetest/TaskRetest.jar`; 4 class declarations; SHA-256 `1e1b514c469b07e5aa5a50895caaf1bdfe7323abe7817e810dfe22077eb50193`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Retester/TaskRetest.md`; roadmap allocation `FEAT-ROBUSTNESS-TASK-RETEST`.
- **Owner:** `app/workspace/Retester/TaskRetest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Retest/automatic-retest project/task configuration and results; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskRetest/TaskRetest.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskRetest/TaskRetest.jar" com.strategyquant.plugin.Task.impl.Retest.RetestTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/TaskRetest`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/TaskRetest/simpleSettings/SimpleRetestSettingsCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/TaskRetest/simpleSettings/simpleSettings.html`; `SQX_REFERENCE_ROOT/internal/plugins/TaskRetest/module.js`.
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
- [ ] **Step 4:** `FR-ROBUSTNESS-TASK-RETEST-RETEST-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.Retest.RetestTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-ROBUSTNESS-TASK-RETEST-RETEST-TASK-BEFORE-START` → `com.strategyquant.plugin.Task.impl.Retest.RetestTask.beforeStart`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-ROBUSTNESS-TASK-RETEST-RETEST-TASK-START` → `com.strategyquant.plugin.Task.impl.Retest.RetestTask.start`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind selected strategy/check configuration, retest jobs and actual robustness results to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_robustness_task_retest.py --no-cov`; expect child-job ownership, threshold evaluation, cancellation and result retention; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture child-job ownership, threshold evaluation, cancellation and result retention and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-robustness-task-retest.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for FEAT-ROBUSTNESS-TASK-RETEST; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 11.18 FEAT-UI-SETTINGS-AUTOMATIC-RETEST - SettingsAutomaticRetest resource contribution

## 1. Objective

- **Goal:** Qualify and connect SettingsAutomaticRetest without assuming a missing backend JAR.
- **Context / Problem Solved:** SettingsAutomaticRetest is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest/module.js`.
- **FR:** `FR-UI-SETTINGS-AUTOMATIC-RETEST-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/Retester/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest`; `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest/SettingsAutomaticRetestCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest/automaticRetest.html`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutomaticRetest/module.js`.
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

# 11.19 P11 integration — Run reproducible robustness checks and publish actual retest outcomes

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

- **UI donors:** `SQX_REFERENCE_ROOT/internal/web/RETESTER`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`. Inspect `SQX_REFERENCE_ROOT/internal/web/RETESTER/layout/LayoutCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossCheckAcceptanceSettingsService.js`.
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
- **Create:** `ui/tests/unit/backend-connections/task-11-19.test.ts`
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

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-11-19.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-retester-robustness-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Retester for 11.19; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
