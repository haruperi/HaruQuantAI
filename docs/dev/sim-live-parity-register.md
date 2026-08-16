# Sim ⇄ Live Parity Register

> **Goal:** `sim` is an exact mirror of `live`. Same flow, same gates, same calculations, same
> semantics, same terminology, same errors, same returns. The route is the only thing that differs;
> everything behind it is identical. Where a number can come from MT5, it comes from MT5.

**Scope:** `app/services/simulator`, `app/services/trading`, `app/services/brokers/metatrader`
**Status:** initial register — 41 items
**Last updated:** 2026-08-14

---

## How to read this

| Severity | Meaning |
|---|---|
| **S1** | Breaks the mirror premise, or silently produces wrong numbers. Fix before trusting any backtest. |
| **S2** | Material divergence in outcomes — a strategy can pass in sim and fail live because of it. |
| **S3** | Semantic/observability divergence — same outcome, different shape, or untestable code path. |
| **S4** | Cosmetic or ergonomic. |

| Effort | Meaning |
|---|---|
| **XS** | < half a day |
| **S** | 1–2 days |
| **M** | ~1 week |
| **L** | multi-week, architectural |

Each item is `ID · Title · Severity · Effort`, then **Current → Target**, evidence, and fix.

---

## Dashboard

| WS | Workstream | Items | S1 | S2 | S3 | S4 |
|---|---|---:|---:|---:|---:|---:|
| **WS-0** | Defects found (fix regardless of parity work) | 5 | 3 | 2 | 0 | 0 |
| **WS-1** | Path convergence — one execution path | 4 | 3 | 1 | 0 | 0 |
| **WS-2** | Trading gate parity | 8 | 0 | 3 | 5 | 0 |
| **WS-3** | MT5-native calculation delegation | 5 | 3 | 2 | 0 | 0 |
| **WS-4** | MT5 symbol semantics | 7 | 1 | 5 | 1 | 0 |
| **WS-5** | MT5 order / position / account semantics | 8 | 2 | 5 | 1 | 0 |
| **WS-6** | Stochastic realism (spread, slippage, latency) | 5 | 0 | 4 | 1 | 0 |
| **WS-7** | Terminology, errors, return shapes | 4 | 0 | 1 | 2 | 1 |
| | **Total** | **41** | **12** | **23** | **10** | **1** |

---

# WS-0 · Defects found

These are bugs, not design gaps. They produce wrong results today.

### GAP-001 · Swap is never charged in any simulation · **S1** · **XS**

**Current → Target:** swap always `0` → swap accrues per rollover per MT5 `swap_mode`.

`LedgerFill.rollover_multiplier` defaults to `Decimal(0)` (`accounting/ledger.py:39`), and **neither**
`_apply_match` nor `_close` ever sets it (`execution/engine.py:293-300`, `420-429`). So
`calculate_execution_costs` always returns `swap = 0`. Every backtest ever run is swap-free.

**Fix:** compute rollover count from the tick timeline crossing broker rollover time (usually 00:00
server time), apply `swap_rollover3days` for the triple-swap weekday, and pass the multiplier into
`LedgerFill`. Depends on GAP-024 for correct swap mode. Add a regression test asserting a multi-day
position accrues non-zero swap.

---

### GAP-002 · `execution_positions` store is written by nothing · **S1** · **S**

**Current → Target:** no writer exists → the store is maintained on every fill and close.

`set_execution_position` and `transition_execution_position` are exported from the package root but
have **zero call sites in `app/`**. Only readers exist:
`actions/positions.py:46`, `actions/runtime.py:148`, `actions/controls.py:228,264`,
`actions/emergency.py:317`.

Consequence: `_current_position_quantity` raises `RECONCILIATION_REQUIRED` for **every**
`close_position`, `modify_position`, and `reduce_exposure` — on **all routes, including live**. This
is not a sim-only problem.

**Fix:** populate the store in `_record_receipt` when a receipt yields a position, and transition it
on close/reduce. The nine-state transition graph already exists in
`state/execution_positions.py`; it just has no driver.

---

### GAP-003 · Partial fills silently drop the remainder · **S1** · **S**

**Current → Target:** unfilled remainder discarded → remainder either stays working or is explicitly
cancelled with evidence.

In `execution/engine.py:558-559`, a `partial` match calls `_apply_match` then
`del self._pending[order_id]`. The `cancelled_quantity` on `MatchResult` is computed
(`execution/matching.py:244`) and then **never used**. No journal event records the drop.

**Fix:** for IOC, emit an explicit partial-then-cancel receipt pair carrying `cancelled_quantity`
(MT5 `TRADE_RETCODE_DONE_PARTIAL`). For GTC (once GAP-030 lands), re-park the remainder with reduced
volume.

---

### GAP-004 · `_dispatch_order_intent_value` timeout is not enforced for sim in practice · **S2** · **XS**

**Current → Target:** sim dispatch is synchronous-in-async → sim honours a latency model and can
genuinely time out.

The `asyncio.timeout` wrapper at `routing/dispatcher.py:511` is real, but `SimTrader.submit_order`
never awaits anything, so it can never elapse. The timeout path — and therefore
`_timeout_receipt` → `unknown_outcome` — is unreachable in sim.

**Fix:** ties to GAP-035 (latency model). Once sim advances a simulated clock, make the timeout
comparison run against simulated elapsed time, not wall clock.

