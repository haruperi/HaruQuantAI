# Trading Execution Pipeline — Full Flow (live, paper, and sim)

Package: `app/services/trading`
Core entry points: `submit_order` / `modify_order` / `cancel_order` / `close_position` / `modify_position` / `reduce_exposure`, plus `run_live_evaluation_cycle`
Shared engine: `_execute_request` in `app/services/trading/actions/orders.py`

---

## 0. The one thing to understand first

**Every mutation — `sim`, `paper`, or `live` — funnels through a single function: `_execute_request`.**
The routes differ in *which gate stack runs* and *which authority receives the intent*, not in the shape of the pipeline.

```
                       ┌─────────────────────────────────────────┐
   public verb  ─────▶ │            _execute_request             │
 (submit_order, ...)   │  actions/orders.py                      │
                       └───────────────┬─────────────────────────┘
                                       │
              ┌────────────────────────┴────────────────────────┐
              │  1. account state + symbol capability read      │
              │  2. validate_order_request  (common)            │
              │  3. _require_clear_authority_scope (common)     │
              └────────────────────────┬────────────────────────┘
                                       │
                    route == paper/live│route == sim
              ┌────────────────────────┴────────────────────────┐
              │                                                 │
   ┌──────────▼──────────────┐               ┌──────────────────▼──────────────┐
   │ evaluate_live_gate      │               │ inline sim gate stack           │
   │ live/gates.py           │               │ (in _execute_request)           │
   │  · session started      │               │  · validate_action_policy       │
   │  · admission_enabled    │               │  · validate_risk_authority      │
   │  · 5 authority reads    │               │  · validate_kill_switch_...     │
   │  · action policy        │               │  · reserve idempotency          │
   │  · risk authority       │               │  · build_execution_plan         │
   │  · kill-switch hierarchy│               │                                 │
   │  · readiness assessment │               │  NO live session                │
   │  · reserve idempotency  │               │  NO pre-audit                   │
   │  · reconciliation_ready │               │  NO adapter capability check    │
   │  · pre-mutation audit   │               │  NO reconciliation gate         │
   │  · build_execution_plan │               │                                 │
   │  · adapter capability   │               │                                 │
   └──────────┬──────────────┘               └──────────────────┬──────────────┘
              └────────────────────────┬────────────────────────┘
                                       │  OrderIntent v1
              ┌────────────────────────▼────────────────────────┐
              │  4. _record_send_attempt   (BEFORE the boundary)│
              │  5. _dispatch_order_intent_value                │
              │  6. _record_receipt                             │
              │  7. _complete_reservation                       │
              │  8. _resolve_unknown  (if reconciliation needed)│
              │  9. _envelope                                   │
              └─────────────────────────────────────────────────┘
```

---

## 1. Layer map

```
HTTP   POST /api/v1/trading/orders          app/services/api/workstation/trading/routes.py
       DELETE /api/v1/trading/orders/{id}
       POST /api/v1/trading/positions/{id}/close
       GET  /api/v1/trading/session
  │    auth → require_human_permission → _governed_preflight → Idempotency-Key
  ▼
API orchestration  build_trading_mutation_source(deps, runtime_policy)
                   app/services/api/workstation/trading/orchestration.py
  │    create_trading_request(**payload) → TradingRequest
  ▼
Public verb        submit_order / cancel_order / close_position ...
                   app/services/trading/actions/{orders,positions,controls,emergency}.py
  │
  ▼
_execute_request   app/services/trading/actions/orders.py
  │
  ├── validation/    validate_order_request, build_execution_plan, assess_execution_readiness,
  │                  validate_action_policy / validate_risk_authority / validate_kill_switch_hierarchy
  ├── live/          LiveSession, evaluate_live_gate, _LiveRuntimeConfig
  ├── state/         reserve_idempotency, apply_execution_event, TradingProjection
  ├── routing/       dispatch_order_intent, validate_adapter_capability, classify_authority_response
  ├── reconciliation/ resolve_unknown_outcome, compare_authority_state
  ├── monitoring/    OperationalEvent, BROKER_STATE_UNKNOWN, emit_runtime_event
  └── contracts/     TradingRequest, OrderIntent v1, ExecutionReceipt v1, TradeRecord v1
```

---

## 2. Composition — `TradingDependencies`

`create_trading_dependencies(**ports)` → frozen `TradingDependencies` (`actions/dependencies.py`). `__post_init__` fails closed on any absent port or invalid bound.

### Authority / execution ports

| Port | Purpose |
|---|---|
| `store` | `TradingStateStore` — events, projections, idempotency rows |
| `connection` | Brokers `BrokerConnectionConfig` (paper/live only) — **`None` for sim** |
| `broker_adapter` | Brokers async adapter (paper/live only) — **`None` for sim** |
| `simulation_dispatch` | `Callable[[OrderIntent], Awaitable[...]]` (sim only) — **`None` for paper/live** |
| `live_session` | `LiveSession` — required for paper/live, unused by sim |
| `clock` | Aware UTC clock |
| `event_sink` | `OperationalEvent` publication boundary |
| `execution_positions` | Process-local execution-position store (memory-only, never persisted) |

