# Trading Runtime Service

The trading runtime package is the broker-independent boundary for trading
requests, response envelopes, event contracts, public tool metadata, and
injected state/infrastructure ports.

## Boundary Role

This package owns platform-neutral trading contracts and persistence port
interfaces. It does not own broker SDK clients, concrete databases, secret
resolution, background schedulers, or live mutation policy storage. Concrete
implementations must be injected from infrastructure layers outside
`app/services/trading/`.

## Retired Live Package

The retired Live package has been folded into this package. Live execution
remains a runtime route and side-effect mode, but session coordination, gate
evaluation, broker dispatch, reconciliation authority, monitoring, and
emergency controls are all owned by `app/services/trading/`.

## Implemented Surface

- `actions/`: platform-independent shared trading action surface.
  - `actions/validation.py`: broker-independent local parameter validation —
    Decimal normalization to dynamic instrument precision, direction-aware
    stop-loss/take-profit geometry, margin sufficiency, market session
    evidence, time-in-force capability, execution protections (mandatory
    slippage and price collars), the immutable fat-finger notional ceiling,
    static defense-in-depth rails, and short-locate verification. Every
    validator accepts explicit evidence inputs rather than reading broker
    state directly, so it runs identically under `route="sim"` and
    `route="live"` (TRD-XM-001).
  - `actions/orders.py`: `buy`/`sell`/`buy_limit`/`sell_limit`/`buy_stop`/
    `sell_stop`/`order_modify`/`order_delete`/`submit_oco_group`. Every order
    action runs local validation first, then packages a request envelope
    through the shared `dispatch_or_package` seam.
  - `actions/positions.py`: `position_open`/`position_close`/
    `position_modify`/`reduce_exposure` position lifecycle controls,
    supporting Close-By-Ticket and Close-By-Symbol addressing under netting
    and hedging account modes. `reduce_exposure` packages a pre-approved risk
    decision only; it never computes sizing itself.
  - `actions/controls.py`: `pause_strategy`/`resume_strategy` (local,
    non-broker-mutating), `sync_positions` (read-only broker/local
    synchronization), `shutdown` (graceful session flush), and
    `trigger_global_kill_switch`/`trigger_strategy_kill_switch`/
    `trigger_symbol_kill_switch` (idempotent, audited, journaled activation).
  - `actions/emergency.py`: `cancel_all_orders`/`close_all_positions`/
    `flatten_account`/`flatten_strategy`/`flatten_symbol` — pre/post-action
    broker state snapshots, partial-completion tolerance, and per-child
    action detail.
  - `actions/_common.py`: the `TradingActionDependencies` bag (injected
    Clock/RNG/tenant/idempotency-store/event-journal/trade-store) and the
    `LiveGatePipeline` protocol — the seam `gates/live_pipeline.py` implements
    for `route="live"` gate evaluation. Until a pipeline is injected, every
    action fails closed to a `packaged_only` response (TRD-FR-055).
