# P03 — Data Manager: datasets, instruments, sessions and custom data

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P02.
- **Scope:** 11 JAR feature tasks, 2 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.

# 3.1 FEAT-DATA-JODA-TIME - joda-time.jar

## 1. Objective

- **Goal:** Provide explicit timezone/session conversion through datetime and tzdata.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Manage authoritative datasets, instruments, sessions and custom bars.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/joda-time.jar`; 232 class declarations; SHA-256 `602fd8006641f8b3afd589acbd9c9b356712bdcf0f9323557ec8648cd234983b`.
- **Inspected reference:** No dedicated docs/sqx coverage; expand archive inspection; roadmap allocation `FEAT-DATA-JODA-TIME`.
- **Owner:** `app/plugins/data/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Market-data structures, readers/writers, bars, instrument/session time rules; downstream P04–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/joda-time.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/joda-time.jar" org.joda.time.Chronology`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Data Manager through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/plugins/data/models.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data/bars.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data/sessions.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data/storage.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_joda_time.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_joda_time.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Provide explicit timezone/session conversion through datetime and tzdata; verify DST gaps/folds, timestamp units and timezone validation.
- [ ] **Step 4:** `FR-DATA-JODA-TIME-CHRONOLOGY-CONTRACT` → `org.joda.time.Chronology`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-DATA-JODA-TIME-CHRONOLOGY-GET-ZONE` → `org.joda.time.Chronology.getZone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-DATA-JODA-TIME-CHRONOLOGY-WITH-UTC` → `org.joda.time.Chronology.withUTC`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_joda_time.py --no-cov`; expect DST gaps/folds, timestamp units and timezone validation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture DST gaps/folds, timestamp units and timezone validation and visible failures.

# 3.2 FEAT-DATA-SQ-DATA-LIB - SQDataLib.jar

## 1. Objective

- **Goal:** Implement versioned market-data models, readers/writers and instrument/session semantics.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Manage authoritative datasets, instruments, sessions and custom bars.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/SQDataLib.jar`; 195 class declarations; SHA-256 `8bf892b35becda5070dc153f4a5fed955d9d724c78686ebb354776fd3a408829`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SQDataLib.md`; roadmap allocation `FEAT-DATA-SQ-DATA-LIB`.
- **Owner:** `app/plugins/data/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Market-data structures, readers/writers, bars, instrument/session time rules; downstream P04–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/SQDataLib.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/SQDataLib.jar" com.strategyquant.datalib.instrument.AliasManager`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Data Manager through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/plugins/data/models.py` (proposed earlier in FEAT-DATA-JODA-TIME)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/data/bars.py` (proposed earlier in FEAT-DATA-JODA-TIME)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/data/sessions.py` (proposed earlier in FEAT-DATA-JODA-TIME)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/data/storage.py` (proposed earlier in FEAT-DATA-JODA-TIME)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/data/README.md` (proposed earlier in FEAT-DATA-JODA-TIME)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_sq_data_lib.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_sq_data_lib.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement versioned market-data models, readers/writers and instrument/session semantics; verify bar precision, data ordering, reader bounds and metadata preservation.
- [ ] **Step 4:** `FR-DATA-SQ-DATA-LIB-ALIAS-MANAGER-CONTRACT` → `com.strategyquant.datalib.instrument.AliasManager`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-DATA-SQ-DATA-LIB-ALIAS-MANAGER-GET-ALIASES` → `com.strategyquant.datalib.instrument.AliasManager.getAliases`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-DATA-SQ-DATA-LIB-ALIAS-MANAGER-GET-ALIAS` → `com.strategyquant.datalib.instrument.AliasManager.getAlias`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_sq_data_lib.py --no-cov`; expect bar precision, data ordering, reader bounds and metadata preservation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture bar precision, data ordering, reader bounds and metadata preservation and visible failures.

# 3.3 FEAT-DATA-APP-DATA-MANAGER - AppDataManager.jar

## 1. Objective

