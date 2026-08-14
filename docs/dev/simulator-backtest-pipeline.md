# Simulator Backtest Pipeline — Full Flow

Package: `app/services/simulator`
Entry point: `run_backtest(request, auth_context, dependencies) -> SimulationResult`
Implementation: `app/services/simulator/run/orchestrator.py`

---

## 0. Layer map

```
HTTP  POST /api/v1/simulation/run          app/services/api/workstation/simulation/routes.py
  │   (auth + permission + Idempotency-Key)
  ▼
API orchestration  _run("run", dto, auth)  app/services/api/workstation/simulation/orchestration.py
  │   builds SimulationBacktestRequestV1 via create_simulation_value(...)
  ▼
Package gate  run_backtest(...)            app/services/simulator/__init__.py  (lazy _operation)
  │   wraps in StandardResponse envelope
  ▼
Orchestrator  run_backtest / _run_backtest_with_evidence
              app/services/simulator/run/orchestrator.py
  │
  ├── validation/   → fail-closed gates
  ├── timeline/     → tick clock
  ├── accounting/   → AccountLedger
  ├── execution/    → EventDrivenExecutionEngine (matching + pricing)
  ├── journal/      → JournalWriter (hash-chained JSONL)
  ├── state/        → SimulationStateStore (sim_runs + artifacts)
  └── reporting/    → SimulationResult, report.md, result.json, manifest.json
```

Alternate callers of the same `run_backtest`:

- `app/services/optimization/execution/adapter.py` — Optimization's own internal backtest-adapter port (`simulation_runner: SimulationRunner = run_backtest`).
- `run_portfolio_backtest` (`run/portfolio.py`) — runs N components through the same path and reconciles them in `PortfolioAggregateLedger`.
- `run_fast_research` (`run/research.py`) — explicitly non-canonical; short-circuits after the timeline.

---

## 1. Composition — build the dependency bundle (once, at startup)

Nothing in the simulator imports Data, Indicators, Strategy, Risk, or Trading directly for the run path. Everything arrives as injected callables.

### 1a. State store

`build_simulation_state_store(artifact_root=...)` → `_DurableSimulationStateStore`
(`state/runtime.py`)

Owns:

- `sim_runs` relational lifecycle rows via `persistence/` (`create/read/update/delete.py`)
- `<artifact_root>/<run_id>/journal.jsonl.partial` → `journal.jsonl` (atomic publish)

### 1b. Dependency bundle

`build_simulation_run_dependencies(state_store=, artifact_root=, fast_research_enabled=, ports=)`
(`run/dependencies.py`)

Requires **exactly** these 11 ports — no more, no fewer, all callable, else `ValueError`:

| Port | Called as | Supplies |
|---|---|---|
| `audit` | `persist_audit_event(event)` | Data-owned durable audit persistence |
| `market_data` | `load_market_data(request)` | Data `MarketDataset v1` (bars/source) |
| `tick_series` | `generate_tick_series(dataset, request)` | Data-owned tick `MarketDataset` |
| `indicators` | `calculate_indicators(dataset, request)` | Indicators `IndicatorSeries v1` |
| `strategy` | `evaluate_strategy(dataset, indicators, request)` | Strategy `TradeIntent v1` tuple |
| `risk` | `review_risk(intents, request)` | Risk `RiskDecision v1` tuple |
| `order_intents` | `build_order_intents(decisions, request)` | Trading `OrderIntent v1` tuple |
| `execution_profile` | `resolve_execution_profile(request)` | `ExecutionProfile` |
| `symbol_specification` | `resolve_symbol_specification(request)` | `SymbolSpecification` |
| `cost_model` | `resolve_cost_model(request)` | `ExecutionCostModel` |
| `fx_evidence` | `resolve_fx_evidence(ids)` | Data `FXConversionEvidence v1` |

The API layer wraps both calls in `build_api_simulation_dependencies(...)` and the result is injected into the FastAPI graph as `simulation.run_source`.

---

## 2. Request construction

`SimulationBacktestRequestV1` (`run/contracts.py`) — frozen, `extra="forbid"`, reference-only.

Fields: `contract_version="v1"`, `schema_id="simulation.backtest_request.v1"`, `request_id`/`workflow_id`/`correlation_id`, strategy ref+version+hash, data ref+version+hash, tick-generation ref+version+hash, execution-profile ref+version+hash, risk-policy ref+version+hash, `symbol`, `timeframe`, `start`/`end` (aware UTC), bounded JSON-safe `parameters`, positive `Decimal initial_balance`, `account_currency`, `asset_class="FX"`, `seed`, `runtime_profile`, `execution_route="sim"`, `canonical`, `config_hash`.