- `execution/`: broker-call coordination primitives.
  - `execution/state_machine.py`: the canonical order/position lifecycle
    transition table (illegal paths such as `Filled` → `Submitted` fail
    closed), version-gated amendment resolution (`evaluate_amendment`
    returns `accepted`/`too_late_to_cancel`/`too_late_to_modify`/
    `amended_after_partial_fill`, always `do_not_retry` on a stale version),
    and idempotent execution-report deduplication on `broker_event_id` within
    a bounded window (`apply_execution_report`). 100% branch-covered.
  - `execution/response_classifier.py`: normalizes provider-specific broker
    responses and streamed execution events into
    `NormalizedTradeResult` (`normalize_broker_response`/
    `classify_stream_event`), classifies unknown/timeout outcomes so callers
    force reconciliation and block retries (`classify_broker_outcome`),
    classifies broker-initiated (non-commanded) events — including
    `stop_out`/`margin_call_action`, which flag a required critical incident
    and a recommended `close_only` session transition — and classifies
    corporate-action notifications (splits, symbol/name changes). Reuses
    `app.utils.errors.classify_broker_error` rather than duplicating retcode
    maps.
  - `execution/rate_limiter.py`: deterministic per-provider token-bucket rate
    limiters (`TokenBucketRateLimiter`/`ProviderRateLimiterRegistry`) driven
    by an injected `Clock`, blocking exhausted requests locally before broker
    dispatch.
  - `execution/broker_capability_validation.py`: validates order type,
    filling mode, and price/volume precision against a declared
    `BrokerCapabilityProfile`, failing closed on any mismatch, and reports
    whether the adapter lacks native Cancel-on-Disconnect support
    (`requires_cancel_on_disconnect_failsafe`) — actually running the local
    heartbeat failsafe is the future responsibility of
    `runtime/session_manager.py`.
  - `execution/shadow.py`: records shadow-route intents and compares expected
    fills/balances against live evidence without ever dispatching a broker
    mutation.
  - `execution/coordinator.py`: broker-independent request-packaging helper
    consumed by `actions/_common.py`'s `dispatch_or_package` seam
    (`ExecutionCoordinator.build_broker_dispatch_payload`); resolves the
    route-based dispatch handler target (`resolve_dispatch_target`); runs
    asynchronous, non-blocking dispatch that returns a `TradingCommandAccepted`
    immediately and resolves a caller-supplied completion callback off an
    injected `AsyncDispatchExecutor` Future (`ExecutionCoordinator.dispatch_async`,
    backed by a thread-safe `InFlightRequestCounter`); generates and
    deterministically truncates globally unique `client_order_id`s for
    broker comment/external-ID/magic-number metadata fields
    (`generate_client_order_id`/`truncate_client_order_id`/
    `build_client_order_id_mapping`); plans multi-account
    `AllocationVector` dispatch as either a native block transaction or
    sliced per-account child payloads (`plan_allocation_dispatch`);
    evaluates two-step open-then-protect SL/TP outcomes, flagging a critical
    incident when an open succeeds without confirmed protection
    (`evaluate_two_step_protection_outcome`); resolves partial-fill residual
    handling actions (`apply_residual_policy`); models the non-atomic
    cancel-then-replace modify workflow as an explicit staged state machine
    that fails closed on out-of-sequence transitions and recommends
    re-entry or dead-letter escalation on replace failure
    (`begin_non_atomic_modify`/`record_cancel_dispatched`/
    `record_cancel_confirmed`/`record_replace_dispatched`/
    `resolve_replace_outcome`); resolves OCO/bracket execution mode and
    fails closed with `OCO_UNSUPPORTED` when neither native nor synthetic
    support is available (`resolve_oco_execution_mode`/
    `require_oco_submission_allowed`), and runs a client-side mutual-
    cancellation watchdog that resolves sibling cancellations exactly once
    per group on a fill or partial fill (`OcoWatchdog`); runs a synthetic
    `MultiLegExecutionCoordinator` watchdog that triggers rollback of every
    other registered leg once any leg rejects or breaches its fill
    tolerance; captures transaction cost facts and later adjustments
    (`capture_transaction_cost`); and finalizes post-response state by
    saving to `TradeStore`, releasing an optional concurrency-lease
    callback, and completing the idempotency lease
    (`finalize_dispatch_outcome`).
  - `execution/reporting.py`: constructs structured trading reports
    bundling positions, orders, execution latency breakdowns, cost entries,
    and reconciliation discrepancies (`build_trading_report`); and builds
    standardized, versioned execution-quality events — realized slippage
    against the mandatory `quote_snapshot`, direction-adjusted
    implementation shortfall, fill latency, partial-fill counts, and
    transaction cost facts — flagging `owner="external"` events so
    analytics excludes them from strategy performance attribution
    (`build_execution_quality_event`). Trading performs no metric
    aggregation of its own; analytics consumes this contract.
