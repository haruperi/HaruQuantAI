# Live — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** `live`
* **Requested package path:** `app/services/live`
* **Requested tests path:** `ttests/unit/app/services/live`
* **Resolved tests path:** `tests/unit/app/services/live`
* **Known example path:** `tests/usage/app/services/10_live.py`
* **Repository:** `haruperi/HaruQuant`
* **Audited ref:** default branch `main`, commit `a39d26498e14772c571d75fa9a5f0e477a1dd912`
* **Package root found:** No
* **Files in the requested package:** 0
* **Module folders in the requested package:** 0

### Files inspected

**Requested package and registration surface**

* `app/services/live/` — repository lookup returned no package.
* `app/services/live.py` — repository lookup returned no module.
* `app/services/__init__.py`
* `app/services/NEW/live/__init__.py` at current `main` — not present.
* `app/services/NEW/live/__init__.py` at prior commit `cae1f33690a4b49c6bca5718237e2b354f2f6fb7` — historical, deleted staging implementation.
* Latest commit deletion diff for `app/services/NEW/live/`.

**Tests and examples**

* `tests/unit/app/services/live/test_live_runtime.py`
* `tests/unit/app/services/live/test_gates_extra.py`
* `tests/unit/app/services/live/test_live_risk_sim_pybots_extra2.py`
* `tests/usage/app/services/10_live.py`

**Related current runtime searched for boundary and overlap evidence**

* `app/api/routes/live.py`
* `app/services/execution/live/__init__.py`
* `app/services/execution/live/bar_monitor.py`
* `app/services/execution/live/config.py`
* `app/services/execution/live/dashboard.py`
* `app/services/execution/live/engine.py`
* `app/services/execution/live/models.py`
* `app/services/execution/live/mt5_compat.py`
* `app/services/execution/live/notification_adapter.py`
* `app/services/execution/live/position_manager.py`
* `app/services/execution/live/run.py`
* `app/services/execution/live/secrets.py`
* `app/services/execution/live/session.py`
* `app/services/execution/live/signal_processor.py`
* `app/services/execution/live/state_manager.py`
* `app/services/execution/live/trade_executor.py`

### Related packages searched

* `app.services.execution.live`
* `app.services.risk.live`
* `app.api.routes.live`
* `app.services`
* `app.utils.settings`
* `app.utils.errors`
* `tests/unit/app/services/live`
* `tests/usage/app/services/10_live.py`
* `docs/upgrade-plan/10-live-runtime.md`
* `docs/upgrade-plan/11-ui-and-api-gateway.md`

### Audit limitations

1. No Version 1 branch, tag, or commit was specified. The audit therefore uses the repository default branch, `main`, at commit `a39d26498e14772c571d75fa9a5f0e477a1dd912`.
2. The requested package does not exist at the audited ref, so there is no current source from which to inventory public signatures, exceptions, side effects, dependencies, or internal call paths.
3. Tests were not executed. Runtime failure is inferred from the absent package, the absence of a parent-package alias, and direct imports of `app.services.live`.
4. Repository-wide static searches were completed through the available GitHub index. Uncommitted local files, ignored files, external deployment bundles, and code on unspecified branches were not accessible.
5. The deleted `app/services/NEW/live` implementation was inspected only as historical evidence. It is not counted as current Version 1 code.
6. `app/services/execution/live` was inspected to identify active overlap and callers, but it is outside the requested package boundary and is not treated as the implementation of `app/services/live`.

---

## 2. Executive Summary

The requested Version 1 package, `app/services/live`, **does not exist** on the current `main` branch. There is no package directory, module file, `__init__.py`, public export registry, entry point, configuration file, registration hook, or runtime implementation under that path.

The repository still contains three unit-test files and one executable usage example that import `app.services.live`, including expected session lifecycle, safety-gate, execution, monitoring, policy, reconciliation, and kill-switch interfaces. These references are test/example-only and cannot resolve against the current source tree. They do not demonstrate production usage.

A separate and active package exists at `app/services/execution/live`. It implements an MT5-oriented multi-strategy execution runtime and is imported by `app/api/routes/live.py` through `LiveTradingSession`. This is not an alias or re-export of `app.services.live`; it is a different package with a different public API and responsibility set.