---

### GAP-005 · `_validate_records` OHLC branch is unreachable on the tick path · **S2** · **XS**

**Current → Target:** dead validation → validation matches the data kind actually supplied.

`validate_market_data` (`validation/validate.py:163-167`) checks `is_ohlcv_record`, but the same
function later requires `dataset.data_kind == "ticks"` (line 208). The OHLC branch can never fire on
a dataset that passes. Bar-quality problems reach the timeline unvalidated.

**Fix:** validate the **source** dataset (bars) with the OHLC rules before tick generation, and the
tick dataset with the tick rules — two calls, two contexts.

---

# WS-1 · Path convergence

The architectural core. Everything else is cheaper once this lands.

### GAP-010 · Backtests bypass the entire Trading domain · **S1** · **L**

**Current → Target:** two disjoint paths → one path, `run_backtest` drives `trading.submit_order`.

```
Path A (backtest)   run_backtest → prepare_run_context → engine.submit_order(intent)   ← DIRECT
Path B (sim route)  trading.submit_order → _execute_request → dispatcher → SimTrader → engine
```

`run/orchestrator.py:571-572` calls `submit_orders_before` / `advance_run_timeline`, which call
`engine.submit_order` directly. A backtest therefore never runs: action-policy validation,
risk-authority + token validation, kill-switch hierarchy, idempotency reservation,
`_record_send_attempt`, `_record_receipt`, `TradeRecord` creation, projection reduction, or
reconciliation.

**Fix:** invert the dependency. `prepare_run_context` should build a `TradingDependencies` bundle
with `simulation_dispatch` bound to the run's `SimTrader`, and `advance_run_timeline` should call
`await trading.submit_order(request, deps)` per due intent instead of `engine.submit_order`. The
simulator keeps owning the clock, the matching, and the journal; Trading owns the gates and the
receipt.

**Sequencing note:** this is the keystone. Do it before WS-2, because WS-2 items become
"already fixed" or trivial once every sim mutation flows through `_execute_request`.

---

### GAP-011 · Two idempotency systems that never meet · **S2** · **S**

**Current → Target:** `sim_runs` request-hash idempotency **or** Trading `reserve_idempotency` →
both, layered, as in live.

Simulator: `resolve_idempotent_run(request_id, request_hash, ...)` guards whole-run replay.
Trading: `reserve_idempotency(idempotency_key, material_hash, ...)` guards per-order replay.
In a backtest only the first runs; per-order idempotency is untested.

**Fix:** keep run-level idempotency where it is (it is a genuinely simulator-owned concern) and let
per-order idempotency flow naturally once GAP-010 lands. Ensure the in-run `TradingStateStore` is
scoped per `run_id` so replaying a run does not collide with the previous run's reservations.

---

### GAP-012 · No `TradingProjection` is built during a backtest · **S1** · **M**

**Current → Target:** journal only → journal **and** projection, both written.

Because Path A skips `_apply_execution_event_value`, a backtest produces no `TradingEvent` stream, no
`unresolved_attempt_ids`, no `TradeRecord`s, and no `authority_state`. Every consumer that reads
Trading projections (reconciliation, evidence reports, operator views) sees nothing for simulated
runs.

**Fix:** falls out of GAP-010. Add an in-memory-or-run-scoped `TradingStateStore` implementation to
the run context so projections are built and can be asserted in tests.

---

### GAP-013 · No `LiveSession` for sim — no lifecycle at all · **S1** · **M**

**Current → Target:** sim has no session → sim runs a `LiveSession` with `execution_route="sim"`.

Sim has no admission control, no startup reconciliation, no drain/flush/shutdown budget, no
`HEALTH_CHANGED` events, and no package-only mode. `_LiveRuntimeConfig` currently constrains
`runtime_profile` and `execution_route` to `Literal["demo", "live"]` (`live/config.py:108-113`).

**Fix:** widen both literals to include `"sim"`. Provide sim lifecycle steps:
`startup_reconcile` → verify the tick dataset and engine are ready; `drain_in_flight` → finish the
current tick; `flush_evidence` → flush the journal; `shutdown_reconcile` → verify ledger invariants.
Admission for `sim` self-enables (like `demo`), never requiring `allow_live_mutations`.

---

# WS-2 · Trading gate parity

Five gates are skipped for `sim` in `_execute_request` (`actions/orders.py:459-505`). Each becomes a
one-line change once GAP-010/GAP-013 land.

### GAP-020 · Readiness assessment is synthesized, not performed · **S2** · **S**

**Current → Target:** `_passed_readiness` fabricates `passed=True` (`actions/orders.py:380-395`) →
real `assess_execution_readiness` against a sim `RouteSnapshot`.

Sim never exercises the 14 readiness codes — `ROUTE_EVIDENCE_STALE`, `RISK_SIZE_MISMATCH`,
`ACTION_CAPABILITY_MISSING`, `ACTION_POLICY_STALE`, etc.

**Fix:** build a `RouteSnapshot` from the simulator's current tick (`observed_at = tick.timestamp`,
`expires_at = tick.timestamp + tick_interval`, `capabilities` from the sim capability declaration in
GAP-023) and run the real assessor. Staleness bounds come from the same `max_staleness_seconds`
config live uses — measured against **simulated** time.

---

### GAP-021 · No pre-mutation audit on sim · **S2** · **XS**

