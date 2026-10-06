# P12 — Portfolio Composer, Portfolio Master and automatic portfolios

- **Source:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P08,P09,P10,P11.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 12 tasks; current archive allocations and resource/integration tasks only.

# 12.1 FEAT-PORTFOLIO-APP-PORTFOLIO-COMPOSER - AppPortfolioComposer.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppPortfolioComposer/AppPortfolioComposer.jar`; 1 raw class entries; SHA-256 `957b37bd0dcc9f84697533357b937708dc0cfae067fda658855620a2b0ea27c4`.
- **Inspected reference:** [AppPortfolioComposer.md](sqx/PortfolioComposer/AppPortfolioComposer.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppPortfolioComposer/AppPortfolioComposer.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppPortfolioComposer/AppPortfolioComposer.jar" com.strategyquant.plugin.App.impl.PortfolioComposer.PortfolioComposerAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/PortfolioComposer/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppPortfolioComposer`; `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOCOMPOSER`; `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppPortfolioComposer/module.js`.
- **Existing UI connection:** Portfolio Composer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`; wire selected portfolio inputs, composition jobs and reconciled aggregate metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/PortfolioComposer/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/PortfolioComposer/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/PortfolioComposer/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/PortfolioComposer/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_portfolio_app_portfolio_composer.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/portfolio_app_portfolio_composer.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerResults.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/composerModel.ts`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Create:** `ui/app/workspace/PortfolioComposer/portfolioComposerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-portfolio-app-portfolio-composer.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-portfolio-workflows-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected portfolio inputs, composition jobs and reconciled aggregate metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PORTFOLIO-APP-PORTFOLIO-COMPOSER-PORTFOLIO-COMPOSER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.PortfolioComposer.PortfolioComposerAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PORTFOLIO-APP-PORTFOLIO-COMPOSER-PORTFOLIO-COMPOSER-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.PortfolioComposer.PortfolioComposerAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PORTFOLIO-APP-PORTFOLIO-COMPOSER-PORTFOLIO-COMPOSER-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.PortfolioComposer.PortfolioComposerAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_app_portfolio_composer.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-portfolio-app-portfolio-composer.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-portfolio-workflows-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Portfolio Composer for FEAT-PORTFOLIO-APP-PORTFOLIO-COMPOSER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 12.2 FEAT-PORTFOLIO-APP-PORTFOLIO-MASTER - AppPortfolioMaster.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster/AppPortfolioMaster.jar`; 1 raw class entries; SHA-256 `93dd223deb0421c07cc1bcd572ae1328513e525a288715933b22d98f56a9a9dd`.
- **Inspected reference:** [AppPortfolioMaster.md](sqx/PortfolioMaster/AppPortfolioMaster.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster/AppPortfolioMaster.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster/AppPortfolioMaster.jar" com.strategyquant.plugin.App.impl.PortfolioMaster.PortfolioMasterAppPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/workspace/PortfolioMaster/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster`; `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOMASTER`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster/module.js`.
- **Existing UI connection:** Portfolio Master; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/PortfolioMaster/PortfolioMasterWorkspace.tsx`; wire portfolio search settings, real search jobs and persisted accepted portfolios.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/PortfolioMaster/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/PortfolioMaster/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/PortfolioMaster/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/PortfolioMaster/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_portfolio_app_portfolio_master.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/portfolio_app_portfolio_master.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/PortfolioMaster/PortfolioMasterWorkspace.tsx`
  - Display portfolio search settings, real search jobs and persisted accepted portfolios from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioMaster/PortfolioMasterProgress.tsx`
  - Display portfolio search settings, real search jobs and persisted accepted portfolios from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioMaster/portfolioMasterModel.ts`
  - Display portfolio search settings, real search jobs and persisted accepted portfolios from backend responses; preserve layout.
- **Create:** `ui/app/workspace/PortfolioMaster/portfolioMasterClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-portfolio-app-portfolio-master.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-portfolio-workflows-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind portfolio search settings, real search jobs and persisted accepted portfolios to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PORTFOLIO-APP-PORTFOLIO-MASTER-PORTFOLIO-MASTER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.PortfolioMaster.PortfolioMasterAppPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PORTFOLIO-APP-PORTFOLIO-MASTER-PORTFOLIO-MASTER-APP-PLUGIN-GET-NAME` → `com.strategyquant.plugin.App.impl.PortfolioMaster.PortfolioMasterAppPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PORTFOLIO-APP-PORTFOLIO-MASTER-PORTFOLIO-MASTER-APP-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.App.impl.PortfolioMaster.PortfolioMasterAppPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_app_portfolio_master.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-portfolio-app-portfolio-master.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-portfolio-workflows-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Portfolio Master for FEAT-PORTFOLIO-APP-PORTFOLIO-MASTER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 12.3 FEAT-PORTFOLIO-FITNESS-METHOD-EXISTING-PORTFOLIO - FitnessMethodExistingPortfolio.jar

## 1. Objective

- **Goal:** Compute the named fitness objective from qualified result inputs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodExistingPortfolio/FitnessMethodExistingPortfolio.jar`; 4 raw class entries; SHA-256 `f9bb50732b5da16ec971304e37e05db9429e457bf83e6e1041d9eab7ce484350`.
- **Inspected reference:** [FitnessMethodExistingPortfolio.md](sqx/Shared/FitnessMethodExistingPortfolio.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodExistingPortfolio/FitnessMethodExistingPortfolio.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodExistingPortfolio/FitnessMethodExistingPortfolio.jar" com.strategyquant.plugin.FitnessMethod.impl.ExistingPortfolio.FitnessExistingPortfolioServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/portfolio/FitnessMethodExistingPortfolio/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio search/composition, correlation, progress and output; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodExistingPortfolio`; `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOCOMPOSER`; `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodExistingPortfolio/FitnessMethodExistingPortfolioService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodExistingPortfolio/FitnessMethodExistingPortfolioCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/FitnessMethodExistingPortfolio/fitnessMethodExistingPortfolio.html`.
- **Existing UI connection:** Portfolio Composer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`; wire selected portfolio inputs, composition jobs and reconciled aggregate metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/portfolio/FitnessMethodExistingPortfolio/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/FitnessMethodExistingPortfolio/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/FitnessMethodExistingPortfolio/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_portfolio_fitness_method_existing_portfolio.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/portfolio_fitness_method_existing_portfolio.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerResults.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/composerModel.ts`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Create:** `ui/app/workspace/PortfolioComposer/portfolioComposerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-portfolio-fitness-method-existing-portfolio.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-portfolio-workflows-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Compute the named fitness objective from qualified result inputs; verify objective direction, ties, missing metrics and nonfinite scores.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected portfolio inputs, composition jobs and reconciled aggregate metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PORTFOLIO-FITNESS-METHOD-EXISTING-PORTFOLIO-FITNESS-EXISTING-PORTFOLIO-SERVLET-CONTRACT` → `com.strategyquant.plugin.FitnessMethod.impl.ExistingPortfolio.FitnessExistingPortfolioServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PORTFOLIO-FITNESS-METHOD-EXISTING-PORTFOLIO-FITNESS-EXISTING-PORTFOLIO-SERVLET-EXECUTE` → `com.strategyquant.plugin.FitnessMethod.impl.ExistingPortfolio.FitnessExistingPortfolioServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PORTFOLIO-FITNESS-METHOD-EXISTING-PORTFOLIO-FITNESS-EXISTING-PORTFOLIO-SERVLET-ON-LIST` → `com.strategyquant.plugin.FitnessMethod.impl.ExistingPortfolio.FitnessExistingPortfolioServlet.onList()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_fitness_method_existing_portfolio.py --no-cov`; expect objective direction, ties, missing metrics and nonfinite scores; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture objective direction, ties, missing metrics and nonfinite scores and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-portfolio-fitness-method-existing-portfolio.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-portfolio-workflows-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Portfolio Composer for FEAT-PORTFOLIO-FITNESS-METHOD-EXISTING-PORTFOLIO; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 12.4 FEAT-PORTFOLIO-PORTFOLIO-COMPOSER - PortfolioComposer.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer/PortfolioComposer.jar`; 15 raw class entries; SHA-256 `46998223c28fb3ddce99dcf44bb5009fef53a8c7df0d09889a455b4aac0a1e16`.
- **Inspected reference:** [PortfolioComposer.md](sqx/PortfolioComposer/PortfolioComposer.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer/PortfolioComposer.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer/PortfolioComposer.jar" com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/portfolio/PortfolioComposer/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio search/composition, correlation, progress and output; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer`; `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOCOMPOSER`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer/PortfolioComposerService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer/PortfolioComposerCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer/results/PCResultsCtrl.js`.
- **Existing UI connection:** Portfolio Composer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`; wire selected portfolio inputs, composition jobs and reconciled aggregate metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/portfolio/PortfolioComposer/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/PortfolioComposer/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/PortfolioComposer/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_portfolio_portfolio_composer.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/portfolio_portfolio_composer.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerResults.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/composerModel.ts`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Create:** `ui/app/workspace/PortfolioComposer/portfolioComposerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-portfolio-portfolio-composer.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-portfolio-workflows-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected portfolio inputs, composition jobs and reconciled aggregate metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PORTFOLIO-PORTFOLIO-COMPOSER-PORTFOLIO-COMPOSER-SERVLET-CONTRACT` → `com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PORTFOLIO-PORTFOLIO-COMPOSER-PORTFOLIO-COMPOSER-SERVLET-EXECUTE` → `com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PORTFOLIO-PORTFOLIO-COMPOSER-PORTFOLIO-COMPOSER-SERVLET-ON-ADD-BUY-HOLD-STRATEGY` → `com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerServlet.onAddBuyHoldStrategy(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_portfolio_composer.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-portfolio-portfolio-composer.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-portfolio-workflows-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Portfolio Composer for FEAT-PORTFOLIO-PORTFOLIO-COMPOSER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 12.5 FEAT-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-CHART - ResultsPortfolioComposerChart.jar

## 1. Objective

- **Goal:** Project the named result series with verified metrics and sampling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerChart/ResultsPortfolioComposerChart.jar`; 2 raw class entries; SHA-256 `afa95f108dad3dcc89b5e556cefcde238df462e5ed95e682d5f9bc9eb28b7592`.
- **Inspected reference:** [ResultsPortfolioComposerChart.md](sqx/PortfolioComposer/ResultsPortfolioComposerChart.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerChart/ResultsPortfolioComposerChart.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerChart/ResultsPortfolioComposerChart.jar" com.strategyquant.plugin.Results.impl.PortfolioComposerChart.PortfolioComposerChartServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/portfolio/ResultsPortfolioComposerChart/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio search/composition, correlation, progress and output; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerChart`; `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOCOMPOSER`; `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerChart/PortfolioComposerChartService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerChart/PortfolioComposerChartCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerChart/portfolioComposerChart.html`.
- **Existing UI connection:** Portfolio Composer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`; wire selected portfolio inputs, composition jobs and reconciled aggregate metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/portfolio/ResultsPortfolioComposerChart/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/ResultsPortfolioComposerChart/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/ResultsPortfolioComposerChart/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_portfolio_results_portfolio_composer_chart.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/portfolio_results_portfolio_composer_chart.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerResults.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/composerModel.ts`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Create:** `ui/app/workspace/PortfolioComposer/portfolioComposerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-portfolio-results-portfolio-composer-chart.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-portfolio-workflows-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project the named result series with verified metrics and sampling; verify units, timestamp alignment, missing samples and reconciled source totals.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected portfolio inputs, composition jobs and reconciled aggregate metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-CHART-PORTFOLIO-COMPOSER-CHART-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.PortfolioComposerChart.PortfolioComposerChartServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-CHART-PORTFOLIO-COMPOSER-CHART-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.PortfolioComposerChart.PortfolioComposerChartServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-CHART-PORTFOLIO-COMPOSER-CHART-SERVLET-ON-PRINT` → `com.strategyquant.plugin.Results.impl.PortfolioComposerChart.PortfolioComposerChartServlet.onPrint(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_results_portfolio_composer_chart.py --no-cov`; expect units, timestamp alignment, missing samples and reconciled source totals; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture units, timestamp alignment, missing samples and reconciled source totals and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-portfolio-results-portfolio-composer-chart.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-portfolio-workflows-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Portfolio Composer for FEAT-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-CHART; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 12.6 FEAT-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-LOG - ResultsPortfolioComposerLog.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerLog/ResultsPortfolioComposerLog.jar`; 2 raw class entries; SHA-256 `4653f9610a2df1b77fc164a9cb14ca21461ef3c58ebefdef570da9eb2bbcc043`.
- **Inspected reference:** [ResultsPortfolioComposerLog.md](sqx/PortfolioComposer/ResultsPortfolioComposerLog.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerLog/ResultsPortfolioComposerLog.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerLog/ResultsPortfolioComposerLog.jar" com.strategyquant.plugin.Results.impl.PortfolioComposerLog.PortfolioComposerLogServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/portfolio/ResultsPortfolioComposerLog/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio search/composition, correlation, progress and output; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerLog`; `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOCOMPOSER`; `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerLog/PortfolioComposerLogService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerLog/PortfolioComposerLogCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerLog/portfolioComposerLog.html`.
- **Existing UI connection:** Portfolio Composer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`; wire selected portfolio inputs, composition jobs and reconciled aggregate metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/portfolio/ResultsPortfolioComposerLog/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/ResultsPortfolioComposerLog/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/ResultsPortfolioComposerLog/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_portfolio_results_portfolio_composer_log.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/portfolio_results_portfolio_composer_log.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerResults.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/composerModel.ts`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Create:** `ui/app/workspace/PortfolioComposer/portfolioComposerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-portfolio-results-portfolio-composer-log.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-portfolio-workflows-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected portfolio inputs, composition jobs and reconciled aggregate metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-LOG-PORTFOLIO-COMPOSER-LOG-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.PortfolioComposerLog.PortfolioComposerLogServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-LOG-PORTFOLIO-COMPOSER-LOG-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.PortfolioComposerLog.PortfolioComposerLogServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-LOG-PORTFOLIO-COMPOSER-LOG-SERVLET-ON-PRINT` → `com.strategyquant.plugin.Results.impl.PortfolioComposerLog.PortfolioComposerLogServlet.onPrint(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_results_portfolio_composer_log.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-portfolio-results-portfolio-composer-log.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-portfolio-workflows-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Portfolio Composer for FEAT-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-LOG; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 12.7 FEAT-PORTFOLIO-RESULTS-PORTFOLIO-CORRELATION - ResultsPortfolioCorrelation.jar

## 1. Objective

- **Goal:** Calculate qualified correlations and apply selection/filter rules.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/ResultsPortfolioCorrelation.jar`; 13 raw class entries; SHA-256 `cb2351d4e02219f853d36abb08ffbacb19b71fbd7c730cf5105273fa359e40f5`.
- **Inspected reference:** [ResultsPortfolioCorrelation.md](sqx/Results/ResultsPortfolioCorrelation.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/ResultsPortfolioCorrelation.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/ResultsPortfolioCorrelation.jar" com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/portfolio/ResultsPortfolioCorrelation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio search/composition, correlation, progress and output; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation`; `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOCOMPOSER`; `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/PortfolioCorrelationService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/PortfolioCorrelationCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/tabs/correlationMatrix/CorrelationMatrixCtrl.js`.
- **Existing UI connection:** Portfolio Composer; exact retained source-map `ui/app/plugins/project/ResultsPortfolioCorrelation/source-map.json`. Target `ui/app/plugins/project/ResultsPortfolioCorrelation/PortfolioCorrelationCtrl.ts`; wire selected portfolio inputs, composition jobs and reconciled aggregate metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/portfolio/ResultsPortfolioCorrelation/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/ResultsPortfolioCorrelation/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/ResultsPortfolioCorrelation/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_portfolio_results_portfolio_correlation.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/portfolio_results_portfolio_correlation.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/ResultsPortfolioCorrelation/PortfolioCorrelationCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/ResultsPortfolioCorrelation/portfolioCorrelation.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/ResultsPortfolioCorrelation/tabs/correlationMatrix/correlationMatrix.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerResults.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/composerModel.ts`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/ResultsPortfolioCorrelation/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-portfolio-results-portfolio-correlation.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-portfolio-workflows-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Calculate qualified correlations and apply selection/filter rules; verify alignment, sample basis, undefined correlation and threshold equality.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected portfolio inputs, composition jobs and reconciled aggregate metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-CORRELATION-PORTFOLIO-CORRELATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-CORRELATION-PORTFOLIO-CORRELATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-CORRELATION-PORTFOLIO-CORRELATION-SERVLET-ON-CORRELATION` → `com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationServlet.onCorrelation(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_results_portfolio_correlation.py --no-cov`; expect alignment, sample basis, undefined correlation and threshold equality; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture alignment, sample basis, undefined correlation and threshold equality and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-portfolio-results-portfolio-correlation.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-portfolio-workflows-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Portfolio Composer for FEAT-PORTFOLIO-RESULTS-PORTFOLIO-CORRELATION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 12.8 FEAT-PORTFOLIO-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER - SettingsAutomaticPortfolioBuilder.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/SettingsAutomaticPortfolioBuilder.jar`; 2 raw class entries; SHA-256 `7d7c8fe7fbc77d52f1aed81a06f8e9104f2d3cbca10e19a9fcba5fdc68177161`.
- **Inspected reference:** [SettingsAutomaticPortfolioBuilder.md](sqx/PortfolioMaster/SettingsAutomaticPortfolioBuilder.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/SettingsAutomaticPortfolioBuilder.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/SettingsAutomaticPortfolioBuilder.jar" com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/portfolio/SettingsAutomaticPortfolioBuilder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio task/config adapters; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder`; `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOMASTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/AutomaticPortfolioBuilderService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/AutomaticPortfolioBuilderCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/automaticPortfolioBuilder.html`.
- **Existing UI connection:** Portfolio Master; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/PortfolioMaster/PortfolioMasterWorkspace.tsx`; wire portfolio search settings, real search jobs and persisted accepted portfolios.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/portfolio/SettingsAutomaticPortfolioBuilder/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/SettingsAutomaticPortfolioBuilder/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/SettingsAutomaticPortfolioBuilder/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_portfolio_settings_automatic_portfolio_builder.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/portfolio_settings_automatic_portfolio_builder.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/PortfolioMaster/PortfolioMasterWorkspace.tsx`
  - Display portfolio search settings, real search jobs and persisted accepted portfolios from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioMaster/PortfolioMasterProgress.tsx`
  - Display portfolio search settings, real search jobs and persisted accepted portfolios from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioMaster/portfolioMasterModel.ts`
  - Display portfolio search settings, real search jobs and persisted accepted portfolios from backend responses; preserve layout.
- **Create:** `ui/app/workspace/PortfolioMaster/portfolioMasterClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-portfolio-settings-automatic-portfolio-builder.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-portfolio-workflows-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind portfolio search settings, real search jobs and persisted accepted portfolios to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PORTFOLIO-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PORTFOLIO-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PORTFOLIO-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER-SERVLET-GET-NUMBER-OF-POSSIBLE-PORTFOLIOS` → `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet.getNumberOfPossiblePortfolios(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_settings_automatic_portfolio_builder.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-portfolio-settings-automatic-portfolio-builder.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-portfolio-workflows-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Portfolio Master for FEAT-PORTFOLIO-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 12.9 FEAT-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO - SettingsCreatePortfolio.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCreatePortfolio/SettingsCreatePortfolio.jar`; 1 raw class entries; SHA-256 `e112b5808ad082166dc18f759673c126a80f327d0cb87d534fa04baed8fd0fd3`.
- **Inspected reference:** [SettingsCreatePortfolio.md](sqx/Shared/SettingsCreatePortfolio.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCreatePortfolio/SettingsCreatePortfolio.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCreatePortfolio/SettingsCreatePortfolio.jar" com.strategyquant.plugin.Settings.impl.CreatePortfolio.SettingsCreatePortfolio`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/portfolio/SettingsCreatePortfolio/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio task/config adapters; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCreatePortfolio`; `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOCOMPOSER`; `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCreatePortfolio/SettingsCreatePortfolioService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCreatePortfolio/SettingsCreatePortfolioCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsCreatePortfolio/settingsCreatePortfolio.html`.
- **Existing UI connection:** Portfolio Composer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`; wire selected portfolio inputs, composition jobs and reconciled aggregate metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/portfolio/SettingsCreatePortfolio/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/SettingsCreatePortfolio/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/SettingsCreatePortfolio/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_portfolio_settings_create_portfolio.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/portfolio_settings_create_portfolio.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerResults.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/composerModel.ts`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Create:** `ui/app/workspace/PortfolioComposer/portfolioComposerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-portfolio-settings-create-portfolio.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-portfolio-workflows-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected portfolio inputs, composition jobs and reconciled aggregate metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO-CONTRACT` → `com.strategyquant.plugin.Settings.impl.CreatePortfolio.SettingsCreatePortfolio`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.CreatePortfolio.SettingsCreatePortfolio.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.CreatePortfolio.SettingsCreatePortfolio.getPreferredPosition()I`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_settings_create_portfolio.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-portfolio-settings-create-portfolio.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-portfolio-workflows-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Portfolio Composer for FEAT-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 12.10 FEAT-PORTFOLIO-TASK-AUTOMATIC-PORTFOLIO-BUILDER - TaskAutomaticPortfolioBuilder.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/TaskAutomaticPortfolioBuilder.jar`; 27 raw class entries; SHA-256 `63a15c31d3c44356a360c32c988b22e30b8c8ddfe581a9bc7ac62050e887e8ce`.
- **Inspected reference:** [TaskAutomaticPortfolioBuilder.md](sqx/PortfolioMaster/TaskAutomaticPortfolioBuilder.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/TaskAutomaticPortfolioBuilder.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/TaskAutomaticPortfolioBuilder.jar" com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.AutomaticPortfolioBuilder`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/portfolio/TaskAutomaticPortfolioBuilder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio task/config adapters; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder`; `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOMASTER`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/simpleSettings/SimpleAutoPortfolioBuilderCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/module.js`.
- **Existing UI connection:** Portfolio Master; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/PortfolioMaster/PortfolioMasterWorkspace.tsx`; wire portfolio search settings, real search jobs and persisted accepted portfolios.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/portfolio/TaskAutomaticPortfolioBuilder/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/TaskAutomaticPortfolioBuilder/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/TaskAutomaticPortfolioBuilder/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_portfolio_task_automatic_portfolio_builder.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/portfolio_task_automatic_portfolio_builder.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/PortfolioMaster/PortfolioMasterWorkspace.tsx`
  - Display portfolio search settings, real search jobs and persisted accepted portfolios from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioMaster/PortfolioMasterProgress.tsx`
  - Display portfolio search settings, real search jobs and persisted accepted portfolios from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioMaster/portfolioMasterModel.ts`
  - Display portfolio search settings, real search jobs and persisted accepted portfolios from backend responses; preserve layout.
- **Create:** `ui/app/workspace/PortfolioMaster/portfolioMasterClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-portfolio-task-automatic-portfolio-builder.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-portfolio-workflows-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind portfolio search settings, real search jobs and persisted accepted portfolios to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PORTFOLIO-TASK-AUTOMATIC-PORTFOLIO-BUILDER-AUTOMATIC-PORTFOLIO-BUILDER-CONTRACT` → `com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.AutomaticPortfolioBuilder`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PORTFOLIO-TASK-AUTOMATIC-PORTFOLIO-BUILDER-AUTOMATIC-PORTFOLIO-BUILDER-START` → `com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.AutomaticPortfolioBuilder.start(Lcom/strategyquant/tradinglib/project/SQProject;Lcom/strategyquant/tradinglib/project/ProgressEngine;Lcom/strategyquant/tradinglib/portfolioMaster/PortfolioMasterSettings;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PORTFOLIO-TASK-AUTOMATIC-PORTFOLIO-BUILDER-AUTOMATIC-PORTFOLIO-BUILDER-GET-CLONED-STRATEGIES` → `com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.AutomaticPortfolioBuilder.getClonedStrategies(Ljava/util/ArrayList;Lcom/strategyquant/tradinglib/Databank;)Ljava/util/ArrayList;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_task_automatic_portfolio_builder.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-portfolio-task-automatic-portfolio-builder.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-portfolio-workflows-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Portfolio Master for FEAT-PORTFOLIO-TASK-AUTOMATIC-PORTFOLIO-BUILDER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 12.11 FEAT-PORTFOLIO-TASK-CREATE-PORTFOLIO - TaskCreatePortfolio.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/TaskCreatePortfolio.jar`; 1 raw class entries; SHA-256 `61f5db94abc1289ed53bb2f6cb421330951c8445c7de518d8a479fd424733b38`.
- **Inspected reference:** [TaskCreatePortfolio.md](sqx/CustomProjects/TaskCreatePortfolio.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/TaskCreatePortfolio.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/TaskCreatePortfolio.jar" com.strategyquant.plugin.Task.impl.CreatePortfolio.CreatePortfolio`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/portfolio/TaskCreatePortfolio/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio task/config adapters; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio`; `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOCOMPOSER`; `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/simpleSettings/SimpleCreatePortfolioSettingsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/simpleSettings/simpleSettings.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/module.js`.
- **Existing UI connection:** Portfolio Composer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`; wire selected portfolio inputs, composition jobs and reconciled aggregate metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/portfolio/TaskCreatePortfolio/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/TaskCreatePortfolio/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/portfolio/TaskCreatePortfolio/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_portfolio_task_create_portfolio.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/portfolio_task_create_portfolio.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerResults.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/composerModel.ts`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Create:** `ui/app/workspace/PortfolioComposer/portfolioComposerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-portfolio-task-create-portfolio.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-portfolio-workflows-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind selected portfolio inputs, composition jobs and reconciled aggregate metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-PORTFOLIO-TASK-CREATE-PORTFOLIO-CREATE-PORTFOLIO-CONTRACT` → `com.strategyquant.plugin.Task.impl.CreatePortfolio.CreatePortfolio`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-PORTFOLIO-TASK-CREATE-PORTFOLIO-CREATE-PORTFOLIO-INIT` → `com.strategyquant.plugin.Task.impl.CreatePortfolio.CreatePortfolio.init()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-PORTFOLIO-TASK-CREATE-PORTFOLIO-CREATE-PORTFOLIO-START` → `com.strategyquant.plugin.Task.impl.CreatePortfolio.CreatePortfolio.start()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_task_create_portfolio.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-portfolio-task-create-portfolio.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-portfolio-workflows-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Portfolio Composer for FEAT-PORTFOLIO-TASK-CREATE-PORTFOLIO; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 12.12 P12 integration — Compose and search portfolios with reconciled aggregate metrics

## 1. Objective

- **Goal:** Compose and search portfolios with reconciled aggregate metrics.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`, P12; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`, `ui/app/workspace/PortfolioMaster/PortfolioMasterWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/PortfolioComposer/composerDraft.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOCOMPOSER`; `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/PORTFOLIOCOMPOSER/layout/LayoutCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/PortfolioComposer/PortfolioComposerService.js`.
- **Existing UI connection:** Portfolio Composer; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`; wire selected portfolio inputs, composition jobs and reconciled aggregate metrics.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/portfolio/service.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/portfolio/aggregation.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/portfolio/search.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/portfolio/correlation.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/PortfolioComposer/routes.py` (proposed earlier in FEAT-PORTFOLIO-APP-PORTFOLIO-COMPOSER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/PortfolioMaster/routes.py` (proposed earlier in FEAT-PORTFOLIO-APP-PORTFOLIO-MASTER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/PortfolioComposer/portfolioComposerClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `ui/app/workspace/PortfolioMaster/PortfolioMasterWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/PortfolioMaster/portfolioMasterClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Create:** `app/plugins/portfolio/README.md`
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_portfolio_workflows_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-portfolio-workflows-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/PortfolioComposer/PortfolioComposerResults.tsx`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/PortfolioComposer/composerModel.ts`
  - Display selected portfolio inputs, composition jobs and reconciled aggregate metrics from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/task-12-12.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify member identity, weights, overlapping exposure, correlation and portfolio fitness.
- [ ] **Step 3:** Implement manual/automatic selection, aggregate accounting and portfolio resource lifecycle.
- [ ] **Step 4:** Connect Composer/Master selection, progress, charts and persisted portfolio revisions.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind selected portfolio inputs, composition jobs and reconciled aggregate metrics to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_portfolio_workflows_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/PortfolioComposer/composerDraft.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-portfolio-workflows-backend.spec.ts`. Assert member/weight round trips, aggregate equity, correlation and deterministic selection; reject missing member, nonaligned calendars, duplicate strategy and invalid weight.
- **Manual / Browser Verification:** Compose two fixture strategies; change weights; reload; run automatic search; reconcile portfolio totals with member ledgers.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-12-12.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-portfolio-workflows-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Portfolio Composer for 12.12; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