Historical evidence shows that a safety-gateway implementation previously existed under `app/services/NEW/live`, not under the canonical path expected by its own imports and tests. The latest audited commit deleted that staging package. At the prior commit, its `__init__.py` imported `app.services.live.*`, even though `app/services/live` was also absent. This indicates the staged package was disconnected from its intended import path before deletion.

No operational workflow can currently be attributed to `app/services/live`. All discovered workflows are test/example descriptions that fail at the import boundary. Current production live-session routing uses `app.services.execution.live` instead.

**Audit evidence trust:** High for current package absence, current import/caller mapping, and stale-reference findings. Medium for runtime consequences because tests could not be executed and unspecified branches or local workspaces were unavailable.

```text
Module folders: 0 | Files: 0 | Public symbols: 0 | Symbols with confirmed callers: 0 (0%) | Workflows found: 3 attempted, 0 operational
```

---

## 3. Actual Package Structure

```text
app
└── services
    └── live                      [ABSENT]
        ├── __init__.py           [ABSENT]
        ├── executor.py           [ABSENT]
        ├── gates.py              [ABSENT]
        ├── monitoring.py         [ABSENT]
        ├── policy.py             [ABSENT]
        ├── ports.py              [ABSENT]
        ├── reconciliation.py     [ABSENT]
        └── session.py            [ABSENT]
```

No current package-level public symbols exist.

### Related current package — not part of the requested boundary

```text
app
└── services
    └── execution
        └── live
            ├── __init__.py
            ├── bar_monitor.py
            ├── config.py
            ├── dashboard.py
            ├── engine.py
            ├── models.py
            ├── mt5_compat.py
            ├── notification_adapter.py
            ├── position_manager.py
            ├── run.py
            ├── secrets.py
            ├── session.py
            ├── signal_processor.py
            ├── state_manager.py
            └── trade_executor.py
```

`app/services/execution/live/__init__.py` lazily exposes:

```text
Config
StateManager
BarMonitor
SignalProcessor
PositionManager
TradeExecutor
LiveTradingNotifier
MultiStrategyEngine
StrategyInstance
LiveTradingSession
ExecutionEngineWrapper
```

These symbols belong to `app.services.execution.live`, not `app.services.live`.

### Historical deleted staging package — not current code

At prior commit `cae1f33690a4b49c6bca5718237e2b354f2f6fb7`:

```text
app
└── services
    └── NEW
        └── live
            ├── README.md
            ├── __init__.py
            ├── executor.py
            ├── gates.py
            ├── monitoring.py
            ├── policy.py
            ├── ports.py
            ├── reconciliation.py
            └── session.py
```

The audited `main` commit deleted this directory. Its registry imported `app.services.live.*`, not `app.services.NEW.live.*`, while the canonical package was absent. It is therefore historical disconnected evidence, not an active package.

---

## 4. Module and File Inventory

There are no modules or files inside the requested package at the audited ref.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
| ------ | ---- | -------------- | ----------- | ------------ | ------------ | ------------ |
| `app.services.live` | _No file exists_ | No current implementation | None | None | **Unused** | **No demonstrated value** |

### Related files consulted but excluded from the requested inventory

| Module | File | Responsibility | Key exports | Why excluded |
| ------ | ---- | -------------- | ----------- | ------------ |
| `app.services` | `app/services/__init__.py` | Generic service-module loading helpers | `load_service_module`, `load_service_symbol`, `resolve_service_attr`, `service_modules` | Contains no alias, registry, or fallback for `app.services.live`. |
| `app.services.execution.live` | `app/services/execution/live/__init__.py` | Lazy registry for the MT5 execution runtime | 11 live execution symbols | Different package boundary and API. |
| `app.services.execution.live` | `app/services/execution/live/engine.py` | Multi-strategy MT5 loop, strategy loading, portfolio/safety checks, trade execution, status export | `StrategyInstance`, `MultiStrategyEngine` | Active overlap, not the requested package. |
| `app.services.execution.live` | `app/services/execution/live/session.py` | Async API/database wrapper around `MultiStrategyEngine` | `ExecutionEngineWrapper`, `LiveTradingSession` | Consumed by the production API route, but belongs to execution. |
| `app.api.routes` | `app/api/routes/live.py` | REST and websocket surface for live trading sessions | Imports `app.services.execution.live.LiveTradingSession` | Confirms current runtime bypasses the requested package. |
| `tests.unit.app.services.live` | Three test files | Tests interfaces expected at `app.services.live` | Session, gates, executor, monitoring, reconciliation symbols | Test references are unresolvable against current source. |
| `tests.usage.app.services` | `tests/usage/app/services/10_live.py` | Eight documented usage examples for the expected safety gateway | Imports multiple `app.services.live.*` modules | Example-only reference; no implementation exists. |
| Historical `app.services.NEW.live` | `app/services/NEW/live/*.py` at prior commit | Staged safety gateway | 39 registry exports | Deleted and never located at the canonical import path. |