**Current → Target:** no audit event, no `AUDIT_FAILED` path → identical fail-closed audit.

**Fix:** falls out of GAP-013 — once sim runs through `evaluate_live_gate`, `write_pre_audit` runs.
Wire `pre_audit_sink` to the simulator journal so the audit event lands in the run's evidence chain.

---

### GAP-022 · `reconciliation_ready` gate absent for sim · **S3** · **S**

**Current → Target:** no gate → sim proves reconciliation authority like live.

**Fix:** implement a sim `AuthoritySnapshot` source that projects `engine.snapshot()` into the
`AuthoritySnapshot` shape (orders, positions, `observed_at`, `expires_at`). This also unlocks
GAP-041 (reconciliation testability) — the simulator becomes its own authority, and
`compare_authority_state` can run for real.

---

### GAP-023 · `validate_adapter_capability` never runs for sim · **S2** · **S**

**Current → Target:** sim declares no capability contract → sim declares one, and it is validated.

Today sim will accept an action or order type that the MT5 adapter would reject at the capability
gate — so a strategy can be developed against capabilities the broker does not have.

**Fix:** have the sim authority publish a capability mapping in the exact adapter shape
(`provider_id`, `contract_version="v1"`, `schema_id="brokers.adapter.v1"`, `provider_api_version`,
`supported_actions`, `supported_order_types`, `security_profile="approved"`,
`operation_timeout_seconds`, `malformed_response_policy`, `rate_limit_policy`,
`mutation_retry_policy`, `redaction_applied`). **Populate it from the live MT5 adapter's own
capability response** so sim can never claim a capability MT5 lacks.

---

### GAP-024 · Sim receipts bypass `classify_authority_response` · **S2** · **S**

**Current → Target:** engine constructs receipts directly → all receipts pass through the same
conservative classifier.

`routing/dispatcher.py:519-539` returns the sim receipt after a scope check, never calling
`_classify_authority_response_value`. The engine's `_receipt` (`execution/engine.py:168-187`) sets
`reconciliation_required=False` **always** and `retry_safe=status in {rejected, cancelled}` — both
different from the live path, where `retry_safe` is unconditionally `False`.

**Fix:** have `SimTrader` return a **raw response mapping** in the same shape the broker path
produces, and let the dispatcher classify it identically. This deletes a whole class of divergence
and is a prerequisite for GAP-025.

---

### GAP-025 · Sim can never produce `unknown_outcome` · **S3** · **S**

**Current → Target:** unreachable → reachable and fault-injectable.

The retry-lock, `BROKER_STATE_UNKNOWN`, incident persistence, and
`resolve_unknown_outcome` machinery is dead code in simulation — the code path most likely to hurt
you live is the one you cannot rehearse.

**Fix:** after GAP-024, add a fault-injection profile to the sim authority: configurable
probabilities for timeout, ambiguous response, rate limit, and malformed success. Belongs with the
scenario engine (`scenarios/`), which already exists for exactly this kind of injection.

---

### GAP-026 · Risk decision arrives via a different port per route · **S3** · **XS**

**Current → Target:** `execution_risk_decision_source` (sim) vs `session.risk_decision_for` (live) →
one source.

Two ports reading the same authority is two things to keep in sync.

**Fix:** falls out of GAP-013 — sim uses the session source like every other route. Retire
`execution_risk_decision_source`, or make it the single implementation the session delegates to.

---

### GAP-027 · `duplicate_completed` returns two different envelope shapes · **S3** · **XS**

**Current → Target:** sim returns a success envelope wrapping the reservation
(`actions/orders.py:486-497`); live returns gate evidence with `dispatch_allowed: False` and a
`receipt_id` (`live/gates.py:166-175`) → one shape.

**Fix:** standardize on the live shape. Callers should never branch on route to read a duplicate.

---

# WS-3 · MT5-native calculation delegation

> **Principle:** if MT5 can compute it, MT5 computes it. The simulator supplies inputs and stores
> results; it does not re-derive.

### GAP-030 · Margin is computed with an internal formula · **S1** · **M**

**Current → Target:** `calculate_margin(volume, price, contract_size, leverage)`
(`accounting/calculations.py`) → `order_calc_margin` via the MT5 adapter.

`calculate_broker_margin` **already exists** (`brokers/_shared/public.py:735`) and wraps
`order_calc_margin(order_type, symbol, volume, price)`
(`brokers/metatrader/calculations.py:21-47`). It has **zero callers anywhere in `app/`**.

The internal flat formula ignores `SYMBOL_TRADE_CALC_MODE` (Forex / Forex-No-Leverage / Futures /
CFD / CFD-Index / CFD-Leverage / Exchange-Stocks — each with a different margin formula), margin
rate tiers, and account-currency conversion. It will not match MT5 for anything but plain leveraged
FX.

**Fix:** inject a `margin_calculator` port into `AccountLedger`, defaulting to the MT5 adapter's
`calculate_margin`. Cache per `(symbol, side, volume, price)` within a run for determinism. Retain
the internal formula only as an explicitly-disclosed offline fallback, surfaced in
`RealismDisclosure`.

**Determinism note:** MT5 calls are wall-clock and network-bound; a backtest must stay reproducible.
Recommend a **calculation cache** materialized once per run and persisted as a run artifact, so
replays are hermetic and auditable. See GAP-034.

---

