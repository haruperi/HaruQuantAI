# P12 — Portfolio Composer, Portfolio Master and automatic portfolios

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P08,P09,P10,P11.
- **Scope:** 11 JAR feature tasks, 0 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.

# 12.1 FEAT-PORTFOLIO-APP-PORTFOLIO-COMPOSER - AppPortfolioComposer.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppPortfolioComposer/AppPortfolioComposer.jar`; 1 class declarations; SHA-256 `53fe64ae3bede7cc0334e4225e569383b8b19e58c3a2be1b0aaf518d85682d4f`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/PortfolioComposer/AppPortfolioComposer.md`; roadmap allocation `FEAT-PORTFOLIO-APP-PORTFOLIO-COMPOSER`.
- **Owner:** `app/workspace/PortfolioComposer/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppPortfolioComposer/AppPortfolioComposer.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppPortfolioComposer/AppPortfolioComposer.jar" com.strategyquant.plugin.App.impl.PortfolioComposer.PortfolioComposerAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** `FR-PORTFOLIO-APP-PORTFOLIO-COMPOSER-PORTFOLIO-COMPOSER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.PortfolioComposer.PortfolioComposerAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PORTFOLIO-APP-PORTFOLIO-COMPOSER-PORTFOLIO-COMPOSER-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.PortfolioComposer.PortfolioComposerAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PORTFOLIO-APP-PORTFOLIO-COMPOSER-PORTFOLIO-COMPOSER-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.PortfolioComposer.PortfolioComposerAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_app_portfolio_composer.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.

# 12.2 FEAT-PORTFOLIO-APP-PORTFOLIO-MASTER - AppPortfolioMaster.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster/AppPortfolioMaster.jar`; 1 class declarations; SHA-256 `dc383514c68569ddf10e9b4b96141807d4849844e9add50dc2a4b7107a2d488e`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/PortfolioMaster/AppPortfolioMaster.md`; roadmap allocation `FEAT-PORTFOLIO-APP-PORTFOLIO-MASTER`.
- **Owner:** `app/workspace/PortfolioMaster/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster/AppPortfolioMaster.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppPortfolioMaster/AppPortfolioMaster.jar" com.strategyquant.plugin.App.impl.PortfolioMaster.PortfolioMasterAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** `FR-PORTFOLIO-APP-PORTFOLIO-MASTER-PORTFOLIO-MASTER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.PortfolioMaster.PortfolioMasterAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PORTFOLIO-APP-PORTFOLIO-MASTER-PORTFOLIO-MASTER-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.PortfolioMaster.PortfolioMasterAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PORTFOLIO-APP-PORTFOLIO-MASTER-PORTFOLIO-MASTER-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.PortfolioMaster.PortfolioMasterAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_app_portfolio_master.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.

# 12.3 FEAT-PORTFOLIO-FITNESS-METHOD-EXISTING-PORTFOLIO - FitnessMethodExistingPortfolio.jar

## 1. Objective