### Read ports

`account_state_source`, `symbol_capability_source`, `action_policy_source`, `kill_switch_state_source`, `execution_risk_decision_source`, `child_risk_decision_source`, `reconciliation_source`, `allocation_decision_source`, `budget_verdict_source`, `eligibility_source`, `rebalance_action_resolver`, `kill_switch_transition`, plus the evaluation-cycle ports `market_data_source`, `evaluation_account_source`, `market_context_source`, `indicator_source`, `strategy_source`, `risk_source`.

### Runtime bounds (all validated positive, fail closed)

- `idempotency_retention_seconds` — positive `int`
- `concurrency_lock_timeout_seconds` — positive `Decimal`
- `broker_operation_timeout_seconds` — positive `Decimal` (default `BROKER_OPERATION_TIMEOUT_SECONDS = 10`)
- `max_staleness_seconds` — must be **exactly** `{route_snapshot, risk_decision, kill_switch}`, each a positive finite `Decimal`

**Mutual exclusion is enforced at dispatch, not at construction**: supplying both a broker adapter and a simulation dispatch for the same intent raises `SCOPE_MISMATCH`.

---

## 3. The request contract

`TradingRequest` (`contracts/models.py`) — `contract_version="v1"`, `schema_id="trading.trading_request.v1"`, frozen.

Key fields: trace IDs (`request_id`, `workflow_id`, `correlation_id`, `causation_id`), `route` (`sim`/`paper`/`live`), `action`, `provider_id`, `account_id`, `portfolio_id`, `strategy_id`/`strategy_version`, `intent_id`, `symbol`, `side`, `order_type`, `quantity_unit`, `quantity` (**Risk-approved size**), `price`/`stop_price`/`stop_loss`/`take_profit`, `time_in_force`/`expiration`, `target_broker_order_id`/`target_broker_position_id`, `expected_version`, `risk_decision_id`, `action_policy_verdict_id`, `approval_token_ref`, `eligibility_decision_id`, `idempotency_key`, `canonical_material_version`, `system_time`, `valid_until`, and instrument metadata (`instrument_min_quantity`, `instrument_max_quantity`, `instrument_quantity_step`, `instrument_price_tick`).

---

## 4. Stage 1 — Common validation (all routes)

### 4a. Evidence reads

```python
account_state = deps.account_state_source(request)
capability, symbol_info = deps.symbol_capability_source(route, provider_id, symbol)
```

A missing `request.symbol` → `INVALID_REQUEST`.

### 4b. `validate_order_request(request, account_state, capability)` — `validation/orders.py`

Fail-closed, in order:

1. `request.account_id == account_state.account_id` → else `SCOPE_MISMATCH`
2. `account_state.connected` and `trading_allowed` → else `SERVICE_UNAVAILABLE`
3. `account_state.expires_at > request.system_time` → else `STALE_EVIDENCE`
4. `submit_order` requires `account_state.margin_available is not None` → else `VALIDATION_FAILED`
5. **Symbol capability** — `supported_order_types` must be a list of strings containing `request.order_type`; `quantity_unit` must match exactly
6. **Instrument evidence** — a quantity requires min/max/step; any price field requires `instrument_price_tick`
7. **Quantity** — within `[min, max]`, and `(quantity − min) % step == 0` (28-digit `localcontext`, `ROUND_HALF_EVEN`)
8. **Price geometry** — every supplied price aligned to tick; then:
   - `stop_loss`/`take_profit` without a reference `price` → `VALIDATION_FAILED`
   - BUY: `stop_loss < price` and `take_profit > price`
   - SELL: `stop_loss > price` and `take_profit < price`
9. **Operation preconditions**
   - `modify_order`/`cancel_order` require `target_broker_order_id`; position actions require `target_broker_position_id`
   - `submit_order` requires `side` and `quantity`
   - order mutations must match a current order in `account_state.orders` with the same symbol, and require `expected_version`
   - position actions must match a current position in `account_state.positions` with the same symbol
   - `close_position`/`reduce_exposure` require `quantity`

### 4c. `_require_clear_authority_scope`

Loads the projection for scope `(route, account_id, authority_id)` where `authority_id = provider_id or "simulation"`. If `projection.unresolved_attempt_ids` is non-empty → **`RECONCILIATION_REQUIRED`**.

> This is the retry lock. One unresolved prior attempt freezes every subsequent mutation in that authority scope.

### 4d. Verb-specific pre-checks (before `_execute_request`)