### GAP-031 · Profit is computed with an internal formula · **S1** · **M**

**Current → Target:** `(exit − entry) × volume` (`execution/engine.py:396-398`) →
`order_calc_profit` via the MT5 adapter.

`calculate_broker_profit` exists (`brokers/_shared/public.py:750`) wrapping
`order_calc_profit(order_type, symbol, volume, price_open, price_close)`. Also **zero callers**.

The internal formula omits contract size entirely and assumes the quote currency is the account
currency. For `GBPUSD` on a USD account it happens to be close; for `EURGBP` on a USD account, or any
JPY cross, it is wrong.

**Fix:** same pattern as GAP-030 — inject a `profit_calculator` port, use it in `_close` and in
`_observe_excursions` for unrealized P&L, cache per run.

---

### GAP-032 · Unrealized P&L (mark-to-market) uses the same wrong formula · **S1** · **S**

**Current → Target:** `(bid − entry) × volume` in `_observe_excursions`
(`execution/engine.py:354-356`) → `order_calc_profit` with the current tick as close price.

This drives `equity`, `free_margin`, MAE/MFE, and therefore the margin check on every subsequent
open. An error here compounds through the whole run.

**Fix:** route through the same cached profit calculator. Given this runs per position per tick,
the cache matters — key on `(symbol, side, volume, entry, current)` quantized to `tick_size`.

---

### GAP-033 · Tick value / tick size are collapsed into a single `point_value` · **S2** · **S**

**Current → Target:** `ExecutionProfile.point_value` → `SYMBOL_TRADE_TICK_VALUE`,
`SYMBOL_TRADE_TICK_VALUE_PROFIT`, `SYMBOL_TRADE_TICK_VALUE_LOSS`, `SYMBOL_TRADE_TICK_SIZE`,
`SYMBOL_POINT` as distinct values.

MT5 distinguishes point (price granularity) from tick size (minimum price change) from tick value
(account-currency value of one tick) — and further splits tick value into profit and loss variants
for asymmetric instruments. Sim has one number doing all five jobs.

**Fix:** extend `SymbolSpecification` (GAP-040) and use the right value per calculation: `point` for
slippage/gap expressed in points, `tick_size` for price quantization, `tick_value` only where MT5
itself would use it.

---

### GAP-034 · No hermetic calculation cache for reproducible runs · **S2** · **M**

**Current → Target:** N/A → a per-run, content-addressed MT5 calculation cache published as an
artifact.

Delegating to MT5 introduces a live dependency into a domain whose entire contract is determinism
(§13 of the backtest pipeline doc). Without a cache, `run_backtest` stops being reproducible and
`request_hash` stops meaning anything.

**Fix:** a `MT5CalculationCache` keyed by canonical JSON of the call arguments, populated on first
use, `fsync`-ed into the run directory as `calculations.json`, hashed into the artifact manifest,
and **replayed from disk** on any subsequent run with the same `data_hash`. Add
`calculation_source: "mt5_live" | "mt5_cached" | "internal_fallback"` to `RealismDisclosure`.

**This is the item that makes WS-3 safe.** Do it alongside GAP-030, not after.

---

# WS-4 · MT5 symbol semantics

> **Good news:** `_map_symbol` (`brokers/metatrader/mapping.py:79`) seeds `raw_dict` from the MT5
> `SymbolInfo` namedtuple via `_asdict()`, so **the full native field set is already preserved** in
> `BrokerSymbolInfo.provider_metadata`. Most of WS-4 is *consuming* data you already have, not
> fetching new data.

### GAP-040 · `SymbolSpecification` carries 5 fields; MT5 exposes dozens that affect fills · **S1** · **M**

**Current → Target:** `minimum_volume`, `maximum_volume`, `volume_step`, `contract_size`, `leverage`
(`accounting/calculations.py:19-28`) → a full MT5-derived specification.

**Fix:** replace `SymbolSpecification` with a projection built directly from
`BrokerSymbolInfo.provider_metadata`, carrying at minimum: `digits`, `point`, `trade_tick_size`,
`trade_tick_value{,_profit,_loss}`, `trade_contract_size`, `volume_min/max/step`, `volume_limit`,
`trade_stops_level`, `trade_freeze_level`, `filling_mode`, `trade_calc_mode`, `trade_mode`,
`swap_mode`, `swap_long`, `swap_short`, `swap_rollover3days`, `margin_initial`,
`margin_maintenance`, `currency_base`, `currency_profit`, `currency_margin`, `session_deals`,
`session_buy_orders`, `session_sell_orders`. Fail closed on any missing field rather than defaulting.

---

### GAP-041 · `trade_stops_level` is not enforced · **S2** · **S**

**Current → Target:** any SL/TP distance accepted → SL/TP closer than `SYMBOL_TRADE_STOPS_LEVEL`
points from market is rejected.

Sim will happily accept a stop one point away and "fill" it. MT5 returns
`TRADE_RETCODE_INVALID_STOPS`. Strategies tuned in sim on tight stops will fail on the first live
order.

**Fix:** validate in `validation/orders.py::_validate_price_geometry` — it already has the request
and instrument metadata, it just lacks the field. Raise the mirrored MT5 error (GAP-060).

---

### GAP-042 · `trade_freeze_level` is not modelled · **S2** · **S**

