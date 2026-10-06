# P09 — Builder: generation, genetic search, improvement and ranking

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P05,P06,P07,P08.
- **Scope:** 12 JAR feature tasks, 2 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.

# 9.1 FEAT-BUILDER-COMMONS-MATH3-3-6-1 - commons-math3-3.6.1.jar

## 1. Objective

- **Goal:** Qualify numerical/random/genetic operators against inspected behavior.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/commons-math3-3.6.1.jar`; 1301 class declarations; SHA-256 `1e56d7b058d28b65abd256b8458e3885b674c1d588fa43cd7d1cbb9c7ef2b308`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-BUILDER-COMMONS-MATH3-3-6-1`.
- **Owner:** `app/plugins/generation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Math, random generators and evolutionary search; audit numerical policy before adaptation; downstream P06,P10–P12,P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/commons-math3-3.6.1.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/commons-math3-3.6.1.jar" org.apache.commons.math3.Field`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
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
- [ ] **Step 4:** `FR-BUILDER-COMMONS-MATH3-3-6-1-FIELD-CONTRACT` → `org.apache.commons.math3.Field`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-BUILDER-COMMONS-MATH3-3-6-1-FIELD-GET-ZERO` → `org.apache.commons.math3.Field.getZero`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-BUILDER-COMMONS-MATH3-3-6-1-FIELD-GET-ONE` → `org.apache.commons.math3.Field.getOne`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_commons_math3_3_6_1.py --no-cov`; expect seed behavior, distributions, selection operators and tolerance bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture seed behavior, distributions, selection operators and tolerance bounds and visible failures.

# 9.2 FEAT-BUILDER-UNCOMMONS-MATHS - uncommons-maths.jar

## 1. Objective

- **Goal:** Qualify numerical/random/genetic operators against inspected behavior.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/uncommons-maths.jar`; 35 class declarations; SHA-256 `b013f2741f7f6a4ea21be0bb511f54503bac321659b6878bafab5d14db0e11f3`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-BUILDER-UNCOMMONS-MATHS`.
- **Owner:** `app/plugins/generation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Math, random generators and evolutionary search; audit numerical policy before adaptation; downstream P06,P10–P12,P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/uncommons-maths.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/uncommons-maths.jar" org.uncommons.maths.Maths`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
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
- [ ] **Step 4:** `FR-BUILDER-UNCOMMONS-MATHS-MATHS-CONTRACT` → `org.uncommons.maths.Maths`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-BUILDER-UNCOMMONS-MATHS-MATHS-FACTORIAL` → `org.uncommons.maths.Maths.factorial`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-BUILDER-UNCOMMONS-MATHS-MATHS-BIG-FACTORIAL` → `org.uncommons.maths.Maths.bigFactorial`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_uncommons_maths.py --no-cov`; expect seed behavior, distributions, selection operators and tolerance bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture seed behavior, distributions, selection operators and tolerance bounds and visible failures.

# 9.3 FEAT-BUILDER-WATCHMAKER-FRAMEWORK - watchmaker-framework.jar

## 1. Objective

- **Goal:** Qualify numerical/random/genetic operators against inspected behavior.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/watchmaker-framework.jar`; 74 class declarations; SHA-256 `3408409623497b46fd70eb6acab62824c9961f3db36b2f79286514f078aff07e`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-BUILDER-WATCHMAKER-FRAMEWORK`.
- **Owner:** `app/plugins/generation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Math, random generators and evolutionary search; audit numerical policy before adaptation; downstream P06,P10–P12,P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/watchmaker-framework.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/watchmaker-framework.jar" org.uncommons.util.concurrent.ConfigurableThreadFactory`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
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
- [ ] **Step 4:** `FR-BUILDER-WATCHMAKER-FRAMEWORK-CONFIGURABLE-THREAD-FACTORY-CONTRACT` → `org.uncommons.util.concurrent.ConfigurableThreadFactory`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-BUILDER-WATCHMAKER-FRAMEWORK-CONFIGURABLE-THREAD-FACTORY-NEW-THREAD` → `org.uncommons.util.concurrent.ConfigurableThreadFactory.newThread`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_builder_watchmaker_framework.py --no-cov`; expect seed behavior, distributions, selection operators and tolerance bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture seed behavior, distributions, selection operators and tolerance bounds and visible failures.

# 9.4 FEAT-BUILDER-APP-BUILDER - AppBuilder.jar

## 1. Objective

