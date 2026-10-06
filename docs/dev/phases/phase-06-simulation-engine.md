# P06 — Execution engine, accounting, trading options and stock picking

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P02,P03,P05.
- **Scope:** 4 JAR feature tasks, 0 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.

# 6.1 FEAT-SHARED-SQ-TRADING-LIB - SQTradingLib.jar

## 1. Objective

- **Goal:** Implement deterministic evaluation, order/fill/accounting and management contracts.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute deterministic strategies and produce reconciled trade/account ledgers.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/libs/SQTradingLib.jar`; 945 class declarations; SHA-256 `9796578273f36ced388b977bf08ff67c149a8897805b0bce00f7b8d3de6241f3`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SQTradingLib.md`; roadmap allocation `FEAT-SHARED-SQ-TRADING-LIB`.
- **Owner:** `app/plugins/simulator/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Trading engine plus shared task/strategy/result types; split by exclusive ownership; downstream P02,P05,P07–P16.
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/libs/SQTradingLib.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/libs/SQTradingLib.jar" com.strategyquant.tradinglib.StrategyBase`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

## 3. File Changes

- **Create:** `app/plugins/simulator/engine.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/simulator/orders.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/simulator/fills.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/simulator/accounting.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/simulator/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_shared_sq_trading_lib.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/shared_sq_trading_lib.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement deterministic evaluation, order/fill/accounting and management contracts; verify event order, same-bar precedence, costs, rounding and reconciled equity.
- [ ] **Step 4:** `FR-SHARED-SQ-TRADING-LIB-STRATEGY-BASE-CONTRACT` → `com.strategyquant.tradinglib.StrategyBase`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-SHARED-SQ-TRADING-LIB-STRATEGY-BASE-INITIALIZE-FROM-MARKET-DATA` → `com.strategyquant.tradinglib.StrategyBase.initializeFromMarketData`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-SHARED-SQ-TRADING-LIB-STRATEGY-BASE-SET-TRADE-CONTROLLERS` → `com.strategyquant.tradinglib.StrategyBase.setTradeControllers`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_shared_sq_trading_lib.py --no-cov`; expect event order, same-bar precedence, costs, rounding and reconciled equity; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture event order, same-bar precedence, costs, rounding and reconciled equity and visible failures.

# 6.2 FEAT-SIMULATOR-SETTINGS-ADVANCED-TM - SettingsAdvancedTM.jar

## 1. Objective

- **Goal:** Implement validated AdvancedTM settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute deterministic strategies and produce reconciled trade/account ledgers.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/SettingsAdvancedTM.jar`; 2 class declarations; SHA-256 `a3cf16125b42b41df82e5ceebd1b74d1380e6eef82a7179188023f94d7e1e460`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsAdvancedTM.md`; roadmap allocation `FEAT-SIMULATOR-SETTINGS-ADVANCED-TM`.
- **Owner:** `app/plugins/simulator/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Advanced trade management, position sizing and trading option schemas; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/SettingsAdvancedTM.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsAdvancedTM/SettingsAdvancedTM.jar" com.strategyquant.plugin.Settings.impl.AdvancedTM.AdvancedTMServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/simulator/management.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/simulator/sizing.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/simulator/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/README.md` (proposed earlier in FEAT-SHARED-SQ-TRADING-LIB)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_simulator_settings_advanced_tm.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/simulator_settings_advanced_tm.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated AdvancedTM settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** `FR-SIMULATOR-SETTINGS-ADVANCED-TM-ADVANCED-TM-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.AdvancedTM.AdvancedTMServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-SIMULATOR-SETTINGS-ADVANCED-TM-ADVANCED-TM-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.AdvancedTM.AdvancedTMServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_simulator_settings_advanced_tm.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.

# 6.3 FEAT-SIMULATOR-SETTINGS-MONEY-MANAGEMENT - SettingsMoneyManagement.jar

## 1. Objective

- **Goal:** Implement validated MoneyManagement settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute deterministic strategies and produce reconciled trade/account ledgers.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement/SettingsMoneyManagement.jar`; 1 class declarations; SHA-256 `d67b40d82bf1925b5b1cb8b47c4aa57c7956dea074d2138b9700da38a431045b`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsMoneyManagement.md`; roadmap allocation `FEAT-SIMULATOR-SETTINGS-MONEY-MANAGEMENT`.
- **Owner:** `app/plugins/simulator/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Advanced trade management, position sizing and trading option schemas; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement/SettingsMoneyManagement.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsMoneyManagement/SettingsMoneyManagement.jar" com.strategyquant.plugin.Settings.impl.MoneyManagement.MoneyManagementSettingsPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Modify:** `app/plugins/simulator/management.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/sizing.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/contracts.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/README.md` (proposed earlier in FEAT-SHARED-SQ-TRADING-LIB)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_simulator_settings_money_management.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/simulator_settings_money_management.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated MoneyManagement settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** `FR-SIMULATOR-SETTINGS-MONEY-MANAGEMENT-MONEY-MANAGEMENT-SETTINGS-PLUGIN-CONTRACT` → `com.strategyquant.plugin.Settings.impl.MoneyManagement.MoneyManagementSettingsPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-SIMULATOR-SETTINGS-MONEY-MANAGEMENT-MONEY-MANAGEMENT-SETTINGS-PLUGIN-GET-HANDLER` → `com.strategyquant.plugin.Settings.impl.MoneyManagement.MoneyManagementSettingsPlugin.getHandler`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-SIMULATOR-SETTINGS-MONEY-MANAGEMENT-MONEY-MANAGEMENT-SETTINGS-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.Settings.impl.MoneyManagement.MoneyManagementSettingsPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_simulator_settings_money_management.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.

