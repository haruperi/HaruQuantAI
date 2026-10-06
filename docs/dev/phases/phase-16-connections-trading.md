# P16 — Connections, terminal integration and explicitly authorized trading

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P02,P03,P04,P06,P08,P13.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 6 tasks; current archive allocations and resource/integration tasks only.

# 16.1 FEAT-CONNECTION-CONNECTION-LIVE-TEST - ConnectionLiveTest.jar

## 1. Objective

- **Goal:** Implement the named connection capability with explicit lifecycle/authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Qualify terminal connections and segregate simulation from authorized trading.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ConnectionLiveTest/ConnectionLiveTest.jar`; 3 raw class entries; SHA-256 `9285422ca69b69efe92f72954b2c5e8f938ec4879f9b5b42819faa128b9c9bfe`.
- **Inspected reference:** [ConnectionLiveTest.md](../../sqx/Shared/ConnectionLiveTest.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ConnectionLiveTest/ConnectionLiveTest.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ConnectionLiveTest/ConnectionLiveTest.jar" com.strategyquant.plugin.Connection.impl.LiveTest.LiveTestConnection`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/connections/ConnectionLiveTest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Connection capability, protocol and connection tests; separate live-effect gate; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ConnectionLiveTest`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerConnections`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletConnection`. No companion JS/HTML/CSS found in these connection directories; exact installed UI consumer is unresolved. Trading is a proposed HaruQuantAI consumer, not observed SQX UI parity.
- **Existing UI connection:** connections; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/DataManager/DataManager.tsx`; wire connection capability/status, configured terminal sandbox and authorization state.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.
- **Retained UI limit:** Data Manager connection-specific controls were not found in the scoped text audit; Trading is a normative target surface. Reconcile a usable existing consumer; this mapping does not authorize new screen construction.

## 3. File Changes

- **Create:** `app/plugins/connections/ConnectionLiveTest/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/ConnectionLiveTest/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/ConnectionLiveTest/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/ConnectionLiveTest/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_connection_connection_live_test.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/connection_connection_live_test.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display connection capability/status, configured terminal sandbox and authorization state from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Trading/TradingDashboard.tsx`
  - Display connection capability/status, configured terminal sandbox and authorization state from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Trading/tradingStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/Trading/tradingClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-connection-connection-live-test.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-connections-trading-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named connection capability with explicit lifecycle/authority; verify handshake, symbol/account mapping, disconnect, timeout and denied live action.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind connection capability/status, configured terminal sandbox and authorization state to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.
- **External authority:** Verify terminal sandbox and denied/disabled live operations; real orders require distinct authorization.