`config_hash` comes from `SimulationBacktestRequestV1.calculate_config_hash(payload)`, which hashes everything **except** `request_id`, `workflow_id`, `correlation_id`, `config_hash` — so trace IDs don't change run identity.

Forbidden inline: DataFrames, provider objects, raw code, secrets, unknown fields.

---

## 3. Governance gates (before any work)

In `_run_backtest_with_evidence`:

1. **`_validate_auth`** — `request.request_id/workflow_id/correlation_id` must equal the `AuthContext` values (`SIM_INVALID_CONFIG`), and the principal must hold `simulation:run` in scopes or permissions (`SIM_UNSUPPORTED_OPERATION`).
2. **`validate_run_inputs(payload)`** (`validation/validate.py`)
   - rejects any key in `{code, source_code, module_path, file_path, callable}` → `SIM_ARBITRARY_CODE_REJECTED`
   - non-empty `symbol` → `SIM_MISSING_SYMBOL`
   - `end >= start` → `SIM_INVALID_DATE_RANGE`
   - all 18 `_REQUIRED_INPUT_FIELDS` present → `SIM_INVALID_CONFIG`
   - payload must survive `canonical_json` → `SIM_INVALID_CONFIG`
3. **`validate_phase_one_scope(payload)`**
   - `asset_class == "FX"` → else `SIM_UNSUPPORTED_ASSET_CLASS`
   - `runtime_profile ∈ {simulation, fast_research}`, `execution_route == "sim"` → else `SIM_UNSUPPORTED_OPERATION`
   - `fast_research` may not claim `canonical=True` → `SIM_UNSUPPORTED_FEATURE`
4. **Run identity** — `request_hash = canonical_digest(full payload)`; `run_id = f"sim-{request_hash[:32]}"`.
5. **Audit** — `emit_simulation_audit(..., "simulation.run_started", request.start, {request_hash, run_id})`.

---

## 4. Idempotency resolution

`resolve_idempotent_run(request_id, request_hash, lookup)` (`journal/replay.py`) reads the `sim_runs` row via `state_store.load_run(request_id)`.

- **No row** → proceed.
- **Row with a different `request_hash`** → `SIM_RUN_ID_CONFLICT` (the request ID is bound to different material).
- **Row `status == "completed"`** → replay path: rehydrate `result_payload`, rebuild each fill through Trading's `create_execution_receipt(**item)`, `SimulationResult.model_validate(...)`. Any structural problem → `SIM_CHECKPOINT_INCOMPATIBLE`. Emits `simulation.run_replayed` and returns immediately — **the engine never runs twice**.

Otherwise: `state_store.record_idempotency(request_id, request_hash, run_id, "started")` writes the `started` row. Everything after this is inside the try/except that flips the row to `failed`.

---

## 5. `prepare_run_context` — the deterministic half

`prepare_run_context(request, dependencies, run_id) -> RunContext`

Strict order:

1. **`load_market_data(request)`** → source `MarketDataset` (bars).
2. **`generate_tick_series(source_dataset, request)`** → tick `MarketDataset`. Simulation constructs **no** ticks itself; Data owns tick derivation.
3. **`validate_market_data(tick_dataset, MarketDataValidationContext(...))`** with `maximum_staleness=timedelta(0)` and `allowed_tick_models=APPROVED_TICK_MODELS`:
   - recomputed dataset digest must equal `request.data_hash` → `SIM_DATA_CHECKSUM_MISMATCH`
   - `dataset.start <= requested_start` and `dataset.end >= requested_end` → `SIM_DATA_COVERAGE_INSUFFICIENT`
   - `available_at <= evaluated_at` → `SIM_LOOKAHEAD_DETECTED`
   - zero staleness tolerance → `SIM_DATA_STALE`
   - `quality_decision ∉ {rejected, not_evaluated}` → `SIM_DATA_SCHEMA_INVALID`
   - records monotonic + unique timestamps, valid OHLC, non-negative spread → `SIM_DATA_NON_MONOTONIC` / `SIM_DATA_DUPLICATE_TIMESTAMP` / `SIM_DATA_OHLC_INVALID` / `SIM_DATA_SPREAD_NEGATIVE`
   - `data_kind == "ticks"` and tick model approved → `SIM_UNSUPPORTED_TICK_MODEL`
   - returns `ValidatedMarketDataEvidence(data_hash, dataset_schema_id, tick_model, record_count, validated_at)`