| Verb | Extra check |
|---|---|
| `modify_order` | requires `expected_version` + target; `_require_order_target_state` proves the target exists in the projection and `expected_version == projection.version` (else `VERSION_CONFLICT`) |
| `cancel_order` | requires target; same `_require_order_target_state` |
| `close_position` | `_current_position_quantity` (execution-position store must know it and not be `UNKNOWN`); `quantity <= current` |
| `modify_position` | position must exist; action-policy `scope["mutable_fields"]` must be a superset of the supplied `{stop_loss, take_profit}` — else `SCOPE_MISMATCH` |
| `reduce_exposure` | `0 < quantity <= current` — a reduction can never increase exposure |

---

## 5. Stage 2A — The **live / paper** gate stack

`evaluate_live_gate(request, evidence, session)` — `live/gates.py`. Fail-fast, strict order.

1. **Schema** — `contract_version == "v1"` and `schema_id == "trading.trading_request.v1"` → else `INVALID_REQUEST`
2. **Session validity** — `session.started` and `request.valid_until > session.now()` → else `GATE_BLOCKED`
3. **Admission** — if `not session.admission_enabled`, return `dispatch_allowed: False, gate: "enablement"` and stop. *Package-only mode: the request is validated but never sent.*
4. **Five parallel authority reads** — `action_policy_for`, `risk_decision_for`, `kill_switches_for`, `readiness_for`, `adapter_capability_for`. Any error → `GATE_BLOCKED` (capability absent → `ADAPTER_INCOMPATIBLE`)
5. **`validate_action_policy`** (`validation/authority.py`) — the verdict must match `verdict_id`, `action`, `decision_id`, all three trace IDs, `scope["account_id"]`, be `allowed`, and satisfy `issued_at <= now < expires_at`. Optional scope keys (`portfolio_id`, `strategy_id`, `symbol`) must match when present → else `SCOPE_MISMATCH`
6. **`validate_risk_authority`** — decision **and** its approval token are checked together:
   - `decision_id`, `intent_id`, all trace IDs
   - `decision.state is APPROVE`
   - **`decision.approved_size == request.quantity`** — Trading never resizes
   - `issued_at <= now < expires_at`
   - `token.token_id == request.approval_token_ref`, `token.decision_id`, `token.action`, token trace IDs, `token.scope["account_id"]`, token lifetime
   - any failure → `GATE_BLOCKED`
7. **`validate_kill_switch_hierarchy`** — the supplied states must be **exactly** the required set: `global`, `strategy:<strategy_id>`, plus `portfolio:<portfolio_id>` and `symbol:<symbol>` when applicable. Missing, extra, or duplicated → `KILL_SWITCH_UNKNOWN`. Any `unknown` → `KILL_SWITCH_UNKNOWN`. Any `active` (outside `allowed_active_levels`) → `KILL_SWITCH_ACTIVE`. Future-dated or older than `max_staleness_seconds["kill_switch"]` → `KILL_SWITCH_STALE`
8. **Readiness** — `readiness.passed` must be `True`, else `GATE_BLOCKED` carrying `failed_checks`. (See §5a.)
9. **Idempotency reservation** — `reserve_idempotency` (§7). `duplicate_active` / `conflict` / `reconciliation_required` → `TRADING_CONCURRENCY_CONFLICT`; `duplicate_completed` → return `dispatch_allowed: False` with the existing `receipt_id` and stop
10. **`session.reconciliation_ready`** must be `True` → else `RECONCILIATION_REQUIRED`
11. **Pre-mutation audit** — `session.write_pre_audit` builds a Utils `AuditEvent v1` from the authenticated principal (trace IDs must match the request) and pushes it through the injected sink. Any failure → **`AUDIT_FAILED`**, and dispatch never happens
12. **`build_execution_plan`** → `OrderIntent` (§6)
13. **`validate_adapter_capability`** (`routing/capabilities.py`) — the adapter must declare: matching `provider_id`, `contract_version == "v1"`, `schema_id == "brokers.adapter.v1"`, a `provider_api_version`, `intent.action ∈ supported_actions`, `intent.order_type ∈ supported_order_types`, `security_profile == "approved"`, `operation_timeout_seconds` **exactly equal** to the runtime timeout, `malformed_response_policy == "unknown_outcome"`, a `rate_limit_policy`, `mutation_retry_policy == "reconcile_before_retry"`, and `redaction_applied is True`. Any deviation → `ADAPTER_INCOMPATIBLE`

Success returns `{dispatch_allowed: True, intent: <OrderIntent JSON>}`. Back in `_execute_request`, `_intent_from_gate` re-parses it and asserts `parsed.request_id == request.request_id` → else `SCOPE_MISMATCH`.

### 5a. Readiness assessment — `validation/readiness.py`

`assess_execution_readiness` accumulates bounded, unique failure codes (max 32) across four evidence classes:

- **Route** — `ROUTE_EVIDENCE_UNAVAILABLE`, `ROUTE_EVIDENCE_STALE`, `ACTION_CAPABILITY_MISSING`
- **Risk decision** — `RISK_DECISION_MISMATCH`, `RISK_NOT_APPROVED`, `RISK_DECISION_STALE`, `RISK_SIZE_MISMATCH`, `RISK_INTENT_MISMATCH`
- **Kill switch** — `KILL_SWITCH_BLOCKING`, `KILL_SWITCH_STALE`
- **Action policy** — `ACTION_POLICY_DENIED`, `ACTION_POLICY_MISMATCH`, `ACTION_POLICY_SCOPE_MISMATCH`, `ACTION_POLICY_STALE`

`passed = not failed`, and a model validator forbids the inconsistent combination (`passed == bool(failed_check_codes)` is rejected).

### 5b. `LiveSession` lifecycle — `live/session.py`

**`start(config, evidence)`**

1. `_validate_live_config` — rejects any key that `is_sensitive_key`, then validates `_LiveRuntimeConfig`: `runtime_profile` must equal `execution_route`, all durations positive `Decimal`, `max_staleness_seconds` exactly the three required classes, `data_authority_id` non-blank
2. `_validate_authorities` — connection/flags/adapter all present; `(execution_route == "live") == (broker environment == "live")` → else `CONFIGURATION_INVALID`; connection enabled; feature-flag id and environment match the connection; adapter contract `v1` / schema `brokers.adapter.v1`; `evidence["data_authority_id"]` matches config; `evidence["adapter_security_profile"] == "approved"` → else `PERMISSION_DENIED`; `evidence["startup_evidence_fresh"] is True` → else `STALE_EVIDENCE`
3. `started = True`, `admission_enabled = False`
4. `await startup_reconcile()` — failure → `RECONCILIATION_REQUIRED`; a `False` result leaves the session **package-only** with `health="reconciliation_required"`
5. Admission is enabled only when `execution_route == "paper"` **or** `allow_live_mutations is True`. Health becomes `ready` or `package_only`; a `HEALTH_CHANGED` `OperationalEvent` is published

> **Live trading requires an explicit `ALLOW_LIVE_MUTATIONS` flag.** Paper self-enables; live does not.

**`stop()`** — disables admission immediately, then runs three steps against a single monotonic `shutdown_budget_seconds` deadline: `drain_in_flight` → `flush_evidence` → `shutdown_reconcile`. Each is individually timed with the *remaining* budget; a failure or timeout is recorded rather than raised. Unresolved steps (plus `shutdown_budget_exceeded` when the deadline passes) are reported, health becomes `shutdown_incomplete`, and the response status is `partial`.

---

## 6. `build_execution_plan` — `TradingRequest` → `OrderIntent v1`

`validation/plans.py`, side-effect free.

1. `readiness.passed` required → else `GATE_BLOCKED`
2. `symbol`, `side`, `quantity` required → else `INVALID_REQUEST`
3. Builds canonical `material` (contract identity, trace IDs, route/provider/account/strategy, symbol/action/side/order_type/quantity_unit, `approved_volume = request.quantity`, prices, TIF/expiration, broker targets, `canonical_material_version`, risk/policy/token references, `created_at`, `valid_until`)
4. `digest = sha256(canonical_json(material))` → becomes `idempotency_hash`
5. `client_order_id = "trd-" + sha256(canonical_json({request_id, idempotency_key, material_hash}))`

The intent carries **both** `approved_volume` and `risk_approved_volume`, set to the same value — so any downstream tampering is detectable (and the sim authority checks exactly that).

---

## 7. Idempotency reservation — `state/idempotency.py`

`digest = sha256(canonical_json(request.model_dump(mode="python")))` over the *whole* request, then `store.reserve_idempotency(key, digest, canonical_material_version, now, now + retention)`.

| Condition | Result |
|---|---|
| `reservation.material_hash != digest` or `status == "conflict"` | `IDEMPOTENCY_CONFLICT` — the caller key was reused for different material |
| `material_version` differs | `VERSION_CONFLICT` |
| `duplicate_active` older than `concurrency_lock_timeout_seconds` | `TRADING_CONCURRENCY_CONFLICT` |
| `new` | proceed to dispatch |
| `duplicate_completed` | return the existing `receipt_id`, **no dispatch** |

`IdempotencyReservation` validators enforce lowercase 64-char SHA-256, aware-UTC timestamps, `expires_at > reserved_at`, and `duplicate_completed` implies a `receipt_id`.

---

## 8. Stage 2B — The **sim** gate stack

Inline in `_execute_request`, no `LiveSession` involved:

```python
now = deps.clock()
validate_action_policy(request, deps.action_policy_source(request), now)
validate_risk_authority(request, deps.execution_risk_decision_source(request), now)
validate_kill_switch_hierarchy(request, deps.kill_switch_state_source(request),
                               deps.max_staleness_seconds["kill_switch"], now)
reservation = _reserve_idempotency_value(...)
plan = build_execution_plan(request, _passed_readiness(request))
```