- `gates/`: deterministic `route="live"` pre-flight middleware. 100%
  branch-covered as a whole package.
  - `gates/policy_matrix.py`: `resolve_policy` looks up per-action
    permission/approval/emergency/side-effect rules from the injected
    `PolicyMatrix`, failing closed with `TRADING_POLICY_UNDEFINED` when an
    action has no configured entry.
  - `gates/approval.py`: verifies operator approval tokens (expiry, revoked/
    consumed status, account/strategy/symbol scope matching) and validates
    that a token's `canonical_request_hash` is bound to the exact order
    parameters it was issued for (`compute_canonical_request_hash`).
    `requires_dual_approval`/`validate_dual_operator_approval` enforce two
    distinct authenticated operators for clearing the global kill switch,
    promotion to `full_live`, and raising any hard cap, regardless of policy
    matrix configuration.
  - `gates/readiness.py`: validates broker connection/trading-allowance/
    permissions/rate-capacity evidence (`validate_broker_readiness`), local
    clock drift and PTP end-to-end latency against configured thresholds
    (`validate_clock_drift`), and exposes a non-mutating
    `run_live_readiness_dry_run`.
  - `gates/kill_switch.py`: `evaluate_kill_switches` blocks non-emergency
    mutations while any switch is active, exempting only policy-matrix
    approved emergency/protective actions — never a caller-supplied flag.
    `clear_kill_switch_after_approval` requires dual approval for the global
    switch. `restore_kill_switch_state`/`persist_kill_switch_state` durably
    round-trip switch state through the injected `TradingStateStore`.
  - `gates/audit_and_compensation.py`: `record_pre_mutation_audit` blocks the
    mutation immediately if the injected audit sink write fails.
  - `gates/pipeline.py`: owns `ComplianceGate` (restricted-symbol fail-closed
    block) and `MarketTurbulenceMonitor` (bounded per-symbol mid-price
    velocity circuit breaker that suspends a symbol and blocks further
    mutations once triggered), a thin wrapper exposing
    `execution/broker_capability_validation.py` as gate 15, and the generic
    `run_gate_pipeline` orchestrator: short-circuits on the first blocking
    gate (downstream steps are recorded as explicit `SKIPPED`/
    `diagnostic_after_failure` results, never executed), and fails closed
    with `DEADLINE_EXCEEDED`/`QUOTE_STALE` if the configured deadline or
    mandatory quote-snapshot TTL is exceeded mid-pipeline. `evaluate_seam_gate`
    remains available for any gate wired later; it fails closed with
    `LIVE_GATE_FAILED` until a real evaluator is injected, so the pipeline can
    never silently pass a gate it does not implement.
  - `gates/live_pipeline.py`: `LiveGatePipelineImpl`, the concrete
    `LiveGatePipeline` satisfying the `actions/_common.py` seam. It assembles
    all sixteen gates in `GateName` order, hands them to `run_gate_pipeline`,
    and performs the broker mutation at gate 16 under a five-second timeout.
    A timeout is classified as an unknown outcome and triggers a forced
    reconciliation pass rather than being reported as a failure. Also exports
    `passthrough_risk_evaluator` — see **Risk Gate** below.
- `execution/broker_dispatch.py`: **the only module in this package permitted
  to call a broker mutation entrypoint.** It imports the active-broker
  resolver, never a provider SDK. `grep -rl "brokers.router" app/services/trading`
  must return exactly this module and the read-only `info/` layer.
- `contracts.py`: route/action enums, promotion and mutation capability enums,
  TIF and FIX execution states, request/response envelopes, quote snapshots,
  allocation vectors, regulatory tags, normalized broker result wrappers,
  order/position state projections, journal event contracts, and tool metadata.
- `state/ports.py`: injected protocols for `TradeStore`, `TradingStateStore`,
  `AuditSink`, `IdempotencyStore`, `EventJournal`, `Clock`, `RNG`, and
  `EncryptionProvider`.