4. **`build_tick_timeline(tick_dataset)`** (`timeline/timeline.py`) → `tuple[Tick, ...]`
   - approved models: `real`, `trading_bar`, `ohlc_m1`, `generated`
   - every record must be a tick record with real `bid` **and** `ask` → `SIM_SPREAD_MISSING`
   - derived (non-`real`) ticks must carry `source_bar_time`, `tick_index_in_bar`, `bar_phase` → `SIM_DATA_SCHEMA_INVALID`
   - each `Tick` gets a monotonic `sequence`; timeline re-checked for monotonic + unique timestamps
5. **`_require_nonempty_timeline`** → empty timeline is `SIM_DATA_COVERAGE_INSUFFICIENT`.
6. **`JournalWriter(state_store, run_id, request_id, correlation_id)`** created and the **first** event written:
   `run_started` with `{config_hash, data_hash, engine_version}` at `timeline[0].timestamp`.
   *A caller that prepares a context owns the resulting journal.*
7. **`resolve_symbol_specification`** → `SymbolSpecification(minimum_volume, maximum_volume, volume_step, contract_size, leverage)`.
8. **`resolve_cost_model`** → `ExecutionCostModel(commission_per_lot_per_side, long_swap_per_lot_rollover, short_swap_per_lot_rollover)`.
9. **`resolve_execution_profile`** → `ExecutionProfile(slippage_mode, fixed_slippage_points, point_value, price_quantum, maximum_slippage_points, maximum_gap_points, liquidity_mode, participation_rate, sessions)`.
10. **`AccountLedger(initial_balance, account_currency, specification, cost_model)`**.
11. **`EventDrivenExecutionEngine(ledger, writer, profile, "simulation-engine-v1")`**.
12. **Signal chain**, all through injected ports:
    `calculate_indicators(source_dataset, request)`
    → `evaluate_strategy(source_dataset, indicators, request)`
    → `review_risk(strategy_intents, request)`
    → `build_order_intents(risk_decisions, request)`
13. **Deterministic ordering**: intents sorted by `(created_at, client_order_id)`.

Note the chain runs against the **source (bar) dataset**, while execution runs against the **tick timeline** — the data view and the execution view are deliberately separate.

Returns `RunContext(timeline, evidence, writer, ledger, profile, engine, order_intents)`.

---

## 6. Timeline advancement — the execution half

```python
unsent = list(order_intents)
receipts = []
submit_orders_before(engine, unsent, receipts, timeline[0].timestamp)
advance_run_timeline(engine, timeline, unsent, receipts)
```

- **`submit_orders_before`** — drains every intent created strictly before the first tick.
- **`advance_run_timeline(engine, timeline, unsent, receipts, start_index=0, max_ticks=None)`** — per tick, in this exact order:
  1. `engine.execute_tick(tick)` → extend `receipts`
  2. drain every `unsent` intent with `created_at <= tick.timestamp` via `engine.submit_order(...)`
  Returns the next unexecuted index. Defaults run the whole timeline; a live/what-if session calls it in bounded increments and gets **byte-identical** journal, receipts, and result hash.

### 6a. `submit_order(intent)`

- route must be `sim` → `SIM_INVALID_CONFIG`
- duplicate `client_order_id` → `SIM_RUN_ID_CONFLICT`
- builds an `accepted` `ExecutionReceipt` via Trading's `create_execution_receipt` (authority `"simulation"`, deterministic `receipt_id = sha256({intent_id, status, sequence})`)
- journals `order_accepted`, parks the intent in `_pending`

### 6b. `execute_tick(tick)` — one tick, fixed order

1. **Monotonicity guard** — `tick.timestamp` and `tick.sequence` must both strictly exceed the last seen → `SIM_DATA_NON_MONOTONIC`.
2. **Session gate** — `_week_second(tick)` must fall inside some `SessionInterval` of the profile. Outside → journal `tick_outside_session`, return `()`. *Skipped, not fatal* — Data may legitimately return closed-market ticks inside a requested range.
3. **`_observe_excursions`** (pre) — per open position, movement = `(bid − entry)·vol` for BUY, `(entry − ask)·vol` for SELL; updates `mae`/`mfe`; sums unrealized → `ledger.mark_to_market(unrealized)`.
4. **`_apply_protective_exits`** — `evaluate_protective_exit(position, tick)`:
   - exit price = `bid` for BUY, `ask` for SELL
   - BUY stop hits on `exit_price <= stop_loss`, target on `exit_price >= take_profit` (mirrored for SELL)
   - both crossed on one tick → `SAME_TICK_PRIORITY = ("STOP_LOSS", "TAKE_PROFIT", "PENDING_ACTIVATION")`, so **STOP_LOSS wins**
   - triggers full-volume `_close(..., exit_reason)`