### Sim vs live/paper — exactly what differs

| Gate | sim | paper / live |
|---|---|---|
| Common validation (§4) | ✅ | ✅ |
| Unresolved-scope lock (§4c) | ✅ | ✅ |
| Action-policy validation | ✅ | ✅ |
| Risk-authority + token validation | ✅ | ✅ |
| Kill-switch hierarchy | ✅ | ✅ |
| Idempotency reservation | ✅ | ✅ |
| `build_execution_plan` | ✅ | ✅ |
| Session started / admission enabled | ❌ | ✅ |
| **Readiness assessment** | ❌ — `_passed_readiness` synthesizes a passed result | ✅ full assessment |
| **Pre-mutation audit (`AUDIT_FAILED`)** | ❌ | ✅ |
| **`reconciliation_ready`** | ❌ | ✅ |
| **`validate_adapter_capability`** | ❌ | ✅ |
| Envelope `places_trade` / `requires_network` | `False` | `True` |

`_passed_readiness` returns `ReadinessAssessment(passed=True, failed_check_codes=(), evidence_refs={request_id, route}, assessed_at=request.system_time)` — an explicit record that readiness was bypassed *because* the route is simulated, not an accidental skip.

Note the sim path returns a `duplicate_completed` reservation as a **success envelope** with `legacy_status="duplicate_completed"`, whereas the live gate returns `dispatch_allowed: False` with the receipt ID. Same outcome, different envelope shape.

---

## 9. Stage 3 — Pre-dispatch persistence

`_record_send_attempt(request, intent, deps)` — **before** anything crosses the authority boundary.

- Reads the projection for `(route, account_id, authority_id)` to get the current version
- `event_id = "trd-event-" + sha256(canonical_json({event_type: "send_attempted", request_id, client_order_id}))`
- Builds a `TradingEvent(event_type="send_attempted", aggregate_version=version, ...)` whose redacted payload carries the request ID, the full intent, and `sha256(idempotency_key)` — never the key itself
- `_apply_execution_event_value(event, store)` appends it and **adds the event ID to `unresolved_attempt_ids`**

> The attempt is durable before the mutation is sent. If the process dies mid-flight, the unresolved attempt survives and blocks every future mutation in that scope until reconciliation clears it.

---

## 10. Stage 4 — Dispatch

`_dispatch_order_intent_value` — `routing/dispatcher.py`. **The single authority mutation boundary.**

`_validate_dispatch_policy` first: `operation_timeout_seconds` must be a finite positive `Decimal` → else `CONFIGURATION_INVALID`.

### 10a. `route == "sim"`

1. `simulation_dispatch` must be present → else `SERVICE_UNAVAILABLE`
2. `connection` and `broker_adapter` must both be `None` → else **`SCOPE_MISMATCH`** ("Sim dispatch received Broker authority")
3. `async with asyncio.timeout(...)` around `await simulation_dispatch(intent)`
   - `TimeoutError` → `_timeout_receipt` (unknown outcome)
   - `TradingError` → re-raised
   - anything else → `_uncertain_failure_receipt` (unknown outcome)
4. Accepts either a bare `ExecutionReceipt` or a successful `StandardResponse[ExecutionReceipt]`; anything else → `MALFORMED_RECEIPT`
5. **Scope verification** — the returned receipt's `client_order_id`, `intent_id`, `route`, `request_id`, and `correlation_id` must all match the intent → else `MALFORMED_RECEIPT`

On the far side of that callback sits `SimTrader.submit_order` (`app/services/simulator/execution/trader.py`), which independently re-checks:

- `intent.route == "sim"` → else `SIM_INVALID_CONFIG`
- **`intent.approved_volume == intent.risk_approved_volume`** → else `SIM_INVALID_VOLUME` ("Approved volume was altered after Risk approval")

…before the simulator's `EventDrivenExecutionEngine` ever sees it.

### 10b. `route ∈ {paper, live}`

1. `simulation_dispatch` must be `None` → else **`SCOPE_MISMATCH`** ("Broker dispatch received Simulation authority")
2. **`_validate_broker_selection`**
   - connection and adapter both present → else `SERVICE_UNAVAILABLE`
   - `is_broker_connection_enabled` → else `GATE_BLOCKED`
   - `intent.provider_id == connection id` → else `SCOPE_MISMATCH`
   - **`route == "live"` requires environment `"live"`**; **`route == "paper"` forbids environment `"live"`** → else `SCOPE_MISMATCH`
   - adapter contract `v1` and schema `brokers.adapter.v1` → else `ADAPTER_INCOMPATIBLE`
