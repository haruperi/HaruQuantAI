# P06 — Execution engine, accounting, trading options and stock picking

- **Source:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P02,P03,P05.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 5 tasks; current archive allocations and resource/integration tasks only.

# 6.1 FEAT-SIMULATOR-SETTINGS-ADVANCED-TM - SettingsAdvancedTM.jar

## 1. Objective

- **Goal:** Implement validated AdvancedTM settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute deterministic strategies and produce reconciled trade/account ledgers.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/SettingsAdvancedTM.jar`; 2 raw class entries; SHA-256 `4a62d88b22f87eeeded005cd121990f373b30fc125a8fe608b1e8ae95b11e30f`.
- **Inspected reference:** [SettingsAdvancedTM.md](sqx/Shared/SettingsAdvancedTM.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/SettingsAdvancedTM.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/SettingsAdvancedTM.jar" com.strategyquant.plugin.Settings.impl.AdvancedTM.AdvancedTMServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/simulator/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Advanced trade management, position sizing and trading option schemas; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptions`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/AdvancedTMService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/AdvancedTMCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/addNewExitPopup.html`.
- **Existing UI connection:** project simulation settings; exact retained source-map `ui/app/plugins/project/SettingsAdvancedTM/source-map.json`. Target `ui/app/plugins/project/SettingsAdvancedTM/AdvancedTMCtrl.ts`; wire server-owned trading/money-management settings, validation, run submission and reconciled execution output.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/simulator/management.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/simulator/sizing.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/simulator/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/README.md` (proposed simulator owner; ratification required)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_simulator_settings_advanced_tm.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/simulator_settings_advanced_tm.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/SettingsAdvancedTM/AdvancedTMCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/SettingsAdvancedTM/addNewExitPopup.tsx`
  - Display server-owned trading/money-management settings, validation, run submission and reconciled execution output from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/SettingsAdvancedTM/advancedTM.tsx`
  - Display server-owned trading/money-management settings, validation, run submission and reconciled execution output from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display server-owned trading/money-management settings, validation, run submission and reconciled execution output from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/FullSettingsView.tsx`
  - Display server-owned trading/money-management settings, validation, run submission and reconciled execution output from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/SettingsAdvancedTM/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-simulator-settings-advanced-tm.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-simulation-engine-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated AdvancedTM settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind server-owned trading/money-management settings, validation, run submission and reconciled execution output to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-SIMULATOR-SETTINGS-ADVANCED-TM-ADVANCED-TMSERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.AdvancedTM.AdvancedTMServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-SIMULATOR-SETTINGS-ADVANCED-TM-ADVANCED-TMSERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.AdvancedTM.AdvancedTMServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_simulator_settings_advanced_tm.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-simulator-settings-advanced-tm.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-simulation-engine-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise project simulation settings for FEAT-SIMULATOR-SETTINGS-ADVANCED-TM; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 6.2 FEAT-SIMULATOR-SETTINGS-MONEY-MANAGEMENT - SettingsMoneyManagement.jar

## 1. Objective

- **Goal:** Implement validated MoneyManagement settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute deterministic strategies and produce reconciled trade/account ledgers.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement/SettingsMoneyManagement.jar`; 1 raw class entries; SHA-256 `7798ced63fad323cb8591dcc4f0075a610147b27ccc9522a202e990e4ba8f57d`.
- **Inspected reference:** [SettingsMoneyManagement.md](sqx/Shared/SettingsMoneyManagement.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement/SettingsMoneyManagement.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement/SettingsMoneyManagement.jar" com.strategyquant.plugin.Settings.impl.MoneyManagement.MoneyManagementSettingsPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/simulator/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Advanced trade management, position sizing and trading option schemas; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptions`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement/MoneyManagementService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement/MoneyManagementCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement/views/moneyManagement.html`.
- **Existing UI connection:** project simulation settings; exact retained source-map `ui/app/plugins/project/SettingsMoneyManagement/source-map.json`. Target `ui/app/plugins/project/SettingsMoneyManagement/MoneyManagementCtrl.ts`; wire server-owned trading/money-management settings, validation, run submission and reconciled execution output.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/plugins/simulator/management.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/sizing.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/contracts.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/README.md` (proposed simulator owner; ratification required)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_simulator_settings_money_management.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/simulator_settings_money_management.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/SettingsMoneyManagement/MoneyManagementCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/SettingsMoneyManagement/views/moneyManagement.tsx`
  - Display server-owned trading/money-management settings, validation, run submission and reconciled execution output from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/SettingsMoneyManagement/module.ts`
  - Display server-owned trading/money-management settings, validation, run submission and reconciled execution output from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display server-owned trading/money-management settings, validation, run submission and reconciled execution output from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/FullSettingsView.tsx`
  - Display server-owned trading/money-management settings, validation, run submission and reconciled execution output from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/SettingsMoneyManagement/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-simulator-settings-money-management.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-simulation-engine-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated MoneyManagement settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind server-owned trading/money-management settings, validation, run submission and reconciled execution output to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-SIMULATOR-SETTINGS-MONEY-MANAGEMENT-MONEY-MANAGEMENT-SETTINGS-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.MoneyManagement.MoneyManagementSettingsPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-SIMULATOR-SETTINGS-MONEY-MANAGEMENT-MONEY-MANAGEMENT-SETTINGS-PLUGIN-GET-HANDLER` → `com.strategyquant.plugin.Settings.impl.MoneyManagement.MoneyManagementSettingsPlugin.getHandler()Lorg/eclipse/jetty/server/Handler;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-SIMULATOR-SETTINGS-MONEY-MANAGEMENT-MONEY-MANAGEMENT-SETTINGS-PLUGIN-GET-PRODUCT` → `com.strategyquant.plugin.Settings.impl.MoneyManagement.MoneyManagementSettingsPlugin.getProduct()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_simulator_settings_money_management.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-simulator-settings-money-management.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-simulation-engine-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise project simulation settings for FEAT-SIMULATOR-SETTINGS-MONEY-MANAGEMENT; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 6.3 FEAT-SIMULATOR-SETTINGS-OPTIONS - SettingsOptions.jar

## 1. Objective

- **Goal:** Implement validated Options settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute deterministic strategies and produce reconciled trade/account ledgers.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptions/SettingsOptions.jar`; 2 raw class entries; SHA-256 `8d661d85eeff6aa112ef97e59b909716a7d20be8192aafa19fc3a68416dc36a2`.
- **Inspected reference:** [SettingsOptions.md](sqx/Shared/SettingsOptions.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptions/SettingsOptions.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptions/SettingsOptions.jar" com.strategyquant.plugin.Settings.impl.Options.SettingsOptionsServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/simulator/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Advanced trade management, position sizing and trading option schemas; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptions`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptions/OptionsService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptions/OptionsCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsOptions/views/options.html`.
- **Existing UI connection:** project simulation settings; exact retained source-map `ui/app/plugins/project/SettingsOptions/source-map.json`. Target `ui/app/plugins/project/SettingsOptions/OptionsCtrl.ts`; wire server-owned trading/money-management settings, validation, run submission and reconciled execution output.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/plugins/simulator/management.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/sizing.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/contracts.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/README.md` (proposed simulator owner; ratification required)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_simulator_settings_options.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/simulator_settings_options.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/SettingsOptions/OptionsCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/SettingsOptions/views/options.tsx`
  - Display server-owned trading/money-management settings, validation, run submission and reconciled execution output from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/SettingsOptions/module.ts`
  - Display server-owned trading/money-management settings, validation, run submission and reconciled execution output from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Display server-owned trading/money-management settings, validation, run submission and reconciled execution output from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Builder/FullSettingsView.tsx`
  - Display server-owned trading/money-management settings, validation, run submission and reconciled execution output from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/SettingsOptions/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-simulator-settings-options.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-simulation-engine-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated Options settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind server-owned trading/money-management settings, validation, run submission and reconciled execution output to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-SIMULATOR-SETTINGS-OPTIONS-SETTINGS-OPTIONS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Options.SettingsOptionsServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-SIMULATOR-SETTINGS-OPTIONS-SETTINGS-OPTIONS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.Options.SettingsOptionsServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-SIMULATOR-SETTINGS-OPTIONS-SETTINGS-OPTIONS-SERVLET-ON-LIST` → `com.strategyquant.plugin.Settings.impl.Options.SettingsOptionsServlet.onList(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_simulator_settings_options.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-simulator-settings-options.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-simulation-engine-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise project simulation settings for FEAT-SIMULATOR-SETTINGS-OPTIONS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 6.4 FEAT-SIMULATOR-NINJATRADER-ENGINE - NinjaTrader engine research and execution qualification

## 1. Objective

- **Goal:** Qualify the advertised NinjaTrader backtest-engine behavior before exposing executable support.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/Snippets.jar`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/extend/Code/NinjaTrader`.
- **Donor:** `SQX_145_REFERENCE_ROOT/docs/overview/export-engines`.
- **Ownership:** proposed `FEAT-SIMULATOR-NINJATRADER-ENGINE` and `FR-SIMULATOR-NINJATRADER-ENGINE-CONSUMED-CONTRACTS`; owner `app/plugins/simulator/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** A full engine is advertised; no complete standalone engine body was found. Templates cannot substitute for engine evidence.
- **UI donors:** Retain the phase engine-selection/settings donors; the inspected export resources do not establish a separate NinjaTrader engine UI or runnable engine.

## 3. File Changes

- **Create:** `app/plugins/simulator/ninjatrader.py` — Qualify the advertised NinjaTrader backtest-engine behavior before exposing executable support.
- **Create:** `app/plugins/simulator/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_simulator_ninjatrader_engine.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-simulator_ninjatrader_engine-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Locate the actual engine body and engine selection/clock registration; keep this task blocked while absent.
- [ ] **Step 3:** Specify fills, session/calendar, order timing, costs and indicator availability from inspected evidence.
- [ ] **Step 4:** Compare independent normal/boundary/failure traces with simulator accounting and target-platform execution.
- [ ] **Step 5:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 6:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_simulator_ninjatrader_engine.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 6.5 P06 integration — Execute deterministic strategies and produce reconciled trade/account ledgers

## 1. Objective

- **Goal:** Execute deterministic strategies and produce reconciled trade/account ledgers.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`, P06; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/Builder/BuilderWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/Builder/fullSettings.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/AlgoWizard`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/AlgoWizard/index.html`.
- **Existing UI connection:** AlgoWizard; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`; wire strategy document load/save/validation, actual run inputs and result IDs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/plugins/simulator/engine.py` (proposed simulator owner; ratification required)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/simulator/clock.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/simulator/orders.py` (proposed simulator owner; ratification required)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/simulator/fills.py` (proposed simulator owner; ratification required)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/simulator/accounting.py` (proposed simulator owner; ratification required)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/simulator/management.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/simulator/sizing.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/strategy/compiler.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/strategy/runtime.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/stock_picking/engine.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/statistics/metrics.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/Builder/BuilderWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Modify:** `ui/app/workspace/Builder/builderClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/plugins/simulator/README.md` (proposed simulator owner; ratification required)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_simulation_engine_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-simulation-engine-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardModel.ts`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardResults.tsx`
  - Display strategy document load/save/validation, actual run inputs and result IDs from backend responses; preserve layout.
- **Create:** `ui/app/workspace/AlgoWizard/algoWizardClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/task-6-5.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify event ordering, alignment, sizing, fills, costs, same-bar precedence and rounding.
- [ ] **Step 3:** Implement strategy evaluation, order lifecycle, advanced management and stock-selection execution.
- [ ] **Step 4:** Persist run configuration, event trace, trades/equity and failures through host storage.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind strategy document load/save/validation, actual run inputs and result IDs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_simulation_engine_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/Builder/fullSettings.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-simulation-engine-backend.spec.ts`. Assert donor event traces, fills, position sizing, costs and reconciled PnL; reject same-bar ambiguity, session gap, missing price, invalid size and cancellation.
- **Manual / Browser Verification:** Run one saved fixture strategy; inspect orders/trades/equity; rerun the same configuration and compare traces under ratified tolerances.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-6-5.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-simulation-engine-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise AlgoWizard for 6.6; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
