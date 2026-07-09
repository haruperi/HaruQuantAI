# Prompt for Building Phase 7: Trading Runtime

Copy and paste this prompt when starting the AI build session for the Trading Runtime module.

---

## Task Objective
You are tasked with building the new Trading Runtime domain (`app/services/trading/`) from scratch as specified in the architecture requirements document: [07_trading.md](file:///c:/Users/rharu/AppDev/HaruquantAI/docs/dev/phase-implementation-plan/07_trading.md).

Since this module is being built completely from scratch, there are no legacy files to clean up in the folder.
* **Precedence:** Precedence is given to the functional requirements defined in [07_trading.md](file:///c:/Users/rharu/AppDev/HaruquantAI/docs/dev/phase-implementation-plan/07_trading.md).
* **Strict Integrity:** Enforce all 186 functional requirements (`TRD-FR-001` through `TRD-FR-186`), 19 non-functional requirements (`TRD-NFR-001` through `TRD-NFR-019`), and all 10 cross-module contract requirements (`TRD-XM-001` through `TRD-XM-010`).
* **Design Parity:** All MQL5-compatible wrappers under `trading/info/` must align with the read-only facades defined in the specification.

---

## 10-Step Workflow per Module
Execute this sequence module-by-module. Do not start a new module until the current module is fully completed, tested, and validated.

1. **Implement Functional Requirements:** Create the module files as specified in Section 3 of [07_trading.md](file:///c:/Users/rharu/AppDev/HaruquantAI/docs/dev/phase-implementation-plan/07_trading.md).
2. **Double Check Requirements:** Verify that every requirement tag mapped to this file is fully satisfied without shortcuts.
3. **Google Standard Docstrings:** Document all modules, classes, and functions using the Google Python Style Guide docstring format (including types, arguments, returns, and exceptions raised).
4. **Strict Logging:** Log every function using the custom system logger (`from app.utils.logger import logger`).
   * Every function must have at least one log.
   * If a function has no specific steps to log, log what the function did (e.g. input/output summary).
   * Use `info` level for routine operational milestones (e.g., successful order validations, gate decisions, or state transitions).
   * Use `debug` level for granular information (e.g., tick/price details, internal bucket fills, or lock updates).
5. **Unit Tests (Coverage Target >= 80% / 100% Branch Coverage for Critical Files):** Add unit tests under `tests/services/trading/`. Ensure coverage is >= 80%.
   * **CRITICAL:** The modules `gates/`, `execution/state_machine.py`, `state/idempotency.py`, and `reconciliation/` MUST achieve **100% branch coverage**, verified in isolation using separate `--cov-branch --cov-fail-under=100` checks.
6. **Usage Examples:** Add a dedicated function inside [07_trading.py](file:///c:/Users/rharu/AppDev/HaruquantAI/tests/usage/07_trading.py) for the current module.
   * Use the naming convention: `example_{#}_{module_name}()` (e.g., `example_01_contracts()`).
   * Structure it so it can be run independently or sequentially. Reference [02_data.py](file:///c:/Users/rharu/AppDev/HaruquantAI/tests/usage/02_data.py) for the style.
7. **Update Module README:** Add a README inside the module folder explaining its boundary role, interface inputs, and dependencies.
8. **Update Changelog & Traceability:** Document structural changes and implementation updates in `docs/dev/phase-implementation-plan/CHANGELOG.md`. Also, update [07_trading.md](file:///c:/Users/rharu/AppDev/HaruquantAI/docs/dev/phase-implementation-plan/07_trading.md) by marking `[X]` for all completed requirements and sub-items. For each completed requirement, add implementation proof directly in the format `*Evidence: <file_path> line <start>-<end>*` (e.g., `*Evidence: app/services/trading/contracts.py line 40-62*`). Ensure line numbers are exact.
9. **Quality Checks:** Run the following commands in the workspace and verify all checks pass:
   * `uv run ruff check --fix app/services/trading`
   * `uv run ruff format app/services/trading`
   * `uv run mypy app/services/trading`
   * `pre-commit run --all-files`
10. **Draft Commit Message:** Output a clean, structured git commit message summarizing the changes for this module. **Do NOT run `git commit` automatically; the user will review and commit manually.**

---

## Formatting and Linting Standards
* **Python Style:** Strict [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).
* **Formatters:** Double quotes, magic trailing commas. Run order: `ruff check --fix` -> `ruff format` -> `mypy`.
* **Typing:** Explicit type hints on all signatures. No generic `Any` types where specific models/collections can be typed.
* **Imports:** Always use absolute imports.
* **Clock/RNG Parity:** Enforce that all timestamps, staleness checks, and randomizations leverage the injected `Clock` and `RNG` dependencies (`TRD-FR-138/140`). Direct imports of `datetime.now`, `time.time`, or similar are strictly prohibited.

---

## Dependency-Safe Implementation Order
Always build from the bottom up, following this rule:

> **Contracts first → Ports & Configs → Primitives (Idempotency, Journal, Error Redaction) → Info Facades → Actions & Validations → Execution & Coordination → Gates Middleware → Reconciliation & Authority → Monitoring & Watchdogs → Run Session Management → Tool Registry & Exports.**

Below is the recommended step-by-step order:

### 0. Package skeleton first
Create the folders and lightweight empty `__init__.py` files to define the workspace structure.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 0.1 | `app/services/trading/__init__.py` | Create placeholder init (final exports will be added last). |

---

### 1. Contracts & Interfaces (Data & State Models)
Defines all shared request/response models, allocations, and type-safe enums.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 1.1 | `app/services/trading/contracts.py` | Defines routes, TIFs, AllocationVector, RegulatoryTags, NormalizedTradeResult, and error envelope structures. <br>**Tracked:** `TRD-FR-004`, `TRD-FR-005`, `TRD-FR-006`, `TRD-FR-007`, `TRD-FR-008`, `TRD-FR-009`, `TRD-FR-010`, `TRD-FR-011`, `TRD-FR-012`, `TRD-FR-013`, `TRD-FR-014`, `TRD-FR-015`, `TRD-FR-016`, `TRD-FR-017`, `TRD-FR-018`. |
| 1.2 | `app/services/trading/state/ports.py` | Declares protocols/abstract interfaces for TradeStore, TradingStateStore, AuditSink, IdempotencyStore, EventJournal, Clock, RNG, and EncryptionProvider. <br>**Tracked:** `TRD-FR-133`, `TRD-FR-134`, `TRD-FR-135`, `TRD-FR-136`, `TRD-FR-137`, `TRD-FR-138`, `TRD-FR-139`, `TRD-FR-140`, `TRD-FR-141`, `TRD-FR-142`. |

---

### 2. Configurations & Security Controls
Handles secrets validation, hot-reloading boundaries, and credential mapping.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 2.1 | `app/services/trading/config/models.py` | Holds route settings, rate limits, timeouts, and secrets references. <br>**Tracked:** `TRD-FR-054`, `TRD-FR-055`, `TRD-FR-056`. |
| 2.2 | `app/services/trading/config/loader.py` | Validates configuration constraints, supports immutable configs, and enforces reloading policies. <br>**Tracked:** `TRD-FR-057`, `TRD-FR-058`, `TRD-FR-059`. |
| 2.3 | `app/services/trading/config/secrets.py` | Resolves database credentials/tokens via references without leaking strings. <br>**Tracked:** `TRD-FR-060`, `TRD-FR-061`. |
| 2.4 | `app/services/trading/config/notifications.py` | Manages operational notifications channel parameters. <br>**Tracked:** `TRD-FR-062`. |
| 2.5 | `app/services/trading/config/security_profile.py` | Defines encryption/security transport profiles. <br>**Tracked:** `TRD-FR-063`. |

---

### 3. Security Boundaries & Error Redaction
Constructs the recursive redaction boundaries and exception mapping structures.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 3.1 | `app/services/trading/security/error_mapping.py` | Translates raw SDK errors into standard error codes. <br>**Tracked:** `TRD-FR-176`, `TRD-FR-177`. |
| 3.2 | `app/services/trading/security/redaction_boundary.py` | Redacts sensitive credentials recursively; exposes a crash-resilient write-ahead DLQ logger. <br>**Tracked:** `TRD-FR-178`, `TRD-FR-179`, `TRD-FR-180`, `TRD-FR-181`. |

---

### 4. Persistence Implementations (Idempotency & Event Journal)
Ensures state transitions are durable, duplicate-free, and forensics-replayable.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 4.1 | `app/services/trading/state/idempotency.py` | Computes JSON-canonical key hashes and tracks active in-progress leases. <br>**Tracked:** `TRD-FR-143`, `TRD-FR-144`, `TRD-FR-145`. |
| 4.2 | `app/services/trading/state/event_journal.py` | Implements append-only journals, logical clock ordering sequence, state snapshots, replay builders, and detached signatures. <br>**Tracked:** `TRD-FR-146`, `TRD-FR-147`, `TRD-FR-148`, `TRD-FR-149`, `TRD-FR-150`, `TRD-FR-151`, `TRD-FR-152`, `TRD-FR-153`, `TRD-FR-154`, `TRD-FR-155`, `TRD-FR-156`. |
| 4.3 | `app/services/trading/state/manager.py` | Exposes local state update coordinators. |

---

### 5. Read-Only Info Facades
Exposes MQL5-compatible read-only wrappers for terminal indicators, accounts, symbols, and historical orders.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 5.1 | `app/services/trading/info/account.py` | Exposes read-only account balance, margin, leverage. <br>**Tracked:** `TRD-FR-050`, `TRD-FR-051`, `TRD-FR-052`, `TRD-FR-053` (collectively across all `info/*` facades). |
| 5.2 | `app/services/trading/info/symbol.py` | Resolves symbol trade sessions, min/max volume limits, tick sizes. <br>**Tracked:** `TRD-FR-050`, `TRD-FR-051`, `TRD-FR-052`, `TRD-FR-053` (collectively). |
| 5.3 | `app/services/trading/info/position.py` | Wraps active broker positions. <br>**Tracked:** `TRD-FR-050`, `TRD-FR-051`, `TRD-FR-052`, `TRD-FR-053` (collectively). |
| 5.4 | `app/services/trading/info/order.py` | Exposes pending order tickets. <br>**Tracked:** `TRD-FR-050`, `TRD-FR-051`, `TRD-FR-052`, `TRD-FR-053` (collectively). |
| 5.5 | `app/services/trading/info/deal.py` | Resolves transaction execution details. <br>**Tracked:** `TRD-FR-050`, `TRD-FR-051`, `TRD-FR-052`, `TRD-FR-053` (collectively). |
| 5.6 | `app/services/trading/info/history_order.py` | Fetches closed historical orders. <br>**Tracked:** `TRD-FR-050`, `TRD-FR-051`, `TRD-FR-052`, `TRD-FR-053` (collectively). |
| 5.7 | `app/services/trading/info/terminal.py` | Exposes broker terminal connection state. <br>**Tracked:** `TRD-FR-050`, `TRD-FR-051`, `TRD-FR-052`, `TRD-FR-053` (collectively). |

---

### 6. Validation & Action Primitives
Implements local parameter validation, fat-finger ceilings, and symbol blocklists.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 6.1 | `app/services/trading/actions/validation.py` | Handles Decimal normalization, stops distance, margin math, account conversion rates, and short locate validation checks. <br>**Tracked:** `TRD-FR-037`, `TRD-FR-038`, `TRD-FR-039`, `TRD-FR-040`, `TRD-FR-041`, `TRD-FR-042`, `TRD-FR-043`, `TRD-FR-044`, `TRD-FR-045`, `TRD-FR-046`, `TRD-FR-047`, `TRD-FR-048`, `TRD-FR-049`. |
| 6.2 | `app/services/trading/actions/orders.py` | Defines basic buy, sell, limit, stop, modify, and delete actions. <br>**Tracked:** `TRD-FR-021`, `TRD-FR-022`, `TRD-FR-023`, `TRD-FR-024`, `TRD-FR-025`. |
| 6.3 | `app/services/trading/actions/positions.py` | Coordinates position modifications, SL/TP setups, and exposure reductions. <br>**Tracked:** `TRD-FR-026`, `TRD-FR-027`. |
| 6.4 | `app/services/trading/actions/controls.py` | Defines strategy pause, resume, shutdown, and kill switches. <br>**Tracked:** `TRD-FR-028`, `TRD-FR-029`, `TRD-FR-030`, `TRD-FR-031`, `TRD-FR-032`, `TRD-FR-033`, `TRD-FR-034`. |
| 6.5 | `app/services/trading/actions/emergency.py` | Coordinates emergency cancel-all and flatten commands. <br>**Tracked:** `TRD-FR-035`, `TRD-FR-036`. |

---

### 7. Execution Primitives & State Machine
Enforces state machine rules, commission calculation, and provider code classification.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 7.1 | `app/services/trading/execution/state_machine.py` | Maps valid order/position lifecycle transitions, version-gated amendments, and duplicate report deduplication. <br>**Tracked:** `TRD-FR-126`, `TRD-FR-127`, `TRD-FR-128`, `TRD-FR-129`, `TRD-FR-130`, `TRD-FR-131`. |
| 7.2 | `app/services/trading/execution/response_classifier.py` | Standardizes broker return codes, server stop-out events, and corporate actions. <br>**Tracked:** `TRD-FR-117`, `TRD-FR-118`, `TRD-FR-119`, `TRD-FR-120`, `TRD-FR-121`, `TRD-FR-122`. |
| 7.3 | `app/services/trading/execution/rate_limiter.py` | Implements client-side token-bucket rate limits per broker provider. <br>**Tracked:** `TRD-FR-123`, `TRD-FR-124`. |
| 7.4 | `app/services/trading/execution/broker_capability_validation.py` | Resolves supported order capabilities (native OCO, CoD, attachment support). <br>**Tracked:** `TRD-FR-115`, `TRD-FR-116`. |
| 7.5 | `app/services/trading/execution/shadow.py` | Implements shadow-routing comparison models. <br>**Tracked:** `TRD-FR-125`. |

---

### 8. Gating Middleware (Policy Matrix & Pre-Flight Checks)
Implements the 16 canonical pre-flight gates, dual approvals, and turbulence halts.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 8.1 | `app/services/trading/gates/policy_matrix.py` | Resolves allowed permission boundaries and emergency rules. <br>**Tracked:** `TRD-FR-089`. |
| 8.2 | `app/services/trading/gates/approval.py` | Verifies single/dual operator approvals and request hash binding validations. <br>**Tracked:** `TRD-FR-090`, `TRD-FR-091`, `TRD-FR-092`. |
| 8.3 | `app/services/trading/gates/readiness.py` | Validates local clock drift and PTP synchronization offset ceilings. <br>**Tracked:** `TRD-FR-093`, `TRD-FR-094`, `TRD-FR-095`, `TRD-FR-096`. |
| 8.4 | `app/services/trading/gates/kill_switch.py` | Evaluates persistent kill-switch matrices. <br>**Tracked:** `TRD-FR-097`, `TRD-FR-098`, `TRD-FR-099`, `TRD-FR-100`. |
| 8.5 | `app/services/trading/gates/audit_and_compensation.py` | Persists pre-mutation audit logs before dispatching. <br>**Tracked:** `TRD-FR-101`. |
| 8.6 | `app/services/trading/gates/pipeline.py` | Orchestrates the 16 canonical gates, ComplianceGate, and MarketTurbulenceGate price velocity checks. <br>**Tracked:** `TRD-FR-083`, `TRD-FR-084`, `TRD-FR-085`, `TRD-FR-086`, `TRD-FR-087`, `TRD-FR-088`. |

---

### 9. Core Coordinator & Reporting
Orchestrates async execution threads, client order IDs, and TCAs.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 9.1 | `app/services/trading/execution/coordinator.py` | Dispatches requests asynchronously, maps allocations, manages synthetic OCO watchdogs, multi-leg spreads, and cancel-and-replace modify recoveries. <br>**Tracked:** `TRD-FR-102`, `TRD-FR-103`, `TRD-FR-104`, `TRD-FR-105`, `TRD-FR-106`, `TRD-FR-107`, `TRD-FR-108`, `TRD-FR-109`, `TRD-FR-110`, `TRD-FR-111`, `TRD-FR-112`, `TRD-FR-113`, `TRD-FR-114`. |
| 9.2 | `app/services/trading/execution/reporting.py` | Exports execution cost entries, slippages, and latencies. <br>**Tracked:** `TRD-FR-132`. |

---

### 10. State Reconciliation
Performs snapshots comparison, unknown outcome lockouts, and orphan deals quarantine.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 10.1 | `app/services/trading/reconciliation/snapshots_and_compare.py` | Compares local TradeStore states against broker query dumps. <br>**Tracked:** `TRD-FR-163`. |
| 10.2 | `app/services/trading/reconciliation/authority_and_retry_guard.py` | Restricts mutations on unresolved socket timeouts or stream gaps. <br>**Tracked:** `TRD-FR-164`, `TRD-FR-165`, `TRD-FR-166`. |
| 10.3 | `app/services/trading/reconciliation/service.py` | Coordinates periodic/startup syncs and enforces external deal quarantine rules. <br>**Tracked:** `TRD-FR-157`, `TRD-FR-158`, `TRD-FR-159`, `TRD-FR-160`, `TRD-FR-161`, `TRD-FR-162`. |

---

### 11. Monitoring & Health
Alerts on drift breaches, triggers circuit breakers, and runs heartbeat heartbeats.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 11.1 | `app/services/trading/monitoring/timeouts_and_staleness.py` | Calculates latency distributions; implements lost-order recovery watchdog. <br>**Tracked:** `TRD-FR-171`, `TRD-FR-172`. |
| 11.2 | `app/services/trading/monitoring/operational_signals.py` | Declares severity signals taxonomy and escalation runbooks. <br>**Tracked:** `TRD-FR-173`, `TRD-FR-174`. |
| 11.3 | `app/services/trading/monitoring/heartbeat_watchdog.py` | Emits liveness heartbeats to external watchdog nodes. <br>**Tracked:** `TRD-FR-175`. |
| 11.4 | `app/services/trading/monitoring/tool_health.py` | Degrades tool status dynamically on consecutive broker timeouts. <br>**Tracked:** `TRD-FR-170`. |
| 11.5 | `app/services/trading/monitoring/service.py` | Evaluates circuit breakers and latencies to downgrade routes dynamically. <br>**Tracked:** `TRD-FR-167`, `TRD-FR-168`, `TRD-FR-169`. |

---

### 12. Promotion Ladder & Preconditions
Controls strategy route mutations promotion sequences.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 12.1 | `app/services/trading/promotion/ladder.py` | Enforces stage matrix promotion validations. <br>**Tracked:** `TRD-FR-182`, `TRD-FR-183`, `TRD-FR-184`. |
| 12.2 | `app/services/trading/promotion/preconditions.py` | Restricts activation when switches or unresolved drifts exist. <br>**Tracked:** `TRD-FR-185`, `TRD-FR-186`. |

---

### 13. Session Runtime Coordination
Controls multi-tenant locks, session scopes, and budget allocations.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 13.1 | `app/services/trading/runtime/session_manager.py` | Manages session lifecycle states, cancel-on-disconnect heartbeats, and reconnect resync loops. <br>**Tracked:** `TRD-FR-064`, `TRD-FR-065`, `TRD-FR-066`, `TRD-FR-067`, `TRD-FR-068`, `TRD-FR-069`, `TRD-FR-070`, `TRD-FR-071`, `TRD-FR-072`. |
| 13.2 | `app/services/trading/runtime/coordination.py` | Resolves optimistic concurrency locks and cross-strategy counter policies. <br>**Tracked:** `TRD-FR-073`, `TRD-FR-074`, `TRD-FR-075`, `TRD-FR-076`. |
| 13.3 | `app/services/trading/runtime/cost_control.py` | Evaluates session/strategy budget caps. <br>**Tracked:** `TRD-FR-077`, `TRD-FR-078`, `TRD-FR-079`. |
| 13.4 | `app/services/trading/runtime/signal_processor.py` | Translates strategy signals into request envelopes. <br>**Tracked:** `TRD-FR-080`, `TRD-FR-081`, `TRD-FR-082`. |

---

### 14. Tools & Registry
Registers tools, exports callable wrappers, and validates input envelopes.

| Order | File | Purpose & Requirements Tracked |
|---|---|---|
| 14.1 | `app/services/trading/tool_registry.py` | Registers callable trading tools, schemas, and metadata. <br>**Tracked:** `TRD-FR-019`, `TRD-FR-020`. |
| 14.2 | `app/services/trading/__init__.py` | Finalizes public export definitions and `__all__` hooks. <br>**Tracked:** `TRD-FR-001`, `TRD-FR-002`, `TRD-FR-003`. |

---

## Cross-Module (XM) & Non-Functional (NFR) Requirements Tracking

To ensure complete coverage, all peer cross-module and non-functional requirements are allocated and verified as follows:

### 🔗 Cross-Module Requirements (`TRD-XM-###`)

*   **TRD-XM-001 (Simulator - Validation Parity):** Validated in `tests/services/trading/actions/test_validation.py` & verified during simulator execution calls.
*   **TRD-XM-002 (Simulator - Paper Fill Ingestion):** Handled in `execution/coordinator.py` under the `paper` handler integration test.
*   **TRD-XM-003 (Data - Session Calendars):** Verified inside `actions/validation.py` session gate test.
*   **TRD-XM-003A (Data - Corporate Splits):** Applied inside `reconciliation/service.py` and `state/ports.py` adjustments test.
*   **TRD-XM-003B (Data - Halt Statuses):** Checked in `runtime/session_manager.py` halt update tests.
*   **TRD-XM-004 (Analytics - TCA logs):** Emitted from `execution/reporting.py` audit sink.
*   **TRD-XM-005 (Risk - Delta pre-check):** Queried inside `gates/pipeline.py` (Gate 7 precheck validation).
*   **TRD-XM-005A (Risk - Post-trade breaches):** Handled in `runtime/session_manager.py` risk event subscription tests.
*   **TRD-XM-006 (Risk/Data - HTB Locates):** Loaded in `actions/validation.py` locate gate test.
*   **TRD-XM-007 (Simulator - Slippage Injection):** Injected in `execution/coordinator.py` test suite.

### ⚙️ Non-Functional Requirements (`TRD-NFR-###`)

*   **TRD-NFR-001 to TRD-NFR-003 (Safe Gates):** Handled inside `gates/pipeline.py` and `promotion/ladder.py`.
*   **TRD-NFR-004 (Shutdown):** Handled inside `runtime/session_manager.py`.
*   **TRD-NFR-005 (Idempotency):** Handled inside `state/idempotency.py`.
*   **TRD-NFR-006 to TRD-NFR-007 (Redaction & Telemetry):** Handled inside `security/redaction_boundary.py`.
*   **TRD-NFR-008 to TRD-NFR-009 (Independence & Async):** Implemented in `execution/coordinator.py`.
*   **TRD-NFR-010 (Isolation):** Verified in `state/ports.py`.
*   **TRD-NFR-011 to TRD-NFR-012 (Branch & Replay determinism):** Enforced in unit tests configurations.
*   **TRD-NFR-013 to TRD-NFR-015 (Chaos & Parity):** Covered in integration testing profiles.
*   **TRD-NFR-016 to TRD-NFR-017 (Tiers Matrix):** Checked in package checklist validations.
*   **TRD-NFR-018 (Non-Goals):** Kept as static boundary checks.
*   **TRD-NFR-019 (Quorum Lease):** Implemented in `state/ports.py` concurrency and state store locks.