---

## 5. Public Behaviour Inventory

### `app/services/live`

**File responsibility:** No current file exists.

No public class, function, method, or constant can be inventoried because the package is absent.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
| ------ | ---- | -------------- | --------------- | ------------ | ------ | ------- | ----- | ------------ | ------------ |
| _None_ | — | No current public behaviour | — | — | — | — | — | **Unused** | **No demonstrated value** |

### Expected but unavailable interfaces

The following interfaces are referenced by current tests/examples or were exposed by the deleted staging registry. They are **not current public symbols** and are not counted in the audit metrics.

| Expected module | Expected symbols | Current source status | Current callers | Usage status | Value status |
| --------------- | ---------------- | --------------------- | --------------- | ------------ | ------------ |
| `app.services.live.session` | `LiveSession`, `LiveSessionStatus`, `start_live_session`, `stop_live_session`, `recover_live_session`, `get_live_session_status` | Module absent | `test_live_runtime.py`; `10_live.py`; upgrade-plan documentation | **Test-only** | **No demonstrated value** |
| `app.services.live.gates` | `LiveGateDecision`, `LiveGateResult`, `evaluate_live_gate`, `require_live_approval`, `enforce_kill_switch_gate`, kill-switch and emergency-action functions | Module absent | All three live test files; `10_live.py` | **Test-only** | **No demonstrated value** |
| `app.services.live.executor` | `LiveSideEffectMode`, `LiveTradeExecutor`, `execute_live_order_intent`, `validate_live_execution_request` | Module absent | `test_live_runtime.py`; `10_live.py` | **Test-only** | **No demonstrated value** |
| `app.services.live.monitoring` | `LiveMonitor`, `LiveHealthSnapshot`, `check_live_readiness`, `record_live_incident`, `emit_live_monitoring_event` | Module absent | `test_live_runtime.py`; `10_live.py` | **Test-only** | **No demonstrated value** |
| `app.services.live.reconciliation` | `ReconciliationMismatch`, `ReconciliationResult`, `ReconciliationStartupGuard`, `reconcile_state` | Module absent | `test_live_runtime.py`; `10_live.py` | **Test-only** | **No demonstrated value** |
| `app.services.live.policy` | `LiveActionPolicy`, `LIVE_ACTION_POLICY_MATRIX`, `LIVE_POLICY_UNDEFINED`, `get_action_policy` | Module absent | Tests in `test_live_runtime.py`; historical registry | **Test-only** | **No demonstrated value** |
| `app.services.live.ports` | `LiveStateStore`, `AuditSink`, `IdempotencyStore` | Module absent | Tests/historical registry only | **Test-only** | **No demonstrated value** |

### Side-effect classification

Because no current implementation exists, side effects cannot be assigned to the expected interfaces. Test descriptions claim fail-closed, package-only, audit, reconciliation, and monitoring behaviour, but those claims are not current code evidence.

---

## 6. Actual Workflows

No working or partially operational workflow was found inside `app.services.live`.

The following are attempted test/example workflows. Each fails before domain behaviour begins because its import boundary is unavailable.

### `V1-WF-LIVE-001` — Expected Live Session Lifecycle

* **Scope:** Test-only cross-domain attempt
* **Trigger:** Running `tests/unit/app/services/live/test_live_runtime.py` or `tests/usage/app/services/10_live.py`
* **Input boundary:** A settings object, session ID, request ID, and optional recovery context
* **Functions and methods used:** Expected `start_live_session()`, `get_live_session_status()`, `stop_live_session()`, `recover_live_session()`
* **Files involved:** Expected `app/services/live/session.py`; current callers in `test_live_runtime.py` and `10_live.py`
* **External dependencies:** `app.utils.settings`, error types, possible persistence ports
* **Output boundary:** Expected live-session object and status envelopes
* **Failure behaviour:** Import of `app.services.live.session` cannot resolve at the audited ref
* **Operational status:** **Broken**
* **Evidence:** The callers directly import `app.services.live.session`; no package/module exists; `app/services/__init__.py` defines no alias.

