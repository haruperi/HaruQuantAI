# Trading Domain — Capability Feature Extraction (from `07_trading.md`)

Source: `docs/dev/phase-implementation-plan/07_trading.md` (Trading Runtime ARD). Module paths follow the plan's target tree under `app.services.trading`. Signatures are taken from, or inferred from, the requirement statements and evidence anchors.

---

## FEAT-TRD-01: Package Facade, Contracts, and Tool Registry (app.services.trading / .contracts / .tool_registry)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `get_trading_tool_registry() -> TradingToolRegistry` | Pure accessor for the registry of callable trading tools (with `get_trading_public_catalog()`). | Missing |
| `TradingRequestEnvelope(...)` | Canonical request contract: route, action, promotion stage, mutation capability, mandatory live `quote_snapshot`, optional `AllocationVector`, `RegulatoryTags`, OCO/bracket linkage, `deadline_utc`, and `schema_version`. | Missing |
| `NormalizedTradeResult(...)` | Single broker-facing normalized result type (retcode, deal, order, volume, price, provider); never exposed raw in public envelopes. | Missing |
| `TradingCommandAccepted` / `BrokerDispatchEvent` / `ExecutionReportEvent` / `ReconciliationResolutionEvent` | Distinct event contracts separating trading commands from execution report updates; async live acceptance is local, not broker confirmation. | Missing |
| Route/action/side-effect/TIF/FIX-state enums | Type-safe enums for routes (`sim`/`paper`/`shadow`/`live`), actions, side-effect modes, retry safety, TIF (`GTC`/`IOC`/`FOK`/`GTD`/`DAY`), and granular FIX execution states. | Missing |

## FEAT-TRD-02: Order Actions (app.services.trading.actions.orders)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `buy(symbol, volume, sl, tp, deviation, magic, comment, ...) -> TradingResponseEnvelope` | Formulate market buy intents with exact parameter parity (with `sell(...)`). | Missing |
| `buy_limit(...)` / `sell_limit(...)` / `buy_stop(...)` / `sell_stop(...)` | Formulate pending order intents including price, expiration, and stop-limit requirements. | Missing |
| `order_modify(ticket, price, sl, tp) -> TradingResponseEnvelope` | Pending-order mutation preserving identity, idempotency keys, and side-effect classification. | Missing |
| `order_delete(ticket) -> TradingResponseEnvelope` | Pending-order cancellation. | Missing |
| OCO/bracket group submission | Submit OCO groups and bracket orders with group-consistency validation before dispatch; all order actions route through the canonical 16-step gate pipeline and fail closed to `packaged_only` until the live pipeline is injected. | Missing |

## FEAT-TRD-03: Position Actions (app.services.trading.actions.positions)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `position_open(...)` / `position_close(...)` / `position_modify(...)` | Position lifecycle controls: Close-By-Symbol, Close-By-Ticket, netting vs. hedging constraints, SL/TP mutation. | Missing |
| `reduce_exposure(scope, target, route, deps) -> TradingResponseEnvelope` | Package partial-close/volume-reduction commands across an approved scope from a validated risk decision; never generates thresholds independently. | Implemented |

## FEAT-TRD-04: Operational Controls and Kill-Switch Triggers (app.services.trading.actions.controls)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `pause_strategy(...)` / `resume_strategy(...)` | Non-broker-mutating operational controls adjusting local state and monitoring projections only. | Implemented |
| `sync_positions(route) -> TradingResponseEnvelope` | Retrieve broker state and synchronize local databases without new orders or mutations. | Implemented |
| `shutdown(timeout) -> TradingResponseEnvelope` | Stop admitting requests, drain in-flight work, flush state/audit, trigger final reconciliation. | Missing |
| `trigger_global_kill_switch(reason, route, deps)` | Activate the global kill switch: persist reason, emit critical event, block non-emergency live mutations (with strategy- and symbol-scoped counterparts; all idempotent, audited, journaled, policy-routed). | Missing |

## FEAT-TRD-05: Emergency Actions (app.services.trading.actions.emergency)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `cancel_all_orders(scope, route, deps)` | Mass cancellation with pre/post broker snapshots and per-child results. | Implemented |
| `close_all_positions(scope, route, deps)` | Mass close with partial-completion tolerance and unknown-outcome reconciliation locks. | Implemented |
| `flatten_account(scope, route, deps)` / `flatten_strategy(strategy_id, route, deps)` / `flatten_symbol(symbol, route, deps)` | First-class scoped flatten actions consuming emergency fail-safe rules from the policy matrix. | Missing |