- **Goal:** Compute the named fitness objective from qualified result inputs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodExistingPortfolio/FitnessMethodExistingPortfolio.jar`; 4 class declarations; SHA-256 `f9e7d2b86e7f666b3e9568363571c2004c36a2137cb2dc9c28aab456aa1442c1`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/FitnessMethodExistingPortfolio.md`; roadmap allocation `FEAT-PORTFOLIO-FITNESS-METHOD-EXISTING-PORTFOLIO`.
- **Owner:** `app/plugins/portfolio/FitnessMethodExistingPortfolio/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio search/composition, correlation, progress and output; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodExistingPortfolio/FitnessMethodExistingPortfolio.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodExistingPortfolio/FitnessMethodExistingPortfolio.jar" com.strategyquant.plugin.FitnessMethod.impl.ExistingPortfolio.FitnessExistingPortfolioServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Compute the named fitness objective from qualified result inputs; verify objective direction, ties, missing metrics and nonfinite scores.
- [ ] **Step 4:** `FR-PORTFOLIO-FITNESS-METHOD-EXISTING-PORTFOLIO-FITNESS-EXISTING-PORTFOLIO-SERVLET-CONTRACT` → `com.strategyquant.plugin.FitnessMethod.impl.ExistingPortfolio.FitnessExistingPortfolioServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PORTFOLIO-FITNESS-METHOD-EXISTING-PORTFOLIO-FITNESS-EXISTING-PORTFOLIO-SERVLET-EXECUTE` → `com.strategyquant.plugin.FitnessMethod.impl.ExistingPortfolio.FitnessExistingPortfolioServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_fitness_method_existing_portfolio.py --no-cov`; expect objective direction, ties, missing metrics and nonfinite scores; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture objective direction, ties, missing metrics and nonfinite scores and visible failures.

# 12.4 FEAT-PORTFOLIO-PORTFOLIO-COMPOSER - PortfolioComposer.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/PortfolioComposer/PortfolioComposer.jar`; 15 class declarations; SHA-256 `f16ea1e94a8f7d134e103372d96cd96f60d8dedfe5970d02413fedc393766cc9`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/PortfolioComposer/PortfolioComposer.md`; roadmap allocation `FEAT-PORTFOLIO-PORTFOLIO-COMPOSER`.
- **Owner:** `app/plugins/portfolio/PortfolioComposer/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio search/composition, correlation, progress and output; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/PortfolioComposer/PortfolioComposer.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/PortfolioComposer/PortfolioComposer.jar" com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** `FR-PORTFOLIO-PORTFOLIO-COMPOSER-PORTFOLIO-COMPOSER-SERVLET-CONTRACT` → `com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PORTFOLIO-PORTFOLIO-COMPOSER-PORTFOLIO-COMPOSER-SERVLET-EXECUTE` → `com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_portfolio_composer.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.

# 12.5 FEAT-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-CHART - ResultsPortfolioComposerChart.jar

## 1. Objective

- **Goal:** Project the named result series with verified metrics and sampling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerChart/ResultsPortfolioComposerChart.jar`; 2 class declarations; SHA-256 `a8e2bdc14fa34fa6e4d02eb06feebba4822e4f01550bb04be28ce06d62f61b6e`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/PortfolioComposer/ResultsPortfolioComposerChart.md`; roadmap allocation `FEAT-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-CHART`.
- **Owner:** `app/plugins/portfolio/ResultsPortfolioComposerChart/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio search/composition, correlation, progress and output; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerChart/ResultsPortfolioComposerChart.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerChart/ResultsPortfolioComposerChart.jar" com.strategyquant.plugin.Results.impl.PortfolioComposerChart.PortfolioComposerChartServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project the named result series with verified metrics and sampling; verify units, timestamp alignment, missing samples and reconciled source totals.
- [ ] **Step 4:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-CHART-PORTFOLIO-COMPOSER-CHART-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.PortfolioComposerChart.PortfolioComposerChartServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-CHART-PORTFOLIO-COMPOSER-CHART-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.PortfolioComposerChart.PortfolioComposerChartServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_results_portfolio_composer_chart.py --no-cov`; expect units, timestamp alignment, missing samples and reconciled source totals; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture units, timestamp alignment, missing samples and reconciled source totals and visible failures.