- **Goal:** Mount the DataManager workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Manage authoritative datasets, instruments, sessions and custom bars.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager/AppDataManager.jar`; 1 class declarations; SHA-256 `3e0b8898e1bb8c9c7c91eb17ec7a99a481fae83e37c935c7595b2c71d1f25447`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/DataManager/AppDataManager.md`; roadmap allocation `FEAT-DATA-APP-DATA-MANAGER`.
- **Owner:** `app/workspace/DataManager/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppDataManager/AppDataManager.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppDataManager/AppDataManager.jar" com.strategyquant.plugin.App.impl.DataManager.DataManagerAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager`; `SQX_REFERENCE_ROOT/internal/web/QDM`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager/module.js`.
- **Existing UI connection:** Data Manager; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Common/dataManagerStore.ts`; wire dataset/catalog load and mutation, server resource IDs and authoritative row counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/DataManager/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_app_data_manager.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_app_data_manager.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display dataset/catalog load and mutation, server resource IDs and authoritative row counts from backend responses; preserve layout.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-data-app-data-manager.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-manager-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the DataManager workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-DATA-APP-DATA-MANAGER-DATA-MANAGER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.DataManager.DataManagerAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-DATA-APP-DATA-MANAGER-DATA-MANAGER-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.DataManager.DataManagerAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-DATA-APP-DATA-MANAGER-DATA-MANAGER-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.DataManager.DataManagerAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/catalog load and mutation, server resource IDs and authoritative row counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_app_data_manager.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-app-data-manager.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-manager-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Data Manager for FEAT-DATA-APP-DATA-MANAGER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 3.4 FEAT-DATA-DATA-MANAGER-BASKET - DataManagerBasket.jar

## 1. Objective

- **Goal:** Implement Basket data-management services and typed UI projections.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Manage authoritative datasets, instruments, sessions and custom bars.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerBasket/DataManagerBasket.jar`; 3 class declarations; SHA-256 `7878ca809dcc933f462fbc1f203ea7fb2d994af4e7af80f070ecf8c073ab322d`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/DataManager/DataManagerBasket.md`; roadmap allocation `FEAT-DATA-DATA-MANAGER-BASKET`.
- **Owner:** `app/workspace/DataManager/DataManagerBasket/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Dataset/instrument/session/basket/custom-data administration; downstream P04–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerBasket/DataManagerBasket.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerBasket/DataManagerBasket.jar" com.strategyquant.plugin.DataManager.impl.Basket.BasketServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerBasket`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DataManagerBasket/service/BasketService.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerBasket/controllers/BasketsCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerBasket/views/addBasketModal.html`.
- **Existing UI connection:** stock groups/baskets; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Catalogs/StockGroups/stockGroupsStore.ts`; wire stock-group/basket membership load/save and update status.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.
- **Retained UI limit:** Stock-group dialogs are a candidate consumer; equivalence to donor baskets is unverified. Ratify semantics and required controls before binding.

## 3. File Changes

- **Create:** `app/workspace/DataManager/DataManagerBasket/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerBasket/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerBasket/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerBasket/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_data_manager_basket.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_data_manager_basket.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Catalogs/StockGroups/stockGroupsStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/Catalogs/StockGroups/StockGroupEditorDialog.tsx`
  - Display stock-group/basket membership load/save and update status from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display stock-group/basket membership load/save and update status from backend responses; preserve layout.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-data-data-manager-basket.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-manager-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement Basket data-management services and typed UI projections; verify stable identity, units, validation, isolated persistence and reload.
- [ ] **Step 4:** `FR-DATA-DATA-MANAGER-BASKET-BASKET-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataManager.impl.Basket.BasketServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-DATA-DATA-MANAGER-BASKET-BASKET-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataManager.impl.Basket.BasketServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind stock-group/basket membership load/save and update status to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_data_manager_basket.py --no-cov`; expect stable identity, units, validation, isolated persistence and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture stable identity, units, validation, isolated persistence and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-data-manager-basket.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-manager-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise stock groups/baskets for FEAT-DATA-DATA-MANAGER-BASKET; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 3.5 FEAT-DATA-DATA-MANAGER-BROKER - DataManagerBroker.jar

## 1. Objective