5. **Pending-order sweep** — for each pending order:
   - `validate_intent_timing(intent.created_at, tick.timestamp)` → `SIM_FEATURE_LOOKAHEAD_DETECTED` if evidence post-dates execution
   - expired (`tick.timestamp >= intent.valid_until`) → `cancelled` receipt, removed
   - else `match_order(intent, tick, profile, stop_limit_armed=armed)`
   - `pending` → re-park with updated `armed`; anything terminal → `_apply_match`, then removed
6. **`_observe_excursions`** (post) — re-mark after fills/closes.
7. **Equity observation** — append `(tick.timestamp, account["equity"])` to `equity_observations`.
8. Return the tuple of receipts produced at this tick.

### 6c. `match_order` — pure, deterministic (`execution/matching.py`)

1. `time_in_force ∈ {FOK, IOC}` → else `SIM_UNSUPPORTED_FILL_POLICY`.
2. **Trigger** (`_triggered`), evaluated on `ask` for BUY / `bid` for SELL:
   - `MARKET` → always
   - `LIMIT` → `side_price <= price` (BUY) / `>=` (SELL); missing price → `SIM_INVALID_CONFIG`
   - `STOP` → `side_price >= stop_price` (BUY) / `<=` (SELL)
   - `STOP_LIMIT` → latches `armed` once the stop is hit, then requires the limit condition; `armed` persists across ticks
   - not triggered → `MatchResult(status="pending", ...)`
3. **Price** (`price_order`, `execution/pricing.py`):
   - base = `tick.ask` (BUY) / `tick.bid` (SELL); non-finite or ≤ 0 → `SIM_INVALID_PRICE`
   - adverse slippage = `fixed_slippage_points × point_value`, applied **against** the order (added for BUY, subtracted for SELL)
   - configured > maximum → `SIM_SLIPPAGE_EXCEEDED`
   - quantized to `price_quantum` with `ROUND_HALF_EVEN`
4. **Gap check** — for `STOP`/`STOP_LIMIT`, `|execution_price − stop_price| / point_value` must be ≤ `maximum_gap_points` → `SIM_GAP_UNCROSSABLE`.
5. **Liquidity** (`_available_quantity`):
   - `unbounded` → full approved volume
   - `tick_volume` → `tick.volume × participation_rate`; missing volume or mismatched `volume_unit` → `SIM_LIQUIDITY_UNAVAILABLE`
6. **Fill policy** — `FOK` with insufficient liquidity → fully `cancelled`, no price. Otherwise `filled` / `partial` / `cancelled` by `filled` vs `approved_volume`.

Simulation **never resizes** an approved volume; Risk already sized it and Trading packed it.

### 6d. `_apply_match` — state mutation

- journals `fill_proposed {client_order_id, quantity, price}` **before** touching money
- `ledger.apply_fill(LedgerFill(action="OPEN", side, volume, price))` → returns itemized `{commission, swap, total}`
- creates the position `sim-position-<client_order_id>` carrying side, volume, entry price/time, SL/TP, magic (`strategy_id`), attributed commission/swap, `mae=mfe=0`
- builds the terminal receipt, journals `order_outcome` with the full receipt dump, records it in `_orders` and `_deals`

### 6e. `AccountLedger.apply_fill` (`accounting/ledger.py`)

- `normalize_volume(volume, specification)` against min/max/step
- `calculate_execution_costs(...)` from the cost model (commission per lot per side, swap × rollover multiplier) — costs are **debits**, added to balance
- **OPEN**: `margin_delta = calculate_margin(volume, price, contract_size, leverage)`; requires `margin_delta <= balance + unrealized + costs.total − used_margin` → else `SIM_INSUFFICIENT_MARGIN`
- **CLOSE**: `margin_released <= used_margin` → else `SIM_ACCOUNT_INVARIANT_BROKEN`
- commits `balance += gross_profit + costs.total`, `used_margin += delta − released`; non-finite balance or negative margin → `SIM_ACCOUNT_INVARIANT_BROKEN`
- accumulates `commission_total`, `swap_total`, `gross_profit_total`