```text
Test or usage script
→ import app.services.live.session
→ ModuleNotFoundError before start_live_session()
→ no session workflow
```

### `V1-WF-LIVE-002` — Expected Gate Evaluation and Intent Execution

* **Scope:** Test-only cross-domain attempt
* **Trigger:** A test/example submits an action such as `submit_order` or `sync_positions`
* **Input boundary:** Action name, request payload, settings, approval context, reconciliation state, kill-switch state, request/correlation IDs
* **Functions and methods used:** Expected `evaluate_live_gate()`, `require_live_approval()`, `enforce_kill_switch_gate()`, `validate_live_execution_request()`, `execute_live_order_intent()`
* **Files involved:** Expected `gates.py`, `policy.py`, `executor.py`, and `ports.py`
* **External dependencies:** Settings, risk kill switch, approval context, audit/idempotency/persistence ports, broker adapter boundary
* **Output boundary:** Expected gate results and classified execution result
* **Failure behaviour:** Import of `app.services.live.gates` or `app.services.live.executor` cannot resolve
* **Operational status:** **Broken**
* **Evidence:** Current code searches find these symbols only in tests, examples, and documentation; no production caller or implementation exists.

```text
Test or usage script
→ import app.services.live.gates / executor
→ import failure
→ no gate decision
→ no execution packaging or broker boundary
```

### `V1-WF-LIVE-003` — Expected Monitoring and Reconciliation

* **Scope:** Test-only cross-domain attempt
* **Trigger:** A test/example requests readiness, monitoring, incident recording, or reconciliation
* **Input boundary:** Internal state, broker-truth snapshot, health data, mismatches, or incident details
* **Functions and methods used:** Expected `check_live_readiness()`, `emit_live_monitoring_event()`, `record_live_incident()`, `reconcile_state()`
* **Files involved:** Expected `monitoring.py`, `reconciliation.py`, and persistence ports
* **External dependencies:** Broker-truth provider, state store, incident/audit sink
* **Output boundary:** Expected health snapshot, monitoring event, incident record, or reconciliation result
* **Failure behaviour:** Import of the expected modules cannot resolve
* **Operational status:** **Broken**
* **Evidence:** The interfaces appear in current tests/examples and the deleted staging registry, but no current source module exists.

```text
Test or usage script
→ import app.services.live.monitoring / reconciliation
→ import failure
→ no readiness or reconciliation result
```

### Current live workflow outside this package

The production API route follows a different path:

```text
HTTP/API request
→ app.api.routes.live
→ app.services.execution.live.LiveTradingSession
→ app.services.execution.live.MultiStrategyEngine
→ risk.live safety/portfolio checks
→ MT5-oriented execution components
```

`app.services.live` does not participate in this current workflow.

---

## 7. Usage and Caller Map

There are no current public symbols to map. The table below records callers of expected but missing interfaces.

| Public symbol or expected interface | Called from | Call type | Runtime or test | Evidence |
| ----------------------------------- | ----------- | --------- | --------------- | -------- |
| `start_live_session` | `tests/unit/app/services/live/test_live_runtime.py`; `tests/usage/app/services/10_live.py`; upgrade-plan docs | Direct import and call | Test/example/docs | No production source hit |
| `stop_live_session` | `test_live_runtime.py`; `10_live.py` | Direct import and call | Test/example | No production source hit |
| `recover_live_session` | `test_live_runtime.py`; `10_live.py` | Direct import and call | Test/example | No production source hit |
| `get_live_session_status` | `test_live_runtime.py`; `10_live.py` | Direct import and call | Test/example | No production source hit |
| `evaluate_live_gate` | `test_live_runtime.py`; `test_gates_extra.py`; `10_live.py` | Direct import and call | Test/example | No production source hit |
| Kill-switch functions | `test_gates_extra.py`; `test_live_runtime.py` | Direct import and call | Test | Module absent |
| `LiveTradeExecutor` | `test_live_runtime.py`; `10_live.py` | Direct import/instantiation | Test/example | Module absent |
| `execute_live_order_intent` | `test_live_runtime.py`; `10_live.py` | Direct import and call | Test/example | No production source hit |
| `validate_live_execution_request` | `test_live_runtime.py`; `10_live.py` | Direct import and call | Test/example | Module absent |
| `LiveMonitor` and monitoring functions | `test_live_runtime.py`; `10_live.py` | Direct import and call | Test/example | Module absent |
| `reconcile_state` and reconciliation models | `test_live_runtime.py`; `10_live.py` | Direct import and call | Test/example | Module absent |
| `LiveActionPolicy` and policy matrix | `test_live_runtime.py`; historical registry | Direct import/access | Test/historical | Module absent |
| `LiveStateStore`, `AuditSink`, `IdempotencyStore` | `test_live_runtime.py`; historical registry | Type/port import | Test/historical | Module absent |
| `LiveTradingSession` from `app.services.execution.live` | `app/api/routes/live.py` | Direct production import | Runtime | Different package; not a caller of `app.services.live` |