- **Goal:** Implement Broker data-management services and typed UI projections.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Manage authoritative datasets, instruments, sessions and custom bars.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerBroker/DataManagerBroker.jar`; 6 class declarations; SHA-256 `ddf4ef361c3b9b52333c4ba93a74cd0f6f2a4ab190878c4c521ae04944ae55fd`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/DataManager/DataManagerBroker.md`; roadmap allocation `FEAT-DATA-DATA-MANAGER-BROKER`.
- **Owner:** `app/workspace/DataManager/DataManagerBroker/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Dataset/instrument/session/basket/custom-data administration; downstream P04–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerBroker/DataManagerBroker.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerBroker/DataManagerBroker.jar" com.strategyquant.plugin.DataManager.impl.Broker.BrokerServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerBroker`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DataManagerBroker/service/BrokerService.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerBroker/controllers/BrokersCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerBroker/views/addBrokerModal.html`.
- **Existing UI connection:** broker profiles; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Catalogs/BrokerProfiles/BrokerProfileEditorDialog.tsx`; wire broker-profile load/save/import and server-owned update jobs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/DataManager/DataManagerBroker/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerBroker/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerBroker/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerBroker/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_data_manager_broker.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_data_manager_broker.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Catalogs/BrokerProfiles/BrokerProfileEditorDialog.tsx`
  - Display broker-profile load/save/import and server-owned update jobs from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/data_source/Catalogs/BrokerProfiles/brokerProfiles.ts`
  - Display broker-profile load/save/import and server-owned update jobs from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display broker-profile load/save/import and server-owned update jobs from backend responses; preserve layout.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-data-data-manager-broker.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-manager-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement Broker data-management services and typed UI projections; verify stable identity, units, validation, isolated persistence and reload.
- [ ] **Step 4:** `FR-DATA-DATA-MANAGER-BROKER-BROKER-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataManager.impl.Broker.BrokerServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-DATA-DATA-MANAGER-BROKER-BROKER-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataManager.impl.Broker.BrokerServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind broker-profile load/save/import and server-owned update jobs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_data_manager_broker.py --no-cov`; expect stable identity, units, validation, isolated persistence and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture stable identity, units, validation, isolated persistence and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-data-manager-broker.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-manager-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise broker profiles for FEAT-DATA-DATA-MANAGER-BROKER; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 3.6 FEAT-DATA-DATA-MANAGER-CUSTOM-DATA - DataManagerCustomData.jar

## 1. Objective

- **Goal:** Implement CustomData data-management services and typed UI projections.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Manage authoritative datasets, instruments, sessions and custom bars.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/DataManagerCustomData.jar`; 5 class declarations; SHA-256 `6fd3ed5e49ae80ff29fd08498ce46644b17a38c17c829503788c9bb4cf9f91d9`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/DataManager/DataManagerCustomData.md`; roadmap allocation `FEAT-DATA-DATA-MANAGER-CUSTOM-DATA`.
- **Owner:** `app/workspace/DataManager/DataManagerCustomData/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Dataset/instrument/session/basket/custom-data administration; downstream P04–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/DataManagerCustomData.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/DataManagerCustomData.jar" com.strategyquant.plugin.DataManager.impl.CustomData.CustomDataServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerCustomData`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/DMCustomDataService.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/DMCustomDataCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/add/CustomDataAddCtrl.js`.
- **Existing UI connection:** custom data; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Indicators/externalIndicatorsStore.ts`; wire custom-data/indicator import, normalized values and error reporting.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/DataManager/DataManagerCustomData/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerCustomData/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerCustomData/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerCustomData/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_data_manager_custom_data.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_data_manager_custom_data.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Indicators/externalIndicatorsStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display custom-data/indicator import, normalized values and error reporting from backend responses; preserve layout.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-data-data-manager-custom-data.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-manager-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement CustomData data-management services and typed UI projections; verify stable identity, units, validation, isolated persistence and reload.
- [ ] **Step 4:** `FR-DATA-DATA-MANAGER-CUSTOM-DATA-CUSTOM-DATA-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataManager.impl.CustomData.CustomDataServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-DATA-DATA-MANAGER-CUSTOM-DATA-CUSTOM-DATA-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataManager.impl.CustomData.CustomDataServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind custom-data/indicator import, normalized values and error reporting to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_data_manager_custom_data.py --no-cov`; expect stable identity, units, validation, isolated persistence and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture stable identity, units, validation, isolated persistence and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-data-manager-custom-data.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-manager-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise custom data for FEAT-DATA-DATA-MANAGER-CUSTOM-DATA; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 3.7 FEAT-DATA-DATA-MANAGER-DATA - DataManagerData.jar