3. **`_invoke_broker`** — exactly one Brokers mutation, mapped by action:

   | Action | Brokers call |
   |---|---|
   | `submit_order` | `build_broker_order_request(...)` → `place_broker_order` |
   | `modify_order` | `build_broker_order_modification_request(...)` → `modify_broker_order` |
   | `cancel_order` | `cancel_broker_order(adapter, target_broker_order_id)` |
   | `modify_position` | `build_broker_position_modification_request(...)` → `modify_broker_position` |
   | `close_position` / `reduce_exposure` | `build_broker_position_close_request(...)` → `close_broker_position` |
   | anything else | `INVALID_REQUEST` |

   `modify_order` additionally rejects any attempt to change `time_in_force` or `expiration` → `ADAPTER_INCOMPATIBLE`, because the verified Brokers modification contract has no such field.

4. Same timeout wrapper: `TimeoutError` → `_timeout_receipt`; `ValueError` → `INVALID_REQUEST`; anything unexpected → `_uncertain_failure_receipt`
5. **`_broker_evidence`** — `metadata.extensions` must carry `broker`, `operation`, `environment`, `timestamp` (parseable UTC) → else `MALFORMED_RECEIPT`
6. Result scope must match the selected connection's id and environment → else `MALFORMED_RECEIPT`
7. **`_broker_raw_response`** normalizes without upgrading evidence:
   - error response → `rejected` only if the code is in `_EXPLICIT_REJECTIONS` (auth/authorization/symbol/account/order/position not found, request invalid/rejected, market closed, insufficient margin/funds); **everything else becomes `unknown_outcome`**; `BROKER_RATE_LIMITED` sets `rate_limited: True`
   - order-shaped result → `_order_result_fields`: `UNKNOWN` → `unknown_outcome`, `REJECTED` → `rejected`, `PARTIAL` → `partial`, cancel action → `cancelled`, fully filled → `filled`, otherwise `accepted`
   - position-shaped result → `accepted` with the position ID as `provider_order_id`
   - unrecognized shape → `status: "success"` with zero fill (which classification then judges)
8. **`_classify_authority_response_value`** (`routing/responses.py`) produces the `ExecutionReceipt`

### 10c. Conservative classification

Nine required text fields must all be present and trimmed. Both policy declarations are re-verified (`malformed_response_policy == "unknown_outcome"`, `mutation_retry_policy == "reconcile_before_retry"`) → else `ADAPTER_INCOMPATIBLE`.

`_classify_status`:

| Input | Receipt status | Classification | `reconciliation_required` |
|---|---|---|---|
| `timed_out` / `ambiguous` / `rate_limited` | `unknown_outcome` | `timeout` / `ambiguous` / `rate_limited` | **True** |
| `status == "success"` with **no** `provider_order_id` | `unknown_outcome` | `malformed_success` | **True** |
| `status == "success"` with a `provider_order_id` | `accepted` | `confirmed` | False |
| one of the finite statuses | that status | `confirmed` | True only for `unknown_outcome` |
| anything else | `unknown_outcome` | `malformed_response` | **True** |

**`retry_safe` is always `False`** on this path. Numbers are parsed strictly: no `bool`, no `float`, must be finite and non-negative. Timestamps must be aware UTC with a zero offset.

> **The design rule: uncertainty is never optimism.** A timeout, a rate limit, a malformed response, or a "success" without a provider order ID all become `unknown_outcome` and freeze the scope.

---

## 11. Stage 5 — Post-dispatch persistence

### 11a. `_record_receipt`

Builds a `TradeRecord v1`:

- `record_id` = deterministic hash of `{receipt_id, request_id}`
- `authority_state = receipt.status`
- `reconciliation_state = "unreconciled" if receipt.reconciliation_required else "reconciled"`
- `fill_ids = receipt.provider_deal_ids`

Appends a `receipt_recorded` event (payload: redacted receipt, `attempt_event_id`, trade record), then **one `fill_recorded` event per `provider_deal_id`**, each re-reading the projection version so the optimistic chain stays intact.

### 11b. Projection reduction — `state/projections.py`

`_apply_execution_event_value` enforces three invariants before writing:

1. **Deduplication** — if `event.event_id` is already in `projection.event_ids`, return unchanged
2. **Optimistic version** — `event.aggregate_version == current.version` → else `VERSION_CONFLICT`
3. **Scope** — `(route, tenant_id, authority_id)` must match → else `SCOPE_MISMATCH`

Then `_project_event` applies the event type:

| Event | Effect |
|---|---|
| `send_attempted` | `orders[event_id] = facts`; **append to `unresolved_attempt_ids`** |
| `receipt_recorded` | record receipt + trade record; back-fill `broker_order_id`/`client_order_id` onto the originating order entry; **remove the attempt from `unresolved` only if `receipt.status != "unknown_outcome"`** |
| `fill_recorded` | `fills[event_id] = facts` |
| `reconciliation_transitioned` | record authority state, merge readiness, remove `resolved_attempt_event_id` from `unresolved` |
| `incident_recorded` | `incidents[event_id] = facts` |

Persistence prefers the store's atomic `apply_event(event, projected, expected_version)`; in-memory test stores fall back to `append_event` + `save_projection`.

