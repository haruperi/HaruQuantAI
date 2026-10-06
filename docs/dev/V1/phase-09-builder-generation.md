# P09 — Builder: generation, genetic search, improvement and ranking

- **Source:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P05,P06,P07,P08.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 15 tasks; current archive allocations and resource/integration tasks only.

# 9.1 FEAT-BUILDER-COMMONS-MATH3-3-6-1 - commons-math3-3.6.1.jar

## 1. Objective

- **Goal:** Qualify numerical/random/genetic operators against inspected behavior.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/commons-math3-3.6.1.jar`; 1301 raw class entries; SHA-256 `1e56d7b058d28b65abd256b8458e3885b674c1d588fa43cd7d1cbb9c7ef2b308`.
- **Inspected reference:** [commons-math3-3.6.1.md](sqx/Libraries/commons-math3-3.6.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/commons-math3-3.6.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/commons-math3-3.6.1.jar" org.apache.commons.math3.Field`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/generation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Math, random generators and evolutionary search; audit numerical policy before adaptation; downstream P06,P10–P12,P15.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Builder through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/plugins/generation/randomness.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/generation/genetics.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/generation/search.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/generation/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_builder_commons_math3_3_6_1.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/builder_commons_math3_3_6_1.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify numerical/random/genetic operators against inspected behavior; verify seed behavior, distributions, selection operators and tolerance bounds.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-BUILDER-COMMONS-MATH3-3-6-1-FIELD-CONTRACT` → `org.apache.commons.math3.Field`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-BUILDER-COMMONS-MATH3-3-6-1-FIELD-GET-ZERO` → `org.apache.commons.math3.Field.getZero()Ljava/lang/Object;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-BUILDER-COMMONS-MATH3-3-6-1-FIELD-GET-ONE` → `org.apache.commons.math3.Field.getOne()Ljava/lang/Object;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_commons_math3_3_6_1.py --no-cov`; expect seed behavior, distributions, selection operators and tolerance bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture seed behavior, distributions, selection operators and tolerance bounds and visible failures.


# 9.2 FEAT-BUILDER-UNCOMMONS-MATHS - uncommons-maths-1.2.2a.jar

## 1. Objective