- `state/trade_store.py`: `InMemoryTradeStore` for tests and non-live routes,
  and `JsonlTradeStore` for durable projections that survive restart. Both
  enforce `expected_version` optimistic concurrency, deduplicate fills on
  `broker_event_id`, maintain Decimal VWAP and remaining-volume projections,
  and namespace every record by `(route, tenant_id)` so non-live routes never
  share storage with live.
- `state/idempotency.py`: canonical SHA-256 idempotency material hashing,
  durable JSONL leases, duplicate rejection, completed-envelope caching, and
  reconciliation-required expiry handling.
- `state/event_journal.py`: encrypted append-only event journal with hash-chain
  records, logical sequence IDs, reconciliation scans, snapshots, replay
  reconstruction, retention seal events, and detached signatures.
- `state/manager.py`: local state update coordinator that persists snapshots and
  journals state-update events through injected stores.
- `tool_registry.py`: pure registry construction for AI-facing trading action
  drafts. The registry exposes no broker mutation tool.
- `config/`: immutable route, timeout, rate-limit, secret-reference,
  notification, credential-rotation, and broker security profile contracts.
- `info/`: broker-neutral read-only facades for account, symbol, position,
  order, deal, historical order, and terminal metadata. Facades resolve the
  active broker through `get_broker_module()`, avoid broker mutation calls,
  return neutral values when data is unavailable, and redact exported payloads.
- `security/`: public trading exception mapping, recursive redaction
  boundaries, and write-ahead dead-letter queue helpers for failed critical
  broker or audit events.
- `reconciliation/`: state snapshot comparison, unknown-outcome authority guards, and startup sync coordination.
- `monitoring/`: dynamic operational metrics, heartbeats, timeouts, circuit breakers, tool health, and incident taxonomy.
- `promotion/`: mandatory linear promotion sequence/matrix checks, Gate 3 compatibility middleware, transition validations with operator approvals (single/dual operator), pre-activation conditions blocking, and simulation metadata lookup.
- `runtime/`: session runtime coordination services.
  - `runtime/session_manager.py`: coordinates explicit session states (`starting`, `running`, `paused`, `stopped`, `recovering`) and six operational modes. Enforces one active live session per scope, runs local heartbeats when Cancel-on-Disconnect is unsupported, handles ambiguous state loading by failing closed to `read_only` paused state, runs local GTD/DAY order expiry watchdog, maintains a thread-safe `HaltedSymbols` set, and blocks mutations to force reconciliation upon reconnection.
  - `runtime/coordination.py`: optimistic concurrency locks per `(account_id, symbol)` with queues and timeouts to prevent unbounded queueing, enforces strategy ownership constraints, and evaluates cross-strategy counter policies.
  - `runtime/cost_control.py`: evaluates and tracks pre-dispatch budget ceilings per request, workflow, strategy, account, and session, and records actual costs post-dispatch (raising critical incident signals on breach).
  - `runtime/signal_processor.py`: transforms approved strategy signals into canonical request envelopes, validating all stage, capability, and risk reference evidence before execution through the gate pipeline.
- `__init__.py`: explicit public import gate with pure registry accessors.

## Inputs

Trading request contracts accept JSON-safe action payloads, route metadata,
promotion stage, mutation capability, optional allocation vectors, optional
regulatory tags, optional OCO/bracket linkage, and quote snapshots. Live
mutation requests require quote snapshots that match the requested symbol.

## Dependencies

The package depends on:

- `pydantic` for contract validation.
- `decimal.Decimal` for broker-critical numeric values.
- `app.utils.logger.logger` for operational logging.

The package must not import provider SDKs such as `MetaTrader5`, cTrader,
Binance, or broker-specific mutation clients. Read-only broker metadata access
is isolated to `info/` and must pass through the active broker resolver.

## Determinism

Trading runtime code must use injected `Clock` and `RNG` ports for all time and
nondeterministic behavior. Direct calls to wall-clock or random APIs are
excluded from this package.

## Configuration And Security

Runtime configuration stores only secret references, never raw secret values.
Live mutation is disabled by default and resolves to `packaged_only` behavior
until policy enables mutation. Configuration reloads are validated through the
loader, versioned with a redacted hash, and immutable live-session keys are
blocked while a session is running.