# 12.6 FEAT-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-LOG - ResultsPortfolioComposerLog.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerLog/ResultsPortfolioComposerLog.jar`; 2 class declarations; SHA-256 `66866d35008ef208b009439c77ef11a2b923ca2bb9360f876c0539098f202d41`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/PortfolioComposer/ResultsPortfolioComposerLog.md`; roadmap allocation `FEAT-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-LOG`.
- **Owner:** `app/plugins/portfolio/ResultsPortfolioComposerLog/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio search/composition, correlation, progress and output; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerLog/ResultsPortfolioComposerLog.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsPortfolioComposerLog/ResultsPortfolioComposerLog.jar" com.strategyquant.plugin.Results.impl.PortfolioComposerLog.PortfolioComposerLogServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-LOG-PORTFOLIO-COMPOSER-LOG-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.PortfolioComposerLog.PortfolioComposerLogServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-COMPOSER-LOG-PORTFOLIO-COMPOSER-LOG-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.PortfolioComposerLog.PortfolioComposerLogServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_results_portfolio_composer_log.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.

# 12.7 FEAT-PORTFOLIO-RESULTS-PORTFOLIO-CORRELATION - ResultsPortfolioCorrelation.jar

## 1. Objective

- **Goal:** Calculate qualified correlations and apply selection/filter rules.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/ResultsPortfolioCorrelation.jar`; 13 class declarations; SHA-256 `8cc910853b04b570650a4805917d30b8319c87c7b44cb9f23988e04564e1116b`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsPortfolioCorrelation.md`; roadmap allocation `FEAT-PORTFOLIO-RESULTS-PORTFOLIO-CORRELATION`.
- **Owner:** `app/plugins/portfolio/ResultsPortfolioCorrelation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio search/composition, correlation, progress and output; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/ResultsPortfolioCorrelation.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/ResultsPortfolioCorrelation.jar" com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Calculate qualified correlations and apply selection/filter rules; verify alignment, sample basis, undefined correlation and threshold equality.
- [ ] **Step 4:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-CORRELATION-PORTFOLIO-CORRELATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PORTFOLIO-RESULTS-PORTFOLIO-CORRELATION-PORTFOLIO-CORRELATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_results_portfolio_correlation.py --no-cov`; expect alignment, sample basis, undefined correlation and threshold equality; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture alignment, sample basis, undefined correlation and threshold equality and visible failures.

# 12.8 FEAT-PORTFOLIO-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER - SettingsAutomaticPortfolioBuilder.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/SettingsAutomaticPortfolioBuilder.jar`; 2 class declarations; SHA-256 `f3bdfb79409f2b8eaf179626cef9462733a669c34f0ea05fb15ddad1219171d7`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/PortfolioMaster/SettingsAutomaticPortfolioBuilder.md`; roadmap allocation `FEAT-PORTFOLIO-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER`.
- **Owner:** `app/plugins/portfolio/SettingsAutomaticPortfolioBuilder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/SettingsAutomaticPortfolioBuilder.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsAutomaticPortfolioBuilder/SettingsAutomaticPortfolioBuilder.jar" com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** `FR-PORTFOLIO-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PORTFOLIO-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PORTFOLIO-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER-SETTINGS-AUTOMATIC-PORTFOLIO-BUILDER-SERVLET-GET-FITNESS-TYPES` → `com.strategyquant.plugin.Settings.impl.AutomaticPortfolioBuilder.SettingsAutomaticPortfolioBuilderServlet.getFitnessTypes`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_settings_automatic_portfolio_builder.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.

# 12.9 FEAT-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO - SettingsCreatePortfolio.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsCreatePortfolio/SettingsCreatePortfolio.jar`; 1 class declarations; SHA-256 `817623e2523694139a6d23e2944eb323d81a510bfcf959c97c6b46aefc07e4b7`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsCreatePortfolio.md`; roadmap allocation `FEAT-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO`.
- **Owner:** `app/plugins/portfolio/SettingsCreatePortfolio/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsCreatePortfolio/SettingsCreatePortfolio.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsCreatePortfolio/SettingsCreatePortfolio.jar" com.strategyquant.plugin.Settings.impl.CreatePortfolio.SettingsCreatePortfolio`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** `FR-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO-CONTRACT` → `com.strategyquant.plugin.Settings.impl.CreatePortfolio.SettingsCreatePortfolio`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.CreatePortfolio.SettingsCreatePortfolio.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO-SETTINGS-CREATE-PORTFOLIO-INIT-PLUGIN` → `com.strategyquant.plugin.Settings.impl.CreatePortfolio.SettingsCreatePortfolio.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_settings_create_portfolio.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.