## 1. Objective

- **Goal:** Implement Data data-management services and typed UI projections.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Manage authoritative datasets, instruments, sessions and custom bars.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData/DataManagerData.jar`; 35 class declarations; SHA-256 `5a050f2411038160bd386a58942c80a209df75612c0aabdd85c4f307817d8ad0`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/DataManager/DataManagerData.md`; roadmap allocation `FEAT-DATA-DATA-MANAGER-DATA`.
- **Owner:** `app/workspace/DataManager/DataManagerData/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Dataset/instrument/session/basket/custom-data administration; downstream P04–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerData/DataManagerData.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerData/DataManagerData.jar" com.strategyquant.plugin.DataManager.impl.Data.DataServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData`; `SQX_REFERENCE_ROOT/internal/web/QDM`; `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData/DMDataService.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData/DMDataCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData/addBrPopup.html`.
- **Existing UI connection:** Data Manager; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Common/dataManagerStore.ts`; wire dataset/catalog load and mutation, server resource IDs and authoritative row counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/DataManager/DataManagerData/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerData/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerData/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerData/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_data_manager_data.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_data_manager_data.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display dataset/catalog load and mutation, server resource IDs and authoritative row counts from backend responses; preserve layout.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-data-data-manager-data.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-manager-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement Data data-management services and typed UI projections; verify stable identity, units, validation, isolated persistence and reload.
- [ ] **Step 4:** `FR-DATA-DATA-MANAGER-DATA-DATA-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataManager.impl.Data.DataServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-DATA-DATA-MANAGER-DATA-DATA-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataManager.impl.Data.DataServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/catalog load and mutation, server resource IDs and authoritative row counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_data_manager_data.py --no-cov`; expect stable identity, units, validation, isolated persistence and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture stable identity, units, validation, isolated persistence and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-data-manager-data.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-manager-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Data Manager for FEAT-DATA-DATA-MANAGER-DATA; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 3.8 FEAT-DATA-DATA-MANAGER-HOME - DataManagerHome.jar

## 1. Objective

- **Goal:** Implement Home data-management services and typed UI projections.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Manage authoritative datasets, instruments, sessions and custom bars.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerHome/DataManagerHome.jar`; 2 class declarations; SHA-256 `3cf66b96908d25488981371c8dffeba035b2ce638f4082cb7d1065b8e982d7f3`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/DataManager/DataManagerHome.md`; roadmap allocation `FEAT-DATA-DATA-MANAGER-HOME`.
- **Owner:** `app/workspace/DataManager/DataManagerHome/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Dataset/instrument/session/basket/custom-data administration; downstream P04–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerHome/DataManagerHome.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerHome/DataManagerHome.jar" com.strategyquant.plugin.DataManager.impl.Home.HomeServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerHome`; `SQX_REFERENCE_ROOT/internal/web/QDM`; `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DataManagerHome/DMHomeService.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerHome/DMHomeCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerHome/home.html`.
- **Existing UI connection:** Data Manager; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Common/dataManagerStore.ts`; wire dataset/catalog load and mutation, server resource IDs and authoritative row counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/DataManager/DataManagerHome/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerHome/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerHome/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerHome/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_data_manager_home.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_data_manager_home.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display dataset/catalog load and mutation, server resource IDs and authoritative row counts from backend responses; preserve layout.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-data-data-manager-home.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-manager-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement Home data-management services and typed UI projections; verify stable identity, units, validation, isolated persistence and reload.
- [ ] **Step 4:** `FR-DATA-DATA-MANAGER-HOME-HOME-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataManager.impl.Home.HomeServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-DATA-DATA-MANAGER-HOME-HOME-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataManager.impl.Home.HomeServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/catalog load and mutation, server resource IDs and authoritative row counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_data_manager_home.py --no-cov`; expect stable identity, units, validation, isolated persistence and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture stable identity, units, validation, isolated persistence and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-data-manager-home.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-manager-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Data Manager for FEAT-DATA-DATA-MANAGER-HOME; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 3.9 FEAT-DATA-DATA-MANAGER-INSTRUMENTS - DataManagerInstruments.jar

## 1. Objective

- **Goal:** Implement Instruments data-management services and typed UI projections.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Manage authoritative datasets, instruments, sessions and custom bars.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/DataManagerInstruments.jar`; 3 class declarations; SHA-256 `8703d07e0f552af045ee4af196a533a8469e18bafe7bc9afa88044b48dc012a8`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/DataManager/DataManagerInstruments.md`; roadmap allocation `FEAT-DATA-DATA-MANAGER-INSTRUMENTS`.
- **Owner:** `app/workspace/DataManager/DataManagerInstruments/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Dataset/instrument/session/basket/custom-data administration; downstream P04–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/DataManagerInstruments.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/DataManagerInstruments.jar" com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerInstruments`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/services/InstrumentService.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/controllers/InstrumentsCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/actions/clone/CloneInstrumentCtrl.js`.
- **Existing UI connection:** instruments; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Catalogs/Instruments/instruments.ts`; wire instrument catalog load/save, units and broker/session references.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/DataManager/DataManagerInstruments/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerInstruments/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerInstruments/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerInstruments/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_data_manager_instruments.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_data_manager_instruments.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Catalogs/Instruments/instruments.ts`
  - Display instrument catalog load/save, units and broker/session references from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/data_source/Catalogs/Instruments/InstrumentEditorDialog.tsx`
  - Display instrument catalog load/save, units and broker/session references from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display instrument catalog load/save, units and broker/session references from backend responses; preserve layout.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-data-data-manager-instruments.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-manager-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement Instruments data-management services and typed UI projections; verify stable identity, units, validation, isolated persistence and reload.
- [ ] **Step 4:** `FR-DATA-DATA-MANAGER-INSTRUMENTS-INSTRUMENTS-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-DATA-DATA-MANAGER-INSTRUMENTS-INSTRUMENTS-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind instrument catalog load/save, units and broker/session references to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_data_manager_instruments.py --no-cov`; expect stable identity, units, validation, isolated persistence and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture stable identity, units, validation, isolated persistence and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-data-manager-instruments.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-manager-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise instruments for FEAT-DATA-DATA-MANAGER-INSTRUMENTS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 3.10 FEAT-DATA-DATA-MANAGER-SESSIONS - DataManagerSessions.jar

## 1. Objective

- **Goal:** Implement Sessions data-management services and typed UI projections.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Manage authoritative datasets, instruments, sessions and custom bars.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerSessions/DataManagerSessions.jar`; 3 class declarations; SHA-256 `8b954d0b88762c75ba4d2cb77536a81d1651370cd75085a57d64fd9355e7067d`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/DataManager/DataManagerSessions.md`; roadmap allocation `FEAT-DATA-DATA-MANAGER-SESSIONS`.
- **Owner:** `app/workspace/DataManager/DataManagerSessions/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Dataset/instrument/session/basket/custom-data administration; downstream P04–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerSessions/DataManagerSessions.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerSessions/DataManagerSessions.jar" com.strategyquant.plugin.DataManager.impl.Sessions.SessionsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerSessions`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DataManagerSessions/services/SessionService.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerSessions/controllers/SessionsCtrl.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerSessions/actions/clone/CloneSessionCtrl.js`.
- **Existing UI connection:** sessions; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Catalogs/Sessions/sessionStore.ts`; wire session templates/elements, timezone validation and persisted revisions.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/DataManager/DataManagerSessions/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerSessions/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerSessions/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/DataManager/DataManagerSessions/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_data_manager_sessions.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_data_manager_sessions.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Catalogs/Sessions/sessionStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/Catalogs/Sessions/SessionElementDialog.tsx`
  - Display session templates/elements, timezone validation and persisted revisions from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display session templates/elements, timezone validation and persisted revisions from backend responses; preserve layout.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-data-data-manager-sessions.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-manager-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement Sessions data-management services and typed UI projections; verify stable identity, units, validation, isolated persistence and reload.