Security boundaries map raw SDK, network, validation, permission, and
persistence exceptions into standard public error codes with request and
correlation IDs. Exported logs, alerts, events, reports, and chat payloads pass
through recursive redaction. Failed critical broker or audit payloads are
written to a redacted JSONL dead-letter log before recovery, and retry
thresholds relocate poison-pill events to manual review.

## Persistence

Idempotency records are derived from canonical JSON command material and stored
as durable leases. Active duplicates are rejected, completed duplicates return
their cached envelopes, and expired live leases transition to reconciliation
instead of retrying automatically.

Journal records are append-only encrypted JSONL entries with logical sequence
IDs and hash-chain records. Snapshots and replay helpers rebuild projections for
recovery or forensic reconstruction, while segment seals and detached
signatures support tamper-evidence checks.

## Execution Lifecycle

Every live mutation (`buy`, `sell`, `position_close`, `order_delete`, …) packages
a request envelope and hands it to the injected `LiveGatePipeline`. Without a
pipeline the action fails closed to `packaged_only` and nothing reaches a broker.
With `LiveGatePipelineImpl` injected, the envelope runs the canonical sixteen
gates in order:

```
[Packaged Request]  (actions/*.py -> dispatch_or_package)
        │
        ▼
 1  local_schema_validation     payload present; symbol required for order submission
 2  compliance                  restricted-symbol list
 3  promotion_stage             route / stage / capability compatibility
 4  session_status              session RUNNING, mode admits mutation, symbol not halted
 5  kill_switch                 policy decides emergency bypass, not the caller
 6  operator_approval           token bound to the canonical request hash
 7  risk_decision               see "Risk Gate" below
 8  market_turbulence           mid-price velocity against the configured threshold
 9  broker_readiness            connection, trade permission, rate-limit capacity
10  clock_drift                 local offset and optional PTP latency
11  idempotency                 durable lease reserved before any mutation
12  concurrency_lease           per (account_id, symbol) lock; released in a finally
13  reconciliation_authority    unresolved stream-gap locks block the scope
14  audit_pre_record            audit write failure blocks the mutation
15  adapter_permission          broker capability profile for type/filling/precision
        │
        ▼
16  dispatch                    execution/broker_dispatch.py, 5.0s timeout
   ┌────┴────────────────┐
   ▼ (Timeout)            ▼ (Broker responded)
[Unknown Outcome]        [Normalize Response]  (execution/response_classifier.py)
   │                      │
[Forced Reconciliation]  [finalize_dispatch_outcome]  (TradeStore + idempotency)
   │                      │
   └──────────┬───────────┘
              ▼
   [Release Concurrency Lease]
```

`run_gate_pipeline` short-circuits on the first blocking gate; every downstream
step is recorded as `SKIPPED` / `diagnostic_after_failure` and never executed.

## Resilience And Operational Safety

### Concurrency leases
Requests serialize per `(account_id, symbol)` through `ConcurrencyLockManager`.
Actions without a symbol — a ticket-addressed close, an account-wide flatten —
resolve to a single `GLOBAL` lease rather than locking on an empty key. The lease
is released in a `finally`, so a gate that blocks downstream of gate 12 cannot
strand it.

### Kill switch
Kill-switch state is evaluated at gate 5. Whether an emergency or protective
action may proceed under an active switch is decided solely by the policy matrix
entry (`emergency_allowed_under_kill_switch`), never by a caller-supplied
override flag. Emergency actions still traverse every other gate; the kill switch
is not a bypass.

### Graceful shutdown
`actions/controls.py::shutdown` stops admitting requests, drains in-flight work
through the injected `drain` callback (bind it to
`ExecutionCoordinator.in_flight.wait_drained`), flushes state, and runs the
injected `reconcile` callback. Every field of `ShutdownResult` reports what
actually happened: `reconciliation_triggered` is True only when a reconcile
callback was supplied *and* completed without raising.