- **Goal:** Mount the Builder workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Generate and improve executable strategies with real build progress and ranking.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder/AppBuilder.jar`; 1 class declarations; SHA-256 `43e6ae1fcdc978c8c25b7fec1940c1c903fd3d711d08e3afa5b4d206c8000d4b`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Builder/AppBuilder.md`; roadmap allocation `FEAT-BUILDER-APP-BUILDER`.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppBuilder/AppBuilder.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppBuilder/AppBuilder.jar" com.strategyquant.plugin.App.impl.Builder.BuilderAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder/module.js`.
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
- [ ] **Step 4:** `FR-BUILDER-APP-BUILDER-BUILDER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.Builder.BuilderAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-BUILDER-APP-BUILDER-BUILDER-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.Builder.BuilderAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-BUILDER-APP-BUILDER-BUILDER-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.Builder.BuilderAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DashboardResults/DashboardResults.jar`; 2 class declarations; SHA-256 `1025b2652a1da807b8e1c707c9001d9200167c6adb02a52e0106b59c0ef3fd88`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/DashboardResults.md`; roadmap allocation `FEAT-BUILDER-DASHBOARD-RESULTS`.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Build progress/result projections; emit actual run state; downstream P10–P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/DashboardResults/DashboardResults.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/DashboardResults/DashboardResults.jar" com.strategyquant.plugin.Dashboard.impl.Results.DashboardResultsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DashboardResults`; `SQX_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DashboardResults/DashboardResultsService.js`; `SQX_REFERENCE_ROOT/internal/plugins/DashboardResults/DashboardResultsCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/DashboardResults/directives/ResultPanelCtrl.js`.
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
- [ ] **Step 4:** `FR-BUILDER-DASHBOARD-RESULTS-DASHBOARD-RESULTS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Dashboard.impl.Results.DashboardResultsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-BUILDER-DASHBOARD-RESULTS-DASHBOARD-RESULTS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Dashboard.impl.Results.DashboardResultsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel/EnginePanel.jar`; 4 class declarations; SHA-256 `e10c17face0f953e75b3e36bdbc23c81941592665b0c7329eb9494bb1f2f45e1`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/GridControl/EnginePanel.md`; roadmap allocation `FEAT-BUILDER-ENGINE-PANEL`.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Build progress/result projections; emit actual run state; downstream P10–P15.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/EnginePanel/EnginePanel.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/EnginePanel/EnginePanel.jar" com.strategyquant.plugin.Engine.impl.Panel.EngineServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel`; `SQX_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel/EngineService.js`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel/directives/fitnessEvolution/FitnessEvolutionService.js`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel/EngineCtrl.js`.
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
- [ ] **Step 4:** `FR-BUILDER-ENGINE-PANEL-ENGINE-SERVLET-CONTRACT` → `com.strategyquant.plugin.Engine.impl.Panel.EngineServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-BUILDER-ENGINE-PANEL-ENGINE-SERVLET-EXECUTE` → `com.strategyquant.plugin.Engine.impl.Panel.EngineServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResult.jar`; 4 class declarations; SHA-256 `d873f8b2800a34cf815706a98f8951fc80981406e9fccf95a0ebc671c0ee023e`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/FitnessMethodStrategyResult.md`; roadmap allocation `FEAT-BUILDER-FITNESS-METHOD-STRATEGY-RESULT`.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy fitness and build command adapter; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResult.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResult.jar" com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult`; `SQX_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResultService.js`; `SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResultCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/fitnessMethodStrategyResult.html`.
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
- [ ] **Step 4:** `FR-BUILDER-FITNESS-METHOD-STRATEGY-RESULT-FITNESS-METHOD-STRATEGY-RESULT-SERVLET-CONTRACT` → `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-BUILDER-FITNESS-METHOD-STRATEGY-RESULT-FITNESS-METHOD-STRATEGY-RESULT-SERVLET-EXECUTE` → `com.strategyquant.plugin.FitnessMethod.impl.StrategyResult.FitnessMethodStrategyResultServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletBuilder/ServletBuilder.jar`; 2 class declarations; SHA-256 `f5abf10d91cc265fefc4a4ec89ca43e70800bc100d9f51b9855faea621c49e82`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Builder/ServletBuilder.md`; roadmap allocation `FEAT-BUILDER-SERVLET-BUILDER`.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Strategy fitness and build command adapter; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletBuilder/ServletBuilder.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ServletBuilder/ServletBuilder.jar" com.strategyquant.plugin.Servlet.impl.Builder.BuilderServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ServletBuilder`; `SQX_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/ServletBuilder/module.js`.
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
- [ ] **Step 4:** `FR-BUILDER-SERVLET-BUILDER-BUILDER-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.Builder.BuilderServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-BUILDER-SERVLET-BUILDER-BUILDER-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.Builder.BuilderServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/SettingsPartsToImprove.jar`; 1 class declarations; SHA-256 `31de31b3ea68df6a2c9313d4c1e25469087c8ac0b178da947a03f4a21460636d`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsPartsToImprove.md`; roadmap allocation `FEAT-BUILDER-SETTINGS-PARTS-TO-IMPROVE`.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Build/improve/search configuration and task execution; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/SettingsPartsToImprove.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/SettingsPartsToImprove.jar" com.strategyquant.plugin.Settings.impl.PartsToImprove.PartsToImproveSettingsPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove`; `SQX_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/PartsToImproveService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/PartsToImproveCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/views/partsToImprove.html`.
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
- [ ] **Step 4:** `FR-BUILDER-SETTINGS-PARTS-TO-IMPROVE-PARTS-TO-IMPROVE-SETTINGS-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.PartsToImprove.PartsToImproveSettingsPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-BUILDER-SETTINGS-PARTS-TO-IMPROVE-PARTS-TO-IMPROVE-SETTINGS-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.PartsToImprove.PartsToImproveSettingsPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-BUILDER-SETTINGS-PARTS-TO-IMPROVE-PARTS-TO-IMPROVE-SETTINGS-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.PartsToImprove.PartsToImproveSettingsPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsRankings/SettingsRankings.jar`; 2 class declarations; SHA-256 `66c06308f8a352bfd31f1e95643b51df017f80827c0beb4e0d7fb4f02bb592db`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsRankings.md`; roadmap allocation `FEAT-BUILDER-SETTINGS-RANKINGS`.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Build/improve/search configuration and task execution; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsRankings/SettingsRankings.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsRankings/SettingsRankings.jar" com.strategyquant.plugin.Settings.impl.Rankings.SettingsRankingsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsRankings`; `SQX_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsRankings/RankingService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsRankings/FitnessFunction/FitnessFunctionService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsRankings/RankingCtrl.js`.
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
- [ ] **Step 4:** `FR-BUILDER-SETTINGS-RANKINGS-SETTINGS-RANKINGS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Rankings.SettingsRankingsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-BUILDER-SETTINGS-RANKINGS-SETTINGS-RANKINGS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.Rankings.SettingsRankingsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-BUILDER-SETTINGS-RANKINGS-SETTINGS-RANKINGS-SERVLET-GET-FITNESS-METHODS` → `com.strategyquant.plugin.Settings.impl.Rankings.SettingsRankingsServlet.getFitnessMethods`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/SettingsWhatToBuild.jar`; 2 class declarations; SHA-256 `a186a61db5e20a129a2845d3a3e079c391013fa530d2f507b44dd95f6b6f0f51`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsWhatToBuild.md`; roadmap allocation `FEAT-BUILDER-SETTINGS-WHAT-TO-BUILD`.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Build/improve/search configuration and task execution; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/SettingsWhatToBuild.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/SettingsWhatToBuild.jar" com.strategyquant.plugin.Settings.impl.WhatToBuild.WhatToBuildServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild`; `SQX_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/WhatToBuildService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/views/settings/buildMode/BuildModeService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/views/settings/conditionsAndPeriods/ConditionsAndPeriodsService.js`.
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
- [ ] **Step 4:** `FR-BUILDER-SETTINGS-WHAT-TO-BUILD-WHAT-TO-BUILD-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.WhatToBuild.WhatToBuildServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-BUILDER-SETTINGS-WHAT-TO-BUILD-WHAT-TO-BUILD-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.WhatToBuild.WhatToBuildServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskBuild/TaskBuild.jar`; 11 class declarations; SHA-256 `e5d2f688ef7820d3e46d2de9bd2e0d6bdcf93b39df74532573d0957eca1a3f70`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Builder/TaskBuild.md`; roadmap allocation `FEAT-BUILDER-TASK-BUILD`.
- **Owner:** `app/workspace/Builder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Build/improve/search configuration and task execution; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskBuild/TaskBuild.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskBuild/TaskBuild.jar" com.strategyquant.plugin.Task.impl.Build.BuildTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/TaskBuild`; `SQX_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/TaskBuild/BuildTaskService.js`; `SQX_REFERENCE_ROOT/internal/plugins/TaskBuild/indicatorsCalibration/IndicatorsCalibrationPopupCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/TaskBuild/simpleSettings/SimpleBuildSettingsCtrl.js`.
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
- [ ] **Step 4:** `FR-BUILDER-TASK-BUILD-BUILD-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.Build.BuildTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-BUILDER-TASK-BUILD-BUILD-TASK-BEFORE-START` → `com.strategyquant.plugin.Task.impl.Build.BuildTask.beforeStart`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-BUILDER-TASK-BUILD-BUILD-TASK-SET-DATABANK-FILTER` → `com.strategyquant.plugin.Task.impl.Build.BuildTask.setDatabankFilter`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind actual strategy/settings submission, build job controls, progress and persisted candidates to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DashboardPanel`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/DashboardPanel/module.js`.
- **FR:** `FR-UI-DASHBOARD-PANEL-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/Builder/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DashboardPanel`; `SQX_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DashboardPanel/DashboardCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/DashboardPanel/dashboard.html`; `SQX_REFERENCE_ROOT/internal/plugins/DashboardPanel/module.js`.
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

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/module.js`.
- **FR:** `FR-UI-SETTINGS-GENETIC-OPTIONS-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/Builder/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions`; `SQX_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/SettingsGeneticOptionsService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/SettingsGeneticOptionsCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/views/geneticOptions.html`.
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

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P09; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/Builder/BuilderWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/Builder/fullSettings.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/web/BUILDER`; `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel`. Inspect `SQX_REFERENCE_ROOT/internal/web/BUILDER/layout/LayoutCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/AppBuilder/module.js`; `SQX_REFERENCE_ROOT/internal/plugins/EnginePanel/EngineService.js`.
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
