# P05 — Strategy vocabulary, indicator/block catalog and numerical primitives

- **Source:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P03.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 7 tasks; current archive allocations and resource/integration tasks only.

# 5.1 FEAT-SHARED-SNIPPETS - Snippets.jar

## 1. Objective

- **Goal:** Inventory and implement enabled snippet families as behavior-owned FRs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Expose executable strategy blocks and qualified indicator primitives.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/Snippets.jar`; 1069 raw class entries; SHA-256 `6815d5acd6e411d078a423f80b605940e2778736d901cade987ea3f421d52924`.
- **Inspected reference:** [Snippets.md](sqx/Libraries/Snippets.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/Snippets.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/Snippets.jar" SQ.Blocks.BarAndTime.BarDayOfWeek`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/indicators/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Building-block/indicator catalog and formula families; sliced across consuming domains; downstream P06–P13,P16.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletConstants`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks/services/BlocksService.js`.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind backend block/constant schemas, typed ports, parameters and availability to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-SHARED-SNIPPETS-BAR-DAY-OF-WEEK-CONTRACT` → `SQ.Blocks.BarAndTime.BarDayOfWeek`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-SHARED-SNIPPETS-BAR-DAY-OF-WEEK-ON-BLOCK-EVALUATE` → `SQ.Blocks.BarAndTime.BarDayOfWeek.OnBlockEvaluate(I)D`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_shared_snippets.py --no-cov`; expect all 948 class dispositions, defaults, warm-up, formulas and boundary vectors; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture all 948 class dispositions, defaults, warm-up, formulas and boundary vectors and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-shared-snippets.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-strategy-primitives-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise strategy block selectors for FEAT-SHARED-SNIPPETS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 5.2 FEAT-STRATEGY-TA-LIB - ta-lib-0.4.0.jar

## 1. Objective

- **Goal:** Qualify consumed indicator formulas and executable indicator contracts.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Expose executable strategy blocks and qualified indicator primitives.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/ta-lib-0.4.0.jar`; 38 raw class entries; SHA-256 `c2d7757cc03a03519eee914c62e8a86596efa66e5c298ac9890aa59b3063aa34`.
- **Inspected reference:** [ta-lib-0.4.0.md](sqx/Libraries/ta-lib-0.4.0.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/ta-lib-0.4.0.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/ta-lib-0.4.0.jar" com.tictactec.ta.lib.CandleSetting`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/indicators/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Building-block/indicator catalog and formula families; sliced across consuming domains; downstream P06–P13,P16.
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
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-STRATEGY-TA-LIB-CANDLE-SETTING-CONTRACT` → `com.tictactec.ta.lib.CandleSetting`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-STRATEGY-TA-LIB-CANDLE-SETTING-COPY-FROM` → `com.tictactec.ta.lib.CandleSetting.CopyFrom(Lcom/tictactec/ta/lib/CandleSetting;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_strategy_ta_lib.py --no-cov`; expect lookback, output alignment, missing values and numerical tolerances; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture lookback, output alignment, missing values and numerical tolerances and visible failures.


# 5.3 FEAT-STRATEGY-SERVLET-CONSTANTS - ServletConstants.jar

## 1. Objective

- **Goal:** Expose Constants commands through the owning domain routes.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Expose executable strategy blocks and qualified indicator primitives.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletConstants/ServletConstants.jar`; 2 raw class entries; SHA-256 `188e5c2312faf36246d0c7d71a2312a9a51f21c2049bec9cd30b98fedec07e24`.
- **Inspected reference:** [ServletConstants.md](sqx/Shared/ServletConstants.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletConstants/ServletConstants.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletConstants/ServletConstants.jar" com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/indicators/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Versioned block/constant catalogs and valid parameter schemas; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletConstants`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks/services/BlocksService.js`.
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
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind backend block/constant schemas, typed ports, parameters and availability to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-STRATEGY-SERVLET-CONSTANTS-CONSTANTS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-STRATEGY-SERVLET-CONSTANTS-CONSTANTS-SERVLET-GET-INSTANCE` → `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet.getInstance()Lcom/strategyquant/plugin/Servlet/impl/Constants/ConstantsServlet;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-STRATEGY-SERVLET-CONSTANTS-CONSTANTS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

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

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks/SettingsBlocks.jar`; 2 raw class entries; SHA-256 `3fab494fec49c6d86e898f1c0e2dfe359496b41f79b607ef071bd9a8fdf1640b`.
- **Inspected reference:** [SettingsBlocks.md](sqx/Shared/SettingsBlocks.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks/SettingsBlocks.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks/SettingsBlocks.jar" com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/indicators/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Versioned block/constant catalogs and valid parameter schemas; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletConstants`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks/services/BlocksService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks/BlocksCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks/views/blockParametersPopup.html`.
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
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind backend block/constant schemas, typed ports, parameters and availability to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-STRATEGY-SETTINGS-BLOCKS-BLOCKS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-STRATEGY-SETTINGS-BLOCKS-BLOCKS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-STRATEGY-SETTINGS-BLOCKS-BLOCKS-SERVLET-ON-LIST` → `com.strategyquant.plugin.Settings.impl.Blocks.BlocksServlet.onList()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_strategy_settings_blocks.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-strategy-settings-blocks.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-strategy-primitives-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise strategy block selectors for FEAT-STRATEGY-SETTINGS-BLOCKS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 5.5 FEAT-INDICATOR-COT-BLOCKS - COT indicator and signal resource catalog

## 1. Objective

- **Goal:** Implement the retained COT calculations and signals with source-bound field/time semantics.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/Snippets.jar`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/extend/Snippets/SQ/Blocks/Indicators/COT`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/extend/Snippets/SQ/Blocks/Indicators/HighestLowest/COTEmergencyExitLong.java`.
- **Ownership:** proposed `FEAT-INDICATOR-COT-BLOCKS` and `FR-INDICATOR-COT-BLOCKS-CONSUMED-CONTRACTS`; owner `app/plugins/indicators/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** Underlying time-map lookup and provider history are unresolved; declaration/formula inspection is not numerical parity.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks`; connect the retained Builder/AlgoWizard block selectors to the approved catalog.

## 3. File Changes

- **Create:** `app/plugins/indicators/impl/cot.py` — Implement the retained COT calculations and signals with source-bound field/time semantics.
- **Create:** `app/plugins/indicators/cot_catalog.py` — Implement the retained COT calculations and signals with source-bound field/time semantics.
- **Create:** `app/plugins/indicators/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_indicator_cot_blocks.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-indicator_cot_blocks-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Disposition all 67 COT-folder additions and both emergency exits; enumerate each consumed function/parameter.
- [ ] **Step 3:** Confirm formulas from readable bodies and compiled metadata; resolve lazy initialization and missing-data conflicts.
- [ ] **Step 4:** Pin time mapping, shifts, defaults, field indices and engine coverage; test independent vectors and failures.
- [ ] **Step 5:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 6:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_indicator_cot_blocks.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 5.6 FEAT-INDICATOR-PROFILE-BLOCKS - Volume/market profile and AnchoredVWAP extensions

## 1. Objective

- **Goal:** Qualify new signals and changed profile kernels without treating them as uniform platform support.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/Snippets.jar`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/extend/Snippets/SQ/Blocks/Indicators/VolumeProfile`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/extend/Snippets/SQ/Blocks/Indicators/TPOProfile`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/extend/Snippets/SQ/Blocks/Indicators/AnchoredVWAP`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/extend/Snippets/SQ/Internal/VolumeProfileIndicatorChart.java`.
- **Ownership:** proposed `FEAT-INDICATOR-PROFILE-BLOCKS` and `FR-INDICATOR-PROFILE-BLOCKS-CONSUMED-CONTRACTS`; owner `app/plugins/indicators/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** A wrapper/annotation does not establish an underlying kernel or cross-platform equivalence.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks`; connect retained block selectors; no new layout is established by indicator source alone.

## 3. File Changes

- **Create:** `app/plugins/indicators/impl/volume_profile.py` — Qualify new signals and changed profile kernels without treating them as uniform platform support.
- **Create:** `app/plugins/indicators/impl/tpo_profile.py` — Qualify new signals and changed profile kernels without treating them as uniform platform support.
- **Create:** `app/plugins/indicators/impl/anchored_vwap.py` — Qualify new signals and changed profile kernels without treating them as uniform platform support.
- **Create:** `app/plugins/indicators/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_indicator_profile_blocks.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Modify:** `ui/app/host/HeaderApplications.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-indicator_profile_blocks-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Disposition the 32 new VP-folder files and changed kernels/TPO/AnchoredVWAP contracts.
- [ ] **Step 3:** Inspect bin sizing, session boundaries, POC/value-area ties, Delta, rounding and warmup; preserve exact operation order.
- [ ] **Step 4:** Record per-block ForEngine limits: generic VolumeProfile omits NT; selected signals and TPO include NT.
- [ ] **Step 5:** Test session transitions, empty bins, equal thresholds, custom hours and independently observed vectors.
- [ ] **Step 6:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 7:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 8:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_indicator_profile_blocks.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 5.7 P05 integration — Expose executable strategy blocks and qualified indicator primitives

## 1. Objective

- **Goal:** Expose executable strategy blocks and qualified indicator primitives.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`, P05; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/AlgoWizard/AlgoWizardWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/AlgoWizard/algoWizardModel.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletConstants`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/SettingsBlocks/services/BlocksService.js`.
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
- **Create:** `ui/tests/unit/backend-connections/task-5-7.test.ts`
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

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-5-7.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-strategy-primitives-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise strategy block selectors for 5.7; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