- [ ] **Step 8:** `FR-CONNECTION-CONNECTION-LIVE-TEST-LIVE-TEST-CONNECTION-CONTRACT` → `com.strategyquant.plugin.Connection.impl.LiveTest.LiveTestConnection`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-CONNECTION-CONNECTION-LIVE-TEST-LIVE-TEST-CONNECTION-INITIALIZE-ENGINES` → `com.strategyquant.plugin.Connection.impl.LiveTest.LiveTestConnection.initializeEngines()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-CONNECTION-CONNECTION-LIVE-TEST-LIVE-TEST-CONNECTION-CONNECT` → `com.strategyquant.plugin.Connection.impl.LiveTest.LiveTestConnection.connect()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_connection_connection_live_test.py --no-cov`; expect handshake, symbol/account mapping, disconnect, timeout and denied live action; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture handshake, symbol/account mapping, disconnect, timeout and denied live action and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-connection-connection-live-test.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-connections-trading-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise connections for FEAT-CONNECTION-CONNECTION-LIVE-TEST; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 16.2 FEAT-CONNECTION-CONNECTION-MT4 - ConnectionMT4.jar

## 1. Objective

- **Goal:** Implement the named connection capability with explicit lifecycle/authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Qualify terminal connections and segregate simulation from authorized trading.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ConnectionMT4/ConnectionMT4.jar`; 7 raw class entries; SHA-256 `e197dc620cdeb9bccc53742aa8c3aa6a3a9bc41aea320f3e95eb3b052e503d7d`.
- **Inspected reference:** [ConnectionMT4.md](../../sqx/Shared/ConnectionMT4.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ConnectionMT4/ConnectionMT4.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ConnectionMT4/ConnectionMT4.jar" com.strategyquant.plugin.Connection.impl.MT4.MT4Bridge`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/connections/ConnectionMT4/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Connection capability, protocol and connection tests; separate live-effect gate; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ConnectionMT4`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerConnections`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletConnection`. No companion JS/HTML/CSS found in these connection directories; exact installed UI consumer is unresolved. Trading is a proposed HaruQuantAI consumer, not observed SQX UI parity.
- **Existing UI connection:** connections; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/DataManager/DataManager.tsx`; wire connection capability/status, configured terminal sandbox and authorization state.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.
- **Retained UI limit:** Data Manager connection-specific controls were not found in the scoped text audit; Trading is a normative target surface. Reconcile a usable existing consumer; this mapping does not authorize new screen construction.

## 3. File Changes

- **Create:** `app/plugins/connections/ConnectionMT4/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/ConnectionMT4/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/ConnectionMT4/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/ConnectionMT4/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_connection_connection_mt4.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/connection_connection_mt4.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display connection capability/status, configured terminal sandbox and authorization state from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Trading/TradingDashboard.tsx`
  - Display connection capability/status, configured terminal sandbox and authorization state from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Trading/tradingStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/Trading/tradingClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-connection-connection-mt4.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-connections-trading-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named connection capability with explicit lifecycle/authority; verify handshake, symbol/account mapping, disconnect, timeout and denied live action.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind connection capability/status, configured terminal sandbox and authorization state to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.
- **External authority:** Verify terminal sandbox and denied/disabled live operations; real orders require distinct authorization.


- [ ] **Step 8:** `FR-CONNECTION-CONNECTION-MT4-MT4-BRIDGE-CONTRACT` → `com.strategyquant.plugin.Connection.impl.MT4.MT4Bridge`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-CONNECTION-CONNECTION-MT4-MT4-BRIDGE-REGISTER-SYMBOL` → `com.strategyquant.plugin.Connection.impl.MT4.MT4Bridge.registerSymbol(Ljava/lang/String;)V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-CONNECTION-CONNECTION-MT4-MT4-BRIDGE-BUY-NOW` → `com.strategyquant.plugin.Connection.impl.MT4.MT4Bridge.buyNow(Ljava/lang/String;D)J`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_connection_connection_mt4.py --no-cov`; expect handshake, symbol/account mapping, disconnect, timeout and denied live action; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture handshake, symbol/account mapping, disconnect, timeout and denied live action and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-connection-connection-mt4.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-connections-trading-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise connections for FEAT-CONNECTION-CONNECTION-MT4; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 16.3 FEAT-CONNECTION-CONNECTION-TEST - ConnectionTest.jar

## 1. Objective

- **Goal:** Implement the named connection capability with explicit lifecycle/authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Qualify terminal connections and segregate simulation from authorized trading.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ConnectionTest/ConnectionTest.jar`; 3 raw class entries; SHA-256 `175ebc8fc349e53672ad787cf9f873591b70695af8fbbd4dab05c0d8779e5e26`.
- **Inspected reference:** [ConnectionTest.md](../../sqx/Shared/ConnectionTest.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ConnectionTest/ConnectionTest.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ConnectionTest/ConnectionTest.jar" com.strategyquant.plugin.Connection.impl.Test.TestConnection`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/connections/ConnectionTest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Connection capability, protocol and connection tests; separate live-effect gate; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ConnectionTest`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerConnections`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletConnection`. No companion JS/HTML/CSS found in these connection directories; exact installed UI consumer is unresolved. Trading is a proposed HaruQuantAI consumer, not observed SQX UI parity.
- **Existing UI connection:** connections; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/DataManager/DataManager.tsx`; wire connection capability/status, configured terminal sandbox and authorization state.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.
- **Retained UI limit:** Data Manager connection-specific controls were not found in the scoped text audit; Trading is a normative target surface. Reconcile a usable existing consumer; this mapping does not authorize new screen construction.

## 3. File Changes

- **Create:** `app/plugins/connections/ConnectionTest/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/ConnectionTest/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/ConnectionTest/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/ConnectionTest/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_connection_connection_test.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/connection_connection_test.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display connection capability/status, configured terminal sandbox and authorization state from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Trading/TradingDashboard.tsx`
  - Display connection capability/status, configured terminal sandbox and authorization state from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Trading/tradingStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/Trading/tradingClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-connection-connection-test.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-connections-trading-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named connection capability with explicit lifecycle/authority; verify handshake, symbol/account mapping, disconnect, timeout and denied live action.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind connection capability/status, configured terminal sandbox and authorization state to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.
- **External authority:** Verify terminal sandbox and denied/disabled live operations; real orders require distinct authorization.


- [ ] **Step 8:** `FR-CONNECTION-CONNECTION-TEST-TEST-CONNECTION-CONTRACT` → `com.strategyquant.plugin.Connection.impl.Test.TestConnection`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-CONNECTION-CONNECTION-TEST-TEST-CONNECTION-INITIALIZE-ENGINES` → `com.strategyquant.plugin.Connection.impl.Test.TestConnection.initializeEngines()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-CONNECTION-CONNECTION-TEST-TEST-CONNECTION-CONNECT` → `com.strategyquant.plugin.Connection.impl.Test.TestConnection.connect()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_connection_connection_test.py --no-cov`; expect handshake, symbol/account mapping, disconnect, timeout and denied live action; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture handshake, symbol/account mapping, disconnect, timeout and denied live action and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-connection-connection-test.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-connections-trading-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise connections for FEAT-CONNECTION-CONNECTION-TEST; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 16.4 FEAT-CONNECTION-DATA-MANAGER-CONNECTIONS - DataManagerConnections.jar

## 1. Objective

- **Goal:** Implement the named connection capability with explicit lifecycle/authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Qualify terminal connections and segregate simulation from authorized trading.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerConnections/DataManagerConnections.jar`; 3 raw class entries; SHA-256 `4272999e7250c713361be4ccce7f02ba7040478a6b1c608e31f9e7b4f965e713`.
- **Inspected reference:** [DataManagerConnections.md](../../sqx/DataManager/DataManagerConnections.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerConnections/DataManagerConnections.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerConnections/DataManagerConnections.jar" com.strategyquant.plugin.DataManager.impl.Connections.ConnectionInfoSender`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/connections/DataManagerConnections/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Connection capability, protocol and connection tests; separate live-effect gate; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerConnections`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletConnection`. No companion JS/HTML/CSS found in these connection directories; exact installed UI consumer is unresolved. Trading is a proposed HaruQuantAI consumer, not observed SQX UI parity.
- **Existing UI connection:** connections; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/DataManager/DataManager.tsx`; wire connection capability/status, configured terminal sandbox and authorization state.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.
- **Retained UI limit:** Data Manager connection-specific controls were not found in the scoped text audit; Trading is a normative target surface. Reconcile a usable existing consumer; this mapping does not authorize new screen construction.

## 3. File Changes

- **Create:** `app/plugins/connections/DataManagerConnections/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/DataManagerConnections/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/DataManagerConnections/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/DataManagerConnections/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_connection_data_manager_connections.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/connection_data_manager_connections.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display connection capability/status, configured terminal sandbox and authorization state from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Trading/TradingDashboard.tsx`
  - Display connection capability/status, configured terminal sandbox and authorization state from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Trading/tradingStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/Trading/tradingClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-connection-data-manager-connections.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-connections-trading-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named connection capability with explicit lifecycle/authority; verify handshake, symbol/account mapping, disconnect, timeout and denied live action.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind connection capability/status, configured terminal sandbox and authorization state to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.
- **External authority:** Verify terminal sandbox and denied/disabled live operations; real orders require distinct authorization.


- [ ] **Step 8:** `FR-CONNECTION-DATA-MANAGER-CONNECTIONS-CONNECTION-INFO-SENDER-CONTRACT` → `com.strategyquant.plugin.DataManager.impl.Connections.ConnectionInfoSender`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-CONNECTION-DATA-MANAGER-CONNECTIONS-CONNECTION-INFO-SENDER-GET-INSTANCE` → `com.strategyquant.plugin.DataManager.impl.Connections.ConnectionInfoSender.getInstance()Lcom/strategyquant/plugin/DataManager/impl/Connections/ConnectionInfoSender;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-CONNECTION-DATA-MANAGER-CONNECTIONS-CONNECTION-INFO-SENDER-START` → `com.strategyquant.plugin.DataManager.impl.Connections.ConnectionInfoSender.start()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_connection_data_manager_connections.py --no-cov`; expect handshake, symbol/account mapping, disconnect, timeout and denied live action; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture handshake, symbol/account mapping, disconnect, timeout and denied live action and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-connection-data-manager-connections.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-connections-trading-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise connections for FEAT-CONNECTION-DATA-MANAGER-CONNECTIONS; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 16.5 FEAT-CONNECTION-SERVLET-CONNECTION - ServletConnection.jar

## 1. Objective

- **Goal:** Implement the named connection capability with explicit lifecycle/authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Qualify terminal connections and segregate simulation from authorized trading.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletConnection/ServletConnection.jar`; 2 raw class entries; SHA-256 `37db7a764fe4988d227ecd49e3cee2318425655b0011a37bd0fa9adfa0065f90`.
- **Inspected reference:** [ServletConnection.md](../../sqx/Shared/ServletConnection.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletConnection/ServletConnection.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/ServletConnection/ServletConnection.jar" com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/connections/ServletConnection/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Connection capability, protocol and connection tests; separate live-effect gate; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/ServletConnection`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerConnections`. No companion JS/HTML/CSS found in these connection directories; exact installed UI consumer is unresolved. Trading is a proposed HaruQuantAI consumer, not observed SQX UI parity.
- **Existing UI connection:** connections; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/DataManager/DataManager.tsx`; wire connection capability/status, configured terminal sandbox and authorization state.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.
- **Retained UI limit:** Data Manager connection-specific controls were not found in the scoped text audit; Trading is a normative target surface. Reconcile a usable existing consumer; this mapping does not authorize new screen construction.

## 3. File Changes

- **Create:** `app/plugins/connections/ServletConnection/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/ServletConnection/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/ServletConnection/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/connections/ServletConnection/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_connection_servlet_connection.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/connection_servlet_connection.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display connection capability/status, configured terminal sandbox and authorization state from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Trading/TradingDashboard.tsx`
  - Display connection capability/status, configured terminal sandbox and authorization state from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Trading/tradingStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/Trading/tradingClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-connection-servlet-connection.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-connections-trading-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named connection capability with explicit lifecycle/authority; verify handshake, symbol/account mapping, disconnect, timeout and denied live action.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind connection capability/status, configured terminal sandbox and authorization state to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.
- **External authority:** Verify terminal sandbox and denied/disabled live operations; real orders require distinct authorization.


- [ ] **Step 8:** `FR-CONNECTION-SERVLET-CONNECTION-CONNECTION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-CONNECTION-SERVLET-CONNECTION-CONNECTION-SERVLET-GET-INSTANCE` → `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet.getInstance()Lcom/strategyquant/plugin/Servlet/impl/Connection/ConnectionServlet;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-CONNECTION-SERVLET-CONNECTION-CONNECTION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet.execute(Ljava/lang/String;Lorg/json/JSONObject;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_connection_servlet_connection.py --no-cov`; expect handshake, symbol/account mapping, disconnect, timeout and denied live action; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture handshake, symbol/account mapping, disconnect, timeout and denied live action and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-connection-servlet-connection.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-connections-trading-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise connections for FEAT-CONNECTION-SERVLET-CONNECTION; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 16.6 P16 integration — Qualify terminal connections and segregate simulation from authorized trading

## 1. Objective

- **Goal:** Qualify terminal connections and segregate simulation from authorized trading.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P16; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/Trading/TradingDashboard.tsx`, `ui/app/workspace/MTAnalyzer/MTAnalyzerWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** httpx, psutil; optional Windows metatrader5 (P16).
- **Existing tests:** `ui/tests/unit/workspace/MTAnalyzer/mtAnalyzer.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerConnections`; `SQX_145_REFERENCE_ROOT/internal/plugins/ServletConnection`. No companion JS/HTML/CSS found in these connection directories; exact installed UI consumer is unresolved. Trading is a proposed HaruQuantAI consumer, not observed SQX UI parity.
- **Existing UI connection:** connections; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/workspace/DataManager/DataManager.tsx`; wire connection capability/status, configured terminal sandbox and authorization state.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.
- **Retained UI limit:** Data Manager connection-specific controls were not found in the scoped text audit; Trading is a normative target surface. Reconcile a usable existing consumer; this mapping does not authorize new screen construction.

## 3. File Changes

- **Create:** `app/plugins/connections/contracts.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/connections/registry.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/connections/lifecycle.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/workspace/Trading/routes.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/workspace/Trading/contracts.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/Trading/TradingDashboard.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/Trading/tradingClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `ui/app/workspace/MTAnalyzer/MTAnalyzerWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Create:** `ui/app/workspace/MTAnalyzer/mTAnalyzerClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Create:** `app/plugins/connections/README.md`
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_connections_trading_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-connections-trading-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display connection capability/status, configured terminal sandbox and authorization state from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/Trading/tradingStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/task-16-6.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify terminal handshake, symbol/account mapping, timeouts and connection lifecycle.
- [ ] **Step 3:** Implement mock/sandbox connection capabilities and read-only account/order projections.
- [ ] **Step 4:** Wire Trading/connection controls; keep live external mutations behind distinct explicit authority.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind connection capability/status, configured terminal sandbox and authorization state to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.
- **External authority:** Verify terminal sandbox and denied/disabled live operations; real orders require distinct authorization.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_connections_trading_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/MTAnalyzer/mtAnalyzer.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-connections-trading-backend.spec.ts`. Assert sandbox connect/disconnect, account projection, symbol mapping and lifecycle cleanup; reject credential failure, lost connection, repeated request and missing live-trading authority.
- **Manual / Browser Verification:** Connect an isolated test adapter; view account/order state; disconnect; confirm real-trading actions remain disabled without distinct authority.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-16-6.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-connections-trading-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise connections for 16.6; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
