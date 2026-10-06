# P16 — Connections, terminal integration and explicitly authorized trading

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P02,P03,P04,P06,P08,P13.
- **Scope:** 5 JAR feature tasks, 0 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.

# 16.1 FEAT-CONNECTION-CONNECTION-LIVE-TEST - ConnectionLiveTest.jar

## 1. Objective

- **Goal:** Implement the named connection capability with explicit lifecycle/authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Qualify terminal connections and segregate simulation from authorized trading.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ConnectionLiveTest/ConnectionLiveTest.jar`; 3 class declarations; SHA-256 `0b91dd781b045416678bf1ad771cf67746b4ce0bc66cf479e77dd6fa854253eb`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ConnectionLiveTest.md`; roadmap allocation `FEAT-CONNECTION-CONNECTION-LIVE-TEST`.
- **Owner:** `app/plugins/connections/ConnectionLiveTest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Connection capability, protocol and connection tests; separate live-effect gate; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ConnectionLiveTest/ConnectionLiveTest.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ConnectionLiveTest/ConnectionLiveTest.jar" com.strategyquant.plugin.Connection.impl.LiveTest.LiveTestConnection`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named connection capability with explicit lifecycle/authority; verify handshake, symbol/account mapping, disconnect, timeout and denied live action.
- [ ] **Step 4:** `FR-CONNECTION-CONNECTION-LIVE-TEST-LIVE-TEST-CONNECTION-CONTRACT` → `com.strategyquant.plugin.Connection.impl.LiveTest.LiveTestConnection`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-CONNECTION-CONNECTION-LIVE-TEST-LIVE-TEST-CONNECTION-INITIALIZE-ENGINES` → `com.strategyquant.plugin.Connection.impl.LiveTest.LiveTestConnection.initializeEngines`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-CONNECTION-CONNECTION-LIVE-TEST-LIVE-TEST-CONNECTION-CONNECT` → `com.strategyquant.plugin.Connection.impl.LiveTest.LiveTestConnection.connect`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_connection_connection_live_test.py --no-cov`; expect handshake, symbol/account mapping, disconnect, timeout and denied live action; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture handshake, symbol/account mapping, disconnect, timeout and denied live action and visible failures.

# 16.2 FEAT-CONNECTION-CONNECTION-MT4 - ConnectionMT4.jar

## 1. Objective

- **Goal:** Implement the named connection capability with explicit lifecycle/authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Qualify terminal connections and segregate simulation from authorized trading.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ConnectionMT4/ConnectionMT4.jar`; 7 class declarations; SHA-256 `fdf875eaf15af4256ff2d74f823e9745addd64d40838ad8d1436eb2dc4cf126c`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ConnectionMT4.md`; roadmap allocation `FEAT-CONNECTION-CONNECTION-MT4`.
- **Owner:** `app/plugins/connections/ConnectionMT4/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Connection capability, protocol and connection tests; separate live-effect gate; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ConnectionMT4/ConnectionMT4.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ConnectionMT4/ConnectionMT4.jar" com.strategyquant.plugin.Connection.impl.MT4.MT4Bridge`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named connection capability with explicit lifecycle/authority; verify handshake, symbol/account mapping, disconnect, timeout and denied live action.
- [ ] **Step 4:** `FR-CONNECTION-CONNECTION-MT4-MT4-BRIDGE-CONTRACT` → `com.strategyquant.plugin.Connection.impl.MT4.MT4Bridge`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-CONNECTION-CONNECTION-MT4-MT4-BRIDGE-REGISTER-SYMBOL` → `com.strategyquant.plugin.Connection.impl.MT4.MT4Bridge.registerSymbol`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-CONNECTION-CONNECTION-MT4-MT4-BRIDGE-BUY-NOW` → `com.strategyquant.plugin.Connection.impl.MT4.MT4Bridge.buyNow`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_connection_connection_mt4.py --no-cov`; expect handshake, symbol/account mapping, disconnect, timeout and denied live action; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture handshake, symbol/account mapping, disconnect, timeout and denied live action and visible failures.

# 16.3 FEAT-CONNECTION-CONNECTION-TEST - ConnectionTest.jar

## 1. Objective

- **Goal:** Implement the named connection capability with explicit lifecycle/authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Qualify terminal connections and segregate simulation from authorized trading.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ConnectionTest/ConnectionTest.jar`; 3 class declarations; SHA-256 `1187a1ba55948383199187e74960e993d741279ef0f2c9d9ac9ef8b9a92469d3`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ConnectionTest.md`; roadmap allocation `FEAT-CONNECTION-CONNECTION-TEST`.
- **Owner:** `app/plugins/connections/ConnectionTest/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Connection capability, protocol and connection tests; separate live-effect gate; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ConnectionTest/ConnectionTest.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ConnectionTest/ConnectionTest.jar" com.strategyquant.plugin.Connection.impl.Test.TestConnection`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named connection capability with explicit lifecycle/authority; verify handshake, symbol/account mapping, disconnect, timeout and denied live action.
- [ ] **Step 4:** `FR-CONNECTION-CONNECTION-TEST-TEST-CONNECTION-CONTRACT` → `com.strategyquant.plugin.Connection.impl.Test.TestConnection`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-CONNECTION-CONNECTION-TEST-TEST-CONNECTION-INITIALIZE-ENGINES` → `com.strategyquant.plugin.Connection.impl.Test.TestConnection.initializeEngines`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-CONNECTION-CONNECTION-TEST-TEST-CONNECTION-CONNECT` → `com.strategyquant.plugin.Connection.impl.Test.TestConnection.connect`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_connection_connection_test.py --no-cov`; expect handshake, symbol/account mapping, disconnect, timeout and denied live action; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture handshake, symbol/account mapping, disconnect, timeout and denied live action and visible failures.

# 16.4 FEAT-CONNECTION-DATA-MANAGER-CONNECTIONS - DataManagerConnections.jar

## 1. Objective

- **Goal:** Implement the named connection capability with explicit lifecycle/authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Qualify terminal connections and segregate simulation from authorized trading.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/DataManagerConnections/DataManagerConnections.jar`; 3 class declarations; SHA-256 `8978514482bcc046e28887fea63697c880dcaa3340fb62b9084ab71400300ab8`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/DataManager/DataManagerConnections.md`; roadmap allocation `FEAT-CONNECTION-DATA-MANAGER-CONNECTIONS`.
- **Owner:** `app/plugins/connections/DataManagerConnections/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Connection capability, protocol and connection tests; separate live-effect gate; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerConnections/DataManagerConnections.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/DataManagerConnections/DataManagerConnections.jar" com.strategyquant.plugin.DataManager.impl.Connections.ConnectionInfoSender`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named connection capability with explicit lifecycle/authority; verify handshake, symbol/account mapping, disconnect, timeout and denied live action.
- [ ] **Step 4:** `FR-CONNECTION-DATA-MANAGER-CONNECTIONS-CONNECTION-INFO-SENDER-CONTRACT` → `com.strategyquant.plugin.DataManager.impl.Connections.ConnectionInfoSender`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-CONNECTION-DATA-MANAGER-CONNECTIONS-CONNECTION-INFO-SENDER-GET-INSTANCE` → `com.strategyquant.plugin.DataManager.impl.Connections.ConnectionInfoSender.getInstance`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-CONNECTION-DATA-MANAGER-CONNECTIONS-CONNECTION-INFO-SENDER-START` → `com.strategyquant.plugin.DataManager.impl.Connections.ConnectionInfoSender.start`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_connection_data_manager_connections.py --no-cov`; expect handshake, symbol/account mapping, disconnect, timeout and denied live action; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture handshake, symbol/account mapping, disconnect, timeout and denied live action and visible failures.

# 16.5 FEAT-CONNECTION-SERVLET-CONNECTION - ServletConnection.jar

## 1. Objective

- **Goal:** Implement the named connection capability with explicit lifecycle/authority.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Qualify terminal connections and segregate simulation from authorized trading.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ServletConnection/ServletConnection.jar`; 2 class declarations; SHA-256 `7e254197a8e29bad9601b7235af0e58ef696c159508c96170465c847b48cd54b`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ServletConnection.md`; roadmap allocation `FEAT-CONNECTION-SERVLET-CONNECTION`.
- **Owner:** `app/plugins/connections/ServletConnection/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Connection capability, protocol and connection tests; separate live-effect gate; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ServletConnection/ServletConnection.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ServletConnection/ServletConnection.jar" com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named connection capability with explicit lifecycle/authority; verify handshake, symbol/account mapping, disconnect, timeout and denied live action.
- [ ] **Step 4:** `FR-CONNECTION-SERVLET-CONNECTION-CONNECTION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-CONNECTION-SERVLET-CONNECTION-CONNECTION-SERVLET-GET-INSTANCE` → `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet.getInstance`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-CONNECTION-SERVLET-CONNECTION-CONNECTION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Servlet.impl.Connection.ConnectionServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_connection_servlet_connection.py --no-cov`; expect handshake, symbol/account mapping, disconnect, timeout and denied live action; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture handshake, symbol/account mapping, disconnect, timeout and denied live action and visible failures.

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

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify terminal handshake, symbol/account mapping, timeouts and connection lifecycle.
- [ ] **Step 3:** Implement mock/sandbox connection capabilities and read-only account/order projections.
- [ ] **Step 4:** Wire Trading/connection controls; keep live external mutations behind distinct explicit authority.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_connections_trading_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/MTAnalyzer/mtAnalyzer.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-connections-trading-backend.spec.ts`. Assert sandbox connect/disconnect, account projection, symbol mapping and lifecycle cleanup; reject credential failure, lost connection, repeated request and missing live-trading authority.
- **Manual / Browser Verification:** Connect an isolated test adapter; view account/order state; disconnect; confirm real-trading actions remain disabled without distinct authority.

## Phase completion gate

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