### Search result

No production/runtime file imports `app.services.live`. Repository-wide searches for:

```text
app.services.live
from app.services.live
start_live_session
evaluate_live_gate
execute_live_order_intent
```

returned tests, examples, and documentation only.

---

## 8. Cross-Domain Surface

### Outbound — this domain depends on

The current requested domain has no code and therefore no current outbound dependencies.

| Depends on (domain/package) | Symbols or capabilities consumed | Where used in this domain | Evidence |
| --------------------------- | -------------------------------- | ------------------------- | -------- |
| _None_ | No current implementation | — | Package absent |

### Historically intended outbound dependencies — not current

| Depends on (domain/package) | Intended capability | Evidence | Current status |
| --------------------------- | ------------------- | -------- | -------------- |
| `app.utils.settings` | Live configuration and fail-closed mode | Current tests and usage example | Referenced only by unavailable package tests |
| `app.utils.errors` | Approved live error codes and validation errors | `test_live_runtime.py` | Utility code may exist, but no current live package consumes it |
| Risk service | Kill-switch state and risk-decision references | Tests and deleted staging design | No current canonical integration |
| Approval/audit/idempotency stores | Approval validation, audit persistence, replay protection | Deleted staging registry and tests | No current canonical integration |
| Broker/state providers | Reconciliation and live execution boundary | Deleted staging design and tests | No current canonical integration |

### Inbound — others depend on this domain

| Consuming domain/package | Symbols consumed from this domain | Purpose | Evidence |
| ------------------------ | --------------------------------- | ------- | -------- |
| `tests/unit/app/services/live/test_live_runtime.py` | Session, gates, executor, monitoring, reconciliation, policy, ports | Unit-test expected safety-gateway behaviour | Test-only and unresolvable |
| `tests/unit/app/services/live/test_gates_extra.py` | Kill-switch and gate functions | Broad extra coverage | Test catches all exceptions, so missing imports may be masked |
| `tests/unit/app/services/live/test_live_risk_sim_pybots_extra2.py` | `ExecutionGates` | Broad smoke-style coverage | Import/call wrapped in `except Exception: pass` |
| `tests/usage/app/services/10_live.py` | Session, gates, executor, monitoring, reconciliation | Eight executable examples | Example-only and unresolvable |
| Upgrade-plan documentation | Session and safety-gateway interfaces | Planned architecture and integration | Documentation, not runtime usage |

### Active live surface outside the requested domain

| Consuming domain/package | Actual symbol consumed | Actual provider | Purpose |
| ------------------------ | ---------------------- | --------------- | ------- |
| `app.api.routes.live` | `LiveTradingSession` | `app.services.execution.live` | Starts and controls the current multi-strategy MT5 execution session |

---

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
| ------ | ------ | ------- | -------- | ---- |
| Expected `app.services.live.session` | `app.services.execution.live.session` | Both describe live-session startup, status, stop, pause/resume or recovery concerns | Tests/examples expect `LiveSession`; API route imports `LiveTradingSession` from execution | Two incompatible live-session surfaces and unclear ownership |
| Expected `app.services.live.gates` | `app.services.risk.live.safety_checks` plus validation inside `execution.live.engine` | Pre-execution blocking and safety decisions | `MultiStrategyEngine._validate_signal()` calls portfolio and safety checks | Intended gateway may be bypassed by execution-owned checks |
| Expected `app.services.live.executor` | `app.services.execution.live.trade_executor` and `MultiStrategyEngine` | Validation and execution of live order intent | Active execution package sends MT5-oriented trades; expected executor tests describe a separate classified gateway | Duplicate execution boundary concepts with different contracts |
| Expected `app.services.live.monitoring` | `execution.live.engine.get_status()`, status JSON export, and `execution.live.dashboard` | Live status and monitoring | Active engine writes `multi_strategy_status.json`; dashboard reads it | Monitoring split across missing gateway and active execution package |
| Historical `app/services/NEW/live` | Expected canonical `app/services/live` | Nearly identical intended safety-gateway API | Historical registry imports `app.services.live.*` from a file located under `app/services/NEW/live` | Staging code was structurally unreachable at its own expected import path |
| Current tests/examples | Current implementation tree | Tests describe a package that no longer exists | Direct imports in four files; no current source package | Tests do not validate the production live runtime |

