# HaruQuant MT5 Broker Adapter Implementation Specification

**Version:** 1.0.0
**Parent Specification:** HaruQuant Execution Module Technical Specification v6.0.0
**Target implementation:** `tools/execution/brokers/mt5.py`
**Status:** Implementation-ready draft
**Scope:** MT5 direct execution adapter for Phase 1 live trading

---

## 1. Purpose

This document defines the concrete implementation requirements for the HaruQuant MT5 broker adapter.

The parent Execution Module specification defines the architecture, policies, state machines, risk/approval dependencies, idempotency, reconciliation, and production safety model. This document narrows that into the exact runtime design required to implement the MT5 adapter safely using the Python `MetaTrader5` package and a local MetaTrader 5 terminal.

The MT5 adapter must act as a broker-safe bridge between HaruQuant execution commands and MT5 terminal operations. It must not contain strategy logic, portfolio logic, LLM decisions, risk approval logic, or human approval logic.

---

## 2. Implementation Boundary

Only the private MT5 adapter boundary may import the external `MetaTrader5` package.

Allowed:

```python
# tools/execution/brokers/mt5.py
import MetaTrader5 as mt5
```

Not allowed:

```python
# agents, workflows, services, strategy files, risk files, or public tools
import MetaTrader5 as mt5
```

All production code must interact through HaruQuant abstractions:

```text
ExecutionGateway
    -> MT5BrokerAdapter
        -> MT5ApiClient
            -> MetaTrader5 package
```

---

## 3. Target Files

Recommended files:

```text
tools/execution/brokers/base.py
tools/execution/brokers/models.py
tools/execution/brokers/errors.py
tools/execution/brokers/mt5.py
tools/execution/brokers/symbols.py
tools/execution/brokers/supervision.py
tools/execution/brokers/reconciliation.py
```

Minimum Phase 1 can start with `mt5.py`, but private helper classes should be split when complexity grows.

Required tests:

```text
tests/unit/tools/execution/brokers/test_mt5.py
tests/unit/tools/execution/brokers/test_mt5_symbol_cache.py
tests/unit/tools/execution/brokers/test_mt5_retcode_policy.py
tests/unit/tools/execution/brokers/test_mt5_precision.py
tests/unit/tools/execution/brokers/test_mt5_reconciliation.py
tests/usage/tools/execution/brokers/mt5.py
```

---

## 4. Bridge Architecture and Threading Model

The Python `MetaTrader5` package must be treated as a blocking terminal-bound API.

Required runtime model:

```text
Execution workflow / gateway
    -> MT5BrokerAdapter
        -> MT5CallExecutor
            -> ThreadPoolExecutor(max_workers=1 per terminal session)
                -> MetaTrader5 package call
```

Rules:

1. One terminal session must use one call executor.
2. One executor must use one worker thread in Phase 1.
3. Broker-mutating calls must never run concurrently for the same terminal session.
4. Read-only calls should also use the same executor in Phase 1 for deterministic ordering.
5. Async gateway code may expose async methods, but MT5 calls must run inside the executor.

Timeout defaults:

| Operation | Timeout |
|---|---:|
| `initialize` | 15 seconds |
| `login` | 15 seconds |
| `account_info` | 3 seconds |
| `terminal_info` | 3 seconds |
| `symbol_info` | 3 seconds |
| `symbol_info_tick` | 2 seconds |
| `order_check` | 5 seconds |
| `order_calc_margin` | 5 seconds |
| `order_send` | 10 seconds |
| `positions_get` | 5 seconds |
| `orders_get` | 5 seconds |
| `history_orders_get` | 10 seconds |
| `history_deals_get` | 10 seconds |

Broker-mutating timeout rule:

```text
If timeout occurs after a mutation may have reached MT5, do not retry. Mark UNKNOWN_OUTCOME and reconcile.
```

---

## 5. Lifecycle State Machine

The adapter must model terminal state explicitly:

```text
UNINITIALIZED
INITIALIZING
INITIALIZED
LOGGING_IN
CONNECTED
DEGRADED
DISCONNECTED
RECONNECTING
SHUTTING_DOWN
SHUTDOWN
FAILED
```

Broker-mutating commands are allowed only in:

```text
CONNECTED
```

Startup sequence:

```text
1. Load sanitized MT5 configuration.
2. Validate terminal path when provided.
3. Create terminal session ID.
4. Initialize MetaTrader5 package.
5. Login if credentials are provided or required.
6. Read terminal_info().
7. Read account_info().
8. Validate expected account, server, and environment.
9. Validate trade permission state where available.
10. Load and refresh symbol metadata.
11. Run startup reconciliation.
12. Mark adapter CONNECTED only after reconciliation passes.
```