- **Goal:** Qualify numerical/random/genetic operators against inspected behavior.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/uncommons-maths-1.2.2a.jar`; 42 raw class entries; SHA-256 `eebe98f2f9d8cb5d2a030a1c3e52cfbb3ee0ff5b6a721a45e62092e3bbf83c5c`.
- **Inspected reference:** [uncommons-maths-1.2.2a.md](sqx/Libraries/uncommons-maths-1.2.2a.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/uncommons-maths-1.2.2a.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/uncommons-maths-1.2.2a.jar" org.uncommons.maths.Maths`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/generation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Math, random generators and evolutionary search; audit numerical policy before adaptation; downstream P06,P10–P12,P15.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Builder through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/generation/randomness.py` (proposed earlier in FEAT-BUILDER-COMMONS-MATH3-3-6-1)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/generation/genetics.py` (proposed earlier in FEAT-BUILDER-COMMONS-MATH3-3-6-1)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/generation/search.py` (proposed earlier in FEAT-BUILDER-COMMONS-MATH3-3-6-1)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/generation/README.md` (proposed earlier in FEAT-BUILDER-COMMONS-MATH3-3-6-1)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_builder_uncommons_maths.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/builder_uncommons_maths.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify numerical/random/genetic operators against inspected behavior; verify seed behavior, distributions, selection operators and tolerance bounds.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-BUILDER-UNCOMMONS-MATHS-MATHS-CONTRACT` → `org.uncommons.maths.Maths`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-BUILDER-UNCOMMONS-MATHS-MATHS-FACTORIAL` → `org.uncommons.maths.Maths.factorial(I)J`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-BUILDER-UNCOMMONS-MATHS-MATHS-BIG-FACTORIAL` → `org.uncommons.maths.Maths.bigFactorial(I)Ljava/math/BigInteger;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_uncommons_maths.py --no-cov`; expect seed behavior, distributions, selection operators and tolerance bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture seed behavior, distributions, selection operators and tolerance bounds and visible failures.


# 9.3 FEAT-BUILDER-WATCHMAKER-FRAMEWORK - watchmaker-framework-0.7.1.jar

## 1. Objective

- **Goal:** Qualify numerical/random/genetic operators against inspected behavior.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/watchmaker-framework-0.7.1.jar`; 74 raw class entries; SHA-256 `f4d1ac73aa475bc403b6a6e8d5bce37f4d69a215e2deaa65ecc57d2e13368fb8`.
- **Inspected reference:** [watchmaker-framework-0.7.1.md](sqx/Libraries/watchmaker-framework-0.7.1.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/watchmaker-framework-0.7.1.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/watchmaker-framework-0.7.1.jar" org.uncommons.util.concurrent.ConfigurableThreadFactory`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/generation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Math, random generators and evolutionary search; audit numerical policy before adaptation; downstream P06,P10–P12,P15.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Builder through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/generation/randomness.py` (proposed earlier in FEAT-BUILDER-COMMONS-MATH3-3-6-1)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/generation/genetics.py` (proposed earlier in FEAT-BUILDER-COMMONS-MATH3-3-6-1)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/generation/search.py` (proposed earlier in FEAT-BUILDER-COMMONS-MATH3-3-6-1)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/generation/README.md` (proposed earlier in FEAT-BUILDER-COMMONS-MATH3-3-6-1)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_builder_watchmaker_framework.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/builder_watchmaker_framework.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify numerical/random/genetic operators against inspected behavior; verify seed behavior, distributions, selection operators and tolerance bounds.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-BUILDER-WATCHMAKER-FRAMEWORK-CONFIGURABLE-THREAD-FACTORY-CONTRACT` → `org.uncommons.util.concurrent.ConfigurableThreadFactory`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-BUILDER-WATCHMAKER-FRAMEWORK-CONFIGURABLE-THREAD-FACTORY-NEW-THREAD` → `org.uncommons.util.concurrent.ConfigurableThreadFactory.newThread(Ljava/lang/Runnable;)Ljava/lang/Thread;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_watchmaker_framework.py --no-cov`; expect seed behavior, distributions, selection operators and tolerance bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture seed behavior, distributions, selection operators and tolerance bounds and visible failures.


# 9.4 FEAT-BUILDER-APP-BUILDER - AppBuilder.jar

## 1. Objective

- **Goal:** Mount the Builder workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder/AppBuilder.jar`; 1 raw class entries; SHA-256 `69c29c561d0d82d4f8841e9fa94fac0ec9a0f6797b8c9e209f9985318c04ac0f`.
- **Inspected reference:** [AppBuilder.md](sqx/Builder/AppBuilder.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder/AppBuilder.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder/AppBuilder.jar" com.strategyquant.plugin.App.impl.Builder.BuilderAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_145_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder/module.js`.
- **Existing UI connection:** Builder; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/builderClient.ts`; wire actual strategy/settings submission, build job controls, progress and persisted candidates.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Builder/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Builder/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Builder/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Builder/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_builder_app_builder.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/builder_app_builder.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ProgressDashboard.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/EnginePanel.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ResultsColumn.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-builder-app-builder.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-builder-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the Builder workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-BUILDER-APP-BUILDER-BUILDER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.Builder.BuilderAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-BUILDER-APP-BUILDER-BUILDER-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.Builder.BuilderAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-BUILDER-APP-BUILDER-BUILDER-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.Builder.BuilderAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_app_builder.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-builder-app-builder.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-builder-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Builder for FEAT-BUILDER-APP-BUILDER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 9.5 FEAT-BUILDER-DASHBOARD-RESULTS - DashboardResults.jar

## 1. Objective

- **Goal:** Deliver the consumed DashboardResults capability in workspace/Builder.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DashboardResults/DashboardResults.jar`; 2 raw class entries; SHA-256 `b2d127ddb067181677a79498cc6fb77f14b43397fe4b044d0626fb8f636ddde0`.
- **Inspected reference:** [DashboardResults.md](sqx/Results/DashboardResults.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/DashboardResults/DashboardResults.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/DashboardResults/DashboardResults.jar" com.strategyquant.plugin.Dashboard.impl.Results.DashboardResultsServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Build progress/result projections; emit actual run state; downstream P10–P15.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DashboardResults`; `SQX_145_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DashboardResults/DashboardResultsService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DashboardResults/DashboardResultsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DashboardResults/directives/ResultPanelCtrl.js`.
- **Existing UI connection:** Builder; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/builderClient.ts`; wire actual strategy/settings submission, build job controls, progress and persisted candidates.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Builder/progress.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Builder/events.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/README.md` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_builder_dashboard_results.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/builder_dashboard_results.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ProgressDashboard.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/EnginePanel.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ResultsColumn.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-builder-dashboard-results.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-builder-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Deliver the consumed DashboardResults capability in workspace/Builder; verify fixed-seed build, allowed blocks, fitness ordering and stop-rule boundaries.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-BUILDER-DASHBOARD-RESULTS-DASHBOARD-RESULTS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Dashboard.impl.Results.DashboardResultsServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-BUILDER-DASHBOARD-RESULTS-DASHBOARD-RESULTS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Dashboard.impl.Results.DashboardResultsServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-BUILDER-DASHBOARD-RESULTS-DASHBOARD-RESULTS-SERVLET-ON-PRINT` → `com.strategyquant.plugin.Dashboard.impl.Results.DashboardResultsServlet.onPrint(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_dashboard_results.py --no-cov`; expect fixed-seed build, allowed blocks, fitness ordering and stop-rule boundaries; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture fixed-seed build, allowed blocks, fitness ordering and stop-rule boundaries and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-builder-dashboard-results.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-builder-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Builder for FEAT-BUILDER-DASHBOARD-RESULTS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 9.6 FEAT-BUILDER-ENGINE-PANEL - EnginePanel.jar

## 1. Objective

- **Goal:** Deliver the consumed EnginePanel capability in workspace/Builder.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel/EnginePanel.jar`; 4 raw class entries; SHA-256 `41c3a4e9037ddde57eefcafb911db5d3fb9626d76c7adead17217bceaa7fdeeb`.
- **Inspected reference:** [EnginePanel.md](sqx/GridControl/EnginePanel.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel/EnginePanel.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel/EnginePanel.jar" com.strategyquant.plugin.Engine.impl.Panel.EngineServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Build progress/result projections; emit actual run state; downstream P10–P15.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel`; `SQX_145_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel/EngineService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel/directives/fitnessEvolution/FitnessEvolutionService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel/EngineCtrl.js`.
- **Existing UI connection:** Builder; exact retained source-map `ui/app/plugins/project/EnginePanel/source-map.json`. Target `ui/app/plugins/project/EnginePanel/EngineCtrl.ts`; wire actual strategy/settings submission, build job controls, progress and persisted candidates.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Builder/progress.py` (proposed earlier in FEAT-BUILDER-DASHBOARD-RESULTS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/events.py` (proposed earlier in FEAT-BUILDER-DASHBOARD-RESULTS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/README.md` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_builder_engine_panel.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/builder_engine_panel.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/EnginePanel/EngineCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/EnginePanel/engine.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/EnginePanel/projectConfigHelpPopup.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ProgressDashboard.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/EnginePanel.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ResultsColumn.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/EnginePanel/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-builder-engine-panel.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-builder-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Deliver the consumed EnginePanel capability in workspace/Builder; verify fixed-seed build, allowed blocks, fitness ordering and stop-rule boundaries.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-BUILDER-ENGINE-PANEL-ENGINE-SERVLET-CONTRACT` → `com.strategyquant.plugin.Engine.impl.Panel.EngineServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-BUILDER-ENGINE-PANEL-ENGINE-SERVLET-EXECUTE` → `com.strategyquant.plugin.Engine.impl.Panel.EngineServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-BUILDER-ENGINE-PANEL-ENGINE-SERVLET-ON-GET-FITNESS-EVOLUTION-STATS` → `com.strategyquant.plugin.Engine.impl.Panel.EngineServlet.onGetFitnessEvolutionStats(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_engine_panel.py --no-cov`; expect fixed-seed build, allowed blocks, fitness ordering and stop-rule boundaries; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture fixed-seed build, allowed blocks, fitness ordering and stop-rule boundaries and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-builder-engine-panel.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-builder-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Builder for FEAT-BUILDER-ENGINE-PANEL; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 9.7 FEAT-BUILDER-FITNESS-METHOD-STRATEGY-RESULT - FitnessMethodStrategyResult.jar

## 1. Objective

- **Goal:** Compute the named fitness objective from qualified result inputs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResult.jar`; 4 raw class entries; SHA-256 `d2d109daf04075fe48e02fa888f53f938710744f1ab628fb7f011ea747cb0b0f`.
- **Inspected reference:** [FitnessMethodStrategyResult.md](sqx/Shared/FitnessMethodStrategyResult.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResult.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResult.jar" com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy fitness and build command adapter; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult`; `SQX_145_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResultService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResultCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/fitnessMethodStrategyResult.html`.
- **Existing UI connection:** Builder; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/builderClient.ts`; wire actual strategy/settings submission, build job controls, progress and persisted candidates.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Builder/fitness.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/routes.py` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/README.md` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_builder_fitness_method_strategy_result.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/builder_fitness_method_strategy_result.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ProgressDashboard.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/EnginePanel.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ResultsColumn.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-builder-fitness-method-strategy-result.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-builder-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Compute the named fitness objective from qualified result inputs; verify objective direction, ties, missing metrics and nonfinite scores.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-BUILDER-FITNESS-METHOD-STRATEGY-RESULT-FITNESS-METHOD-STRATEGY-RESULT-SERVLET-CONTRACT` → `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-BUILDER-FITNESS-METHOD-STRATEGY-RESULT-FITNESS-METHOD-STRATEGY-RESULT-SERVLET-EXECUTE` → `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-BUILDER-FITNESS-METHOD-STRATEGY-RESULT-FITNESS-METHOD-STRATEGY-RESULT-SERVLET-ON-LIST` → `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet.onList()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_fitness_method_strategy_result.py --no-cov`; expect objective direction, ties, missing metrics and nonfinite scores; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture objective direction, ties, missing metrics and nonfinite scores and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-builder-fitness-method-strategy-result.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-builder-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Builder for FEAT-BUILDER-FITNESS-METHOD-STRATEGY-RESULT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 9.8 FEAT-BUILDER-SERVLET-BUILDER - ServletBuilder.jar

## 1. Objective

- **Goal:** Configure and execute build generation/improvement against owned jobs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletBuilder/ServletBuilder.jar`; 2 raw class entries; SHA-256 `75b59bfe39e275e8531ada6365a6b16faf5add62688e237a71433e27eddd6b03`.
- **Inspected reference:** [ServletBuilder.md](sqx/Builder/ServletBuilder.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletBuilder/ServletBuilder.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletBuilder/ServletBuilder.jar" com.strategyquant.plugin.Servlet.impl.Builder.BuilderServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy fitness and build command adapter; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletBuilder`; `SQX_145_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ServletBuilder/module.js`.
- **Existing UI connection:** Builder; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/builderClient.ts`; wire actual strategy/settings submission, build job controls, progress and persisted candidates.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Builder/fitness.py` (proposed earlier in FEAT-BUILDER-FITNESS-METHOD-STRATEGY-RESULT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/routes.py` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/README.md` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_builder_servlet_builder.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/builder_servlet_builder.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ProgressDashboard.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/EnginePanel.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ResultsColumn.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-builder-servlet-builder.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-builder-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Configure and execute build generation/improvement against owned jobs; verify block constraints, preserved strategy parts, stop rules and repeatability.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-BUILDER-SERVLET-BUILDER-BUILDER-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.Builder.BuilderServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-BUILDER-SERVLET-BUILDER-BUILDER-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.Builder.BuilderServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-BUILDER-SERVLET-BUILDER-BUILDER-SERVLET-ON-GET-BUILD-TEMPLATE` → `com.strategyquant.plugin.Servlet.impl.Builder.BuilderServlet.onGetBuildTemplate(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_servlet_builder.py --no-cov`; expect block constraints, preserved strategy parts, stop rules and repeatability; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture block constraints, preserved strategy parts, stop rules and repeatability and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-builder-servlet-builder.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-builder-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Builder for FEAT-BUILDER-SERVLET-BUILDER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 9.9 FEAT-BUILDER-SETTINGS-PARTS-TO-IMPROVE - SettingsPartsToImprove.jar

## 1. Objective

- **Goal:** Configure and execute build generation/improvement against owned jobs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/SettingsPartsToImprove.jar`; 1 raw class entries; SHA-256 `7b34d7fb9d20b96ae581200d4f6e950f71ea22bd35fe8448b40f6a876095d6d5`.
- **Inspected reference:** [SettingsPartsToImprove.md](sqx/Shared/SettingsPartsToImprove.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/SettingsPartsToImprove.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/SettingsPartsToImprove.jar" com.strategyquant.plugin.Settings.impl.PartsToImprove.PartsToImproveSettingsPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Build/improve/search configuration and task execution; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove`; `SQX_145_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/PartsToImproveService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/PartsToImproveCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/views/partsToImprove.html`.
- **Existing UI connection:** Builder; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/builderClient.ts`; wire actual strategy/settings submission, build job controls, progress and persisted candidates.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Builder/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Builder/settings.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/contracts.py` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/README.md` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_builder_settings_parts_to_improve.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/builder_settings_parts_to_improve.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ProgressDashboard.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/EnginePanel.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ResultsColumn.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-builder-settings-parts-to-improve.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-builder-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Configure and execute build generation/improvement against owned jobs; verify block constraints, preserved strategy parts, stop rules and repeatability.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-BUILDER-SETTINGS-PARTS-TO-IMPROVE-PARTS-TO-IMPROVE-SETTINGS-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.PartsToImprove.PartsToImproveSettingsPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-BUILDER-SETTINGS-PARTS-TO-IMPROVE-PARTS-TO-IMPROVE-SETTINGS-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.PartsToImprove.PartsToImproveSettingsPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-BUILDER-SETTINGS-PARTS-TO-IMPROVE-PARTS-TO-IMPROVE-SETTINGS-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.PartsToImprove.PartsToImproveSettingsPlugin.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_settings_parts_to_improve.py --no-cov`; expect block constraints, preserved strategy parts, stop rules and repeatability; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture block constraints, preserved strategy parts, stop rules and repeatability and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-builder-settings-parts-to-improve.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-builder-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Builder for FEAT-BUILDER-SETTINGS-PARTS-TO-IMPROVE; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 9.10 FEAT-BUILDER-SETTINGS-RANKINGS - SettingsRankings.jar

## 1. Objective

- **Goal:** Implement validated Rankings settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsRankings/SettingsRankings.jar`; 2 raw class entries; SHA-256 `abbe6504b602945607a4f412bf247fe5710481d7726056398957ac6f5886da06`.
- **Inspected reference:** [SettingsRankings.md](sqx/Shared/SettingsRankings.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsRankings/SettingsRankings.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsRankings/SettingsRankings.jar" com.strategyquant.plugin.Settings.impl.Rankings.SettingsRankingsServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Build/improve/search configuration and task execution; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsRankings`; `SQX_145_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsRankings/RankingService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsRankings/FitnessFunction/FitnessFunctionService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsRankings/RankingCtrl.js`.
- **Existing UI connection:** Builder; exact retained source-map `ui/app/plugins/project/SettingsRankings/source-map.json`. Target `ui/app/plugins/project/SettingsRankings/RankingCtrl.ts`; wire actual strategy/settings submission, build job controls, progress and persisted candidates.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Builder/service.py` (proposed earlier in FEAT-BUILDER-SETTINGS-PARTS-TO-IMPROVE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/settings.py` (proposed earlier in FEAT-BUILDER-SETTINGS-PARTS-TO-IMPROVE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/contracts.py` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/README.md` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_builder_settings_rankings.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/builder_settings_rankings.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/SettingsRankings/RankingCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/SettingsRankings/FitnessFunction/FitnessFunctionCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/SettingsRankings/FitnessFunction/fitnessFunction.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ProgressDashboard.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/EnginePanel.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ResultsColumn.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/SettingsRankings/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-builder-settings-rankings.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-builder-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated Rankings settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-BUILDER-SETTINGS-RANKINGS-SETTINGS-RANKINGS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Rankings.SettingsRankingsServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-BUILDER-SETTINGS-RANKINGS-SETTINGS-RANKINGS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.Rankings.SettingsRankingsServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-BUILDER-SETTINGS-RANKINGS-SETTINGS-RANKINGS-SERVLET-GET-FITNESS-METHODS` → `com.strategyquant.plugin.Settings.impl.Rankings.SettingsRankingsServlet.getFitnessMethods()Lorg/json/JSONArray;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_settings_rankings.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-builder-settings-rankings.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-builder-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Builder for FEAT-BUILDER-SETTINGS-RANKINGS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 9.11 FEAT-BUILDER-SETTINGS-WHAT-TO-BUILD - SettingsWhatToBuild.jar

## 1. Objective

- **Goal:** Configure and execute build generation/improvement against owned jobs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/SettingsWhatToBuild.jar`; 2 raw class entries; SHA-256 `b836d5729770602d51b99f1b73edeaaa370518e003fc45bd54fcc4cfd8217518`.
- **Inspected reference:** [SettingsWhatToBuild.md](sqx/Shared/SettingsWhatToBuild.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/SettingsWhatToBuild.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/SettingsWhatToBuild.jar" com.strategyquant.plugin.Settings.impl.WhatToBuild.WhatToBuildServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Build/improve/search configuration and task execution; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild`; `SQX_145_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/WhatToBuildService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/views/settings/buildMode/BuildModeService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/views/settings/conditionsAndPeriods/ConditionsAndPeriodsService.js`.
- **Existing UI connection:** Builder; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/builderClient.ts`; wire actual strategy/settings submission, build job controls, progress and persisted candidates.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Builder/service.py` (proposed earlier in FEAT-BUILDER-SETTINGS-PARTS-TO-IMPROVE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/settings.py` (proposed earlier in FEAT-BUILDER-SETTINGS-PARTS-TO-IMPROVE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/contracts.py` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/README.md` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_builder_settings_what_to_build.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/builder_settings_what_to_build.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ProgressDashboard.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/EnginePanel.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ResultsColumn.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-builder-settings-what-to-build.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-builder-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Configure and execute build generation/improvement against owned jobs; verify block constraints, preserved strategy parts, stop rules and repeatability.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-BUILDER-SETTINGS-WHAT-TO-BUILD-WHAT-TO-BUILD-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.WhatToBuild.WhatToBuildServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-BUILDER-SETTINGS-WHAT-TO-BUILD-WHAT-TO-BUILD-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.WhatToBuild.WhatToBuildServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-BUILDER-SETTINGS-WHAT-TO-BUILD-WHAT-TO-BUILD-SERVLET-ON-LIST-FILES` → `com.strategyquant.plugin.Settings.impl.WhatToBuild.WhatToBuildServlet.onListFiles()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_settings_what_to_build.py --no-cov`; expect block constraints, preserved strategy parts, stop rules and repeatability; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture block constraints, preserved strategy parts, stop rules and repeatability and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-builder-settings-what-to-build.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-builder-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Builder for FEAT-BUILDER-SETTINGS-WHAT-TO-BUILD; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 9.12 FEAT-BUILDER-TASK-BUILD - TaskBuild.jar

## 1. Objective

- **Goal:** Configure and execute build generation/improvement against owned jobs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskBuild/TaskBuild.jar`; 11 raw class entries; SHA-256 `38d7920fafa619f5521a5d147f2f57d2bc265f251aae02d6076bd972c49643d4`.
- **Inspected reference:** [TaskBuild.md](sqx/Builder/TaskBuild.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskBuild/TaskBuild.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskBuild/TaskBuild.jar" com.strategyquant.plugin.Task.impl.Build.BuildTask`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Build/improve/search configuration and task execution; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskBuild`; `SQX_145_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskBuild/BuildTaskService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskBuild/indicatorsCalibration/IndicatorsCalibrationPopupCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskBuild/simpleSettings/SimpleBuildSettingsCtrl.js`.
- **Existing UI connection:** Builder; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/builderClient.ts`; wire actual strategy/settings submission, build job controls, progress and persisted candidates.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Builder/service.py` (proposed earlier in FEAT-BUILDER-SETTINGS-PARTS-TO-IMPROVE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/settings.py` (proposed earlier in FEAT-BUILDER-SETTINGS-PARTS-TO-IMPROVE)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/contracts.py` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/workspace/Builder/README.md` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_builder_task_build.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/builder_task_build.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ProgressDashboard.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/EnginePanel.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ResultsColumn.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-builder-task-build.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-builder-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Configure and execute build generation/improvement against owned jobs; verify block constraints, preserved strategy parts, stop rules and repeatability.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-BUILDER-TASK-BUILD-BUILD-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.Build.BuildTask`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-BUILDER-TASK-BUILD-BUILD-TASK-INIT-PARAMS` → `com.strategyquant.plugin.Task.impl.Build.BuildTask.initParams()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-BUILDER-TASK-BUILD-BUILD-TASK-BEFORE-START` → `com.strategyquant.plugin.Task.impl.Build.BuildTask.beforeStart()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_task_build.py --no-cov`; expect block constraints, preserved strategy parts, stop rules and repeatability; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture block constraints, preserved strategy parts, stop rules and repeatability and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-builder-task-build.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-builder-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Builder for FEAT-BUILDER-TASK-BUILD; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 9.13 FEAT-UI-DASHBOARD-PANEL - DashboardPanel resource contribution

## 1. Objective

- **Goal:** Qualify and connect DashboardPanel without assuming a missing backend JAR.
- **Context / Problem Solved:** DashboardPanel is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DashboardPanel`; narrow source: `SQX_145_REFERENCE_ROOT/internal/plugins/DashboardPanel/module.js`.
- **FR:** `FR-UI-DASHBOARD-PANEL-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/Builder/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DashboardPanel`; `SQX_145_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DashboardPanel/DashboardCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DashboardPanel/dashboard.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/DashboardPanel/module.js`.
- **Existing UI connection:** Builder; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/builderClient.ts`; wire actual strategy/settings submission, build job controls, progress and persisted candidates.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/Builder/resource_contributions.py`
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/workspace/Builder/README.md` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_dashboard_panel.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/Builder/BuilderWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ProgressDashboard.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/EnginePanel.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ResultsColumn.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-dashboard-panel.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-builder-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-DASHBOARD-PANEL-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_dashboard_panel.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Start a bounded fixed-seed build; pause/resume/stop; inspect real rankings; rerun and compare the qualified result sequence. Inspect the DashboardPanel contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-dashboard-panel.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-builder-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Builder for FEAT-UI-DASHBOARD-PANEL; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 9.14 FEAT-UI-SETTINGS-GENETIC-OPTIONS - SettingsGeneticOptions resource contribution

## 1. Objective

- **Goal:** Qualify and connect SettingsGeneticOptions without assuming a missing backend JAR.
- **Context / Problem Solved:** SettingsGeneticOptions is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions`; narrow source: `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/module.js`.
- **FR:** `FR-UI-SETTINGS-GENETIC-OPTIONS-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/Builder/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions`; `SQX_145_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/SettingsGeneticOptionsService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/SettingsGeneticOptionsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/views/geneticOptions.html`.
- **Existing UI connection:** Builder; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/builderClient.ts`; wire actual strategy/settings submission, build job controls, progress and persisted candidates.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Builder/resource_contributions.py` (proposed earlier in FEAT-UI-DASHBOARD-PANEL)
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/workspace/Builder/README.md` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_settings_genetic_options.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/Builder/BuilderWorkspace.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ProgressDashboard.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/EnginePanel.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ResultsColumn.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-settings-genetic-options.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-builder-generation-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-SETTINGS-GENETIC-OPTIONS-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_settings_genetic_options.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Start a bounded fixed-seed build; pause/resume/stop; inspect real rankings; rerun and compare the qualified result sequence. Inspect the SettingsGeneticOptions contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-settings-genetic-options.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-builder-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Builder for FEAT-UI-SETTINGS-GENETIC-OPTIONS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 9.15 P09 integration — Generate and improve executable strategies with real build progress and ranking

## 1. Objective

- **Goal:** Generate and improve executable strategies with real build progress and ranking.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`, P09; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/Builder/BuilderWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/Builder/fullSettings.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/BUILDER/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppBuilder/module.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/EnginePanel/EngineService.js`.
- **Existing UI connection:** Builder; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/builderClient.ts`; wire actual strategy/settings submission, build job controls, progress and persisted candidates.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/Builder/workspace.py` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/Builder/progress.py` (proposed earlier in FEAT-BUILDER-DASHBOARD-RESULTS)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/Builder/fitness.py` (proposed earlier in FEAT-BUILDER-FITNESS-METHOD-STRATEGY-RESULT)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/generation/randomness.py` (proposed earlier in FEAT-BUILDER-COMMONS-MATH3-3-6-1)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/generation/genetics.py` (proposed earlier in FEAT-BUILDER-COMMONS-MATH3-3-6-1)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/generation/search.py` (proposed earlier in FEAT-BUILDER-COMMONS-MATH3-3-6-1)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/generation/improvement.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/ranking/fitness.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/ranking/filters.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/Builder/BuilderWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/workspace/Builder/README.md` (proposed earlier in FEAT-BUILDER-APP-BUILDER)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_builder_generation_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-builder-generation-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/ProgressDashboard.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/EnginePanel.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/ResultsColumn.tsx`
  - Display actual strategy/settings submission, build job controls, progress and persisted candidates from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/task-9-15.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify seed handling, grammar constraints, genetic evolution, fitness and stopping rules.
- [ ] **Step 3:** Implement generation/improvement/islands using the qualified evaluator and simulator.
- [ ] **Step 4:** Publish job lifecycle, best results and rankings to Builder; persist reproducible settings.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_builder_generation_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/Builder/fullSettings.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-builder-generation-backend.spec.ts`. Assert fixed-seed build, allowed blocks, fitness ordering and stop-rule boundaries; reject impossible constraints, duplicate candidates, invalid fitness and cancellation.
- **Manual / Browser Verification:** Start a bounded fixed-seed build; pause/resume/stop; inspect real rankings; rerun and compare the qualified result sequence.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-9-15.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-builder-generation-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Builder for 9.15; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