`positions` is declared but **must always be empty** in a durable projection (`_reject_persisted_positions`) — current positions are memory-only, held in `deps.execution_positions`.

### 11c. `_complete_reservation`

`store.complete_idempotency(key, digest, receipt_id, now, status=...)` where status is `"reconciliation_required"` when the receipt demands it, else `"completed"`. Failure → `PERSISTENCE_FAILED`.

---

## 12. Stage 6 — Unknown-outcome resolution

Runs whenever `receipt.reconciliation_required` is `True`. `_resolve_unknown` → `resolve_unknown_outcome` (`reconciliation/authority.py`).

1. Receipt must actually be `unknown_outcome` with `reconciliation_required` → else `INVALID_REQUEST`
2. `snapshot_source(receipt.route)` → `AuthoritySnapshot`; unreachable → `SERVICE_UNAVAILABLE`; route mismatch → `SCOPE_MISMATCH`
3. `_load_context` — loads the projection and the unresolved attempts; the originating `send_attempted` event for this `request_id` **must** be findable → else `PERSISTENCE_FAILED`
4. **`compare_authority_state`** (`reconciliation/compare.py`) — both sides are flattened into class-prefixed keys (`order:<id>`, `position:<id>`) and compared by `canonical_json` equality:
   - `missing_internal_ids` — the authority knows about it, Trading doesn't
   - `missing_authority_ids` — Trading knows about it, the authority doesn't
   - `mismatched_ids` — both know, facts differ
   - `stale_authority` — `authority.observed_at < projection.updated_at`
   - severity: `critical` if `missing_internal` or `mismatched`, else `warning` if any class, else `none`
5. **Transition decision**

   | Condition | Transition | `retry_allowed` |
   |---|---|---|
   | any unresolved scope | `retry_locked` | False |
   | clean **and** an `approved_retry` record already exists in `projection.authority_state` for this receipt | `approved_retry` | **True** |
   | clean, no approval | `resolved_no_retry` | False |

6. Two events are persisted in sequence: `incident_recorded`, then `reconciliation_transitioned` (which carries `resolved_attempt_event_id` — `None` when retry-locked, so the lock survives)
7. On `retry_locked`, `_resolve_unknown` builds a `BROKER_STATE_UNKNOWN` `OperationalEvent` — `severity="critical"`, `facts={retry_locked: True, unresolved_scope}`, `source_refs={receipt_id, incident_id}` — and emits it through `deps.event_sink`. Failure to build or emit → `SERVICE_UNAVAILABLE`

`emit_runtime_event` is itself defensive: if the sink rejects the event, it offers an `EVENT_DELIVERY_FAILED` incident to the same sink before raising; if *that* also fails, it raises `SERVICE_UNAVAILABLE` with both identities in the trace context.

> **There is no blind retry anywhere in this package.** An unknown outcome can only be cleared by reconciliation proving the authority and Trading agree, and a retry additionally requires a pre-recorded `approved_retry` transition.

---

## 13. Stage 7 — The response envelope

`_envelope(request, receipt)`:

- `receipt.status == "unknown_outcome"` → **error** response, `code="UNKNOWN_OUTCOME"`, `risk_level="critical"`, raw receipt in `error.details["receipt"]`, `legacy_status="unknown_outcome"`
- otherwise → **success** response with the raw receipt in `data`, and `legacy_status` mapped: `accepted → "sent"`, `rejected`, `partial`, `filled`, `cancelled`

Both set `places_trade` and `requires_network` to `route in {paper, live}` — so a sim mutation is never marked as touching money or the network.

Every public verb wraps its `_value` implementation in `try/except Exception` → `map_trading_error(error, {"request_id": ...})`. Nothing raw escapes the package boundary.

---

## 14. The live/paper evaluation cycle

`run_live_evaluation_cycle(deps, evidence)` — `actions/runtime.py`. This is the automated path that produces requests instead of receiving them.

```
asyncio.timeout(live_workflow_timeout_seconds):
    dataset        = await market_data_source(evidence)          # Data
    account        = await evaluation_account_source(evidence)   # Data
    market_context = await market_context_source(dataset, ev)    # Data
    indicators     = await indicator_source(dataset, evidence)   # Indicators
    intent         = await strategy_source(dataset, account, indicators, ev)   # Strategy
    if intent is None:  → success, {"mutation_performed": False}, read_only
    decision       = await risk_source(intent, account, market_context, ev)    # Risk
    request        = _approved_request(intent, decision, deps, evidence)
    _check_timeout(deps, started_at, evidence)
    return await _execute_request(request, deps, evidence)
```

**A neutral strategy result is a normal outcome**, returned as a read-only success — not an error.

`_approved_request` refuses to build anything unless Risk genuinely approved:

- `decision.state is APPROVE`, `decision.intent_id == intent.intent_id`, `approved_size is not None`, `token is not None`, `expires_at > now` → else `PERMISSION_DENIED`
- route comes from `live_session.config.execution_route`; provider from the Broker connection
- `quantity = decision.approved_size` (**never the strategy's proposal**)
- `valid_until = min(decision.expires_at, token.expires_at)` — the tighter of the two
- instrument metadata comes from `symbol_capability_source`

`_ACTION_BY_INTENT` maps Strategy intent types to Trading verbs: `OPEN`/`INCREASE` → `submit_order`, `CLOSE` → `close_position`, `REDUCE` → `reduce_exposure`, `MODIFY` → `modify_position`, `CANCEL` → `cancel_order`.

`_state_target` resolves broker targets from Trading's own state, never from the strategy: `OPEN`/`INCREASE` need none; `CANCEL` searches `projection.orders` by symbol; everything else searches the process-local execution positions. **Exactly one match is required** — zero or many → `RECONCILIATION_REQUIRED` ("target is ambiguous").

Timeout handling is doubled: an `asyncio.timeout` around the whole cycle, plus an explicit `_check_timeout` immediately before mutation. Either path emits a `WORKFLOW_TIMEOUT` `OperationalEvent` and raises `WORKFLOW_TIMEOUT` — so the cycle can never dispatch after its budget expired.

---

## 15. Error taxonomy

| Code | Typical trigger |
|---|---|
| `INVALID_REQUEST` | missing symbol/target, action-verb mismatch, unmapped action |
| `VALIDATION_FAILED` | quantity/price/geometry/capability/precondition failure |
| `SCOPE_MISMATCH` | account, route/environment, provider, policy scope, or receipt scope mismatch; mixed sim/broker authority |
| `STALE_EVIDENCE` | account-state evidence expired; startup evidence not fresh |
| `GATE_BLOCKED` | session inactive, authority read failed, action policy or Risk approval invalid, readiness failed, plan build failed, provider disabled |
| `PERMISSION_DENIED` | Risk did not approve; adapter security not approved; action policy unavailable |
| `KILL_SWITCH_UNKNOWN` / `KILL_SWITCH_ACTIVE` / `KILL_SWITCH_STALE` | hierarchy unproven / active / stale |
| `AUDIT_FAILED` | pre-mutation audit write failed (live/paper only) |
| `IDEMPOTENCY_CONFLICT` | caller key reused for different canonical material |
| `TRADING_CONCURRENCY_CONFLICT` | active reservation, or lock exceeded its bound |
| `VERSION_CONFLICT` | stale `expected_version` or stale event `aggregate_version` |
| `RECONCILIATION_REQUIRED` | unresolved attempt in scope, projection absent, ambiguous target, unknown outcome still locked |
| `ADAPTER_INCOMPATIBLE` | any capability/contract/schema/policy declaration mismatch |
| `MALFORMED_RECEIPT` | missing/invalid authority evidence, scope mismatch, unrepresentable response |
| `UNKNOWN_OUTCOME` | envelope code for a receipt requiring reconciliation |
| `SERVICE_UNAVAILABLE` | authority absent, event delivery failed, snapshot unavailable |
| `PERSISTENCE_FAILED` | projection read/write or idempotency write failed |
| `CONFIGURATION_INVALID` | invalid timeout/staleness/retention bounds, secret material in config |
| `WORKFLOW_TIMEOUT` | evaluation cycle exceeded its bound |

---

## 16. Safety invariants

1. **Trading never resizes.** `approved_volume = risk_approved_volume = request.quantity = decision.approved_size`, checked at the readiness gate, the authority gate, the plan builder, and again inside `SimTrader`.
2. **The attempt is durable before the mutation is sent**, and it stays unresolved until a *known* outcome is recorded.
3. **One unresolved attempt freezes the whole authority scope** (`_require_clear_authority_scope`).
4. **Uncertainty is always `unknown_outcome`.** Timeouts, rate limits, malformed responses, and success-without-an-order-ID all classify conservatively. `retry_safe` is `False` on the dispatch path.
5. **No blind retry.** Clearing a lock needs reconciliation agreement; retrying needs a pre-recorded `approved_retry`.
6. **Live requires an explicit flag** (`allow_live_mutations`); paper does not; sim never touches a broker.
7. **Route and environment are cross-checked twice** — at session start and again at dispatch.
8. **Sim and broker authority are mutually exclusive** — supplying both is `SCOPE_MISMATCH`, in both directions.
9. **Pre-mutation audit is fail-closed** on live/paper: `AUDIT_FAILED` stops dispatch.
10. **Payloads are redacted** through `_redacted_envelope_data`; the idempotency key is persisted only as a SHA-256 hash; config rejects any `is_sensitive_key`.
11. **All identities are deterministic hashes** — `client_order_id`, `idempotency_hash`, `receipt_id`, every `event_id`, `record_id`, `report_id`, `resolution_id`.
12. **Current positions are memory-only.** A durable projection carrying position bodies is rejected outright.