Shutdown sequence:

```text
1. Block new commands.
2. Wait for in-flight non-mutating calls to finish or timeout.
3. Mark unknown broker-mutating attempts as UNKNOWN_OUTCOME.
4. Persist terminal shutdown event.
5. Call mt5.shutdown().
6. Mark state SHUTDOWN.
```

---

## 6. Heartbeat and Terminal Health

Heartbeat defaults:

| Environment | Interval |
|---|---:|
| live | 1 second |
| demo | 5 seconds |
| paper/simulated adapter | 10 seconds |

Heartbeat must collect:

- terminal state;
- account state;
- last successful MT5 call timestamp;
- watched-symbol quote age;
- trade permission state;
- executor queue depth;
- in-flight command count.

Health states:

```text
HEALTHY
DEGRADED
UNHEALTHY
RECOVERING
MANUAL_REVIEW_REQUIRED
```

New sends must be blocked in `UNHEALTHY`, `RECOVERING`, and `MANUAL_REVIEW_REQUIRED`.

---

## 7. Process Supervision and Recovery

The adapter monitors terminal health. A separate terminal supervisor may start or restart the MT5 process.

Auto-restart must be disabled by default in live production.

If enabled, auto-restart requires:

- new sends blocked;
- no active in-flight broker mutation, or all in-flight commands persisted as `UNKNOWN_OUTCOME`;
- restart audit record;
- post-restart reconciliation before new sends.

Reconnect rule:

```text
After reconnect or terminal restart, no broker-mutating command may be sent until reconciliation completes.
```

---

## 8. Dynamic Symbol and Contract Metadata Refresh

The adapter must maintain a symbol specification cache containing:

```text
symbol
broker_symbol
visible
trade_mode
order_mode
filling_mode
expiration_mode
digits
point
trade_tick_size
trade_tick_value
contract_size
volume_min
volume_max
volume_step
volume_limit
spread
spread_float
stops_level
freeze_level
margin_initial
margin_maintenance
last_refresh_utc
source_terminal_session_id
```

Refresh triggers:

| Trigger | Requirement |
|---|---|
| Startup | Refresh all configured trade symbols. |
| Timer | Refresh active symbols every 60 seconds in live mode. |
| Before send | Refresh target symbol if cache age > 5 seconds. |
| Before modify/cancel | Refresh target symbol if cache age > 5 seconds. |
| After broker error | Refresh on invalid price/stops/volume/fill, market closed, off quotes, or requote. |
| Session boundary | Refresh at session open/close windows. |
| Symbol selection | Refresh after `symbol_select`. |

If material symbol specs change mid-session, emit `SYMBOL_SPEC_CHANGED` and block new sends if the change affects risk, volume, tick value, contract size, or trade mode.

---

## 9. Precision, Point, Pip, Volume, and Price Normalization

Internal values must use `Decimal` until the final MT5 request boundary.

Price normalization:

```text
normalized_price = round(price, digits)
normalized_sl = round(sl, digits)
normalized_tp = round(tp, digits)
```

Volume normalization:

```text
steps = floor((requested_volume - volume_min) / volume_step)
normalized_volume = volume_min + steps * volume_step
```

Volume must not be rounded upward if that increases risk beyond the approved risk decision.

Point/pip rule:

```text
point = MT5 symbol_info.point
pip = display/strategy concept, not a universal MT5 primitive
```

For most 5-digit FX and 3-digit JPY symbols:

```text
pip = 10 * point
```

For metals, indices, crypto, CFDs, and broker-specific symbols, use `point`, `trade_tick_size`, and broker metadata only.

Deviation conversion:

```text
deviation_points = ceil(abs(max_price_slippage) / point)
```

The adapter must enforce:

```text
0 <= deviation_points <= max_allowed_deviation_points
```

Reject with `DEVIATION_EXCEEDS_RISK_APPROVAL` if violated.

---

## 10. MT5 Request Assembly

Every MT5 trade request must be assembled from a validated HaruQuant command and include the required fields for that action:

```text
action
symbol
volume
type
price
sl
tp
deviation
magic
comment
type_time
type_filling
```

Depending on operation, also include:

```text
order
position
position_by
expiration
stoplimit
```

Before `order_send()` for new orders and modifications, run `order_check()` where applicable.

For new entry orders, run `order_calc_margin()` and compare against approved risk/margin state.

