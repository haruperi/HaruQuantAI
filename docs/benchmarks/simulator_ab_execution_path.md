# Simulator A/B Execution-Path Analysis

## Purpose

This document maps the complete business-relevant execution paths of the old
HaruQuant event-driven Simulator example and the new HaruQuantAI canonical
Simulation example. It defines stable measurement boundaries for an A/B
benchmark so optimization decisions can be based on evidence rather than
aggregate wall time.

The comparison uses genuine read-only MT5 history. It does not treat current
performance results as outcome-parity evidence because important strategy,
data-volume, and execution differences remain.

## Contents

1. [Executive summary](#executive-summary)
2. [Observed baseline](#observed-baseline)
3. [Current parity limitations](#current-parity-limitations)
4. [Old execution path](#old-execution-path)
5. [New execution path](#new-execution-path)
6. [Structural comparison](#structural-comparison)
7. [A/B instrumentation design](#ab-instrumentation-design)
8. [Controlled-test requirements](#controlled-test-requirements)
9. [Recommended experiment sequence](#recommended-experiment-sequence)
10. [Interpretation rules](#interpretation-rules)
11. [Source reference index](#source-reference-index)

## Executive summary

The latest normal unprofiled comparison on 2026-08-16 was:

| Measurement | Old event-driven example | New canonical Example 7 |
|---|---:|---:|
| Normal engine/example time | 2.9519 seconds | 10.3491 seconds |
| Process wall time | 7.5612 seconds | 16.3657 seconds |
| Canonical execution kernel | 2.9519 seconds | 4.7888 seconds |
| Relative execution time | 1.0x | 1.62x |
| Source bars returned | 5,000 | 6,710 |
| Approximate measurement bars | 4,500 | 6,210 |
| Derived ticks | 18,000 | 24,840 |
| Closed-trade records | 32 | 42 |

The new run processes about 38% more ticks and genuinely covers the requested
year. That difference cannot explain the complete runtime gap.

The observed new hot path is dominated by canonical Python work inside the
tick and strategy loops:

| Operation | Observed call count |
|---|---:|
| Tick executions | 24,840 |
| Point-in-time cycle calls | 24,840 |
| Full strategy evaluations | 6,210 |
| Canonical signals constructed | 24,840 |
| Pydantic `validate_python` calls | 319,461 |
| Response metadata builds | 124,752 |
| Response-oriented wrapper calls | More than 112,000 |
| Logger emission-path calls | About 1.86 million |

The observed old event-driven configuration did not remain exclusively inside
its compact Numba turbo kernel. Its profile showed a Python tick loop and an
unexpected repeated MT5 dependency:

| Old operation | Observed call count | Profiled cumulative time |
|---|---:|---:|
| Scheduled callback checks | 18,000 | 3.337 seconds |
| Position monitoring | 1,619 | 3.147 seconds |
| Strict profit calculations | 1,683 | 3.144 seconds |
| MT5 `terminal_info()` | 3,439 | 3.026 seconds |

This means both implementations have avoidable overhead. The new system has
more canonical safeguards, while the old system repeatedly reaches into MT5
during a preloaded-data backtest.

## Observed baseline

### Compact canonical runtime result

The approved internal-runtime correction retained canonical public contracts
while allowing the already validated orchestrator to call private raw engine
and ledger operations. The registered naive strategy is canonically bound once,
then emits compact active action names from its parity-tested incremental EMA
state. Strategies without an explicitly tested compact implementation continue
through the full canonical signal path, including martingale, pyramiding,
hedging, and other multi-action strategies.

| Measurement | Before (s) | After (s) | Reduction |
|---|---:|---:|---:|
| Canonical Simulation B16-B25 | 27.0881 | 4.7888 | 82.32% |
| Complete Example 7 B28 | 34.1646 | 10.3491 | 69.70% |
| Process wall | 39.7208 | 16.3657 | 58.80% |

The successful before/after runs both retained 6,710 source bars, 24,840
canonical ticks, 42 closed-trade records, ending equity `10079.900000000`, and
net PnL `79.900000000`. The optimized Simulation kernel is 1.67 times the old
event-driven 2.9519-second time while processing 38% more ticks. The old time
scaled linearly to 24,840 ticks is approximately 4.12 seconds, placing the new
4.79-second kernel about 16% above the workload-normalized reference.

Optimization stopped at this gate because the strong target of at most six
seconds was achieved. No tick, point-in-time decision, provider check, fill,
accounting effect, journal event, terminal liquidation, or Analytics step was
removed.

### 2026-08-16 low-overhead stage baseline

All values below are from successful normal runs, not profiler time. `Included`
means the current accumulator measures the containing group without adding a
second nested clock; it must not be interpreted as an independently measured
duration.

| Old path | Duration (s) | Measurement status |
|---|---:|---|
| A01-A02 startup/configuration | 4.5942 | Process wall less printed Example 1-3 durations; includes imports and provider startup |
| A03-A14 vectorized path | 0.7834 | Direct old Example 2 timer |
| A03-A14 event-driven path | 2.9519 | Direct old Example 3 timer |
| A01-A14 complete catalogue | 7.5612 | External process watchdog wall clock |

| New path | Duration (s) | Measurement status |
|---|---:|---|
| B01-B05 startup, demo snapshot, and account facts | 5.5562 | Process wall less B28 total; includes imports, API settings, MT5 connection, specification/account reads |
| B06-B10 market retrieval and quality | 1.6363 | Direct accumulator |
| B11-B15 request and canonical tick generation | 4.1467 | Direct accumulator |
| B16-B25 canonical Simulation | 27.0881 | Direct accumulator |
| B26-B27 Analytics report | 0.3066 | Direct accumulator |
| B28 rendering and complete example | 34.1646 | Inclusive example timer; rendering is included, not isolated |
| B01-B28 complete process | 39.7208 | External process watchdog wall clock |

The current direct accumulator deliberately avoids per-tick clocks. Individual
B16-B25 rows remain attributable through the existing profile evidence below,
while their normal-time total is the directly measured 27.0881 seconds. A
future optimization benchmark should add counters or sampling before adding a
clock to every tick, signal, response, or validation call.

### Current result and workload evidence

| Evidence | Old event-driven | New canonical |
|---|---:|---:|
| Requested dates | 2025-01-01 through 2025-12-31 | 2025-01-01 through 2025-12-31 |
| Source bars | 5,000 (provider call remains capped) | 6,710 (complete interval including warmup) |
| Derived ticks | 18,000 | 24,840 |
| Closed trades | 32 | 42 |
| Strategy averages | EMA 20/50/200 | EMA 20/50/200 |
| Final equity | 10,036.82 | 10,079.90 |

The dates and visible strategy inputs now match, but dataset parity does not:
the unchanged old provider call returns only 5,000 bars and therefore processes
18,000 ticks. The new path genuinely covers the year and must not be shortened
to make its wall time appear closer.

### Runtime interpretation

| Run | Normal time | cProfile time | Profiled function calls |
|---|---:|---:|---:|
| Old full usage catalogue | 10.143 seconds | 11.821 seconds | 7,774,514 |
| Old Example 3 only, inside catalogue | 2.989 seconds | 4.356 seconds | Included above |
| New Example 7 | 26.909 seconds | 104.725 seconds | 225,671,408 total profile calls |

cProfile disproportionately slows Python-heavy validation, response, logging,
and serialization paths. Normal wall time is the performance baseline. Profile
call counts and call relationships are attribution evidence; profiled wall time
must not be compared directly with normal wall time.

### Workload-normalized reference

The old example processed 18,000 ticks. Scaling its 2.989-second normal runtime
linearly to 24,840 ticks produces an approximate reference of 4.12 seconds.
This is not a prediction, but it is a more useful lower-bound comparison than
2.989 seconds.

## Current parity limitations

The visible configuration is substantially closer, but the current results are
not computationally equivalent.

| Dimension | Old | New | Consequence |
|---|---|---|---|
| Requested period | Warmup Dec 2024; measurement 2025 | Same | Frontend parity |
| Retrieved bars | Limited to 5,000 | Complete 6,710 | Old run truncates the year |
| Measurement ticks | 18,000 | 24,840 | Different workload |
| Strategy | `TrendFollowingStrategy` | `naive-ma-trend` | Different registered implementation |
| Average type | EMA 20/50/200 | SMA 20/50/200 | Different signals and trades |
| Declared volume | 0.1 lot | 0.1 lot | Visible parity |
| Executed volume | Path-dependent; turbo kernel hardcodes 0.01 | 0.1 | Must be measured from actual fills |
| Spread | Fixed 10 points | Fixed 10 points | Intended parity |
| Slippage | Declared fixed 1 point | Applied fixed 1 point | Old selected path must be verified |
| Contract size | 100,000 | 100,000 | New accounting application requires audit |
| Commission | 7 per lot per side convention | 7 per lot per side | Intended parity |
| Point-in-time proof | Implicit dataframe alignment | Explicit timestamp and availability | Different assurance level |
| Persistence | Result-oriented | Journal, artifacts, idempotency | Additional new work |
| Reporting | Small summary | Full Analytics report | Additional new work |

### Accounting hypothesis requiring verification

The new closed-trade evidence contains examples where raw price difference is
multiplied by volume but appears not to be multiplied by the EURUSD contract
size. The observed total was almost entirely commission:

| Value | Observation |
|---|---:|
| Closed records | 44 |
| Commission per round trip at 0.1 lot | 1.40 USD |
| Total commission | -61.60 USD |
| Reported net PnL | -61.598374 USD |
| Implied total price contribution | About 0.001626 USD |

This is a hypothesis, not an established defect. A focused accounting test must
verify price difference, side, volume, contract size, gross PnL, commission,
and net PnL before performance results are compared.

## Old execution path

Entry point:
`C:/Users/rharu/AppDev/HaruQuant/tests/usage/app/services/08_simulator.py`

### Old path overview

```text
Process startup and imports
  -> construct frontend configuration
  -> retrieve MT5 bars through the old Data gateway
  -> parse SimulationConfig
  -> prepare EURUSD dataframe
  -> calculate all EMA signals over the dataframe
  -> generate four trading-bar ticks per retained bar
  -> select event-driven execution path
  -> process each tick and scheduled callback
  -> monitor positions and calculate PnL
  -> materialize trades and equity
  -> construct result
  -> build and print symbol summary
```

### Old stage index

| ID | Stage | Primary boundary | Required measurement |
|---|---|---|---|
| A01 | Startup and imports | Module entry | Import duration by package |
| A02 | Frontend configuration | Example function | Construct, parse, validate |
| A03 | MT5 retrieval | `fetch_real_ohlcv_data` | Cache, provider, conversion |
| A04 | Simulation preparation | `prepare`, `prepare_symbol` | Frame and symbol preparation |
| A05 | Strategy signals | `TrendFollowingStrategy.on_bar` | EMA and signal-column timings |
| A06 | Tick generation | `TicksGenerator.generate` | Four-tick generation costs |
| A07 | Event engine entry | `_run_event_driven_simulation_impl` | Setup and array extraction |
| A08 | Execution-path selection | Fast-path predicate | Selected path and reasons |
| A09 | Per-tick loop | Scheduled callbacks | Per-turn aggregate timings |
| A10 | Position monitoring | `monitor_positions` | Price, MT5, PnL checks |
| A11 | Entry execution | Position creation | Actual volume and entry costs |
| A12 | Exit/accounting | Position close | Gross, costs, net PnL |
| A13 | Result construction | Runner result | Trades, equity, model costs |
| A14 | Reporting | Symbol summary | Summary and rendering |

### A01 - Startup and imports

The process imports the Simulator façade, configuration models, strategy
registry, MT5 broker client, Data gateway, indicators, risk, reporting,
database, and utility packages.

| Measurement | Meaning |
|---|---|
| `A01.import_total` | Complete module-import duration |
| `A01.strategy_registry_import` | Strategy registry and strategy modules |
| `A01.simulation_import` | Simulation engine and runner modules |
| `A01.mt5_import` | MetaTrader package and broker adapter |
| `A01.other_import` | Remaining application imports |

The full profile attributed approximately 5.5 seconds to import relationships.
This is process-start cost and must be separated from warm-service execution.

### A02 - Frontend configuration

The event-driven example declares EURUSD H1, December warmup, the 2025
measurement period, EMA 20/50/200, 10,000 USD initial balance, leverage 100,
contract size 100,000, 10-point spread, one-point slippage, and 0.1 lot.

| Step | Check or implementation |
|---:|---|
| 1 | Construct nested configuration dictionary |
| 2 | Call `Engine.run()` |
| 3 | Parse dictionary into `SimulationConfig` |
| 4 | Validate engine type |
| 5 | Validate account values |
| 6 | Validate source, symbol, timeframe, and interval |
| 7 | Validate strategy name and parameters |
| 8 | Validate tick, spread, slippage, and position-size configuration |

Measurements: `A02.config_construct`, `A02.config_parse`, and
`A02.config_validate`.

### A03 - MT5 retrieval

```text
fetch_real_ohlcv_data
  -> Data service get_data
  -> gateway.execute_gateway_dataframe_request
  -> cache lookup
  -> MT5 connection/read
  -> dataframe conversion
```

| Step | Check or implementation |
|---:|---|
| 1 | Normalize symbol and timeframe |
| 2 | Build cache identity |
| 3 | Inspect cache freshness |
| 4 | Select the MT5 provider |
| 5 | Verify MT5 connection readiness |
| 6 | Retrieve historical rates |
| 7 | Convert provider rows to dataframe records |
| 8 | Normalize the datetime index |
| 9 | Normalize expected OHLCV columns |
| 10 | Construct cache records where applicable |

| Measurement | Counter or duration |
|---|---|
| `A03.cache_lookup` | Cache lookup time |
| `A03.cache_decision` | Fresh/stale/miss decision |
| `A03.provider_resolution` | MT5 adapter selection |
| `A03.mt5_connect` | Readiness and connection time |
| `A03.mt5_copy_rates` | Historical retrieval time |
| `A03.row_conversion` | Broker-row conversion |
| `A03.dataframe_construction` | Dataframe materialization |
| `A03.cache_write` | Cache persistence |
| `bars_requested` | Requested rows |
| `bars_received` | Returned rows |
| `bars_in_measurement` | Rows retained for execution |

The old provider boundary returned only 5,000 bars for the requested interval.

### A04 - Simulation preparation

```text
Engine.run
  -> SimulationRunner.run
  -> configuration parsing
  -> prepare
  -> prepare_symbol
```

The preparer accepts the preloaded dataframe, locates EURUSD, validates OHLCV
fields, establishes the datetime index, applies interval boundaries, resolves
point value, resolves the strategy class, and instantiates the strategy.

| Measurement | Meaning |
|---|---|
| `A04.config_to_runtime` | Parsed configuration to runner state |
| `A04.symbol_prepare` | Complete per-symbol preparation |
| `A04.frame_validation` | Dataframe checks |
| `A04.interval_filter` | Warmup and measurement filtering |
| `A04.symbol_specification` | Point and contract information |
| `A04.strategy_resolution` | Registry lookup |
| `A04.strategy_instantiation` | Strategy construction and initialization |

### A05 - EMA strategy calculation

The old strategy calculates the complete signal dataframe before tick
execution.

| Order | Operation |
|---:|---|
| 1 | Initialize `TrendFollowingStrategy` |
| 2 | Calculate EMA 20 |
| 3 | Calculate EMA 50 |
| 4 | Calculate EMA 200 |
| 5 | Project previous EMA 20 and EMA 50 |
| 6 | Detect upward and downward crossovers |
| 7 | Apply EMA 200 trend filter |
| 8 | Populate entry signal column |
| 9 | Populate exit signal column |

| Rule | Definition |
|---|---|
| Long entry | EMA20 crosses above EMA50 and EMA50 is above EMA200 |
| Short entry | EMA20 crosses below EMA50 and EMA50 is below EMA200 |
| Long exit | EMA20 crosses below EMA50 |
| Short exit | EMA20 crosses above EMA50 |

Measurements: `A05.ema20`, `A05.ema50`, `A05.ema200`,
`A05.previous_values`, `A05.crossovers`, `A05.signal_columns`, and
`A05.total`.

### A06 - Old trading-bar tick generation

For every retained measurement bar, the generator creates four ticks.

| Step | Operation |
|---:|---|
| 1 | Resolve OHLC waypoint order |
| 2 | Resolve tick phases |
| 3 | Apply fixed spread to produce bid/ask |
| 4 | Assign intrabar timestamps |
| 5 | Project signal columns to ticks |
| 6 | Attach symbol and timeframe |
| 7 | Materialize the tick dataframe |

Observed: approximately 4,500 bars produced 18,000 ticks.

Measurements: `A06.generator_setup`, `A06.waypoint_generation`,
`A06.spread_application`, `A06.timestamp_generation`,
`A06.signal_projection`, `A06.dataframe_materialization`, and `A06.total`.

### A07 - Event engine entry

```text
SimulationRunner._run_prepared
  -> Engine.run_prepared
  -> Engine.run_event_driven
  -> _run_event_driven_simulation_impl
```

| Step | Check or implementation |
|---:|---|
| 1 | Reject missing data |
| 2 | Validate positive position size |
| 3 | Install commission in account state |
| 4 | Install slippage settings |
| 5 | Require dataframe-like input |
| 6 | Require bid and ask columns |
| 7 | Build case-insensitive column mapping |
| 8 | Expose bid/ask as NumPy arrays |
| 9 | Extract entry and exit signals |
| 10 | Extract pending, SL, TP, symbol, phase, and timestamp arrays |
| 11 | Resolve actual run position size |

### A08 - Execution-path selection

The engine evaluates whether the Numba turbo kernel is safe:

| Predicate | Required for turbo path |
|---|---|
| Run schedule | Disabled |
| Risk subsystem | Disabled |
| Strategy | Not stateful |
| Numba | Available |
| Engine symbol mapping | Available |

The benchmark must record the selected path and every predicate. The observed
profile contained the Python callback and position-monitoring path, so it must
not be described as an exclusively compiled execution.

### A09 - Old per-tick loop

Executed 18,000 times.

| Turn | Check or implementation |
|---:|---|
| 1 | Read bid and ask |
| 2 | Resolve symbol |
| 3 | Update latest market state |
| 4 | Run scheduled callbacks |
| 5 | Inspect pending orders |
| 6 | Inspect open positions |
| 7 | Check SL/TP |
| 8 | Read precomputed entry signal |
| 9 | Read precomputed exit signal |
| 10 | Open, close, or remain neutral |
| 11 | Update selected equity snapshots |
| 12 | Notify configured observers |
| 13 | Increment processed-tick count |

Required aggregate measurements:

| Name | Meaning |
|---|---|
| `A09.tick_total` | Complete tick-turn time |
| `A09.market_state_update` | Price-state mutation |
| `A09.scheduled_callbacks` | Callback dispatch |
| `A09.pending_orders` | Pending-order processing |
| `A09.position_monitor` | Position checks |
| `A09.signal_read` | Signal array access |
| `A09.entry_handling` | Entry work |
| `A09.exit_handling` | Exit work |
| `A09.equity_snapshot` | Equity updates |
| `A09.observers` | Observer callbacks |

### A10 - Position monitoring

Observed calls:

| Operation | Calls | Profiled cumulative time |
|---|---:|---:|
| `monitor_positions` | 1,619 | 3.147 seconds |
| `_strict_order_calc_profit` | 1,683 | 3.144 seconds |
| MT5 `terminal_info()` | 3,439 | 3.026 seconds |

The path inspects positions, obtains current prices, evaluates SL/TP, calculates
floating or realized PnL, detects exit signals, and closes positions. Repeated
`terminal_info()` calls are a high-priority old-path measurement because the
run already has preloaded data and symbol configuration.

### A11 - Entry execution

| Step | Operation |
|---:|---|
| 1 | Find or allocate a position slot |
| 2 | Resolve BUY or SELL |
| 3 | Use ask for BUY or bid for SELL |
| 4 | Assign ticket |
| 5 | Resolve actual volume |
| 6 | Assign stop-loss and take-profit |
| 7 | Store active position state |

The turbo kernel contains a hardcoded `0.01` volume while the frontend declares
`0.1`. The selected execution path and actual fill volume must be captured in
every benchmark.

### A12 - Exit and accounting

| Step | Operation |
|---:|---|
| 1 | Select executable exit bid or ask |
| 2 | Calculate signed price difference |
| 3 | Multiply by volume |
| 4 | Multiply by contract size |
| 5 | Calculate two-sided commission |
| 6 | Update balance |
| 7 | Materialize completed trade |
| 8 | Release active position slot |

Every closed trade must expose entry, exit, side, volume, contract size, gross
PnL, commission, and net PnL for parity reconciliation.

### A13 - Result construction

The engine resolves final balance, finalizes the equity curve, converts trade
arrays/state to trade objects, assembles metrics, attaches the processed-tick
count, and constructs the result wrapper.

Measurements: `A13.trade_conversion`, `A13.equity_conversion`,
`A13.metrics`, and `A13.result_model`.

### A14 - Old reporting

The example prints balance, equity, and trade count, then calls
`build_symbol_summary()`, groups trades by EURUSD, sums reported PnL, and prints
the result. It does not produce the same full Analytics report as the new path.

Measurements: `A14.summary_build` and `A14.output_render`.

## New execution path

Entry point: `tests/legacy/08_simulator.py::example_07_backtest_simulation`

### New path overview

```text
Process startup and imports
  -> compose verified dev/demo provider context
  -> build canonical Data request
  -> retrieve and normalize genuine MT5 bars
  -> run canonical Data quality inspection
  -> separate warmup and measurement bars
  -> build initial Simulation request
  -> generate canonical trading-bar ticks
  -> hash-bind the exact tick dataset
  -> build isolated dependencies and authority
  -> enter canonical asynchronous Simulation
  -> validate request and idempotency state
  -> prepare timeline, ledger, engine, provider, and journal
  -> execute every tick
  -> build point-in-time evidence at every decision instant
  -> evaluate registered strategy for every newly visible bar
  -> execute entries, exits, and terminal liquidation
  -> finalize journal and Simulation artifacts
  -> build Analytics report
  -> render metrics, caveats, and closed trades
```

### New stage index

| ID | Stage | Primary boundary | Required measurement |
|---|---|---|---|
| B01 | Startup and imports | Module entry | Imports by domain |
| B02 | Provider composition | Runtime context | Settings, credentials, demo proof |
| B03 | Data request | `_get_dataset` | Request construction/validation |
| B04 | Data retrieval/quality | Data pipeline | Provider through canonical dataset |
| B05 | Warmup/measurement | Usage projection | Record filtering and copies |
| B06 | Initial request | Request builder | Hash and contract validation |
| B07 | Tick generation | Data tick derivation | Kernel through tick models |
| B08 | Exact request binding | Usage composition | Tick hash and final request |
| B09 | Dependencies/authority | Usage composition | State, evaluator, hashes, auth |
| B10 | Async Simulation entry | Public API | Authentication and idempotency |
| B11 | Run preparation | `prepare_run_context` | Timeline, ledger, engine, journal |
| B12 | Timeline advancement | Main loop | All tick-turn components |
| B13 | Tick execution | `execute_tick` | Execution checks and responses |
| B14 | Point-in-time view | Evaluation cursor | Visibility and cache behavior |
| B15 | Strategy cycle gate | Usage dependency | Neutral versus full evaluation |
| B16 | Strategy evidence | Usage dependency | Window and evidence construction |
| B17 | Strategy binding | Usage dependency | Invariants and context |
| B18 | SMA strategy | Registered evaluator | Math and causal checks |
| B19 | Signal contracts | Strategy mechanics | Four signal constructions |
| B20 | Logging | Cross-cutting | Calls, checks, actual emissions |
| B21 | Result interpretation | Usage dependency | Snapshot and action choice |
| B22 | Entry execution | Trading/Simulation | Intent through queued order |
| B23 | Exit/accounting | Simulation engine | Close, ledger, closed trade |
| B24 | Terminal liquidation | Orchestrator | End-policy closure |
| B25 | Simulation finalization | Orchestrator | Result, journal, artifacts |
| B26 | Analytics input | Usage composition | Source and configuration |
| B27 | Analytics report | Analytics public API | Complete metric calculation |
| B28 | Rendering | Usage output | Metrics, caveats, trades |

### B01 - Startup and imports

The standalone example imports the API composition, Data, Strategy, Trading,
Simulator, Analytics, Utils, and caller-owned SQLite state infrastructure.

| Measurement | Meaning |
|---|---|
| `B01.import_total` | Complete import duration |
| `B01.api_import` | API composition imports |
| `B01.data_import` | Data imports |
| `B01.strategy_import` | Strategy imports |
| `B01.simulator_import` | Simulator imports |
| `B01.analytics_import` | Analytics imports |
| `B01.test_composition_import` | Caller-owned state composition |

### B02 - Provider runtime composition

| Order | Check or implementation |
|---:|---|
| 1 | Read persisted system settings |
| 2 | Resolve effective environment |
| 3 | Require `dev` |
| 4 | Compose MT5 broker configuration |
| 5 | Resolve credential reference without exposing its value |
| 6 | Require `demo` destination |
| 7 | Load typed provider settings |
| 8 | Enter Data provider settings context |
| 9 | Enter broker connection resolver context |

Measurements: `B02.settings_read`, `B02.environment_check`,
`B02.broker_config`, `B02.credential_resolution`, `B02.demo_check`, and
`B02.context_install`.

### B03 - Canonical market-data request

The request binds MT5, EURUSD, H1 bars, December 2024 warmup through the end of
2025, limit 10,000, disabled cache, research context, warning quality behavior,
and Decimal-string precision.

Checks cover source ID, symbol, data kind, timeframe, UTC interval, positive
limit, maximum limit, cache policy, quality policy, precision policy, and
request identity.

Measurements: `B03.request_construct` and `B03.request_validation`.

### B04 - Canonical Data retrieval and quality

```text
get_market_data
  -> response boundary
  -> _fetch_market_dataset_raw
```

| Order | Check or implementation |
|---:|---|
| 1 | Validate operation metadata |
| 2 | Resolve MT5 source descriptor |
| 3 | Verify source capability |
| 4 | Enforce record limit |
| 5 | Verify/run Data migrations as required |
| 6 | Build cache key |
| 7 | Explicitly bypass cache |
| 8 | Resolve provider adapter |
| 9 | Resolve demo connection |
| 10 | Read MT5 historical bars |
| 11 | Normalize timestamps and OHLCV values |
| 12 | Normalize source identity and availability |
| 13 | Construct canonical OHLCV records |
| 14 | Validate ordering |
| 15 | Detect duplicates |
| 16 | Detect missing intervals |
| 17 | Ignore ordinary weekend closures |
| 18 | Load persisted Economic Calendar coverage |
| 19 | Match relevant EUR/USD events |
| 20 | Require full interval coverage |
| 21 | Classify supported closures |
| 22 | Preserve event IDs, providers, and matching basis |
| 23 | Retain unmatched intervals as `MISSING_BARS` |
| 24 | Detect price spikes |
| 25 | Calculate quality score and decision |
| 26 | Construct quality report |
| 27 | Construct canonical market dataset |
| 28 | Wrap Data response |

| Measurement | Meaning |
|---|---|
| `B04.source_descriptor` | Source lookup |
| `B04.migrations` | Persistence readiness |
| `B04.cache_bypass` | Cache decision |
| `B04.provider_resolution` | Adapter/connection composition |
| `B04.mt5_read` | Genuine provider retrieval |
| `B04.raw_normalization` | Raw-to-canonical conversion |
| `B04.record_validation` | Record model validation |
| `B04.ordering_check` | Ordering proof |
| `B04.duplicate_detection` | Duplicate inspection |
| `B04.gap_detection` | Gap discovery |
| `B04.weekend_classification` | Weekend removal |
| `B04.calendar_coverage` | Calendar coverage proof |
| `B04.calendar_matching` | Closure qualification |
| `B04.spike_detection` | Price anomaly inspection |
| `B04.quality_score` | Score and decision |
| `B04.dataset_build` | Dataset model construction |
| `B04.response_wrap` | Public Data response |

### B05 - Warmup and measurement projection

The complete 6,710-bar dataset is retained for point-in-time strategy context.
The usage program selects 6,210 records inside 2025 for tick generation, copies
quality counts, and builds a measurement dataset.

| Counter | Observed value |
|---|---:|
| Source bars | 6,710 |
| Warmup bars | 500 |
| Measurement bars | 6,210 |

Measurements: `B05.measurement_filter`, `B05.quality_copy`, and
`B05.dataset_copy`.

### B06 - Initial Simulation request

| Order | Operation |
|---:|---|
| 1 | Generate request/workflow/correlation IDs |
| 2 | Bind strategy identity |
| 3 | Bind Data and tick-generation identities |
| 4 | Bind execution and risk identities |
| 5 | Build provider revision binding |
| 6 | Calculate initial authority-state hash |
| 7 | Set `sim`, canonical mode, and terminal liquidation |
| 8 | Calculate configuration hash |
| 9 | Validate `SimulationBacktestRequest` |

Measurements: `B06.ids`, `B06.authority_state_hash`,
`B06.provider_binding`, `B06.config_hash`, and `B06.request_validation`.

### B07 - Canonical tick generation

| Order | Check or implementation |
|---:|---|
| 1 | Validate `trading_bar` model |
| 2 | Validate fixed-spread model |
| 3 | Validate 10 spread points |
| 4 | Validate point value |
| 5 | Require bar input |
| 6 | Resolve H1 duration |
| 7 | Resolve four tick offsets |
| 8 | Resolve OHLC waypoint order |
| 9 | Scale Decimal values for kernel representation |
| 10 | Generate kernel arrays |
| 11 | Validate kernel lengths and phases |
| 12 | Convert values back to Decimal |
| 13 | Construct canonical tick records |
| 14 | Assign timestamp and `available_at` |
| 15 | Assign bid, ask, phase, and lineage |
| 16 | Construct 24,840-record tick dataset |
| 17 | Construct tick quality evidence |
| 18 | Wrap Data response |

Measurements: `B07.contract_validation`, `B07.kernel_input`,
`B07.kernel_execution`, `B07.kernel_validation`, `B07.decimal_conversion`,
`B07.tick_model_construction`, `B07.dataset_construction`, and
`B07.response_wrap`.

### B08 - Exact tick/request binding

The example dumps the exact tick dataset, calculates its canonical hash,
installs strategy parameters, sets genuine first/last tick boundaries, aligns
provider revision coverage, recalculates the complete request hash, and
revalidates the request.

Measurements: `B08.tick_dump`, `B08.tick_hash`, `B08.request_update`,
`B08.config_hash`, and `B08.final_request_validation`.

### B09 - Dependencies and authority

| Order | Operation |
|---:|---|
| 1 | Create temporary state root |
| 2 | Create artifact root |
| 3 | Initialize SQLite Simulation state |
| 4 | Initialize audit path |
| 5 | Store exact tick dataset |
| 6 | Create strategy evaluator probe |
| 7 | Read and hash evaluator source |
| 8 | Hash strategy parameters |
| 9 | Create Strategy validation policy |
| 10 | Create simulation-only authorization context |

Measurements: `B09.temp_state`, `B09.sqlite_init`, `B09.strategy_probe`,
`B09.source_hash`, `B09.parameter_hash`, `B09.validation_policy`, and
`B09.auth_context`.

### B10 - Canonical asynchronous Simulation entry

```text
asyncio.run
  -> run_backtest_async public boundary
  -> orchestrator.run_backtest_async
  -> _run_backtest_with_evidence_async
```

Initial checks validate authentication, request identity, sim route, canonical
mode, execution/calculation bindings, tick lineage, market evidence class,
decision policy, certification target, and terminal liquidation. The
orchestrator persists a start audit event, resolves idempotency, and records the
run as started.

Measurements: `B10.async_entry`, `B10.auth`, `B10.request_contracts`,
`B10.phase_scope`, `B10.audit_start`, `B10.idempotency_lookup`, and
`B10.idempotency_start`.

### B11 - Run-context preparation

| Order | Check or implementation |
|---:|---|
| 1 | Load source dataset |
| 2 | Confirm symbol and timeframe |
| 3 | Load exact generated tick dataset |
| 4 | Verify exact tick hash |
| 5 | Create market-validation context |
| 6 | Validate model, ordering, availability, hash, and coverage |
| 7 | Build 24,840-value Simulator timeline |
| 8 | Require non-empty timeline |
| 9 | Initialize journal writer |
| 10 | Append `run_started` |
| 11 | Resolve symbol specification |
| 12 | Resolve commission/swap model |
| 13 | Resolve execution profile |
| 14 | Load and validate provider revisions |
| 15 | Initialize account ledger |
| 16 | Initialize event-driven execution engine |
| 17 | Load and hash-check initial authority state |
| 18 | Load account activity |
| 19 | Validate exclusive ownership |
| 20 | Construct run context |

Profiled `build_tick_timeline()` cumulative time was 5.028 seconds. Required
measurements should separate tick-to-Simulator-model conversion from tuple
materialization and validation.

### B12 - Timeline advancement

Executed for all 24,840 ticks.

| Turn | Check or implementation |
|---:|---|
| 1 | Submit intents created before the tick boundary |
| 2 | Execute canonical tick |
| 3 | Validate and unwrap tick response |
| 4 | Accumulate receipts |
| 5 | Build point-in-time visible evidence |
| 6 | Invoke owner-supplied strategy cycle |
| 7 | Await result |
| 8 | Validate and unwrap result |
| 9 | Accumulate mutation or neutral evidence |
| 10 | Submit newly actionable orders at correct system time |

Measurements: `B12.pre_tick_orders`, `B12.execute_tick`,
`B12.execute_tick_response`, `B12.point_in_time`, `B12.strategy_cycle`,
`B12.strategy_response`, `B12.post_cycle_orders`, and `B12.total`.

### B13 - Canonical tick execution

Observed: 24,840 calls and 49,680 excursion observations.

| Turn | Check or implementation |
|---:|---|
| 1 | Validate sequence |
| 2 | Validate monotonic timestamp |
| 3 | Resolve provider revision |
| 4 | Validate trading session |
| 5 | Update latest market price |
| 6 | Inspect pending orders |
| 7 | Validate intent timing |
| 8 | Validate fill policy and trade mode |
| 9 | Validate filling mode |
| 10 | Validate volume bounds and step |
| 11 | Validate liquidity policy |
| 12 | Calculate fixed adverse slippage |
| 13 | Quantize execution price |
| 14 | Fill or reject eligible orders |
| 15 | Apply ledger mutations |
| 16 | Update position state |
| 17 | Observe MAE/MFE before and after processing |
| 18 | Construct receipts |
| 19 | Wrap response |

Measurements use the corresponding `B13.*` names for every row above.

### B14 - Point-in-time visibility

Executed 24,840 times.

| Turn | Check or implementation |
|---:|---|
| 1 | Bisect source timestamps |
| 2 | Bisect source `available_at` values |
| 3 | Select the smaller visible prefix |
| 4 | Reject an empty prefix |
| 5 | Reuse cached view if visible count is unchanged |
| 6 | Otherwise slice visible records |
| 7 | Copy quality counts |
| 8 | Copy point-in-time dataset view |
| 9 | Invoke evaluation cycle |

Invalid ordering uses the correctness-preserving full-filter fallback.

Required counters: cursor calls, cache hits, prefix changes, fallback calls,
and future-record rejections.

### B15 - Strategy-cycle gate

The cycle is called 24,840 times. It selects the latest visible bar, verifies
availability, checks the minimum history, compares the latest bar with the last
evaluated bar, and returns neutral for duplicate intrabar evaluations.

| Counter | Observed value |
|---|---:|
| Cycle calls | 24,840 |
| Full bar evaluations | 6,210 |
| Duplicate-bar neutral returns | 18,630 |

Measurements: `B15.latest_record`, `B15.lookahead_check`,
`B15.minimum_history`, `B15.duplicate_gate`, and `B15.full_evaluation`.

### B16 - Bounded strategy evidence

For every new bar, the composition selects the last 200 records, copies
quality counts, copies the bounded dataset, retrieves strategy binding, creates
the execution context, creates signal evidence, and crosses the Strategy public
boundary.

Measurements: `B16.window_slice`, `B16.quality_copy`, `B16.dataset_copy`,
`B16.strategy_binding`, `B16.execution_context`, and `B16.signal_evidence`.

### B17 - Strategy binding

Invariant manifest, reference, configuration, and evaluator objects are created
once. A new execution context is created for each of 6,210 evaluated bars.

| Operation | Calls | Profiled cumulative time |
|---|---:|---:|
| `_strategy_binding` | 6,210 | 3.455 seconds |
| `create_strategy_execution_context` | 6,210 | 3.349 seconds |

Measurements separate the cache check, four once-per-run objects, and
per-bar context construction.

### B18 - Incremental SMA evaluation

| Turn | Check or implementation |
|---:|---|
| 1 | Enter Strategy response guard |
| 2 | Execute evaluator logging call |
| 3 | Require no external indicators |
| 4 | Read and validate 20/50/200 parameters |
| 5 | Extract canonical bars |
| 6 | Require complete window |
| 7 | Build immutable record identities |
| 8 | Require strict timestamp order |
| 9 | Require one-bar causal progression |
| 10 | Convert 200 Decimal closes to floats |
| 11 | Sum current and previous fast windows |
| 12 | Sum current and previous slow windows |
| 13 | Sum current filter window |
| 14 | Detect crossovers |
| 15 | Apply trend filter |
| 16 | Construct diagnostic facts |
| 17 | Construct four signals |

Observed `_bar_records()` calls: 37,260, or six per full strategy evaluation.

### B19 - Four canonical signal contracts

Observed `_make_signal()` calls: 24,840.

Each signal constructs and validates its ID, name, side, active flag, validity,
facts, lineage, redaction state, request/workflow/correlation identities,
Pydantic model, response metadata, and response envelope.

| Related operation | Observed count |
|---|---:|
| Signals | 24,840 |
| Pydantic `validate_python` | 319,461 |
| Response metadata builds | 124,752 |
| Response wrapper relationships | More than 112,000 |

Measurements: `B19.id`, `B19.fields`, `B19.facts_freeze`,
`B19.lineage_freeze`, `B19.redaction`, `B19.pydantic`, `B19.metadata`, and
`B19.response`.

### B20 - High-frequency logging

| Operation | Observed calls |
|---|---:|
| `logger.debug()` | About 1.823 million |
| Logger emission path | About 1.861 million |
| Default-configuration checks | About 1.861 million |

Cumulative profile values overlap with their parents and must not be added.
The benchmark must separately count log method calls, enabled checks, default
configuration checks, and records actually emitted.

### B21 - Interpret strategy result

For each complete evaluation, the composition unwraps the Strategy response,
builds the active-signal set, snapshots the engine, inspects positions, chooses
the appropriate exit or entry signal, and returns an action or neutral result.

Measurements: `B21.response_unwrap`, `B21.active_set`,
`B21.engine_snapshot`, `B21.position_check`, and `B21.action_selection`.

### B22 - Entry construction and submission

| Order | Operation |
|---:|---|
| 1 | Increment deterministic sequence |
| 2 | Construct order material |
| 3 | Bind request/workflow/correlation |
| 4 | Bind strategy identity |
| 5 | Set actual 0.1 volume |
| 6 | Calculate idempotency hash |
| 7 | Bind risk lineage and validity |
| 8 | Validate order intent |
| 9 | Submit through Simulation authority |
| 10 | Validate route, timing, ownership, and volume |
| 11 | Queue order |
| 12 | Construct receipt |

Measurements use `B22.*` for material, hash, validation, submission, queue, and
receipt.

### B23 - Exit and accounting

| Order | Operation |
|---:|---|
| 1 | Read position ID and volume |
| 2 | Request close through Simulation authority |
| 3 | Resolve executable side and price |
| 4 | Apply slippage |
| 5 | Calculate signed price movement |
| 6 | Apply volume and contract size |
| 7 | Calculate commission |
| 8 | Post ledger transaction |
| 9 | Update balance and equity |
| 10 | Materialize closed-trade record |
| 11 | Remove position |
| 12 | Journal state transition |
| 13 | Construct response |

Every measurement must retain the complete accounting equation so the
contract-size hypothesis can be resolved before performance comparisons.

### B24 - Terminal liquidation

The orchestrator snapshots remaining positions, checks
`close_open_positions_at_end`, closes each remaining position through the same
Simulation authority, and counts terminal liquidations.

Measurements: `B24.snapshot`, `B24.policy`, and `B24.close`.

### B25 - Simulation finalization

| Order | Operation |
|---:|---|
| 1 | Snapshot ledger |
| 2 | Reconcile balance and equity |
| 3 | Construct timeline evidence |
| 4 | Construct closed trades |
| 5 | Construct and validate Simulation result |
| 6 | Append completion journal event |
| 7 | Flush and fsync journal |
| 8 | Finalize journal metadata |
| 9 | Build and write JSON result |
| 10 | Build and write Markdown report |
| 11 | Build and write artifact manifest |
| 12 | Record completed idempotency state |
| 13 | Persist completion audit event |

Measurements use `B25.*` for each row and include journal event count and
artifact bytes.

### B26 - Analytics input

The usage program verifies closed trades, converts every trade to Analytics
source material, copies Data quality status and calendar provenance, attaches
provider/route metadata, constructs zero risk-free-rate evidence, constructs
statistical settings, and constructs the Analytics run configuration.

Measurements: `B26.trade_dump`, `B26.quality_metadata`,
`B26.analytics_config`, and `B26.source_construct`.

### B27 - Analytics report

```text
build_performance_report
  -> source normalization and validation
  -> equity and PnL metrics
  -> risk-adjusted metrics
  -> drawdown metrics
  -> trade metrics
  -> cost metrics
  -> benchmark metrics
  -> statistical validation
  -> quality flags and caveats
  -> report hashes and response
```

Each listed component requires a separate duration and input-size counter.
Bootstrap and permutation iterations must also be counted.

### B28 - Output rendering

The script indexes metrics, renders the measurement period and metric values,
then prints strategy identity, quality flags, all caveats, and all complete
closed-trade records.

Measurements: `B28.metric_index`, `B28.metric_render`,
`B28.quality_render`, `B28.caveat_render`, `B28.closed_trade_render`, and
`B28.stdout_write`.

## Structural comparison

| Concern | Old | New |
|---|---|---|
| Source bars | Truncated to 5,000 | Complete 6,710 |
| Measurement bars | About 4,500 | 6,210 |
| Ticks | 18,000 | 24,840 |
| Strategy calculation | EMA dataframe calculation | SMA bounded-window calculation |
| Calculation frequency | One dataframe operation | 6,210 canonical evaluations |
| Point-in-time checks | Implicit alignment | 24,840 explicit checks |
| Signal form | Dataframe columns | 24,840 validated models |
| Tick execution | Python/array-oriented | Canonical engine call per tick |
| Response envelopes | Limited | More than 112,000 relationships |
| Model validations | Limited | 319,461 observed calls |
| Logging | Relatively limited | About 1.86 million emission-path calls |
| Persistence | Result-oriented | Journal, artifacts, idempotency |
| Analytics | Symbol summary | Full performance report |
| No-lookahead evidence | Implicit | Explicit timestamp and availability |

## A/B instrumentation design

### Timing accumulator

Hot-loop instrumentation must not log or print per turn. It should update a
small in-memory accumulator using `time.perf_counter_ns()`.

```python
@dataclass(slots=True)
class TimingAccumulator:
    elapsed_ns: dict[str, int]
    calls: dict[str, int]
    minimum_ns: dict[str, int]
    maximum_ns: dict[str, int]
```

Each boundary records inclusive nanoseconds, call count, minimum, and maximum.
Parent/child relationships must be known so exclusive time can be calculated
without double-counting.

### High-frequency histogram

| Bucket | Duration |
|---|---:|
| H01 | Less than 1 microsecond |
| H02 | 1-5 microseconds |
| H03 | 5-10 microseconds |
| H04 | 10-50 microseconds |
| H05 | 50-100 microseconds |
| H06 | 100-500 microseconds |
| H07 | 0.5-1 millisecond |
| H08 | 1-5 milliseconds |
| H09 | More than 5 milliseconds |

### Required top-level timings

| Sequence | Shared measurement |
|---:|---|
| 1 | Startup |
| 2 | Provider setup |
| 3 | Data retrieval |
| 4 | Data normalization |
| 5 | Data quality |
| 6 | Strategy preparation |
| 7 | Tick generation |
| 8 | Request preparation |
| 9 | Timeline preparation |
| 10 | Tick execution |
| 11 | Point-in-time processing |
| 12 | Strategy evaluation |
| 13 | Order execution |
| 14 | Accounting |
| 15 | Persistence |
| 16 | Result construction |
| 17 | Analytics/reporting |
| 18 | Rendering |
| 19 | Total |

### Required counters

| Category | Counters |
|---|---|
| Data | Bars requested, returned, normalized, warmup, measurement |
| Quality | Duplicates, weekend gaps, calendar closures, missing bars, spikes |
| Ticks | Generated, executed, neutral, order-affecting |
| Evaluation | Cycle calls, full evaluations, duplicate neutral returns, fallbacks |
| Strategy | Bar extractions, indicator operations, signals built, active signals |
| Trading | Intents, submissions, fills, rejections |
| Positions | Opened, examined, closed, terminally liquidated |
| Accounting | Gross PnL calculations, commission calculations, ledger postings |
| Contracts | Pydantic validations, response envelopes, metadata builds |
| Canonicalization | Hashes, JSON serializations, bytes processed |
| Logging | Calls by level, configuration checks, records emitted |
| Persistence | Journal events, flushes, fsyncs, artifact count and bytes |
| Analytics | Trades, equity points, benchmark points, statistical iterations |

### Measurement record format

Every A/B result should contain:

| Field | Purpose |
|---|---|
| Run ID | Unique benchmark identity |
| Implementation | Old or new |
| Git revision/worktree digest | Exact code identity |
| Dataset hash | Exact bars used |
| Tick dataset hash | Exact ticks used |
| Strategy identity/hash | Exact algorithm |
| Configuration hash | Complete run settings |
| Python version | Runtime identity |
| Warm/cold indicator | Import/cache state |
| Stage timing map | Inclusive/exclusive measurements |
| Counter map | Work performed |
| Result reconciliation | Signals, trades, PnL, costs |

## Controlled-test requirements

A fair computational A/B test must satisfy every control below.

| ID | Control | Verification |
|---|---|---|
| C01 | Retrieve genuine bars once | Persist source hash and provider provenance |
| C02 | Feed exact same bars to both | Equal row count and record digest |
| C03 | Use complete interval | Equal warmup and measurement counts |
| C04 | Use same tick stream | Equal tick count, timestamp, bid, ask, phase |
| C05 | Use same MA type | EMA in both or SMA in both |
| C06 | Use same periods | 20/50/200 |
| C07 | Use same timing policy | Equal decision timestamps |
| C08 | Use actual 0.1 volume | Verify every fill and closed trade |
| C09 | Use same spread | Verify bid/ask at every tick |
| C10 | Use same slippage | Verify every execution price |
| C11 | Use same contract size | Reconcile gross PnL equation |
| C12 | Use same commission | Reconcile per-side and round-trip costs |
| C13 | Use same liquidation policy | Equal terminal behavior |
| C14 | Compare signals | Name, side, active state, timestamp |
| C15 | Compare orders | Action, side, volume, time |
| C16 | Compare fills | Price, volume, costs, sequence |
| C17 | Compare closed trades | Entry, exit, side, volume, PnL |
| C18 | Separate normal/profile runs | Never mix timing types |
| C19 | Repeat measurements | Median and dispersion, not one sample |
| C20 | Preserve process cleanup | Kill only benchmark descendants on timeout |

## Recommended experiment sequence

| Experiment | Purpose | Instrumentation level |
|---|---|---|
| E01 | Cold direct-script runtime | Top-level wall clock only |
| E02 | Warm direct-script runtime | Top-level wall clock only |
| E03 | Stage attribution | Low-overhead stage accumulator |
| E04 | Per-turn distribution | Counters and bounded histograms |
| E05 | Call attribution | Sampling profiler or cProfile |
| E06 | Data parity | Source and tick reconciliation |
| E07 | Strategy parity | Signal-by-signal reconciliation |
| E08 | Execution parity | Order/fill/trade reconciliation |
| E09 | Accounting proof | Known-case and aggregate equations |
| E10 | Candidate optimization | Repeat E01-E09 before/after |

For normal timing, run multiple repetitions and report median, minimum,
maximum, and median absolute deviation. Provider retrieval should be reported
separately because network and terminal latency can vary independently of the
backtest engine.

## Interpretation rules

1. Do not add cumulative profile times; parent times contain child times.
2. Do not compare cProfile runtime with normal runtime.
3. Do not call a path faster if it performs less work without reporting that
   workload difference.
4. Do not compare PnL until signals, ticks, volume, contract size, slippage, and
   commission reconcile.
5. Do not remove point-in-time checks merely because the old application lacks
   equivalent explicit evidence.
6. Optimize repeated implementation work after separating it from required
   business checks.
7. Measure logging calls and actual emissions separately.
8. Measure object construction, validation, response wrapping, and
   serialization separately.
9. Treat import time as cold-start cost, not per-run engine cost.
10. Preserve every tick and every required decision evaluation.
11. Use exact hashes to prove A/B input identity.
12. Require an accounting invariant before trusting performance statistics.

## Source reference index

### Old application

| Concern | Source |
|---|---|
| Usage example | `C:/Users/rharu/AppDev/HaruQuant/tests/usage/app/services/08_simulator.py` |
| Strategy | `C:/Users/rharu/AppDev/HaruQuant/data/strategies/baselines/trend_following.py` |
| Simulation runner | `C:/Users/rharu/AppDev/HaruQuant/app/services/simulation/runner.py` |
| Data preparation | `C:/Users/rharu/AppDev/HaruQuant/app/services/simulation/data_preparation.py` |
| Event-driven engine | `C:/Users/rharu/AppDev/HaruQuant/app/services/simulation/event_driven.py` |
| Engine composition | `C:/Users/rharu/AppDev/HaruQuant/app/services/simulation/engine.py` |

### New application

| Concern | Source |
|---|---|
| Usage example | `tests/legacy/08_simulator.py` |
| Data pipeline | `app/services/data/market_data/pipeline.py` |
| Data quality | `app/services/data/integrity/` |
| Calendar closure evidence | `app/services/data/economic_calendar/closures.py` |
| Tick derivation | `app/services/data/transformation/tick_derivation.py` |
| Timeline | `app/services/simulator/timeline/timeline.py` |
| Orchestration | `app/services/simulator/run/orchestrator.py` |
| Point-in-time evaluation | `app/services/simulator/run/evaluation.py` |
| Execution engine | `app/services/simulator/execution/engine.py` |
| Strategy evaluator | `app/services/strategy/evaluators/naive_ma_trend_incremental.py` |
| Analytics builder | `app/services/analytics/reports/builder.py` |
| Analytics serialization | `app/services/analytics/reports/serialization.py` |

## Current evidence summary

The current evidence supports three immediate conclusions:

1. The comparison needs an exact shared dataset and strategy algorithm before
   outcome parity can be assessed.
2. The new performance investigation should begin with signal construction,
   response envelopes, Pydantic validation, high-frequency logging, timeline
   construction, and tick response handling.
3. Accounting correctness must be proven before either system's performance
   metrics are used to judge strategy quality.