# 12.10 FEAT-PORTFOLIO-TASK-AUTOMATIC-PORTFOLIO-BUILDER - TaskAutomaticPortfolioBuilder.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/TaskAutomaticPortfolioBuilder.jar`; 27 class declarations; SHA-256 `450ba385bf39bba43abaf92faa06dec7f30d2a8aca1daffb03ce4c24fae4a2d6`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/PortfolioMaster/TaskAutomaticPortfolioBuilder.md`; roadmap allocation `FEAT-PORTFOLIO-TASK-AUTOMATIC-PORTFOLIO-BUILDER`.
- **Owner:** `app/plugins/portfolio/TaskAutomaticPortfolioBuilder/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/TaskAutomaticPortfolioBuilder.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskAutomaticPortfolioBuilder/TaskAutomaticPortfolioBuilder.jar" com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.AutomaticPortfolioBuilder`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** `FR-PORTFOLIO-TASK-AUTOMATIC-PORTFOLIO-BUILDER-AUTOMATIC-PORTFOLIO-BUILDER-CONTRACT` → `com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.AutomaticPortfolioBuilder`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PORTFOLIO-TASK-AUTOMATIC-PORTFOLIO-BUILDER-AUTOMATIC-PORTFOLIO-BUILDER-START` → `com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.AutomaticPortfolioBuilder.start`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_task_automatic_portfolio_builder.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.

# 12.11 FEAT-PORTFOLIO-TASK-CREATE-PORTFOLIO - TaskCreatePortfolio.jar

## 1. Objective

- **Goal:** Implement the named portfolio selection/composition/result capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Compose and search portfolios with reconciled aggregate metrics.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/TaskCreatePortfolio.jar`; 1 class declarations; SHA-256 `939f4c1b46c4c87abe8294370b17d41f75cb1cd18d9cdfd913914bb6d8766c00`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/CustomProjects/TaskCreatePortfolio.md`; roadmap allocation `FEAT-PORTFOLIO-TASK-CREATE-PORTFOLIO`.
- **Owner:** `app/plugins/portfolio/TaskCreatePortfolio/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Portfolio task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/TaskCreatePortfolio.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskCreatePortfolio/TaskCreatePortfolio.jar" com.strategyquant.plugin.Task.impl.CreatePortfolio.CreatePortfolio`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named portfolio selection/composition/result capability; verify member identity, weights, alignment, aggregate accounting and search bounds.
- [ ] **Step 4:** `FR-PORTFOLIO-TASK-CREATE-PORTFOLIO-CREATE-PORTFOLIO-CONTRACT` → `com.strategyquant.plugin.Task.impl.CreatePortfolio.CreatePortfolio`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-PORTFOLIO-TASK-CREATE-PORTFOLIO-CREATE-PORTFOLIO-START` → `com.strategyquant.plugin.Task.impl.CreatePortfolio.CreatePortfolio.start`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-PORTFOLIO-TASK-CREATE-PORTFOLIO-CREATE-PORTFOLIO-GET-RUNNING-STATUS` → `com.strategyquant.plugin.Task.impl.CreatePortfolio.CreatePortfolio.getRunningStatus`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_portfolio_task_create_portfolio.py --no-cov`; expect member identity, weights, alignment, aggregate accounting and search bounds; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture member identity, weights, alignment, aggregate accounting and search bounds and visible failures.

# 12.12 P12 integration — Compose and search portfolios with reconciled aggregate metrics

## 1. Objective

- **Goal:** Compose and search portfolios with reconciled aggregate metrics.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P12; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/PortfolioComposer/PortfolioComposerWorkspace.tsx`, `ui/app/workspace/PortfolioMaster/PortfolioMasterWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/PortfolioComposer/composerDraft.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify member identity, weights, overlapping exposure, correlation and portfolio fitness.
- [ ] **Step 3:** Implement manual/automatic selection, aggregate accounting and portfolio resource lifecycle.
- [ ] **Step 4:** Connect Composer/Master selection, progress, charts and persisted portfolio revisions.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_portfolio_workflows_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/PortfolioComposer/composerDraft.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-portfolio-workflows-backend.spec.ts`. Assert member/weight round trips, aggregate equity, correlation and deterministic selection; reject missing member, nonaligned calendars, duplicate strategy and invalid weight.
- **Manual / Browser Verification:** Compose two fixture strategies; change weights; reload; run automatic search; reconcile portfolio totals with member ledgers.

## Phase completion gate

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