## FEAT-TRD-06: Order Request Validation and Un-Overrideable Rails (app.services.trading.actions.validation)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_order_request(...) -> ValidationOutcome` | Combined parameter validation; failures return structured `VALIDATION_FAILED`/`INVALID_INPUT` and short-circuit execution. | Implemented |
| `validate_volume(...)` | Min/max/step volume checks against dynamically resolved broker symbol metadata, with round-down Decimal normalization at instrument precision. | Missing |
| `validate_stops(...)` | Direction-aware minimum-distance and stop-level geometry rules for SL/TP. | Missing |
| `validate_margin(...)` | Free-margin sufficiency check before broker dispatch. | Missing |
| `validate_market_session(...)` | Session availability from data-module calendar evidence; fails closed on missing/expired evidence in live-sensitive routes. | Missing |
| `validate_short_locate(...)` | Short-sale locate/HTB verification from a `LocateSnapshot`; fails closed without valid locate. | Missing |
| Fat-finger cap and defense-in-depth rails | Immutable account-currency notional ceiling plus local rails (mutation attempts per window, max open positions, daily notional ceiling), evaluated without external risk signatures; raising rails requires dual-control approval. | Missing |

## FEAT-TRD-07: Read-Only Info Facades (app.services.trading.info)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `AccountInfo` / `SymbolInfo` / `PositionInfo` / `OrderInfo` / `DealInfo` / `HistoryOrderInfo` / `TerminalInfo` wrappers | MQL5-compatible read-only wrappers resolving the active broker via `get_broker_module()`; no mutations, safe defaults on disconnect, redaction-filtered payloads. | Missing |

## FEAT-TRD-08: Trading Configuration, Secrets, and Security Profile (app.services.trading.config)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| Config models (`models.py`) | Route enablement, `ALLOW_LIVE_MUTATIONS` (default false → `packaged_only`), broker selection, rate limits, cost budgets, timeouts, capability-evidence TTLs, secret references. | Missing |
| Config loader (`loader.py`) | Fail-closed startup validation, versioned effective config with journaled change events, and live-session immutability for safety-critical keys. | Missing |
| Secrets resolution (`secrets.py`) | Reference-based credential retrieval; rotation failures transition the session to `read_only` without crashing or silently retrying. | Missing |
| Notification construction (`notifications.py`) | Strictly redacted operational notifications to configured approved channels only. | Missing |
| Security profile (`security_profile.py`) | Live mutation requires a verified broker-communication security profile (transport encryption, certificate rules, logging restrictions). | Missing |

## FEAT-TRD-09: Session, Concurrency, Cost, and Signal Runtime (app.services.trading.runtime)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| Session manager (`session_manager.py`) | Session states (starting/running/paused/stopped/recovering) and six operational modes; single live session per scope; fail-closed recovery to paused/`read_only`; Cancel-on-Disconnect heartbeat failsafe; GTD/DAY expiry watchdog; policy-gated synthetic stop/OCO emulation; `HaltedSymbols` set; reconnect auto-resync with forced reconciliation. | Missing |
| Concurrency coordination (`coordination.py`) | Optimistic locks keyed `(account_id, symbol)`, lock timeouts, backpressure rejection, strategy ownership enforcement, and cross-strategy netting-conflict detection with policy-driven `block`/`warn_and_allow`/`allow`. | Missing |
| Cost control (`cost_control.py`) | Cost budgets per request/workflow/strategy/account/session; pre-dispatch violations block, post-dispatch violations raise critical incidents. | Missing |
| Signal processor (`signal_processor.py`) | Transform approved strategy signals into `TradingRequestEnvelope` intents after verifying route, promotion stage, capability, risk reference, and approval evidence; never bypasses the gate pipeline. | Missing |