`snapshot()` returns an immutable `MappingProxyType`: `balance, equity (= balance + unrealized), used_margin, free_margin (= equity − used_margin), unrealized, commission, swap, gross_profit, account_currency`.

### 6f. `_close` — position exit

- exit price = `bid` for BUY, `ask` for SELL (never mid)
- `gross_profit = (exit − entry) × qty` for BUY, `(entry − exit) × qty` for SELL
- `margin_released = used_margin × qty / current_volume` (pro-rata)
- journals `position_close_proposed {position_id, quantity, price, exit_reason}` first
- `ledger.apply_fill(LedgerFill(action="CLOSE", ...))`
- appends a `ClosedTradeRecord` with pro-rata (`share = qty / current_volume`) commission, swap, MAE, MFE
- partial closes reduce `volume`; full closes delete the position

---

## 7. Terminal liquidation

After the timeline is exhausted:

```python
terminal_state = engine.snapshot()
for position in terminal_state["positions"]:
    engine.close_position(position_id, position["volume"])
```

`close_position` closes at the **current (final) tick's** bid/ask with `exit_reason="REQUESTED"`. This is disclosed in the result as a limitation: *"Terminal liquidation uses the final observed bid or ask."*

---

## 8. Journal finalization

`journal/writer.py` — `JOURNAL_FORMAT = "jsonl-v1"`, `JOURNAL_FSYNC_INTERVAL = 100`, sidecar disabled.

1. `writer.append("run_completed", {"receipt_count": len(receipts)}, timeline[-1].timestamp)`
2. `writer.finalize()`

Every `append` builds material `{run_id, sequence, occurred_at, event_type, payload | {request_id}, previous_hash, correlation_id, causation_id, schema_version="v1"}`, adds `event_hash = canonical_digest(material)`, validates as `JournalEvent`, serializes with `canonical_json`, and hands it to `state_store.append_journal`. The store re-parses, re-canonicalizes, asserts contiguous `sequence`, and appends one line to `journal.jsonl.partial`. Group commit `fsync`s every 100 events.

`finalize()` refuses an empty or already-finalized journal, flushes the tail, then `state_store.finalize_journal(run_id, sequence, tail_hash)`:

- re-reads and re-validates every line
- asserts event count and tail hash match
- `fsync` then `partial.replace(final)` — **atomic publication** to `journal.jsonl`
- returns the SHA-256 of the canonical bytes

The chain is verifiable later by `replay_journal(path, reducer)`: sequence continuity, `previous_hash` linkage (genesis = 64 zeros), recomputed `event_hash`, and `sequence == 0` must be a `run_started` carrying `{config_hash, data_hash, engine_version}`. Any break → `SIM_CHECKPOINT_INCOMPATIBLE`.

### Journal event vocabulary

`run_started`, `order_accepted`, `tick_outside_session`, `fill_proposed`, `order_outcome`, `position_close_proposed`, `run_completed`.

---

## 9. Result construction

`_completed_result(...)` reads **every** monetary field from the completed ledger snapshot — no constants:

```
net_profit = gross_profit + commission + swap
assert net_profit == final_balance − request.initial_balance   # else SIM_ACCOUNT_INVARIANT_BROKEN
```

Produces `SimulationResult` (`reporting/contracts.py`, `schema_id="simulation.result.v1"`):

- identity: `run_id`, `request_hash`, `config_hash`, `data_hash`, `engine_version="simulation-engine-v1"`, `status="completed"`
- references: `journal_ref = "<run_id>/journal.jsonl"`, `artifact_manifest_ref = "<run_id>/manifest.json"`
- evidence: `fills` (Trading receipts only, filtered by `is_execution_receipt`), `closed_trades`
- `accounting`: `AccountingSummary(final_balance, final_equity, used_margin, free_margin, gross_profit, commission, swap, net_profit)`
- `diagnostics: ()`
- `realism`: `RealismDisclosure(tick_model, slippage_model, liquidity_model, session_model="explicit_utc_intervals", data_quality="passed", assumptions, limitations)`

---

## 10. Artifact publication

`_publish_result(result, artifact_root, created_at=timeline[-1].timestamp)` — note the timestamp is the **final tick time**, not wall clock, so artifacts are reproducible.