# 6.4 FEAT-SIMULATOR-SETTINGS-OPTIONS - SettingsOptions.jar

## 1. Objective

- **Goal:** Implement validated Options settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Execute deterministic strategies and produce reconciled trade/account ledgers.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsOptions/SettingsOptions.jar`; 2 class declarations; SHA-256 `05ccd670b25beb681bde41255b8453b44aa517ccfa198ba7ea5685dd6faab046`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsOptions.md`; roadmap allocation `FEAT-SIMULATOR-SETTINGS-OPTIONS`.
- **Owner:** `app/plugins/simulator/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Advanced trade management, position sizing and trading option schemas; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsOptions/SettingsOptions.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsOptions/SettingsOptions.jar" com.strategyquant.plugin.Settings.impl.Options.SettingsOptionsServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Modify:** `app/plugins/simulator/management.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/sizing.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/contracts.py` (proposed earlier in FEAT-SIMULATOR-SETTINGS-ADVANCED-TM)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/plugins/simulator/README.md` (proposed earlier in FEAT-SHARED-SQ-TRADING-LIB)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_simulator_settings_options.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/simulator_settings_options.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated Options settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** `FR-SIMULATOR-SETTINGS-OPTIONS-SETTINGS-OPTIONS-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Options.SettingsOptionsServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-SIMULATOR-SETTINGS-OPTIONS-SETTINGS-OPTIONS-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.Options.SettingsOptionsServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_simulator_settings_options.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.

# 6.5 P06 integration — Execute deterministic strategies and produce reconciled trade/account ledgers

## 1. Objective

- **Goal:** Execute deterministic strategies and produce reconciled trade/account ledgers.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P06; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/Builder/BuilderWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/Builder/fullSettings.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

## 3. File Changes

- **Modify:** `app/plugins/simulator/engine.py` (proposed earlier in FEAT-SHARED-SQ-TRADING-LIB)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/simulator/clock.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/simulator/orders.py` (proposed earlier in FEAT-SHARED-SQ-TRADING-LIB)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/simulator/fills.py` (proposed earlier in FEAT-SHARED-SQ-TRADING-LIB)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/plugins/simulator/accounting.py` (proposed earlier in FEAT-SHARED-SQ-TRADING-LIB)
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
- **Modify:** `app/plugins/simulator/README.md` (proposed earlier in FEAT-SHARED-SQ-TRADING-LIB)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_simulation_engine_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-simulation-engine-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify event ordering, alignment, sizing, fills, costs, same-bar precedence and rounding.
- [ ] **Step 3:** Implement strategy evaluation, order lifecycle, advanced management and stock-selection execution.
- [ ] **Step 4:** Persist run configuration, event trace, trades/equity and failures through host storage.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_simulation_engine_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/Builder/fullSettings.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-simulation-engine-backend.spec.ts`. Assert donor event traces, fills, position sizing, costs and reconciled PnL; reject same-bar ambiguity, session gap, missing price, invalid size and cancellation.
- **Manual / Browser Verification:** Run one saved fixture strategy; inspect orders/trades/equity; rerun the same configuration and compare traces under ratified tolerances.

## Phase completion gate

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.