- [ ] **Step 4:** `FR-DATA-DATA-MANAGER-SESSIONS-SESSIONS-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataManager.impl.Sessions.SessionsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-DATA-DATA-MANAGER-SESSIONS-SESSIONS-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataManager.impl.Sessions.SessionsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind session templates/elements, timezone validation and persisted revisions to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_data_manager_sessions.py --no-cov`; expect stable identity, units, validation, isolated persistence and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture stable identity, units, validation, isolated persistence and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-data-manager-sessions.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-manager-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise sessions for FEAT-DATA-DATA-MANAGER-SESSIONS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 3.11 FEAT-DATA-SETTINGS-DATA - SettingsData.jar

## 1. Objective

- **Goal:** Implement validated Data settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Manage authoritative datasets, instruments, sessions and custom bars.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsData/SettingsData.jar`; 1 class declarations; SHA-256 `69be16089a6f5ec0e6160e9f4980abf384b8ac57449de32a687fc8e0e8fdd3f1`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsData.md`; roadmap allocation `FEAT-DATA-SETTINGS-DATA`.
- **Owner:** `app/plugins/data/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Execution data-selection schema and validation; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsData/SettingsData.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsData/SettingsData.jar" com.strategyquant.plugin.Settings.impl.Data.DataSettingsPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsData`; `SQX_REFERENCE_ROOT/internal/web/QDM`; `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/SettingsData/ComplexitiesService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsData/DataService.js`; `SQX_REFERENCE_ROOT/internal/plugins/SettingsData/DataCtrl.js`.
- **Existing UI connection:** Data Manager; exact retained source-map `ui/app/plugins/project/SettingsData/source-map.json`. Target `ui/app/plugins/project/SettingsData/DataCtrl.ts`; wire dataset/catalog load and mutation, server resource IDs and authoritative row counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data/selection.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/data/README.md` (proposed earlier in FEAT-DATA-JODA-TIME)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_settings_data.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_settings_data.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/project/SettingsData/DataCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/project/SettingsData/views/data.tsx`
  - Display dataset/catalog load and mutation, server resource IDs and authoritative row counts from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/project/SettingsData/module.ts`
  - Display dataset/catalog load and mutation, server resource IDs and authoritative row counts from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display dataset/catalog load and mutation, server resource IDs and authoritative row counts from backend responses; preserve layout.
- **Create:** `ui/app/plugins/project/SettingsData/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-data-settings-data.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-manager-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated Data settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** `FR-DATA-SETTINGS-DATA-DATA-SETTINGS-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Data.DataSettingsPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-DATA-SETTINGS-DATA-DATA-SETTINGS-PLUGIN-GET-HANDLER` → `com.strategyquant.plugin.Settings.impl.Data.DataSettingsPlugin.getHandler`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-DATA-SETTINGS-DATA-DATA-SETTINGS-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.Data.DataSettingsPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 9:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/catalog load and mutation, server resource IDs and authoritative row counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 10:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_settings_data.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-settings-data.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-manager-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Data Manager for FEAT-DATA-SETTINGS-DATA; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 3.12 FEAT-UI-DATA-MANAGER-ACTIONS - DataManagerActions resource contribution