**Current → Target:** modification/close always permitted → orders and positions within
`SYMBOL_TRADE_FREEZE_LEVEL` of the trigger price reject modification and closure.

**Fix:** check in `modify_order`, `cancel_order`, `modify_position`, `close_position` against the
current tick. MT5 returns `TRADE_RETCODE_INVALID_STOPS` here too.

---

### GAP-043 · `filling_mode` is ignored; sim supports only FOK/IOC · **S2** · **S**

**Current → Target:** `SUPPORTED_FILL_POLICIES = ("FOK", "IOC")` (`execution/matching.py:22`) →
per-symbol filling support read from the `filling_mode` bitmask, plus `RETURN`.

The MT5 adapter already decodes this bitmask correctly (`metatrader/commands.py:153-163`) — sim
ignores it. A symbol permitting only `RETURN` will reject both policies sim supports.

**Fix:** read `filling_mode` from the specification and validate the requested policy against it.
Implement `RETURN` semantics (partial fill, remainder stays working) — see GAP-003 and GAP-052.

---

### GAP-044 · `volume_limit` (max total volume per symbol) is not enforced · **S2** · **XS**

**Current → Target:** unlimited aggregate exposure → `SYMBOL_VOLUME_LIMIT` enforced across all
positions and pending orders in the symbol.

**Fix:** check aggregate volume in `AccountLedger.apply_fill` before the margin check.
MT5 returns `TRADE_RETCODE_LIMIT_VOLUME`.

---

### GAP-045 · `trade_mode` (DISABLED/LONGONLY/SHORTONLY/CLOSEONLY/FULL) is ignored · **S2** · **XS**

**Current → Target:** all sides always tradeable → per-symbol trade mode enforced.

`_map_symbol` already decodes this to a string (`mapping.py:98-120`). Sim never reads it.

**Fix:** validate side against `trade_mode` in `validate_order_request`. MT5 returns
`TRADE_RETCODE_TRADE_DISABLED` / `TRADE_RETCODE_LONG_ONLY` / `TRADE_RETCODE_SHORT_ONLY` /
`TRADE_RETCODE_CLOSE_ONLY`.

---

### GAP-046 · Sessions are hand-configured UTC intervals, not MT5 symbol sessions · **S2** · **M**

**Current → Target:** `ExecutionProfile.sessions` as literal week-second ranges
(`execution/pricing.py:21-43`) → `SYMBOL_SESSION_QUOTE` / `SYMBOL_SESSION_TRADE` per symbol per day,
plus holidays.

Today a tick outside the configured window is silently journalled as `tick_outside_session` and
skipped (`execution/engine.py:524-537`). If the window is wrong, trades vanish without a signal.

**Fix:** source sessions from `SymbolInfoSessionQuote` / `SymbolInfoSessionTrade` via the adapter,
cached per run (GAP-034). Distinguish *quote* sessions (ticks arrive) from *trade* sessions (orders
accepted) — sim currently conflates them. Outside a trade session, MT5 returns
`TRADE_RETCODE_MARKET_CLOSED` rather than silently skipping.

---

### GAP-047 · Symbol metadata reaches sim through a hand-built port · **S3** · **S**

**Current → Target:** `resolve_symbol_specification(request)` returns a hand-assembled DTO →
the port delegates to `get_broker_symbol_info` against the real MT5 adapter.

**Fix:** make the default implementation of the port a thin MT5 adapter call plus the GAP-040
projection. Hand-built specifications remain possible for unit tests only, and must be explicitly
disclosed.

---

# WS-5 · MT5 order / position / account semantics

### GAP-050 · Netting vs hedging is not modelled · **S1** · **L**

**Current → Target:** one position per order, `sim-position-<client_order_id>`
(`execution/engine.py:303`) → position accounting follows `ACCOUNT_MARGIN_MODE`.

On `ACCOUNT_MARGIN_MODE_RETAIL_NETTING`, MT5 **merges** all volume in a symbol into a single position
with a volume-weighted average entry price; an opposing order reduces or reverses it. Sim always
hedges. On a netting account, sim diverges from reality at the **second order in the same symbol** —
different position count, different margin, different close behaviour, different P&L attribution.

**Fix:** read `ACCOUNT_MARGIN_MODE` from the account snapshot and implement both position models in
the engine. Netting: merge on same-side fill (VWAP entry), reduce on opposing fill, reverse when the
opposing volume exceeds the position. Hedging: current behaviour. This is the largest single item in
the register and deserves its own design note.

---

### GAP-051 · No stop-out / margin call · **S1** · **M**

**Current → Target:** margin checked only on OPEN (`accounting/ledger.py:150-161`) → margin level
monitored per tick, with margin call and forced liquidation.

MT5 force-closes positions when margin level falls below `ACCOUNT_MARGIN_SO_SO`. Sim never
liquidates, so a strategy that would have been stopped out survives to recover — the single most
optimistic bias available in a backtest.

**Fix:** after `_observe_excursions`, compute `margin_level = equity / used_margin × 100` and compare
against `ACCOUNT_MARGIN_SO_CALL` / `ACCOUNT_MARGIN_SO_SO`, honouring `ACCOUNT_STOPOUT_MODE`
(percent vs money). On breach, liquidate in MT5's order (largest loss first) until the level
recovers. Journal `margin_call` and `stop_out` events.

---

### GAP-052 · GTC is rejected in sim but accepted live · **S2** · **S**