## FEAT-TRD-10: Canonical Live Gate Pipeline (app.services.trading.gates)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_gate_pipeline(...)` | 16-step short-circuiting fail-closed pipeline (schema validation → compliance → promotion → session → kill switch → approvals → risk signature → turbulence → readiness → clock drift → idempotency → lease → reconciliation authority → audit pre-record → adapter permission → async dispatch) with per-gate latency budgets and `DEADLINE_EXCEEDED`/`QUOTE_STALE` enforcement. | Missing |
| `ComplianceGate` | Early restricted-symbol-list blocking. | Missing |
| `MarketTurbulenceGate` | Rolling mid-price velocity circuit breaker halting mutations and suspending symbols per policy. | Missing |
| Policy matrix lookup (`policy_matrix.py`) | Permission/approval/emergency/side-effect rules; missing actions fail closed with `TRADING_POLICY_UNDEFINED`. | Missing |
| Approval verification (`approval.py`) | Operator approval ID/expiry/revocation/scope checks, `canonical_request_hash` request binding, and dual-operator control for kill-switch clearance, `full_live` promotion, and hard-cap raises. | Missing |
| Readiness checks (`readiness.py`) | Broker connection/permission/rate-limit readiness, clock drift gating (50 ms threshold, PTP wire-timestamp latency), and non-mutating `run_live_readiness_dry_run()`. | Missing |
| Kill-switch gate (`kill_switch.py`) | Active switches block non-emergency mutations; `clear_kill_switch_after_approval` requires governance evidence; state durably persisted and restored before first gate evaluation after restart. | Missing |
| Audit pre-recording (`audit_and_compensation.py`) | Pre-mutation audit write must succeed before broker dispatch; write failure blocks the mutation. | Missing |

## FEAT-TRD-11: Async Execution Coordinator and Order Lifecycle (app.services.trading.execution)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `ExecutionCoordinator.dispatch_async(...)` | Route-based async dispatch (sim/paper/shadow/live) with Futures callbacks, in-flight counters, and finalization (TradeStore updates, lease/idempotency completion). | Missing |
| `generate_client_order_id(...)` / `truncate_client_order_id(...)` | Globally unique client order IDs propagated to broker metadata with deterministic truncation mapping. | Missing |
| `plan_allocation_dispatch(...)` | Multi-account `AllocationVector` slicing or native block-trade delegation. | Missing |
| Two-step protection and non-atomic modify handling | Atomic open-then-protect SL/TP workflows and reserve→cancel→replace modify staging with critical incident/dead-letter escalation on replace failure. | Missing |
| OCO/multi-leg coordination | `OcoWatchdog` sibling cancellation, native/synthetic/fail-closed OCO mode resolution, and `MultiLegExecutionCoordinator` with atomic rollback on leg failure. | Missing |
| `apply_residual_policy(...)` | Partial-fill residual handling: leave/cancel/replace/retry-after-delay/escalate. | Missing |
| Broker capability validation (`broker_capability_validation.py`) | Fail-closed adapter capability checks (order types, filling modes, precision, rate limits, CoD support). | Missing |
| Response classifier (`response_classifier.py`) | Normalize provider responses; unknown outcomes force reconciliation and block retries; classify broker-initiated events (`server_side_sl_tp_fill`, `stop_out`, `margin_call_action`, `broker_admin_action`, `expiration`) and `CorporateActionEvent`s. | Missing |
| Rate limiter (`rate_limiter.py`) | Token-bucket per-provider limits with local pre-dispatch blocking. | Missing |
| State machine (`state_machine.py`) | Enforced FIX-state transition table, version-gated amendments (`TOO_LATE_TO_CANCEL`/`TOO_LATE_TO_MODIFY`), authoritative execution-report application, and `broker_event_id` deduplication. | Missing |
| Reporting (`reporting.py`) | Structured trading reports plus versioned `ExecutionQualityEvent`s (realized slippage bps, implementation shortfall, fill latency, cost facts). | Missing |
| Shadow execution (`shadow.py`) | Record intents and compare expected fills against live quotes without broker dispatch. | Missing |