---

## 11. Comment Encoding and Reconciliation

MT5 comments are not authoritative. They may be truncated, removed, or changed by broker infrastructure.

Phase 1 comment format:

```text
HQ1-{env}-{sid}-{cmd}-{chk}
```

Example:

```text
HQ1-L-S7F3A2-C91B20-A8D1
```

Rules:

- must be ASCII-safe;
- must fit inside configured MT5 comment limit;
- must not contain raw account IDs, secrets, full strategy names, or full request IDs;
- full mapping must be persisted locally.

Reconciliation fallback order if comment fails:

```text
1. magic number
2. symbol
3. volume
4. order/deal/position ticket
5. execution time window
6. price tolerance
7. local in-flight command records
8. strategy/account scope
```

Low-confidence reconciliation enters `MANUAL_REVIEW_REQUIRED`.

---

## 12. Retcode-to-Action Matrix

Every MT5 retcode must map to a deterministic HaruQuant action.

| MT5 condition | Action |
|---|---|
| Done / placed / accepted | Persist receipt, update state, reconcile. |
| Partial fill | Persist partial receipt and cumulative fill; remain active until terminal. |
| Requote / price changed | Refresh quote/symbol; retry only if policy allows and after revalidation. |
| Off quotes | Do not retry immediately; mark degraded or blocked. |
| Market closed | Block until session open. |
| Invalid stops | Refresh symbol, validate stops/freeze levels, reject unless rebuild allowed. |
| Invalid volume | Refresh symbol, rerun normalization, reject if risk approval no longer matches. |
| Invalid fill mode | Try approved fallback only if symbol metadata and policy allow. |
| No money | Reject and request risk/margin revalidation. |
| Trade disabled | Mark account/symbol blocked or unhealthy. |
| Trade context busy | Backoff and retry up to limit if not unknown outcome. |
| Too many requests | Backoff and throttle polling. |
| Timeout after send | Mark `UNKNOWN_OUTCOME`; reconcile only. |
| Position/order not found | Reconcile; if already terminal and idempotent, return prior receipt; otherwise manual review. |
| Unknown retcode after mutation | Mark `UNKNOWN_OUTCOME`; reconcile only. |

Default retry limits:

| Scenario | Retry |
|---|---:|
| Requote / price changed | 0 live, 1 demo if enabled |
| Trade context busy | 3 with exponential backoff |
| Too many requests | 3 with longer backoff |
| Invalid fill fallback | 1 if explicitly allowed |
| Off quotes | 0 immediate retries |
| Timeout after send | 0, reconcile only |
| Unknown retcode after mutation | 0, reconcile only |

---

## 13. Modify Validation and Requote Policy

Before modifying SL/TP or pending-order price, the adapter must:

1. refresh quote if stale;
2. refresh symbol spec if stale;
3. validate `stops_level`;
4. validate `freeze_level`;
5. validate min price-change threshold;
6. validate risk decision scope and expiry;
7. validate idempotency fingerprint.

Negligible modify requests below threshold may be treated as no-op success if broker state already matches expected state.

Default Phase 1 live requote behavior for modify requests:

```text
fail immediately and reconcile
```

---

## 14. Fill and Position Tracking

The Phase 1 adapter assumes no reliable native push callback through the Python package.

Polling strategy:

| Poller | Live Interval |
|---|---:|
| In-flight command poller | 250 ms to 1 sec |
| Active orders poller | 1 sec |
| Position poller | 1 sec |
| History deals poller | 2 to 5 sec |
| Full reconciliation poller | 30 to 60 sec |
| Heartbeat poller | 1 sec |

Partial-fill rule:

```text
0 < cumulative_filled_volume < requested_volume -> PARTIALLY_FILLED
```

A command may move to `FILLED` only when cumulative broker-confirmed filled volume equals requested volume within configured tolerance.

Terminal state must not rely solely on immediate `order_send()` response when follow-up confirmation is required.

---

## 15. Session Sequence Tracking

MT5 Python does not expose FIX-style sequence numbers, so HaruQuant must maintain local session sequence tracking.

Each terminal session must track:

```text
terminal_session_id
local_sequence_number
last_successful_heartbeat_seq
last_broker_mutation_seq
in_flight_command_ids
last_reconciled_deal_time_utc
last_reconciled_order_time_utc
```

On restart/reconnect:

- reload unresolved sequence records;
- reconcile broker state before new sends;
- mark unresolved gaps as manual review.

---

## 16. Required Environment Variables