**Current → Target:** `SIM_UNSUPPORTED_FILL_POLICY` for GTC → GTC pending orders rest and trigger.

Your own usage example places a GTC pending order (`tests/legacy/07_trading.py`, `"time_in_force":
"GTC"`). The same request succeeds on `mt5` and fails on `sim` — a direct violation of the
"route is the only difference" premise.

**Fix:** implement `ORDER_TIME_GTC`, `ORDER_TIME_DAY`, `ORDER_TIME_SPECIFIED`,
`ORDER_TIME_SPECIFIED_DAY`. Resting orders already have a home in `_pending`; they need expiry
semantics per type rather than the current single `valid_until` comparison
(`execution/engine.py:548`).

---

### GAP-053 · MT5's order/deal/position triad is collapsed · **S2** · **M**

**Current → Target:** receipt + position → `order` (the instruction), `deal` (the execution), and
`position` (the resulting exposure) as distinct, queryable entities with MT5's own ticket semantics.

Sim synthesizes `sim-deal-<client_order_id>-<sequence>` (`execution/engine.py:164`) as a formality.
There is no deal history, so `history_deals_get`-equivalent queries have nothing to return, and
commission/swap attribution per deal is not reproducible.

**Fix:** model deals explicitly in the engine, with `DEAL_ENTRY_IN` / `DEAL_ENTRY_OUT` /
`DEAL_ENTRY_INOUT` / `DEAL_ENTRY_OUT_BY`, and expose sim equivalents of `history_orders_get` and
`history_deals_get`. This is what makes sim *feel* like MT5 to a strategy author.

---

### GAP-054 · Position ticket scheme is not MT5-shaped · **S3** · **XS**

**Current → Target:** `sim-position-<client_order_id>` → monotonic integer tickets.

MT5 tickets are `ulong` counters, and plenty of strategy code treats them as such (sorting,
comparison, storage as integers).

**Fix:** issue monotonic integers from a per-run counter seeded deterministically from `run_id`.
Keep the string form only in journal payloads.

---

### GAP-055 · No requote modelling · **S2** · **S**

**Current → Target:** price is whatever the tick says → configurable requote on market orders when
price moves beyond `deviation`.

MT5 market orders carry a `deviation` (max slippage in points); if the market moves further between
request and execution, the server returns `TRADE_RETCODE_REQUOTE` or `TRADE_RETCODE_PRICE_CHANGED`.
Sim always fills at the computed price.

**Fix:** carry `deviation` on the intent, and once latency exists (GAP-035) compare the price at
request time with the price at execution time. Beyond `deviation` → requote retcode.

---

### GAP-056 · Protective orders have no sim lifecycle · **S2** · **M**

**Current → Target:** SL/TP are plain position attributes evaluated inline
(`execution/matching.py:69-107`) → Trading's `protective_orders/` module governs them on both routes.

`build_protective_order_plan`, `resize_protective_orders`, and `verify_protective_order_coverage`
never run in sim. Coverage gaps that would be caught live are invisible in backtests.

**Fix:** falls largely out of GAP-010. Then represent SL/TP as real resting orders in the engine
rather than position fields, so the same coverage verification applies.

---

### GAP-057 · Trade ownership / orphan detection absent in sim · **S3** · **S**

**Current → Target:** `magic = strategy_id` stamped on the position (`execution/engine.py:314`) →
`trade_ownership/` registry and `detect_orphaned_trade` run identically.

**Fix:** falls out of GAP-010; then assign ownership in `_record_receipt` on both routes.

---

# WS-6 · Stochastic realism

> Requested explicitly: randomised slippage (with event-clustering), generated spread, and
> everything else that narrows the gap to live fills.
>
> **Constraint that governs this whole workstream:** randomness must be *seeded and reproducible*.
> `SimulationBacktestRequestV1` already carries `seed` — it is currently **unused**. Every stochastic
> component must draw from a PRNG derived from `(seed, run_id, symbol, tick.sequence)` so the same
> request always produces the same path, and `request_hash` keeps its meaning.

### GAP-060 · The `realism/` module is built but wired to nothing · **S2** · **M**

**Current → Target:** `realism/` (latency, queue, pricing, races, views — FEAT-SIM-12) is never
imported by `run/` or `execution/` → it is the execution model for canonical runs.

Canonical runs use only `ExecutionProfile.slippage_mode ∈ {none, fixed_points}`
(`execution/pricing.py:51`). `LatencyProfile`, `QueueModel`, `QueueFillResult`, and
`RealisticExecutionResult` already exist and are unused.

**Fix:** make the realism providers first-class inputs to `prepare_run_context` and have
`price_order` / `match_order` consume them. This is the foundation for GAP-061..064 — do it first.

---

### GAP-061 · `seed` is carried but never used · **S2** · **XS**

**Current → Target:** `request.seed` accepted and hashed into `config_hash`, then ignored → seeds a
per-run PRNG hierarchy.

**Fix:** derive independent streams per concern so adding one stochastic component does not shift
another's draws:
`slippage_rng = PCG64(hash(seed, run_id, "slippage", symbol))`, likewise for `spread`, `latency`,
`requote`, `fill_probability`. Record the seed and the stream names in `RealismDisclosure`.

---

### GAP-062 · Spread is inherited from the tick series, never modelled · **S2** · **M**

**Current → Target:** spread is whatever Data's tick generator produced → an explicit spread model
calibrated to MT5.

