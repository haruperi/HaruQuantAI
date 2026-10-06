# P05 — Strategy vocabulary, indicator/block catalog and numerical primitives

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P03.
- **Scope:** 4 JAR feature tasks, 0 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.

# 5.1 FEAT-SHARED-SNIPPETS - Snippets.jar

## 1. Objective

- **Goal:** Inventory and implement enabled snippet families as behavior-owned FRs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Expose executable strategy blocks and qualified indicator primitives.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/Snippets.jar`; 948 class declarations; SHA-256 `d6dcad795f670b1b12cbbe772ec6f15d98c2fb5ab265f0f63505eb0e589229a0`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-SHARED-SNIPPETS`.
- **Owner:** `app/plugins/indicators/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Building-block/indicator catalog and formula families; sliced across consuming domains; downstream P06–P13,P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/Snippets.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/Snippets.jar" SQ.Blocks.BarAndTime.BarDayOfWeek`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks`; `SQX_REFERENCE_ROOT/internal/plugins/ServletConstants`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks/services/BlocksService.js`.
- **Existing UI connection:** strategy block selectors; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/settings/BuildingBlocksTab.tsx`; wire backend block/constant schemas, typed ports, parameters and availability.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/indicators/catalog.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/indicators/base.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/indicators/validation.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/indicators/impl/bar_day_of_week.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/indicators/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_shared_snippets.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/shared_snippets.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/settings/BuildingBlocksTab.tsx`
  - Display backend block/constant schemas, typed ports, parameters and availability from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardBlockEditor.tsx`
  - Display backend block/constant schemas, typed ports, parameters and availability from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardModel.ts`
  - Display backend block/constant schemas, typed ports, parameters and availability from backend responses; preserve layout.
- **Create:** `ui/app/workspace/AlgoWizard/algoWizardClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-shared-snippets.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-strategy-primitives-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Inventory and implement enabled snippet families as behavior-owned FRs; verify all 948 class dispositions, defaults, warm-up, formulas and boundary vectors.
- [ ] **Step 4:** `FR-SHARED-SNIPPETS-BAR-DAY-OF-WEEK-CONTRACT` → `SQ.Blocks.BarAndTime.BarDayOfWeek`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-SHARED-SNIPPETS-BAR-DAY-OF-WEEK-ON-BLOCK-EVALUATE` → `SQ.Blocks.BarAndTime.BarDayOfWeek.OnBlockEvaluate`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind backend block/constant schemas, typed ports, parameters and availability to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_shared_snippets.py --no-cov`; expect all 948 class dispositions, defaults, warm-up, formulas and boundary vectors; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture all 948 class dispositions, defaults, warm-up, formulas and boundary vectors and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-shared-snippets.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-strategy-primitives-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise strategy block selectors for FEAT-SHARED-SNIPPETS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 5.2 FEAT-STRATEGY-TA-LIB - ta-lib.jar

## 1. Objective

- **Goal:** Qualify consumed indicator formulas and executable indicator contracts.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Expose executable strategy blocks and qualified indicator primitives.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/ta-lib.jar`; 48 class declarations; SHA-256 `6495cc4f5ed2ed6220686dd7051c6f42ebeafeab46689b16b5763cffe34a0574`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-STRATEGY-TA-LIB`.
- **Owner:** `app/plugins/indicators/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Building-block/indicator catalog and formula families; sliced across consuming domains; downstream P06–P13,P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/ta-lib.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/ta-lib.jar" com.tictactec.ta.lib.CandleSetting`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds strategy block selectors through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/indicators/catalog.py` (proposed earlier in FEAT-SHARED-SNIPPETS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/indicators/base.py` (proposed earlier in FEAT-SHARED-SNIPPETS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/indicators/validation.py` (proposed earlier in FEAT-SHARED-SNIPPETS)
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/indicators/impl/qualified_vectors.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/indicators/README.md` (proposed earlier in FEAT-SHARED-SNIPPETS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_strategy_ta_lib.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/strategy_ta_lib.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify consumed indicator formulas and executable indicator contracts; verify lookback, output alignment, missing values and numerical tolerances.
- [ ] **Step 4:** `FR-STRATEGY-TA-LIB-CANDLE-SETTING-CONTRACT` → `com.tictactec.ta.lib.CandleSetting`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-STRATEGY-TA-LIB-CANDLE-SETTING-COPY-FROM` → `com.tictactec.ta.lib.CandleSetting.CopyFrom`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_strategy_ta_lib.py --no-cov`; expect lookback, output alignment, missing values and numerical tolerances; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture lookback, output alignment, missing values and numerical tolerances and visible failures.

# 5.3 FEAT-STRATEGY-SERVLET-CONSTANTS - ServletConstants.jar

## 1. Objective

- **Goal:** Expose Constants commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Expose executable strategy blocks and qualified indicator primitives.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletConstants/ServletConstants.jar`; 2 class declarations; SHA-256 `0269ef64e3e4318025b53301ebb61eeef39c585f751ad4a5dd11425687928acf`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ServletConstants.md`; roadmap allocation `FEAT-STRATEGY-SERVLET-CONSTANTS`.
- **Owner:** `app/plugins/indicators/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Versioned block/constant catalogs and valid parameter schemas; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletConstants/ServletConstants.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ServletConstants/ServletConstants.jar" com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/ServletConstants`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks/services/BlocksService.js`.
- **Existing UI connection:** strategy block selectors; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/settings/BuildingBlocksTab.tsx`; wire backend block/constant schemas, typed ports, parameters and availability.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/plugins/indicators/catalog.py` (proposed earlier in FEAT-SHARED-SNIPPETS)
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/indicators/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/indicators/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/indicators/README.md` (proposed earlier in FEAT-SHARED-SNIPPETS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_strategy_servlet_constants.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/strategy_servlet_constants.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/settings/BuildingBlocksTab.tsx`
  - Display backend block/constant schemas, typed ports, parameters and availability from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardBlockEditor.tsx`
  - Display backend block/constant schemas, typed ports, parameters and availability from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardModel.ts`
  - Display backend block/constant schemas, typed ports, parameters and availability from backend responses; preserve layout.