---

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
| ---- | ------- | ------------------ | ---------- | -------- |
| `app/services/live` | No package, module, exports, or registry exists at audited ref | Direct package/file fetch; repository code search; parent registration inspection | **High** | Both `app/services/live/` and `app/services/live.py` are absent; no alias in `app/services/__init__.py` |
| `tests/unit/app/services/live/test_live_runtime.py` | Targets an unavailable package; cannot validate current production runtime | Import search; symbol search; package existence check | **High** | Repeated direct imports of `app.services.live.*` |
| `tests/unit/app/services/live/test_gates_extra.py` | Targets unavailable gate functions and swallows all exceptions | File inspection; package search | **High** | Every function call is wrapped in broad `try/except Exception: pass` |
| `tests/unit/app/services/live/test_live_risk_sim_pybots_extra2.py::test_live_extra2` | References unavailable `ExecutionGates`; broad exception handling prevents the test from proving functionality | File inspection; symbol search | **High** | Import and call are swallowed by `except Exception: pass` |
| `tests/usage/app/services/10_live.py` | Executable examples target unavailable modules | Full import block inspection; package/symbol search | **High** | Imports `executor`, `gates`, `monitoring`, `reconciliation`, and `session` from `app.services.live` |
| Upgrade-plan live interfaces | Documentation describes symbols with no current implementation | Symbol searches and source-tree check | **High** | `start_live_session` appears in docs/tests/examples only |
| Historical `app/services/NEW/live` | Deleted staging implementation, not current code | Current-ref lookup; prior-ref lookup; latest commit deletion diff | **High** | Files existed at prior commit and were deleted at audited commit |
| `app.services.execution.live` as substitute for requested package | Provides real live execution value but does not implement the expected public contract | Registry, engine, session, route, and caller inspection | **High** | Different import path, exports, responsibilities, and runtime caller |

No item is labelled dead code solely from absence of production callers. The canonical package itself is absent; the stale test/example files are labelled questionable or obsolete references rather than dead production code.

---

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
| --------------------- | ------------------ | -------------- | -------- |
| Canonical package import | No `app/services/live` package or alias | All expected imports fail before behaviour begins | Package lookup plus `app/services/__init__.py` inspection |
| Live session lifecycle | Expected session module is absent | Start/stop/recovery/status workflow is unavailable through the documented interface | `test_live_runtime.py` and `10_live.py` |
| Gate evaluation | Expected gates module is absent | Approval, kill-switch, staleness, reconciliation, and audit gates cannot run through canonical API | Tests/examples import `app.services.live.gates` |
| Live intent execution | Expected executor module is absent | Package-only/shadow/micro-live classification workflow is unavailable | Tests/examples import `app.services.live.executor` |
| Monitoring/readiness | Expected monitoring module is absent | Documented health and incident workflow cannot run | Tests/examples import `app.services.live.monitoring` |
| Reconciliation | Expected reconciliation module is absent | No canonical internal-vs-broker-truth reconciliation workflow | Tests/examples import `app.services.live.reconciliation` |
| Persistence ports | Expected ports module is absent | No canonical live state, audit, or idempotency contract | Historical registry and tests |
| Production API integration | API route imports `app.services.execution.live`, not `app.services.live` | Expected safety gateway is not on the current API call path | `app/api/routes/live.py` |
| Historical staging promotion | `app/services/NEW/live` was never installed at canonical path and was later deleted | Staged implementation did not become the tested package | Prior commit registry and latest deletion commit |
| Test reliability | Extra tests catch all exceptions | Missing imports and broken calls may still produce passing tests | `test_gates_extra.py`; `test_live_risk_sim_pybots_extra2.py` |