### Broker synchronous timeouts
The broker call runs on an injected executor with a **5.0-second** timeout. On
timeout the system cannot know whether the order reached the matching engine, so
the outcome is classified `UNKNOWN_OUTCOME` with
`retry_safety=RETRY_AFTER_RECONCILIATION`, and a forced reconciliation pass runs
immediately. A timeout is never reported as a failure.

### Unknown outcomes versus rejections
A broker that responds with a non-success retcode is a **rejection**
(`BROKER_MUTATION_REJECTED`, safe to retry). A broker that does not respond is an
**unknown outcome** (`UNKNOWN_OUTCOME`, reconcile before retrying). The success
retcode set is `{10009, 10008, 0}`.

## Risk Gate

Gate 7 (`RISK_DECISION`) currently ships with `passthrough_risk_evaluator`, which
passes unconditionally and logs a warning containing the literal string
`RISK_DECISION passthrough` on every live evaluation.

This preserves exact behavioral parity with the retired `app/services/trader`
package, which performed no pre-trade risk checks. **It is not a new gap; it is
the existing gap, made visible.** `LiveGatePipelineImpl` takes `risk_evaluator`
with no default, so every call site must name its choice explicitly.

Wire `app/services/risk` into this gate before scaling live position size.

## Usage

```python
from decimal import Decimal

from app.services.trading.actions import TradingActionDependencies, buy
from app.services.trading.contracts import (
    MutationCapability, PromotionStage, TradingRoute,
)
from app.services.trading.gates.live_pipeline import (
    LiveGateEvidence, LiveGatePipelineImpl, passthrough_risk_evaluator,
)

pipeline = LiveGatePipelineImpl(
    clock=clock,
    tenant_id="tenant-1",
    evidence=LiveGateEvidence(...),
    policy_matrix=policy_matrix,
    session_manager=session_manager,
    turbulence_monitor=turbulence_monitor,
    idempotency_store=idempotency_store,
    lock_manager=lock_manager,
    authority_guard=authority_guard,
    audit_sink=audit_sink,
    trade_store=trade_store,
    dispatch_executor=executor,
    dispatch_callable_factory=broker_dispatch_factory,
    risk_evaluator=passthrough_risk_evaluator,  # see "Risk Gate"
)

deps = TradingActionDependencies(
    clock=clock, rng=rng, tenant_id="tenant-1", gate_pipeline=pipeline,
)

response = buy(
    symbol="EURUSD",
    volume=Decimal("0.10"),
    deviation_points=20,
    route=TradingRoute.LIVE,
    promotion_stage=PromotionStage.MICRO_LIVE,
    mutation_capability=MutationCapability.MICRO_LIVE,
    request_id="req-1",
    correlation_id="corr-1",
    context=order_validation_context,
    deps=deps,
    quote_snapshot=quote,
)

print(response.status.value, response.side_effect_mode.value)
print(response.data["result"]["deal"])
```

Omit `gate_pipeline` and the same call returns `packaged_only` without touching a
broker. That is the intended default.

A full runnable example, including an emergency flatten and a graceful shutdown,
lives in `tests/usage/07_trading.py`.

## MQL5 Emulation Wrappers

To ease porting MetaTrader strategies, `info/` exposes read-only facades matching
the standard MQL5 interface. They resolve the active broker through
`get_broker_module()` and never mutate.

- **`AccountInfo`** — login, balance, equity, margin, free margin, margin level,
  leverage, trading permissions.
- **`SymbolInfo`** — ask, bid, point size, digits, lot bounds, volume step, stop
  levels, margin and profit calculations.
- **`TerminalInfo`** — broker connection status, terminal build, path settings.
- **`PositionInfo`** — active open positions (ticket, volume, price, type, profit,
  sl, tp, comment).
- **`OrderInfo`** — active pending orders awaiting execution.
- **`HistoryOrderInfo`** — historical pending orders, filled or cancelled.
- **`DealInfo`** — execution transactions corresponding to position transitions.