- **Create:** `ui/app/workspace/AlgoWizard/algoWizardClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-strategy-servlet-constants.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-strategy-primitives-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Expose Constants commands through the owning domain routes; verify command parsing, typed outputs, authority, validation errors and cancellation.
- [ ] **Step 4:** `FR-STRATEGY-SERVLET-CONSTANTS-CONSTANTS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-STRATEGY-SERVLET-CONSTANTS-CONSTANTS-SERVLET-GET-INSTANCE` → `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet.getInstance`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-STRATEGY-SERVLET-CONSTANTS-CONSTANTS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind backend block/constant schemas, typed ports, parameters and availability to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_strategy_servlet_constants.py --no-cov`; expect command parsing, typed outputs, authority, validation errors and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture command parsing, typed outputs, authority, validation errors and cancellation and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-strategy-servlet-constants.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-strategy-primitives-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise strategy block selectors for FEAT-STRATEGY-SERVLET-CONSTANTS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 5.4 FEAT-STRATEGY-SETTINGS-BLOCKS - SettingsBlocks.jar

## 1. Objective

- **Goal:** Implement validated Blocks settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Expose executable strategy blocks and qualified indicator primitives.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks/SettingsBlocks.jar`; 2 class declarations; SHA-256 `34983dd20362d2b1c0645fe1dd87250f8c154bf8763904e61d736a509f72d31d`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsBlocks.md`; roadmap allocation `FEAT-STRATEGY-SETTINGS-BLOCKS`.
- **Owner:** `app/plugins/indicators/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Versioned block/constant catalogs and valid parameter schemas; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks/SettingsBlocks.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks/SettingsBlocks.jar" com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks`; `SQX_REFERENCE_ROOT/internal/plugins/ServletConstants`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks/services/BlocksService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks/BlocksCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks/views/blockParametersPopup.html`.
- **Existing UI connection:** strategy block selectors; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/settings/BuildingBlocksTab.tsx`; wire backend block/constant schemas, typed ports, parameters and availability.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/plugins/indicators/catalog.py` (proposed earlier in FEAT-SHARED-SNIPPETS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/indicators/routes.py` (proposed earlier in FEAT-STRATEGY-SERVLET-CONSTANTS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/indicators/contracts.py` (proposed earlier in FEAT-STRATEGY-SERVLET-CONSTANTS)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/indicators/README.md` (proposed earlier in FEAT-SHARED-SNIPPETS)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_strategy_settings_blocks.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/strategy_settings_blocks.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/settings/BuildingBlocksTab.tsx`
  - Display backend block/constant schemas, typed ports, parameters and availability from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardBlockEditor.tsx`
  - Display backend block/constant schemas, typed ports, parameters and availability from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardModel.ts`
  - Display backend block/constant schemas, typed ports, parameters and availability from backend responses; preserve layout.
- **Create:** `ui/app/workspace/AlgoWizard/algoWizardClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-strategy-settings-blocks.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-strategy-primitives-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated Blocks settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** `FR-STRATEGY-SETTINGS-BLOCKS-BLOCKS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-STRATEGY-SETTINGS-BLOCKS-BLOCKS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-STRATEGY-SETTINGS-BLOCKS-BLOCKS-SERVLET-LOAD-STOCKPICKER-DEFAULT-BLOCKS` → `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet.loadStockpickerDefaultBlocks`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind backend block/constant schemas, typed ports, parameters and availability to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_strategy_settings_blocks.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-strategy-settings-blocks.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-strategy-primitives-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise strategy block selectors for FEAT-STRATEGY-SETTINGS-BLOCKS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 5.5 P05 integration — Expose executable strategy blocks and qualified indicator primitives

## 1. Objective

- **Goal:** Expose executable strategy blocks and qualified indicator primitives.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P05; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/AlgoWizard/algoWizardModel.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks`; `SQX_REFERENCE_ROOT/internal/plugins/ServletConstants`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsBlocks/services/BlocksService.js`.
- **Existing UI connection:** strategy block selectors; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/Builder/settings/BuildingBlocksTab.tsx`; wire backend block/constant schemas, typed ports, parameters and availability.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/plugins/indicators/catalog.py` (proposed earlier in FEAT-SHARED-SNIPPETS)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/indicators/base.py` (proposed earlier in FEAT-SHARED-SNIPPETS)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/indicators/validation.py` (proposed earlier in FEAT-SHARED-SNIPPETS)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/indicators/contracts.py` (proposed earlier in FEAT-STRATEGY-SERVLET-CONSTANTS)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/strategy/nodes.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/strategy/parameters.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/strategy/types.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/expressions/evaluator.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/AlgoWizard/algoWizardClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/plugins/indicators/README.md` (proposed earlier in FEAT-SHARED-SNIPPETS)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_strategy_primitives_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-strategy-primitives-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/Builder/settings/BuildingBlocksTab.tsx`
  - Display backend block/constant schemas, typed ports, parameters and availability from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardBlockEditor.tsx`
  - Display backend block/constant schemas, typed ports, parameters and availability from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/AlgoWizard/algoWizardModel.ts`
  - Display backend block/constant schemas, typed ports, parameters and availability from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/task-5-5.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Inventory all enabled Snippets/indicator families; specify parameters, types, defaults and warm-up.
- [ ] **Step 3:** Implement independently written formulas/evaluators with missing-value and unit policies.
- [ ] **Step 4:** Serve an authoritative versioned block catalog to authoring and generation consumers.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind backend block/constant schemas, typed ports, parameters and availability to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_strategy_primitives_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/AlgoWizard/algoWizardModel.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-strategy-primitives-backend.spec.ts`. Assert formula vectors, warm-up counts, defaults, input/output types and catalog versioning; reject insufficient samples, nonfinite values, invalid parameter ranges and unknown versions.
- **Manual / Browser Verification:** Open AlgoWizard; select an indicator; compare its parameter schema and computed fixture values with inspected donor outputs.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-5-5.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-strategy-primitives-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise strategy block selectors for 5.5; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