Under `<artifact_root>/<run_id>/`:

| File | Built by | Media type |
|---|---|---|
| `journal.jsonl` | already published by `finalize_journal` | `application/x-ndjson` |
| `result.json` | `build_json_report(result)` — `canonical_json(model_dump)` | `application/json` |
| `report.md` | `build_markdown_report(result)` — deterministic, **no Analytics metrics** | `text/markdown` |
| `manifest.json` | `build_artifact_manifest(run_root, (journal, result, report), created_at)` | — |

Each write goes through `_write_completed_text`: write to `<name>.tmp`, `flush`, `os.fsync`, `Path.replace` — atomic, no torn files. Failure → `SIM_PERSISTENCE_FAILED`.

The manifest resolves each path `strict=True`, asserts containment under the approved root, rejects duplicate names, and asserts the set/order exactly equals `CANONICAL_ARTIFACT_TYPES`. Each `ArtifactEntry` carries `relative_path`, `media_type`, `size_bytes`, `sha256`, `created_at`.

---

## 11. Lifecycle close-out

1. `state_store.record_idempotency(request_id, request_hash, run_id, "completed", result.model_dump())` — the `sim_runs` row moves `started → completed` with the full result payload. Transitions are monotonic: an identical replay is a no-op, a terminal row cannot change, a mismatched `request_hash`/`run_id` raises `SIM_RUN_ID_CONFLICT`.
2. `emit_simulation_audit(..., "simulation.run_completed", timeline[-1].timestamp, {request_hash, run_id})`.
3. Returns `(result, engine.equity_observations)` internally; the public `run_backtest` discards the equity series and returns only `SimulationResult`.

---

## 12. Failure paths

| Where | Behaviour |
|---|---|
| Any `SimulationError` inside the try block | `record_idempotency(..., "failed")`, re-raise |
| Any other exception | logged with traceback, `record_idempotency(..., "failed")`, re-raised as `SIM_INTERNAL_ERROR` ("Simulation failed safely") |
| `run_backtest` wrapper | catches `SimulationError`, emits `simulation.run_failed` audit at `request.end`, re-raises |
| Package gate (`simulator/__init__.py`) | wraps everything in a `StandardResponse` envelope; `unwrap_simulation_response` unpacks it |
| API layer | `to_simulation_error_payload(error)` → bounded public code; `SIMULATION_RUNTIME_UNAVAILABLE` → HTTP 503 |

**A failed or incomplete run is never published as a `SimulationResult`.** Partial journals stay as `.partial` and are never atomically promoted.

---

## 13. Determinism guarantees

The same `request_hash` always reproduces the same run because:

- `run_id` is derived from the request hash, not from time or a counter
- intents are sorted by `(created_at, client_order_id)` before submission
- receipt IDs are `sha256({intent_id, status, sequence})`
- artifact `created_at` is the final tick timestamp
- `canonical_json` / `canonical_digest` everywhere; `Decimal` arithmetic with `ROUND_HALF_EVEN` throughout
- no network access, no wall clock, no RNG on the execution path
- Data owns tick derivation; Simulation constructs no prices of its own
- the journal is a hash chain, so any divergence is detectable by replay

---

## 14. Variant paths

### Fast research (`run/research.py`)

Same auth + `validate_run_inputs` + `validate_phase_one_scope`, then requires `runtime_profile == "fast_research"`, `canonical is False`, and `dependencies.fast_research_enabled`. Loads market data → tick series → timeline, then computes only mid-quote returns `(mid_t − mid_{t−1}) / mid_{t−1}`. Returns `FastResearchResult`. **No ledger, no engine, no journal, no fills, no artifacts, no promotion evidence.**

### Portfolio (`run/portfolio.py`)

Projects a `PortfolioBacktestRequestV1` into ordered `PortfolioComponentRequest`s, runs each through the same single-run path, and reconciles them in `PortfolioAggregateLedger`: each component's `initial_balance` must equal its allocated balance, allocations must sum exactly to the portfolio balance, and the component count must match — else `SIM_AGGREGATE_UNRECONCILED`. Publishes `PortfolioSimulationResult` (`simulation.portfolio_result.v1`).

### Incremental / live what-if

`prepare_run_context` + repeated `advance_run_timeline(..., start_index=, max_ticks=)` drives the identical engine in bounded increments. The per-tick order is unchanged, so a run completed in N calls is indistinguishable from one completed in a single call.