For `real` tick models the spread is genuine. For derived models (`ohlc_m1`, `trading_bar`,
`generated`) the spread is synthesized by Data with no MT5 grounding — and those are the models most
backtests use.

**Fix:** add a spread model to `realism/pricing.py` supporting:
- **fixed** — constant points (baseline)
- **stochastic** — draw around a mean with configurable variance, floored at `SYMBOL_SPREAD` minimum
- **session-dependent** — widen at rollover, thin during overlap; parameterized per session from
  GAP-046
- **event-clustered** — see GAP-063

Calibrate from the live MT5 `spread` field, sampled and stored as a run artifact.

---

### GAP-063 · No slippage model, and no event clustering · **S2** · **M**

**Current → Target:** deterministic adverse `fixed_slippage_points × point_value`
(`execution/pricing.py:153`) → a stochastic model with regime clustering.

**Fix:** layered model in `realism/pricing.py`:

1. **Base** — draw from a right-skewed distribution (log-normal or gamma), asymmetric by side,
   bounded by `maximum_slippage_points`. Adverse-biased, but permit occasional positive slippage as
   MT5 does.
2. **Volume-dependent** — scale with `order_volume / tick_volume` using the existing `QueueModel`.
3. **Event clusters** — a two-state Markov regime (calm / stressed) with configurable transition
   probabilities; the stressed regime multiplies both spread and slippage variance and raises the
   requote probability. Drive transitions either stochastically or from a **scheduled economic
   calendar**, which is the higher-fidelity option and connects to
   `trading/monitoring/economic_events.py` — already present and currently unused by sim.
4. **Gap events** — weekend and news gaps, where the next tick opens beyond `maximum_gap_points`.
   The `SIM_GAP_UNCROSSABLE` path already exists (`execution/matching.py:228-232`) but can only fire
   on supplied data; the model should be able to generate them.

Every draw is seeded (GAP-061), and the realized values must be journalled per fill so a run can be
audited after the fact.

---

### GAP-064 · No latency model — the simulated clock is instantaneous · **S2** · **M**

**Current → Target:** submit and fill occur at the same tick → `LatencyProfile` shifts execution to
the first tick at or after `request_time + total_latency`.

`LatencyProfile` already models seven distinct domains (`market_ms`, `client_ms`, `network_ms`,
`broker_ms`, `venue_ms`, `report_ms`, `processing_ms`) and is unused. Zero latency is the second
most optimistic bias in a backtest after missing stop-outs.

**Fix:** apply latency in the engine's submit path so the fill price is taken from the tick at the
delayed timestamp. This unblocks GAP-055 (requote) and GAP-004 (real timeout paths). Latency should
itself be stochastic — a base profile plus a seeded jitter distribution, widened in the stressed
regime from GAP-063.

---

### GAP-065 · Realized realism values are not disclosed per fill · **S3** · **S**

**Current → Target:** `RealismDisclosure` reports model *names* only
(`run/orchestrator.py:194-202`) → per-fill realized slippage, spread, latency, and regime.

Without this, a stochastic run cannot be audited or explained.

**Fix:** extend the `fill_proposed` journal event with `realized_slippage_points`,
`realized_spread_points`, `realized_latency_ms`, `regime`, and the PRNG stream position. Aggregate
distributions into the run report.

---

# WS-7 · Terminology, errors, and return shapes

> Requested: *"MT5 semantics and terminology should be exact in sim — inputs/args,
> exceptions/errors, results/returns."*

### GAP-070 · Sim error codes are `SIM_*`, not MT5 retcodes · **S2** · **M**

**Current → Target:** `SIM_INSUFFICIENT_MARGIN`, `SIM_INVALID_VOLUME`, `SIM_GAP_UNCROSSABLE`, … →
MT5 `TRADE_RETCODE_*` as the primary identity, with the `SIM_*` code retained as an internal
category.

Suggested mapping (verify each against the MT5 documentation for your build before implementing):

| Sim condition | MT5 retcode |
|---|---|
| insufficient free margin | `TRADE_RETCODE_NO_MONEY` |
| volume below min / above max / off step | `TRADE_RETCODE_INVALID_VOLUME` |
| aggregate volume over `volume_limit` | `TRADE_RETCODE_LIMIT_VOLUME` |
| SL/TP inside stops or freeze level | `TRADE_RETCODE_INVALID_STOPS` |
| price off tick / invalid | `TRADE_RETCODE_INVALID_PRICE` |
| tick outside trade session | `TRADE_RETCODE_MARKET_CLOSED` |
| symbol `trade_mode` disallows the side | `TRADE_RETCODE_TRADE_DISABLED` |
| filling policy unsupported for symbol | `TRADE_RETCODE_INVALID_FILL` |
| price moved beyond `deviation` | `TRADE_RETCODE_REQUOTE` / `TRADE_RETCODE_PRICE_CHANGED` |
| partial fill under IOC/RETURN | `TRADE_RETCODE_DONE_PARTIAL` |
| successful fill | `TRADE_RETCODE_DONE` |
| position already closed | `TRADE_RETCODE_POSITION_CLOSED` |
| dispatch timeout | `TRADE_RETCODE_TIMEOUT` |

**Fix:** add the retcode to `SimulationError` and to the receipt's `response_classification`, so a
strategy branching on retcodes behaves identically on both routes. Keep `SIM_*` for the internal
catalogue and error-category routing.