```text
MT5_ENABLED
MT5_LOGIN
MT5_PASSWORD
MT5_SERVER
MT5_TERMINAL_PATH
MT5_ENVIRONMENT
MT5_ACCOUNT_ALIAS
MT5_EXPECTED_CURRENCY
MT5_EXPECTED_MODE
MT5_MAGIC_REGISTRY_PATH
MT5_MAX_ORDER_SEND_TIMEOUT_SECONDS
MT5_HEARTBEAT_INTERVAL_SECONDS
MT5_SYMBOL_REFRESH_SECONDS
MT5_RECONCILIATION_INTERVAL_SECONDS
```

All secrets must be redacted in logs, audit records, exceptions, and test snapshots.

---

## 17. MT5 Adapter Error Codes

```text
MT5_INITIALIZE_FAILED
MT5_LOGIN_FAILED
MT5_SHUTDOWN_FAILED
MT5_TERMINAL_UNAVAILABLE
MT5_TERMINAL_DISCONNECTED
MT5_TERMINAL_NOT_TRADE_ALLOWED
MT5_ACCOUNT_MISMATCH
MT5_ACCOUNT_READ_ONLY
MT5_SYMBOL_NOT_FOUND
MT5_SYMBOL_NOT_VISIBLE
MT5_SYMBOL_SELECT_FAILED
MT5_SYMBOL_SPEC_STALE
MT5_SYMBOL_SPEC_CHANGED
MT5_VOLUME_NORMALIZATION_FAILED
MT5_PRICE_NORMALIZATION_FAILED
MT5_INVALID_FILLING_MODE
MT5_INVALID_EXPIRATION_MODE
MT5_ORDER_CHECK_FAILED
MT5_MARGIN_CALC_FAILED
MT5_RETCODE_REQUOTE
MT5_RETCODE_PRICE_CHANGED
MT5_RETCODE_OFF_QUOTES
MT5_RETCODE_MARKET_CLOSED
MT5_RETCODE_INVALID_STOPS
MT5_RETCODE_INVALID_VOLUME
MT5_RETCODE_NO_MONEY
MT5_RETCODE_TRADE_DISABLED
MT5_RETCODE_TRADE_CONTEXT_BUSY
MT5_RETCODE_TOO_MANY_REQUESTS
MT5_ORDER_SEND_TIMEOUT_UNKNOWN_OUTCOME
MT5_COMMENT_PARSE_FAILED
MT5_RECONCILIATION_CONFIDENCE_LOW
MT5_POLLING_THROTTLED
MT5_RECONNECT_RECONCILIATION_REQUIRED
MT5_SESSION_SEQUENCE_GAP
```

---

## 18. Testing Matrix

Unit tests must cover:

- initialization success/failure;
- login failure;
- account mismatch;
- read-only account detection;
- symbol not found;
- symbol selection failure;
- symbol spec refresh;
- mid-session symbol spec change;
- volume normalization;
- price normalization;
- deviation conversion;
- deviation risk rejection;
- comment encoding and parsing;
- order_check failure;
- margin calculation failure;
- retcode action matrix;
- order_send timeout unknown outcome;
- no blind retry after unknown outcome;
- partial-fill polling;
- idempotent cancel/modify behavior;
- restart requires reconciliation;
- heartbeat degraded state;
- polling throttled state.

A fake MT5 module must simulate terminal/account/symbol/order/deal/position behavior.

Demo MT5 validation must pass before live micro-lot rollout.

---

## 19. Acceptance Criteria

The MT5 adapter is complete when:

- [ ] no production module imports `MetaTrader5` except the adapter boundary;
- [ ] all MT5 calls are isolated through a single-session executor;
- [ ] all broker-mutating calls are persisted before send;
- [ ] every broker-mutating timeout becomes `UNKNOWN_OUTCOME`;
- [ ] startup and reconnect reconciliation block new sends until complete;
- [ ] symbol metadata cache supports refresh triggers and diff events;
- [ ] price, volume, point, pip, and deviation normalization are tested;
- [ ] MT5 comments fit within configured limit and are not authoritative;
- [ ] magic number and local records are the reconciliation source of truth;
- [ ] retcode handling is deterministic and tested;
- [ ] polling detects fills and partial fills;
- [ ] rate-limit backoff prevents excessive MT5 calls;
- [ ] terminal supervision is separated from broker logic;
- [ ] all MT5 error codes are documented;
- [ ] all tests pass with coverage above 80%;
- [ ] demo validation passes before live micro-lot rollout.