---

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
| -- | ------- | -------- | ------ | -------- |
| `V1-ISSUE-LIVE-001` | Requested package is absent | `app/services/live` | No current domain implementation or public API can be used | Direct repository lookup and code search |
| `V1-ISSUE-LIVE-002` | Tests and examples target a nonexistent import path | `tests/unit/app/services/live/*`; `tests/usage/app/services/10_live.py` | Test suite and examples are detached from current production code | Direct `app.services.live.*` imports |
| `V1-ISSUE-LIVE-003` | Historical implementation was stored under a staging path while importing the canonical path | Historical `app/services/NEW/live/__init__.py` | The staged package was structurally inconsistent and could not serve as the expected canonical registry without relocation | Historical file path versus its `from app.services.live...` imports |
| `V1-ISSUE-LIVE-004` | Latest commit deleted the staged live safety gateway without removing its tests/examples | Commit `a39d26498e14772c571d75fa9a5f0e477a1dd912` | Leaves stale interfaces and misleading coverage assets | Commit deletion diff plus current tests |
| `V1-ISSUE-LIVE-005` | Production API uses a different live runtime package | `app/api/routes/live.py` → `app.services.execution.live.LiveTradingSession` | The documented/tested canonical gateway does not participate in active API flow | Import at `app/api/routes/live.py` |
| `V1-ISSUE-LIVE-006` | Live responsibility is fragmented across execution, risk, API, and deleted gateway concepts | `app/services/execution/live`; `app/services/risk/live`; expected `app/services/live` | Ownership, safety authority, and comparison against future requirements are ambiguous | Execution engine imports risk safety/portfolio components while tests describe separate gates |
| `V1-ISSUE-LIVE-007` | Extra tests suppress all exceptions | `test_gates_extra.py`; `test_live_risk_sim_pybots_extra2.py` | Tests can pass despite missing imports, missing symbols, or runtime failures | Broad `except Exception: pass` around imports/calls |
| `V1-ISSUE-LIVE-008` | Parent service package provides no compatibility alias | `app/services/__init__.py` | `app.services.live` cannot resolve indirectly to `app.services.execution.live` | Generic loader helpers only; no alias or `sys.modules` registration |
| `V1-ISSUE-LIVE-009` | Documentation and usage contracts are stale | `docs/upgrade-plan/10-live-runtime.md`; `10_live.py` | Users and future audits may infer capabilities that are not in current code | Symbol search finds documented interfaces but no implementation |
| `V1-ISSUE-LIVE-010` | Current production live runtime and expected safety gateway have incompatible public models | `LiveTradingSession`/`MultiStrategyEngine` versus expected `LiveSession`/gate/executor interfaces | Callers cannot transparently switch paths; tests do not cover current runtime | Different registries and caller paths |

---

## 13. V1 Capability Catalogue

### Confirmed current capabilities in `app.services.live`

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
| ------------- | ---------- | ---------------------- | ----------- | ------------ | ------------ | ----- |
| `V1-CAP-LIVE-000` | No active canonical live-domain capability | No files under `app/services/live` | None | **Unused** | **No demonstrated value** | The active runtime is located under `app/services/execution/live` and must be audited separately if it is intended to represent this domain. |

### Referenced but unavailable interfaces — not counted as current capabilities

| Reference ID | Intended capability | Missing implementation | Attempted workflow(s) | Usage status | Value status | Notes |
| ------------ | ------------------- | ---------------------- | --------------------- | ------------ | ------------ | ----- |
| `V1-REF-LIVE-001` | Live session lifecycle | `app/services/live/session.py` | `V1-WF-LIVE-001` | **Test-only** | **No demonstrated value** | Expected start, stop, status, and recovery interface |
| `V1-REF-LIVE-002` | Deterministic live gate chain | `app/services/live/gates.py` | `V1-WF-LIVE-002` | **Test-only** | **No demonstrated value** | Expected approval, kill-switch, staleness, reconciliation, and audit gates |
| `V1-REF-LIVE-003` | Live order-intent validation and execution classification | `app/services/live/executor.py` | `V1-WF-LIVE-002` | **Test-only** | **No demonstrated value** | Expected package-only/shadow/live side-effect modes |
| `V1-REF-LIVE-004` | Live monitoring and incident recording | `app/services/live/monitoring.py` | `V1-WF-LIVE-003` | **Test-only** | **No demonstrated value** | Expected readiness and health snapshots |
| `V1-REF-LIVE-005` | Broker-truth reconciliation | `app/services/live/reconciliation.py` | `V1-WF-LIVE-003` | **Test-only** | **No demonstrated value** | Expected mismatch classification and startup guard |
| `V1-REF-LIVE-006` | Live action policy matrix | `app/services/live/policy.py` | `V1-WF-LIVE-002` | **Test-only** | **No demonstrated value** | Historical registry only |
| `V1-REF-LIVE-007` | Live persistence port contracts | `app/services/live/ports.py` | `V1-WF-LIVE-002`, `V1-WF-LIVE-003` | **Test-only** | **No demonstrated value** | Expected state, audit, and idempotency protocols |
| `V1-REF-LIVE-008` | Emergency live actions and kill switches | `app/services/live/gates.py` | `V1-WF-LIVE-002` | **Test-only** | **No demonstrated value** | Extra tests swallow all failures |