---

### GAP-071 · Sim result shapes are not MT5 result shapes · **S2** · **M**

**Current → Target:** `ExecutionReceipt` only → an MT5-shaped result available alongside it.

MT5 returns `OrderSendResult` with `retcode`, `deal`, `order`, `volume`, `price`, `bid`, `ask`,
`comment`, `request_id`, `retcode_external`. A strategy written against MT5 reads those fields.

**Fix:** have the sim authority produce an `OrderSendResult`-shaped payload that the MT5 adapter's
own mapping layer converts into an `ExecutionReceipt` — reusing
`brokers/metatrader/mapping.py` rather than parallel-implementing it. Sim then produces receipts
through *literally the same code* as live, which is the strongest possible parity guarantee.

---

### GAP-072 · No sim equivalents of MT5's read API · **S3** · **M**

**Current → Target:** `engine.snapshot()` returns a bespoke mapping → sim exposes
`positions_get`, `orders_get`, `history_orders_get`, `history_deals_get`, `account_info`,
`symbol_info`, `symbol_info_tick` equivalents with MT5 field names.

**Fix:** implement the read side of the MT5 adapter surface against engine state. Depends on GAP-053
for deal history. This is what makes "running sim feels exactly like running MT5" true in practice
rather than just at the mutation boundary.

---

### GAP-073 · Envelope flags differ by route · **S4** · **XS**

**Current → Target:** `places_trade` / `requires_network` are `False` for sim
(`actions/orders.py:84-85`) → keep them honest but stop consumers branching on route.

These flags are *correct* — sim genuinely places no trade and needs no network. The problem is
downstream code reading them as a proxy for "is this real".

**Fix:** leave the flags accurate; add an explicit `route` extension and audit consumers to branch on
that instead.

---

# Suggested sequencing

Dependencies matter more than severity here — several S1s are cheap once their prerequisite lands.

### Phase 0 — Defects (days)
`GAP-001` swap · `GAP-002` execution positions · `GAP-005` OHLC validation

Independent, cheap, and currently producing wrong numbers. `GAP-002` is a live bug.

### Phase 1 — Path convergence (weeks) — *the keystone*
`GAP-010` → `GAP-013` → `GAP-012` → `GAP-011`

Then WS-2 largely collapses: `GAP-021`, `GAP-026`, `GAP-027`, `GAP-057` fall out for free, and
`GAP-020`, `GAP-022`, `GAP-023` become small.

### Phase 2 — MT5 as the calculation authority (weeks)
`GAP-034` cache **first**, then `GAP-030` margin · `GAP-031` profit · `GAP-032` mark-to-market ·
`GAP-033` tick values

Do the cache first or you will lose reproducibility and not notice until a replay diverges.

### Phase 3 — MT5 symbol and account semantics (weeks)
`GAP-040` specification → `GAP-041`..`GAP-047` · then `GAP-050` netting/hedging · `GAP-051` stop-out

`GAP-050` and `GAP-051` are the two largest fidelity wins in the register and both depend on
`GAP-040`.

### Phase 4 — Order model completeness (weeks)
`GAP-052` GTC · `GAP-053` order/deal/position triad · `GAP-003` partial fills · `GAP-056` protective
orders · `GAP-054` tickets

### Phase 5 — Stochastic realism (weeks)
`GAP-060` wire `realism/` → `GAP-061` seed → `GAP-064` latency → `GAP-062` spread → `GAP-063`
slippage + clustering → `GAP-055` requote → `GAP-065` disclosure

Latency before spread/slippage: requote and timeout semantics depend on a non-instantaneous clock.

### Phase 6 — Surface mirroring (weeks)
`GAP-070` retcodes · `GAP-071` result shapes · `GAP-072` read API · `GAP-073` flags · `GAP-024`,
`GAP-025` fault injection

---

## Two design tensions worth deciding early

**1 · Determinism vs live MT5 delegation.**
The simulator's stated contract is bit-reproducible runs with no network access on the execution
path (`README.md` §1, "Does not own"). Routing margin and profit through MT5 breaks that literally.
`GAP-034` (the calculation cache) is the reconciliation: MT5 is consulted once, the answers are
hashed into the run manifest, and every replay is hermetic. Decide explicitly whether a cache miss
on replay is a hard failure (recommended) or a silent re-fetch.

**2 · Where the mirror boundary sits.**
Two viable architectures:

- **(a) Sim as a Brokers adapter.** Implement a `simulator` provider inside
  `app/services/brokers/` exposing the same `BrokerAdapter` v1 contract as MT5. Trading then has
  *no* sim-specific code at all — `simulation_dispatch` disappears, and `route` genuinely becomes
  the only difference.
- **(b) Sim as a Trading dispatch target.** Current design; keep `simulation_dispatch` and close the
  gaps individually.

**(a) is the stronger answer to the stated goal** and would subsume `GAP-023`, `GAP-024`, `GAP-026`,
`GAP-071`, `GAP-073` outright — sim would be validated by the same capability gate, classified by the
same classifier, and mapped by the same mapping layer. It is also a larger refactor and cuts across
the ownership boundary in `docs/PROJECT.md` (Brokers owns adapters; Simulation owns simulated
fills). Worth resolving before Phase 1, since `GAP-010` is implemented differently under each.