## 1. Objective

- **Goal:** Qualify and connect DataManagerActions without assuming a missing backend JAR.
- **Context / Problem Solved:** DataManagerActions is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerActions`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/DataManagerActions/styles.css`.
- **FR:** `FR-UI-DATA-MANAGER-ACTIONS-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/DataManager/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerActions`; `SQX_REFERENCE_ROOT/internal/web/QDM`; `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DataManagerActions/exportToCsv/ExportToCsvService.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerActions/exportToMT4/ExportToMT4Service.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerActions/exportToMT5/ExportToMT5Service.js`.
- **Existing UI connection:** Data Manager; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Common/dataManagerStore.ts`; wire dataset/catalog load and mutation, server resource IDs and authoritative row counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/workspace/DataManager/resource_contributions.py`
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/workspace/DataManager/README.md` (proposed earlier in FEAT-DATA-APP-DATA-MANAGER)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_data_manager_actions.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-data-manager-actions.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-manager-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-DATA-MANAGER-ACTIONS-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/catalog load and mutation, server resource IDs and authoritative row counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_data_manager_actions.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Create a fixture dataset and session; edit instrument precision; reload the page; confirm persisted values and visible invalid-input errors. Inspect the DataManagerActions contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-data-manager-actions.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-manager-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Data Manager for FEAT-UI-DATA-MANAGER-ACTIONS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 3.13 FEAT-UI-DATA-MANAGER-HELP - DataManagerHelp resource contribution

## 1. Objective

- **Goal:** Qualify and connect DataManagerHelp without assuming a missing backend JAR.
- **Context / Problem Solved:** DataManagerHelp is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerHelp`; narrow source: `SQX_REFERENCE_ROOT/internal/plugins/DataManagerHelp/module.js`.
- **FR:** `FR-UI-DATA-MANAGER-HELP-RESOURCE-WORKFLOW`; proposed owning README `app/workspace/DataManager/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerHelp`; `SQX_REFERENCE_ROOT/internal/web/QDM`; `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData`. Inspect `SQX_REFERENCE_ROOT/internal/plugins/DataManagerHelp/help.html`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerHelp/module.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerHelp/styles.css`.
- **Existing UI connection:** Data Manager; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Common/dataManagerStore.ts`; wire dataset/catalog load and mutation, server resource IDs and authoritative row counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/DataManager/resource_contributions.py` (proposed earlier in FEAT-UI-DATA-MANAGER-ACTIONS)
  - Mount only verified resource/action contributions through this owning capability.
- **Modify:** `app/workspace/DataManager/README.md` (proposed earlier in FEAT-DATA-APP-DATA-MANAGER)
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_data_manager_help.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-data-manager-help.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-manager-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-DATA-MANAGER-HELP-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/catalog load and mutation, server resource IDs and authoritative row counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_data_manager_help.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Create a fixture dataset and session; edit instrument precision; reload the page; confirm persisted values and visible invalid-input errors. Inspect the DataManagerHelp contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-data-manager-help.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-manager-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Data Manager for FEAT-UI-DATA-MANAGER-HELP; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

# 3.14 P03 integration — Manage authoritative datasets, instruments, sessions and custom bars

## 1. Objective

- **Goal:** Manage authoritative datasets, instruments, sessions and custom bars.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P03; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/DataManager/DataManager.tsx`; backend counterparts are proposed.
- **Declared dependencies:** FastAPI, Pydantic, Uvicorn, psutil; host persistence choice remains unratified.
- **Existing tests:** No audited phase backend suite; create the integration tests below.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_REFERENCE_ROOT/internal/web/QDM`; `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData`. Inspect `SQX_REFERENCE_ROOT/internal/web/QDM/layout/QDMService.js`; `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager/module.js`; `SQX_REFERENCE_ROOT/internal/plugins/DataManagerData/DMDataService.js`.
- **Existing UI connection:** Data Manager; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Common/dataManagerStore.ts`; wire dataset/catalog load and mutation, server resource IDs and authoritative row counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/workspace/DataManager/workspace.py` (proposed earlier in FEAT-DATA-APP-DATA-MANAGER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/DataManager/routes.py` (proposed earlier in FEAT-DATA-APP-DATA-MANAGER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/DataManager/contracts.py` (proposed earlier in FEAT-DATA-APP-DATA-MANAGER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/data/models.py` (proposed earlier in FEAT-DATA-JODA-TIME)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/data/bars.py` (proposed earlier in FEAT-DATA-JODA-TIME)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/data/sessions.py` (proposed earlier in FEAT-DATA-JODA-TIME)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/data/storage.py` (proposed earlier in FEAT-DATA-JODA-TIME)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/workspace/DataManager/README.md` (proposed earlier in FEAT-DATA-APP-DATA-MANAGER)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_data_manager_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-data-manager-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/task-3-14.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Define dataset IDs, instrument precision, time zones, sessions and versioned selection contracts.
- [ ] **Step 3:** Implement isolated create/edit/read/delete, bar validation and custom-data/basket relationships.
- [ ] **Step 4:** Connect DataManager controls to durable services and publish selection metadata to consumers.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/catalog load and mutation, server resource IDs and authoritative row counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_data_manager_workflow.py --no-cov`; `npm --prefix ui run test:ui -- tests/e2e/sqx-data-manager-backend.spec.ts`. Assert dataset reload, instrument precision, basket membership and DST/session boundaries; reject duplicate/out-of-order bars, invalid timezone and unauthorized dataset deletion.
- **Manual / Browser Verification:** Create a fixture dataset and session; edit instrument precision; reload the page; confirm persisted values and visible invalid-input errors.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-3-14.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-manager-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Data Manager for 3.14; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