## FEAT-TRD-12: State Ports, Idempotency, and Event Journal (app.services.trading.state)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `TradingStateStore` / `AuditSink` / `IdempotencyStore` / `TradeStore` / `EventJournal` protocols | Abstract persistence ports with strict sim/paper/shadow tenant isolation; VWAP and remaining-volume tracking; corporate-action position adjustment. | Implemented |
| `Clock` / `RNG` protocols | Injected time (`now_utc`, `monotonic`, `now_ptp`) and seeded randomness; direct clock/random calls prohibited package-wide for deterministic replay. | Missing |
| Idempotency (`idempotency.py`) | SHA-256 canonical-JSON keys; restart-surviving records; TTL leases expiring to reconciliation-required; in-progress duplicates rejected, completed duplicates return cached envelopes. | Missing |
| Event journal (`event_journal.py`) | Append-only hash-chained journal with sequence IDs, snapshots + replay rebuild, startup in-flight command scan with scope locks, compaction preserving hash chains, scheduled integrity verification, at-rest encryption with detached signatures, and WORM compliance. | Missing |
| `replay_builder(...)` | Re-materialize exact TradeStore projections (portfolio, balance, positions, P&L, exposure) at any historical timestamp from snapshot + journal replay. | Missing |

## FEAT-TRD-13: Broker Reconciliation (app.services.trading.reconciliation)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| Reconciliation service (`service.py`) | Startup/pre-trade/periodic/post-unknown/shutdown runs comparing local state to broker truth (positions, orders, balance, margin); mismatches block live mutation until resolved; orphan/external deals adopt-quarantined or blocked per policy. | Missing |
| Snapshot comparison (`snapshots_and_compare.py`) | Config-driven absolute price/volume drift thresholds and mismatch severity computation. | Missing |
| Authority and retry guard (`authority_and_retry_guard.py`) | Unknown outcomes transition authority to `UNRESOLVED`, blocking scoped mutations; stream gaps halt live mutation while duplicate events are idempotently dropped. | Missing |

## FEAT-TRD-14: Operational Monitoring and Circuit Breakers (app.services.trading.monitoring)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| Monitoring service (`service.py`) | Aggregate status events; automatic circuit breakers on consecutive rejects, unknown outcomes, drift, p95 latency, stream gaps, and durability failures; dynamic latency-based capability downgrade (`full_live` → `micro_live`/`read_only`). | Missing |
| Tool health (`tool_health.py`) | Dynamic health degradation after consecutive timeouts/adapter failures. | Missing |
| Timeouts and staleness (`timeouts_and_staleness.py`) | Bounded-sample latency tracking and lost-order life-to-live watchdog raising `STALE_ORDER` incidents with forced reconciliation. | Missing |
| Operational signals (`operational_signals.py`) | Severity-tiered signals with dedup, rate limiting, escalation chains, and mandatory runbook references validated at startup. | Missing |
| Heartbeat watchdog (`heartbeat_watchdog.py`) | Dead-man's-switch liveness heartbeat to an external watchdog endpoint. | Missing |

## FEAT-TRD-15: Error Mapping, Redaction, and Dead-Letter Recovery (app.services.trading.security)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| Error mapping (`error_mapping.py`) | `TradingError` hierarchy mapping raw SDK/network errors to standard codes with request/correlation IDs; no raw traces or secrets in public errors. | Missing |
| Redaction boundary (`redaction_boundary.py`) | Recursive, case-insensitive, denylist-first redaction of all exported data. | Missing |
| Dead-letter queue | Durable exactly-once DLQ with write-ahead log, restart replay before mutation enablement, and poison-pill isolation to `ManualReviewDLQ` after N failed retries. | Missing |

## FEAT-TRD-16: Promotion Ladder and Preconditions (app.services.trading.promotion)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| Promotion ladder (`ladder.py`) | Mandatory stage ladder mapped to routes/capabilities; no step-skipping; explicit operator approval; strategies cannot self-promote. | Missing |
| Preconditions (`preconditions.py`) | Live activation hard-blocked on active kill switches, unresolved reconciliation, stale context, or missing security profiles; `sim` broker metadata reads restricted to reproducibility-safe modes. | Missing |

---

**Note:** the trading package is platform-independent (no provider SDK imports; all broker calls via the injected broker router), default-deny for live mutation (`packaged_only` unless explicitly enabled), and imposes no strategy, risk-model, or market-data logic of its own. Cross-module contracts (TRD-XM) bind the simulator (validation parity, paper fill engine), data (session calendars, halts, corporate actions, locates), analytics (execution-quality events), and risk (exposure-delta pre-check, `RiskBreachEvent` forced flatten).