---

## 14. Audit Conclusions

### Valuable behaviour worth preserving

No valuable behaviour can be confirmed inside `app.services.live` because the package is absent.

The repository does contain real live-trading behaviour under `app.services.execution.live`, including:

* an API-controlled `LiveTradingSession`;
* a `MultiStrategyEngine`;
* bar monitoring and signal processing;
* position and trade execution;
* safety and portfolio checks through `app.services.risk.live`;
* state persistence, notifications, status export, and a terminal dashboard.

Those capabilities are outside this audit boundary. They should not be treated as evidence that the requested canonical safety gateway exists.

### Behaviour that exists but is disconnected

The repository contains extensive tests, examples, documentation, and historical deleted source describing:

* session lifecycle;
* live readiness and deterministic gates;
* approval and kill-switch enforcement;
* live intent validation;
* side-effect classification;
* reconciliation;
* monitoring and incident recording;
* policy lookup;
* audit, state, and idempotency ports.

None of these interfaces is currently connected to a resolvable `app.services.live` package.

### Likely dead weight

The following items currently provide no demonstrated runtime value for the requested package:

* `tests/unit/app/services/live/test_live_runtime.py`;
* `tests/unit/app/services/live/test_gates_extra.py`;
* the live portion of `test_live_risk_sim_pybots_extra2.py`;
* `tests/usage/app/services/10_live.py`;
* documentation references to the unavailable canonical interfaces.

They should not be labelled production dead code because they are tests/examples/documentation, but they are stale or disconnected at the audited ref.

### Duplicated responsibilities

Live-session management, safety checks, trade execution, and monitoring concepts are split between:

* expected but missing `app.services.live`;
* active `app.services.execution.live`;
* active `app.services.risk.live`;
* `app.api.routes.live`;
* historical deleted `app/services/NEW/live`.

This creates overlapping names and responsibilities without one confirmed canonical boundary.

### Important uncertainties

1. The intended Version 1 snapshot may exist on another branch, tag, local checkout, or uncommitted workspace.
2. The user may have intended `app/services/execution/live` rather than `app/services/live`.
3. The historical `app/services/NEW/live` package may have been intended for later relocation, but no current relocation or alias exists.
4. Tests were not executed, although static evidence strongly indicates canonical imports cannot resolve.

### Areas requiring manual confirmation

* Confirm the exact Version 1 branch/tag/commit to audit.
* Confirm whether the target should be:
  * current `app/services/execution/live`;
  * historical `app/services/NEW/live`;
  * or a missing/uncommitted `app/services/live`.
* Confirm whether stale tests/examples should be removed, restored against a canonical package, or redirected to the current execution runtime. This audit records the issue only and does not prescribe a Version 2 design.

---

## Final Validation

* Every current Python file in `app/services/live` is represented: **Yes — there are zero files.**
* Every documented current public export exists in code: **No — documented/tested exports are unavailable.**
* Every current `__init__.py` export was checked: **Yes — no `app/services/live/__init__.py` exists.**
* Parent-package alias or dynamic registration was checked: **Yes — none exists in `app/services/__init__.py`.**
* Callers were searched across the available repository: **Yes.**
* Direct imports, calls, docs references, tests, examples, API routes, and alternate package imports were checked: **Yes.**
* Inbound and outbound cross-domain usage is summarized: **Yes.**
* Production usage is distinguished from test/example usage: **Yes.**
* Workflows are based on actual import/call evidence: **Yes; all canonical workflows are classified Broken.**
* Uncertain findings are labelled: **Yes.**
* No Version 2 design was invented: **Yes.**
* No repository code was changed: **Yes.**
