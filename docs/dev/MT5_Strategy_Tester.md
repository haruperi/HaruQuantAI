# Build-Once Implementation Plan — Python MetaTrader 5 Strategy Tester
## Purpose
This plan reorganizes the extracted requirements from the five tutorial articles into a production implementation order. It deliberately **does not** recreate the tutorial's incremental refactors. The first implementation of each component should be its final architectural form: configuration-driven `Tester`, canonical ledger, runtime-mode router, local history store, MT5-compatible façade, validation-first execution engine, and thread-safe multi-symbol runner.
## Scope and Audit Basis
- **Input task count:** **217** atomic tasks extracted from the original five-part plan.
- **Output task count:** **217** atomic tasks in this reordered plan.
- **Count policy:** Each checkbox below is one auditable implementation requirement. The plan relocates requirements to their earliest correct dependency phase; it does not delete tutorial requirements or introduce a second implementation pass.
## Build-Once Rules
1. Build the final `Tester` architecture in Phase 1; do not first ship a separate minimal simulator and later rename/refactor it.
2. Maintain one canonical ledger for active positions, pending orders, historical orders, deals, and account state.
3. Keep replay mode and terminal mode behind one runtime router; strategy code must not need separate APIs.
4. Implement validation before any operation can mutate the ledger.
5. Introduce thread-safety before parallel multi-symbol execution, not after race conditions appear.
6. Treat GUI and reporting as consumers of canonical state; they must not own business logic.
## Phase Summary
| Phase | Scope | Tasks | Completion Gate |
|---|---|---:|---|
| 1 | Final Architecture, Runtime Contracts, and Canonical Models | 28 | A test can construct a Tester from validated configuration, initialize canonical state, and enter tester or terminal mode without loading market data or executing trades. |
| 2 | Historical Market Data, Local Storage, and Market-State Services | 32 | The engine can synchronize history, retrieve deterministic bar/tick windows from local storage, and provide current tick and symbol metadata through one runtime-mode-aware interface. |
| 3 | Ledger, Account State, Pricing, Margin, and Read APIs | 28 | Given tick and symbol metadata, the module can calculate margin/P&L, model positions and account state, write immutable deal history, and answer public state queries without submitting orders. |
| 4 | Trade Validation, Pending Orders, and the Low-Level Execution Dispatcher | 35 | Invalid requests leave all state unchanged; valid requests produce correctly linked ledger changes and MT5-compatible results. |
| 5 | Public Trade API and Position/Order Lifecycle Management | 24 | A strategy can open, close, modify, cancel, and inspect trades exclusively through public APIs while the engine monitors exits, triggers, and state transitions correctly. |
| 6 | Tester Orchestration, Modelling Modes, and Single-Symbol Strategy Execution | 31 | A configured strategy can run against real ticks, generated ticks, M1 OHLC, or new bars while all market, account, order, and position state is maintained in a documented event order. |
| 7 | Historical Queries, Reports, Visual Inspection, and Terminal-Parity Scenarios | 15 | A completed run produces queryable historical state and durable report artifacts; visual tools consume canonical state only; terminal comparison remains explicit and isolated. |
| 8 | Multi-Symbol, Multi-Timeframe, Concurrent Replay, and Performance Controls | 24 | Multiple symbols and timeframes can be tested concurrently without race conditions, duplicate history fetches, or unnecessary per-tick indicator recomputation. |
| **Total** | **Complete simulator/tester module** | **217** | **All source requirements accounted for** |

---

# Phase 1 — Final Architecture, Runtime Contracts, and Canonical Models

**Objective:** Establish the final, non-tutorial architecture before implementing behavior: a configuration-driven Tester, one canonical state model, MT5-compatible records, and reusable runtime services.

**Completion Gate:** A test can construct a Tester from validated configuration, initialize canonical state, and enter tester or terminal mode without loading market data or executing trades.

- [ ] **SIM-001 — Define the final module boundary around a `Tester` runtime rather than first building a disposable `TradeSimulator` and later renaming it.**
  - *Technical Details:* Retain simulator behavior inside the final Tester domain; expose explicit initialization, replay, monitoring, reporting, and teardown lifecycle hooks.
  - *Source Trace:* P4 — From Simulator to Tester.
- [ ] **SIM-002 — Create tester-specific logging and output-path isolation.**
  - *Technical Details:* Use the tester/bot name to separate logs, reports, curves, generated ticks, and history artifacts.
  - *Source Trace:* P4 — From Simulator to Tester.
- [ ] **SIM-003 — Define the complete test-run lifecycle contract.**
  - *Technical Details:* Specify initialize → synchronize/load history → replay → monitor → collect results → report → deinitialize; do not embed lifecycle orchestration in UI or strategy code.
  - *Source Trace:* P4 — From Simulator to Tester.
- [ ] **SIM-004 — Define a JSON-based tester configuration contract.**
  - *Technical Details:* Include bot name, `symbols`, primary `timeframe`, start/end dates, `modelling`, `deposit`, and `leverage`.
  - *Source Trace:* P4 — Tester Configuration and Initialization.
- [ ] **SIM-005 — Implement the final configuration-driven Tester constructor.**
  - *Technical Details:* Use a constructor equivalent to `Tester(tester_config, mt5_instance)` instead of a later refactor from many positional arguments.
  - *Source Trace:* P4 — Tester Configuration and Initialization.
- [ ] **SIM-006 — Validate tester configuration before history import or replay startup.**
  - *Technical Details:* Validate symbols, timeframe, dates, modelling mode, deposit, and leverage; reject invalid configurations before mutable engine state is created.
  - *Source Trace:* P4 — Tester Configuration and Initialization.
- [ ] **SIM-007 — Normalize all configured test dates into UTC-aware internal timestamps.**
  - *Technical Details:* Use one time basis for MT5 data, tick replay, expiry comparisons, history filters, curves, and reports.
  - *Source Trace:* P4 — Tester Configuration and Initialization.
- [ ] **SIM-008 — Preallocate per-symbol replay metadata collections.**
  - *Technical Details:* Maintain final containers equivalent to `TESTER_ALL_TICKS_INFO` and `TESTER_ALL_BARS_INFO`, including symbol, dataset, size, and replay counter.
  - *Source Trace:* P4 — Tester Configuration and Initialization.
- [ ] **SIM-009 — Treat the configured host symbol/timeframe as context while retaining a first-class configured symbol list.**
  - *Technical Details:* Do not architect the engine around a single chart; all downstream APIs must accept arbitrary configured symbols and timeframes.
  - *Source Trace:* P4 — Tester Configuration and Initialization.
- [ ] **SIM-010 — Create the `HistoryManager` as the sole historical-data orchestration service.**
  - *Technical Details:* Place it in a dedicated history-management module and make the Tester depend on it rather than duplicating history logic.
  - *Source Trace:* P5 — Multi-Timeframe Data Handling.
- [ ] **SIM-011 — Configure `HistoryManager` with terminal access, symbols, date range, timeframe, logger, worker limits, and history root.**
  - *Technical Details:* Support fields equivalent to `mt5_instance`, `symbols`, `start_dt`, `end_dt`, `timeframe`, `LOGGER`, `max_fetch_workers`, `max_cpu_workers`, and `history_dir`.
  - *Source Trace:* P5 — Multi-Timeframe Data Handling.
- [ ] **SIM-012 — Declare local Parquet storage as the canonical historical-data cache.**
  - *Technical Details:* All replay-mode `copy_rates_*` and `copy_ticks_*` calls must resolve from this local store, not opportunistically from the terminal.
  - *Source Trace:* P5 — Multi-Timeframe Data Handling.
- [ ] **SIM-013 — Set safe default worker limits as configuration defaults.**
  - *Technical Details:* Bound I/O fetch workers by symbol count and reserve one CPU core when deriving CPU-worker defaults; allow explicit overrides.
  - *Source Trace:* P5 — Multi-Timeframe Data Handling.
- [ ] **SIM-014 — Provide logger-backed diagnostics with a console fallback.**
  - *Technical Details:* Use structured informational and critical error reporting without making a logger mandatory for simple local tests.
  - *Source Trace:* P5 — Multi-Timeframe Data Handling.
- [ ] **SIM-015 — Implement the final Tester/Simulator constructor with simulator name, MT5 module instance, deposit, and leverage inputs.**
  - *Technical Details:* Keep `simulator_name` for artifact isolation and retain the MT5 instance for metadata, terminal delegation, and reference calculations.
  - *Source Trace:* P1 — Trading Simulator 101.
- [ ] **SIM-016 — Store shared simulation-account configuration and expose its setter APIs.**
  - *Technical Details:* Persist starting deposit, leverage, magic number, deviation points, and account identity fields in explicit state; implement `set_magicnumber(magic_number)` and `set_deviation_in_points(deviation_points)` rather than ad hoc globals.
  - *Source Trace:* P1 — Trading Simulator 101; P1 — RealTime Trade Simulation in Python.
- [ ] **SIM-017 — Define a canonical internal position-record template.**
  - *Technical Details:* Include ticket, time fields, magic, symbol, type, volume, open/current price, SL, TP, commission, margin, fee, swap, profit, and comment.
  - *Source Trace:* P1 — Trading Simulator 101.
- [ ] **SIM-018 — Define a canonical internal pending-order-record template.**
  - *Technical Details:* Include all shared trade fields plus trigger price, expiry date, expiration mode, order state, and related position/order IDs.
  - *Source Trace:* P1 — Trading Simulator 101.
- [ ] **SIM-019 — Define a canonical immutable deal-record template.**
  - *Technical Details:* Include entry/exit direction, reason, execution price, costs, P/L, balance impact, and position/order linkage.
  - *Source Trace:* P1 — Trading Simulator 101.
- [ ] **SIM-020 — Create the canonical active-state containers.**
  - *Technical Details:* Maintain distinct active position and pending-order containers; maintain separate immutable deal and historical-order ledgers.
  - *Source Trace:* P1 — Trading Simulator 101; P2 — history_orders_total and history_orders_get.
- [ ] **SIM-021 — Implement a single monotonically increasing ticket generator.**
  - *Technical Details:* Use one collision-free identifier source across orders, positions, and deals; preserve linkage when a pending order becomes a position.
  - *Source Trace:* P1 — Trading Simulator 101.
- [ ] **SIM-022 — Enforce immutable historical-deal policy from the first implementation.**
  - *Technical Details:* Historical deals must never be modified or deleted after creation, including after reporting or UI refreshes.
  - *Source Trace:* P1 — Working with Deals.
- [ ] **SIM-023 — Define the complete simulated account-information structure.**
  - *Technical Details:* Track balance, credit, floating P/L, equity, used margin, free margin, margin level, leverage, currency, stop-out fields, and broker/account identity values.
  - *Source Trace:* P1 — Monitoring the Account; P2 — account_info.
- [ ] **SIM-024 — Define the MT5-compatible `TradeOrder` record shape.**
  - *Technical Details:* Include setup/done/expiration timestamps, ticket, type, filling/time policy, state, magic, position IDs, reason, volumes, prices, SL/TP, current price, symbol, comment, and external ID.
  - *Source Trace:* P2 — orders_total and orders_get.
- [ ] **SIM-025 — Define the MT5-compatible `TradePosition` record shape.**
  - *Technical Details:* Include ticket, open/update timestamps, type, magic, identifier, reason, volume, entry/current prices, SL/TP, swap, profit, symbol, comment, and external ID.
  - *Source Trace:* P2 — positions_total and positions_get.
- [ ] **SIM-026 — Define the MT5-compatible `AccountInfo` record shape.**
  - *Technical Details:* Expose account permissions, leverage, margin configuration, currency data, balance/equity/margin values, stop-out thresholds, assets/liabilities, and broker identity fields.
  - *Source Trace:* P2 — account_info.
- [ ] **SIM-027 — Implement explicit runtime-mode state and a mode-transition API.**
  - *Technical Details:* Maintain flags equivalent to `IS_RUNNING` and `IS_TESTER`; implement `Start(IS_TESTER: bool)` and route runtime behavior from this mode rather than scattered conditionals.
  - *Source Trace:* P2 — Overloading MetaTrader 5 Functions.
- [ ] **SIM-028 — Define a consistent MT5-compatible result/error contract before execution logic exists.**
  - *Technical Details:* Reserve `retcode`, `order`, `deal`, and `position` fields for trade results and establish controlled failure semantics for unavailable/invalid resources.
  - *Source Trace:* P3 — The order_send Method; P2 — Query APIs.

*Dependencies:* None (foundation phase).

---

# Phase 2 — Historical Market Data, Local Storage, and Market-State Services

**Objective:** Build the data plane once: terminal extraction, normalized Parquet persistence, lazy replay reads, symbol metadata caching, and current-tick state.

**Completion Gate:** The engine can synchronize history, retrieve deterministic bar/tick windows from local storage, and provide current tick and symbol metadata through one runtime-mode-aware interface.

- [ ] **SIM-029 — Validate and select a symbol before every terminal historical-data request.**
  - *Technical Details:* Use a helper equivalent to `ensure_symbol(symbol)` and return a controlled error for unresolvable instruments.
  - *Source Trace:* P2 — Handling MetaTrader 5 Historical Ticks.
- [ ] **SIM-030 — Implement historical tick retrieval by symbol and UTC date range.**
  - *Technical Details:* Use MT5-compatible `copy_ticks_range(symbol, date_from, date_to, flags)` and request `COPY_TICKS_ALL` when full replay data is needed.
  - *Source Trace:* P2 — Handling MetaTrader 5 Historical Ticks.
- [ ] **SIM-031 — Split long tick-history requests into bounded monthly intervals.**
  - *Technical Details:* Use UTC-aware month boundaries, cap the final interval at the requested end date, and stop when the next interval begins after the requested end date.
  - *Source Trace:* P2 — Handling MetaTrader 5 Historical Ticks.
- [ ] **SIM-032 — Normalize tick timestamps and derive partition fields.**
  - *Technical Details:* Convert epoch times to UTC timestamps and add `year` and `month` fields without losing `time_msc` precision.
  - *Source Trace:* P2 — Handling MetaTrader 5 Historical Ticks.
- [ ] **SIM-033 — Persist tick datasets as partitioned Parquet files.**
  - *Technical Details:* Use a hierarchy comparable to `History/Ticks/<symbol>/year=<year>/month=<month>` and preserve bid, ask, last, volume, time, time_msc, flags, and real volume.
  - *Source Trace:* P2 — Handling MetaTrader 5 Historical Ticks.
- [ ] **SIM-034 — Detect and record incomplete terminal-provided tick coverage.**
  - *Technical Details:* Do not assume a requested range is complete; store coverage/missing-interval diagnostics when broker or terminal history is bounded.
  - *Source Trace:* P2 — Handling MetaTrader 5 Historical Ticks.
- [ ] **SIM-035 — Implement historical bar retrieval by symbol, timeframe, and UTC date range.**
  - *Technical Details:* Use MT5-compatible `copy_rates_range` behavior and preserve a direct path for terminal-mode delegation.
  - *Source Trace:* P2 — Handling MetaTrader 5 Historical Bars.
- [ ] **SIM-036 — Process bar history in monthly partitions rather than a single large in-memory query.**
  - *Technical Details:* Fetch incrementally, normalize timestamps to UTC, and preserve correct final-period boundaries.
  - *Source Trace:* P2 — Handling MetaTrader 5 Historical Bars.
- [ ] **SIM-037 — Normalize bars into the canonical MT5-compatible OHLCV schema.**
  - *Technical Details:* Preserve `time`, `open`, `high`, `low`, `close`, `tick_volume`, `spread`, and `real_volume`.
  - *Source Trace:* P2 — Handling MetaTrader 5 Historical Bars.
- [ ] **SIM-038 — Persist bar datasets as partitioned Parquet by symbol and timeframe.**
  - *Technical Details:* Use a hierarchy comparable to `History/Bars/<symbol>/<timeframe>/year=<year>/month=<month>`.
  - *Source Trace:* P2 — Handling MetaTrader 5 Historical Bars.
- [ ] **SIM-039 — Standardize persisted bar output for parity with live MT5 calls.**
  - *Technical Details:* Ensure replay storage can be converted into the same structured/dictionary-compatible representation that terminal calls return.
  - *Source Trace:* P2 — Handling MetaTrader 5 Historical Bars.
- [ ] **SIM-040 — Implement `copy_ticks_from(symbol, date_from, count, flags)` for replay mode and terminal mode.**
  - *Technical Details:* In tester mode, query only required local tick partitions; in terminal mode, delegate to MT5.
  - *Source Trace:* P2 — copy_ticks_from and copy_ticks_range.
- [ ] **SIM-041 — Implement `copy_ticks_range(symbol, date_from, date_to, flags)` for replay mode and terminal mode.**
  - *Technical Details:* Return only the requested inclusive time range and preserve the requested tick-flag behavior.
  - *Source Trace:* P2 — copy_ticks_from and copy_ticks_range.
- [ ] **SIM-042 — Filter replayed ticks by MT5 flag mask and impose deterministic tick order.**
  - *Technical Details:* Filter using supplied flags; sort by `time` then `time_msc` so same-second ticks replay in a stable order.
  - *Source Trace:* P2 — copy_ticks_from and copy_ticks_range.
- [ ] **SIM-043 — Return canonical tick fields from all tick-copy APIs.**
  - *Technical Details:* Return `time`, `bid`, `ask`, `last`, `volume`, `time_msc`, `flags`, and `volume_real` in a consistent shape.
  - *Source Trace:* P2 — copy_ticks_from and copy_ticks_range.
- [ ] **SIM-044 — Use lazy/streaming reads for tick replay queries.**
  - *Technical Details:* Read only requested columns and partitions; do not load a full archive to serve a short window.
  - *Source Trace:* P2 — copy_ticks_from and copy_ticks_range.
- [ ] **SIM-045 — Implement `copy_rates_from(symbol, timeframe, date_from, count)`.**
  - *Technical Details:* Return the requested number of bars beginning at the requested timestamp under the shared replay/live routing policy.
  - *Source Trace:* P2 — copy_rates_from, copy_rates_from_pos, and copy_rates_range.
- [ ] **SIM-046 — Implement `copy_rates_from_pos(symbol, timeframe, start_pos, count)`.**
  - *Technical Details:* Support index-based historical windows used by indicators and strategy calculations, including recent-bar access.
  - *Source Trace:* P2 — copy_rates_from, copy_rates_from_pos, and copy_rates_range.
- [ ] **SIM-047 — Implement `copy_rates_range(symbol, timeframe, date_from, date_to)`.**
  - *Technical Details:* Return deterministic, time-sorted bars inside the requested range.
  - *Source Trace:* P2 — copy_rates_from, copy_rates_from_pos, and copy_rates_range.
- [ ] **SIM-048 — Use lazy Parquet scans for replay-mode bar queries.**
  - *Technical Details:* Filter by timestamp, select MT5-equivalent columns, and collect only the required results.
  - *Source Trace:* P2 — copy_rates_from, copy_rates_from_pos, and copy_rates_range.
- [ ] **SIM-049 — Normalize terminal structured arrays into the same rate representation used by replay mode.**
  - *Technical Details:* Implement a converter equivalent to `__mt5_rates_to_dicts` so strategies do not branch by runtime mode.
  - *Source Trace:* P2 — copy_rates_from, copy_rates_from_pos, and copy_rates_range.
- [ ] **SIM-050 — Handle absent or empty bar results without crashing strategy code.**
  - *Technical Details:* Return controlled empty/none results and log root causes rather than letting malformed values propagate.
  - *Source Trace:* P2 — copy_rates_from, copy_rates_from_pos, and copy_rates_range.
- [ ] **SIM-051 — Maintain a per-symbol current-tick cache.**
  - *Technical Details:* Use a structure equivalent to `tick_cache: dict[str, namedtuple]` as the single simulated market-state source.
  - *Source Trace:* P2 — Overloading MetaTrader 5 Functions.
- [ ] **SIM-052 — Implement `TickUpdate(symbol, tick)`.**
  - *Technical Details:* Normalize accepted tick representations and update the canonical current tick for the given instrument.
  - *Source Trace:* P2 — Overloading MetaTrader 5 Functions.
- [ ] **SIM-053 — Implement `symbol_info_tick(symbol)` through the runtime-mode router.**
  - *Technical Details:* Return the cached simulated tick in tester mode and delegate to `mt5_instance.symbol_info_tick(symbol)` in terminal mode.
  - *Source Trace:* P2 — symbol_info_tick.
- [ ] **SIM-054 — Reject or report uninitialized tick state explicitly.**
  - *Technical Details:* Never fabricate prices when the requested symbol has not yet received a tick.
  - *Source Trace:* P2 — symbol_info_tick.
- [ ] **SIM-055 — Maintain a static symbol-information cache.**
  - *Technical Details:* Use `symbol_info_cache` to avoid repeated terminal calls during testing while retaining all fields needed for validation and accounting.
  - *Source Trace:* P2 — Overloading MetaTrader 5 Functions.
- [ ] **SIM-056 — Implement `symbol_info(symbol)` through the shared cache and runtime router.**
  - *Technical Details:* Fetch terminal data once when required, cache it, and return `None` or a controlled error for missing instruments.
  - *Source Trace:* P2 — symbol_info.
- [ ] **SIM-057 — Ensure cached symbol metadata includes all execution and accounting fields.**
  - *Technical Details:* Include digits, point, contract size, volume limits/step, stop/freeze levels, tick size/value, calculation mode, and margin properties.
  - *Source Trace:* P2 — symbol_info.
- [ ] **SIM-058 — Synchronize all configured timeframes into local storage before replay begins.**
  - *Technical Details:* Expose a method comparable to `hist_manager.synchronize_timeframes()` so later rate queries are deterministic and local.
  - *Source Trace:* P5 — Extracting Data Directly from MetaTrader 5.
- [ ] **SIM-059 — Implement a historical-bar fetch worker.**
  - *Technical Details:* Provide `_fetch_bars_worker(symbol, timeframe, return_df=False)` that returns symbol, dataset, size, and counter metadata when required.
  - *Source Trace:* P5 — Extracting Data Directly from MetaTrader 5.
- [ ] **SIM-060 — Implement a historical-tick fetch worker.**
  - *Technical Details:* Provide `_fetch_ticks_worker(symbol, return_df=False)` with the same normalized metadata contract.
  - *Source Trace:* P5 — Extracting Data Directly from MetaTrader 5.

*Dependencies:* All completion gates through Phase 1.

---

# Phase 3 — Ledger, Account State, Pricing, Margin, and Read APIs

**Objective:** Implement one canonical ledger and valuation engine before any trade dispatcher mutates it, then expose state through MT5-compatible query APIs.

**Completion Gate:** Given tick and symbol metadata, the module can calculate margin/P&L, model positions and account state, write immutable deal history, and answer public state queries without submitting orders.

- [ ] **SIM-061 — Implement the canonical internal profit-calculation method.**
  - *Technical Details:* Use a method equivalent to `_calculate_profit(action, symbol, entry_price, exit_price, lotsize)` and accept only supported buy/sell directions.
  - *Source Trace:* P1 — Calculating Profits/Losses Made By a Position.
- [ ] **SIM-062 — Delegate instrument-specific profit calculations to MT5-compatible logic when available.**
  - *Technical Details:* Use `mt5_instance.order_calc_profit(order_type, symbol, lotsize, entry_price, exit_price)` for parity in terminal mode and reference validation.
  - *Source Trace:* P1 — Calculating Profits/Losses Made By a Position.
- [ ] **SIM-063 — Implement public `order_calc_profit(action, symbol, volume, price_open, price_close)`.**
  - *Technical Details:* Return P/L in account currency through the shared runtime-mode abstraction.
  - *Source Trace:* P2 — order_calc_profit and order_calc_margin.
- [ ] **SIM-064 — Support calculation-mode-specific profit formulas.**
  - *Technical Details:* Cover Forex, CFD, stocks, futures, bonds, and collateral-style modes; apply tick-value/tick-size formulas where required.
  - *Source Trace:* P2 — order_calc_profit and order_calc_margin.
- [ ] **SIM-065 — Implement public `order_calc_margin(...)`.**
  - *Technical Details:* Use simulated leverage and symbol margin mode in tester mode; delegate to MT5 in terminal mode.
  - *Source Trace:* P2 — order_calc_profit and order_calc_margin.
- [ ] **SIM-066 — Implement the internal margin-calculation service.**
  - *Technical Details:* Use a method equivalent to `_calculate_margin(symbol, volume, open_price, margin_rate=1.0)` and isolate broker-specific margin-rate assumptions.
  - *Source Trace:* P1 — Simulating a Position.
- [ ] **SIM-067 — Support margin formulas across the article’s instrument calculation modes.**
  - *Technical Details:* Cover FOREX, FOREX without leverage, CFD, leveraged CFD, CFD index, exchange stocks, futures, bonds, and collateral modes.
  - *Source Trace:* P1 — Simulating a Position.
- [ ] **SIM-068 — Provide controlled fallbacks for unsupported or failed P/L and margin calculations.**
  - *Technical Details:* Log the cause and return deterministic failures rather than allowing `None`/invalid values to corrupt the account.
  - *Source Trace:* P1 — Simulating a Position; P2 — order_calc_profit and order_calc_margin.
- [ ] **SIM-069 — Implement internal market-position construction.**
  - *Technical Details:* Use `_open_position(pos_type, volume, symbol, price, sl=0.0, tp=0.0, comment='')` and always instantiate a fresh record from the canonical template.
  - *Source Trace:* P1 — Simulating a Position.
- [ ] **SIM-070 — Populate all position execution and accounting fields at open time.**
  - *Technical Details:* Assign simulated time, ticket, magic, instrument, direction, volume, entry price, exits, costs, profit, margin, and comment.
  - *Source Trace:* P1 — Simulating a Position.
- [ ] **SIM-071 — Calculate and persist required margin before adding a position to active state.**
  - *Technical Details:* Append a position only after the required margin is calculated and all prerequisites have been satisfied.
  - *Source Trace:* P1 — Simulating a Position.
- [ ] **SIM-072 — Implement account monitoring as the sole account-revaluation operation.**
  - *Technical Details:* Provide `monitor_account(verbose)` or equivalent; read active positions rather than duplicating balance/equity formulas elsewhere.
  - *Source Trace:* P1 — Monitoring the Account.
- [ ] **SIM-073 — Calculate floating P/L, equity, used margin, free margin, and margin level consistently.**
  - *Technical Details:* Use `equity = balance + unrealized_pl`, `free_margin = equity - margin`, and avoid division when margin is zero.
  - *Source Trace:* P1 — Monitoring the Account.
- [ ] **SIM-074 — Realize closed-position P/L into balance exactly once.**
  - *Technical Details:* Update balance before removing the position from active state and before subsequent account monitoring.
  - *Source Trace:* P1 — Monitoring the Account.
- [ ] **SIM-075 — Expose optional account diagnostics without changing account behavior.**
  - *Technical Details:* Log balance, equity, margin, free margin, margin level, and floating P/L only when diagnostics are enabled.
  - *Source Trace:* P1 — Monitoring the Account.
- [ ] **SIM-076 — Create an entry deal whenever a market position is opened.**
  - *Technical Details:* Write an immutable deal record with entry direction, execution price, volume, costs, and ticket linkage.
  - *Source Trace:* P1 — Working with Deals.
- [ ] **SIM-077 — Create an exit deal whenever a position is partially or fully closed.**
  - *Technical Details:* Record reason, direction, close price, volume, costs, P/L, and resulting balance.
  - *Source Trace:* P1 — Working with Deals.
- [ ] **SIM-078 — Create linked deals when a triggered pending order becomes a market position.**
  - *Technical Details:* Preserve order ticket, position ticket, and deal ticket relationships.
  - *Source Trace:* P1 — Working with Deals.
- [ ] **SIM-079 — Model deal direction and closure reason explicitly.**
  - *Technical Details:* Capture entry versus exit and reasons such as take profit, stop loss, manual close, expiration, or balance adjustment.
  - *Source Trace:* P1 — Working with Deals.
- [ ] **SIM-080 — Implement public active-position retrieval.**
  - *Technical Details:* Expose `get_positions()` and return active canonical position records without requiring callers to inspect private containers.
  - *Source Trace:* P1 — Managing and Controlling Positions and Orders Externally.
- [ ] **SIM-081 — Implement public active-order retrieval.**
  - *Technical Details:* Expose `get_orders()` and return active pending-order records through the canonical ledger.
  - *Source Trace:* P1 — Managing and Controlling Positions and Orders Externally.
- [ ] **SIM-082 — Implement public deal-history retrieval.**
  - *Technical Details:* Expose `get_deals(start_time=None, end_time=None, from_db=False)` with interval filtering and optional persistence-backed source.
  - *Source Trace:* P1 — Managing and Controlling Positions and Orders Externally.
- [ ] **SIM-083 — Implement `orders_total()`.**
  - *Technical Details:* Return active pending-order count in tester mode and delegate to MT5 in terminal mode.
  - *Source Trace:* P2 — orders_total and orders_get.
- [ ] **SIM-084 — Implement `orders_get(symbol=None, group=None, ticket=None)`.**
  - *Technical Details:* Support unfiltered, symbol, group, and ticket filters and return MT5-compatible `TradeOrder` instances.
  - *Source Trace:* P2 — orders_total and orders_get.
- [ ] **SIM-085 — Implement controlled order-query failure behavior.**
  - *Technical Details:* Return `None` or empty controlled results according to the API contract and surface diagnostics through logging/last-error state.
  - *Source Trace:* P2 — orders_total and orders_get.
- [ ] **SIM-086 — Implement `positions_total()`.**
  - *Technical Details:* Return active position count in tester mode and delegate to MT5 in terminal mode.
  - *Source Trace:* P2 — positions_total and positions_get.
- [ ] **SIM-087 — Implement `positions_get(symbol=None, group=None, ticket=None)`.**
  - *Technical Details:* Support unfiltered, symbol, group, and ticket filters and return MT5-compatible `TradePosition` instances.
  - *Source Trace:* P2 — positions_total and positions_get.
- [ ] **SIM-088 — Implement `account_info()` through the runtime router.**
  - *Technical Details:* Return simulated account state in tester mode and delegate to `mt5_instance.account_info()` in terminal mode; fail controlledly if account data cannot be initialized.
  - *Source Trace:* P2 — account_info.

*Dependencies:* All completion gates through Phase 2.

---

# Phase 4 — Trade Validation, Pending Orders, and the Low-Level Execution Dispatcher

**Objective:** Build validation before mutation, then implement one MT5-style `order_send` dispatcher capable of processing validated market, pending, close, modify, and delete requests.

**Completion Gate:** Invalid requests leave all state unchanged; valid requests produce correctly linked ledger changes and MT5-compatible results.

- [ ] **SIM-089 — Implement a central position/order validation entry point.**
  - *Technical Details:* Use a method equivalent to `_position_validation(volume, symbol, pos_type, open_price, sl=0.0, tp=0.0, expiry_date=None)`.
  - *Source Trace:* P1 — Trade Validations.
- [ ] **SIM-090 — Load current symbol properties before validating a request.**
  - *Technical Details:* Retrieve minimum/maximum volume, volume step, point, stop level, freeze level, bid, ask, and all required margin metadata.
  - *Source Trace:* P1 — Trade Validations.
- [ ] **SIM-091 — Reject requested volume below the instrument minimum.**
  - *Technical Details:* Use `lots_min` from canonical symbol metadata.
  - *Source Trace:* P1 — Trade Validations.
- [ ] **SIM-092 — Reject requested volume above the instrument maximum.**
  - *Technical Details:* Use `lots_max` from canonical symbol metadata.
  - *Source Trace:* P1 — Trade Validations.
- [ ] **SIM-093 — Reject requested volume that violates the volume-step increment.**
  - *Technical Details:* Use a floating-point tolerance when checking multiples of `lots_step`.
  - *Source Trace:* P1 — Trade Validations.
- [ ] **SIM-094 — Validate market-entry price against current executable prices and configured deviation.**
  - *Technical Details:* Refresh ticks; compare buys to ask and sells to bid; convert deviation points through symbol `point`.
  - *Source Trace:* P1 — Trade Validations.
- [ ] **SIM-095 — Reject requests when required bid/ask data is missing or zero.**
  - *Technical Details:* Do not allow price validation or execution to continue with invalid market state.
  - *Source Trace:* P1 — Trade Validations.
- [ ] **SIM-096 — Validate stop-loss and take-profit directional logic.**
  - *Technical Details:* For buys require SL below entry and TP above; for sells require SL above entry and TP below.
  - *Source Trace:* P1 — Trade Validations.
- [ ] **SIM-097 — Implement reusable stop-level and freeze-level checks.**
  - *Technical Details:* Provide a helper equivalent to `_check_stop_level()` and apply it to opening and modification flows.
  - *Source Trace:* P1 — Trade Validations.
- [ ] **SIM-098 — Create a dedicated `TradeValidators` component.**
  - *Technical Details:* Inject symbol metadata, current tick state, account state, MT5 constants, and logger dependencies instead of duplicating validation logic in the dispatcher.
  - *Source Trace:* P3 — Trade Validation Class.
- [ ] **SIM-099 — Implement reusable lot-size validation in `TradeValidators`.**
  - *Technical Details:* Provide a method equivalent to `is_valid_lotsize` and consolidate min/max/step rules.
  - *Source Trace:* P3 — Trade Validation Class.
- [ ] **SIM-100 — Implement free-margin validation.**
  - *Technical Details:* Provide `is_there_enough_money(margin_required, free_margin)`; reject invalid margin calculations and margin requirements larger than free margin.
  - *Source Trace:* P3 — Trade Validation Class.
- [ ] **SIM-101 — Implement precision-aware market-price equality validation.**
  - *Technical Details:* Use symbol digits/epsilon logic so buy requests correspond to current ask and sell requests to current bid within tolerance.
  - *Source Trace:* P3 — Trade Validation Class.
- [ ] **SIM-102 — Implement reusable SL validation.**
  - *Technical Details:* Provide `is_valid_sl(entry, sl, order_type)` and apply buy/sell action maps.
  - *Source Trace:* P3 — Trade Validation Class.
- [ ] **SIM-103 — Implement reusable TP validation.**
  - *Technical Details:* Provide `is_valid_tp(entry, tp, order_type)` and apply buy/sell action maps.
  - *Source Trace:* P3 — Trade Validation Class.
- [ ] **SIM-104 — Define the `MqlTradeRequest`-compatible request schema.**
  - *Technical Details:* Support `action`, `magic`, `order`, `symbol`, `volume`, `price`, `stoplimit`, `sl`, `tp`, `deviation`, `type`, `type_filling`, `type_time`, `expiration`, `comment`, `position`, and `position_by`.
  - *Source Trace:* P3 — The order_send Method.
- [ ] **SIM-105 — Implement `order_send(request)` as the only low-level execution mutation gateway.**
  - *Technical Details:* Parse and normalize request fields before changing positions, orders, deals, or account state.
  - *Source Trace:* P3 — The order_send Method.
- [ ] **SIM-106 — Derive execution timestamps from the symbol tick cache.**
  - *Technical Details:* Normalize both second and millisecond times to UTC before writing positions, orders, and deals.
  - *Source Trace:* P3 — The order_send Method.
- [ ] **SIM-107 — Return MT5-style success and failure results from `order_send`.**
  - *Technical Details:* Return `retcode` and applicable `order`, `deal`, and `position` tickets; return explicit unsupported/invalid action codes.
  - *Source Trace:* P3 — The order_send Method.
- [ ] **SIM-108 — Dispatch the appropriate validator set for every `TRADE_ACTION_*` request.**
  - *Technical Details:* Apply volume, funds, price, SL/TP, stop/freeze, pending-order, and expiration validations according to action type.
  - *Source Trace:* P3 — All Validators Inside order_send.
- [ ] **SIM-109 — Validate position-close requests before closing.**
  - *Technical Details:* Confirm target position exists; require an opposite order type; use bid to close buys and ask to close sells.
  - *Source Trace:* P3 — All Validators Inside order_send.
- [ ] **SIM-110 — Validate pending-order modification requests before applying them.**
  - *Technical Details:* Confirm order existence and validate entry price, SL, TP, expiration, and stop-limit changes.
  - *Source Trace:* P3 — All Validators Inside order_send.
- [ ] **SIM-111 — Validate position SL/TP modification requests before applying them.**
  - *Technical Details:* Confirm position existence, direction, current freeze constraints, and modification timestamps.
  - *Source Trace:* P3 — All Validators Inside order_send.
- [ ] **SIM-112 — Make all validation failures non-destructive.**
  - *Technical Details:* Return a controlled failure and leave active and historical containers exactly unchanged.
  - *Source Trace:* P3 — All Validators Inside order_send.
- [ ] **SIM-113 — Implement base pending-order creation.**
  - *Technical Details:* Use `_place_a_pending_order(order_type, volume, symbol, open_price, sl=0.0, tp=0.0, comment='', expiry_date=None, expiration_mode='gtc')`.
  - *Source Trace:* P1 — Market’s Pending Orders.
- [ ] **SIM-114 — Support the initial standard pending-order set.**
  - *Technical Details:* Implement buy limit, buy stop, sell limit, and sell stop; explicitly reject unsupported stop-limit variants until intentionally added.
  - *Source Trace:* P1 — Market’s Pending Orders.
- [ ] **SIM-115 — Validate and normalize pending-order type.**
  - *Technical Details:* Reject unknown types before state mutation.
  - *Source Trace:* P1 — Market’s Pending Orders.
- [ ] **SIM-116 — Validate pending-order trigger-price placement relative to the market.**
  - *Technical Details:* Buy limits below market, buy stops above, sell limits above, sell stops below using executable bid/ask semantics.
  - *Source Trace:* P1 — Market’s Pending Orders.
- [ ] **SIM-117 — Enforce minimum pending-order distance from the current market.**
  - *Technical Details:* Use symbol stop level multiplied by point size.
  - *Source Trace:* P1 — Market’s Pending Orders.
- [ ] **SIM-118 — Validate pending-order expiry timestamps.**
  - *Technical Details:* Require supplied expiration values to be later than UTC simulation time.
  - *Source Trace:* P1 — Market’s Pending Orders.
- [ ] **SIM-119 — Persist complete pending-order execution/account metadata.**
  - *Technical Details:* Store ticket, type, symbol, requested price, SL/TP, magic, margin, expiry, and expiration mode.
  - *Source Trace:* P1 — Market’s Pending Orders.
- [ ] **SIM-120 — Implement pending-order modification as a dedicated operation.**
  - *Technical Details:* Provide `order_modify(order, new_open_price, new_sl, new_tp, new_expiry=None, new_expiration_mode=None)`.
  - *Source Trace:* P1 — Modifying Pending Orders.
- [ ] **SIM-121 — Refresh relevant market quotes before evaluating pending-order modifications.**
  - *Technical Details:* Use current ask/bid for trigger-price validation.
  - *Source Trace:* P1 — Modifying Pending Orders.
- [ ] **SIM-122 — Validate modified pending-order trigger direction by order type.**
  - *Technical Details:* Reuse the same market-relative rules used at order placement.
  - *Source Trace:* P1 — Modifying Pending Orders.
- [ ] **SIM-123 — Validate all modified pending-order fields before replacement.**
  - *Technical Details:* Validate SL, TP, expiry, and expiration mode; preserve ticket identity and historical linkage.
  - *Source Trace:* P1 — Modifying Pending Orders.

*Dependencies:* All completion gates through Phase 3.

---

# Phase 5 — Public Trade API and Position/Order Lifecycle Management

**Objective:** Expose the validated execution engine through a strategy-friendly `CTrade` interface and implement all ongoing position and pending-order lifecycle behavior.

**Completion Gate:** A strategy can open, close, modify, cancel, and inspect trades exclusively through public APIs while the engine monitors exits, triggers, and state transitions correctly.

- [ ] **SIM-124 — Implement position modification through a public lifecycle operation.**
  - *Technical Details:* Provide `position_modify(pos, new_sl, new_tp) -> bool` that copies, validates, and replaces only after success.
  - *Source Trace:* P1 — Modifying Positions.
- [ ] **SIM-125 — Validate position modifications against current executable market price.**
  - *Technical Details:* Reject buy SL at/above market and sell SL at/below market.
  - *Source Trace:* P1 — Modifying Positions.
- [ ] **SIM-126 — Reapply stop-level and freeze-level rules to all modified SL/TP values.**
  - *Technical Details:* Perform the same final validation rules as opening before committing a replacement.
  - *Source Trace:* P1 — Modifying Positions.
- [ ] **SIM-127 — Preserve all unmodified fields during a position modification.**
  - *Technical Details:* Update only SL/TP and required timestamps; retain ticket, symbol, volume, entry, P/L, and accounting data.
  - *Source Trace:* P1 — Modifying Positions.
- [ ] **SIM-128 — Implement `monitor_positions(verbose)` over active positions.**
  - *Technical Details:* Refresh each symbol’s bid/ask state and inspect every active position without mutating the container during iteration.
  - *Source Trace:* P1 — Monitoring Positions.
- [ ] **SIM-129 — Update stored current price and unrealized P/L for each active position.**
  - *Technical Details:* Use the correct executable side and the canonical profit-calculation service.
  - *Source Trace:* P1 — Monitoring Positions.
- [ ] **SIM-130 — Detect SL/TP exit conditions and close triggered positions.**
  - *Technical Details:* Create linked exit deals and realize account effects through the canonical close path.
  - *Source Trace:* P1 — Monitoring Positions.
- [ ] **SIM-131 — Provide optional position diagnostics.**
  - *Technical Details:* Include ticket, symbol, time, direction, volume, SL/TP, and current profit without affecting execution.
  - *Source Trace:* P1 — Monitoring Positions.
- [ ] **SIM-132 — Implement pending-order deletion.**
  - *Technical Details:* Provide `order_delete(selected_order) -> bool` and operate only on active pending orders.
  - *Source Trace:* P1 — Deleting Pending Orders.
- [ ] **SIM-133 — Return clear success/failure results when deleting an order.**
  - *Technical Details:* Remove existing tickets; return a controlled warning/failure for absent tickets.
  - *Source Trace:* P1 — Deleting Pending Orders.
- [ ] **SIM-134 — Keep deletion distinct from execution history.**
  - *Technical Details:* Do not create a deal merely because an untriggered pending order was cancelled.
  - *Source Trace:* P1 — Deleting Pending Orders.
- [ ] **SIM-135 — Implement `monitor_pending_orders()`.**
  - *Technical Details:* Use separate expired and triggered collections so active-order iteration remains safe.
  - *Source Trace:* P1 — Monitoring Pending Orders.
- [ ] **SIM-136 — Enforce configured pending-order expiration policies.**
  - *Technical Details:* Support at least `gtc`, `daily`, and `daily_excluding_stops` using UTC-aware comparisons.
  - *Source Trace:* P1 — Monitoring Pending Orders.
- [ ] **SIM-137 — Update each pending order’s current price from current bid/ask state.**
  - *Technical Details:* Use ask for buy-related and bid for sell-related pending orders.
  - *Source Trace:* P1 — Monitoring Pending Orders.
- [ ] **SIM-138 — Detect each supported pending-order trigger condition.**
  - *Technical Details:* Apply correct buy-limit, buy-stop, sell-limit, and sell-stop comparisons.
  - *Source Trace:* P1 — Monitoring Pending Orders.
- [ ] **SIM-139 — Convert successfully triggered pending orders into market positions.**
  - *Technical Details:* Pass stored volume, symbol, current executable price, SL, TP, and comment to the validated market-order path.
  - *Source Trace:* P1 — Monitoring Pending Orders.
- [ ] **SIM-140 — Remove processed triggered and expired orders from active state.**
  - *Technical Details:* Keep terminal history records intact while clearing only active state.
  - *Source Trace:* P1 — Monitoring Pending Orders.
- [ ] **SIM-141 — Implement a high-level `CTrade` class bound to the Tester.**
  - *Technical Details:* Initialize with tester/simulator, magic number, symbol filling type, and deviation points.
  - *Source Trace:* P3 — The CTrade Class Inside a Simulator.
- [ ] **SIM-142 — Resolve symbol-specific order filling policy in `CTrade`.**
  - *Technical Details:* Provide `_get_type_filling(symbol)` or equivalent and reject initialization when a valid policy cannot be determined.
  - *Source Trace:* P3 — The CTrade Class Inside a Simulator.
- [ ] **SIM-143 — Implement high-level market-position submission.**
  - *Technical Details:* Provide `position_open(symbol, volume, order_type, price, sl=0.0, tp=0.0, comment='')` that constructs `TRADE_ACTION_DEAL` requests.
  - *Source Trace:* P3 — The CTrade Class Inside a Simulator.
- [ ] **SIM-144 — Implement strategy-facing convenience methods.**
  - *Technical Details:* Expose `buy`, `sell`, pending-order helpers, close helpers, and order/position modification helpers that delegate only to `order_send`.
  - *Source Trace:* P3 — The CTrade Class Inside a Simulator.
- [ ] **SIM-145 — Enforce MT5-compatible comment constraints in high-level methods.**
  - *Technical Details:* Truncate or reject comments beyond the configured maximum before building requests.
  - *Source Trace:* P3 — The CTrade Class Inside a Simulator.
- [ ] **SIM-146 — Make public query APIs the only supported strategy inspection mechanism.**
  - *Technical Details:* Use `positions_get`, `orders_get`, and history APIs instead of allowing strategies to read private ledger containers.
  - *Source Trace:* P3 — Managing Orders and Positions in a Simulator.
- [ ] **SIM-147 — Verify lifecycle state after every public operation.**
  - *Technical Details:* Test counts, remaining active state, historical orders, and historical deals after open, close, modify, cancel, expiry, and trigger scenarios.
  - *Source Trace:* P3 — Managing Orders and Positions in a Simulator.

*Dependencies:* All completion gates through Phase 4.

---

# Phase 6 — Tester Orchestration, Modelling Modes, and Single-Symbol Strategy Execution

**Objective:** Build deterministic event replay over the finished execution engine, support all modeller modes, and define the strategy callback and boot sequence once.

**Completion Gate:** A configured strategy can run against real ticks, generated ticks, M1 OHLC, or new bars while all market, account, order, and position state is maintained in a documented event order.

- [ ] **SIM-148 — Initialize and verify the MT5 terminal before constructing a tester or importing data.**
  - *Technical Details:* Call `mt5.initialize()`; on failure log `mt5.last_error()`, shut down cleanly, and abort.
  - *Source Trace:* P1 — RealTime Trade Simulation in Python; P3 — Performing Trading Actions in a Simulator.
- [ ] **SIM-149 — Construct the configured Tester with explicit deposit and leverage semantics.**
  - *Technical Details:* Use the final config-driven constructor while preserving the prior simulator account assumptions.
  - *Source Trace:* P3 — Performing Trading Actions in a Simulator.
- [ ] **SIM-150 — Instantiate `CTrade` with stable magic number, symbol filling policy, and deviation settings.**
  - *Technical Details:* Use one configured trade interface per active trading context.
  - *Source Trace:* P1 — RealTime Trade Simulation in Python; P3 — Performing Trading Actions in a Simulator.
- [ ] **SIM-151 — Feed current tick state into the Tester before strategy trading operations.**
  - *Technical Details:* Retrieve a tick and call `TickUpdate(symbol, tick)` before any strategy submits an order.
  - *Source Trace:* P3 — Performing Trading Actions in a Simulator.
- [ ] **SIM-152 — Expose an explicit terminal/live mode for debugging outside replay mode.**
  - *Technical Details:* Use an intentional configuration or CLI switch such as `--mt5`; never accidentally send live orders because replay data is unavailable.
  - *Source Trace:* P3 — Performing Trading Actions in a Simulator.
- [ ] **SIM-153 — Implement real-tick test initialization for every configured symbol.**
  - *Technical Details:* Load historical ticks through the history service for the full configured test window.
  - *Source Trace:* P4 — Strategy Testing Based on REAL TICKS.
- [ ] **SIM-154 — Store real-tick replay metadata per symbol.**
  - *Technical Details:* Record symbol, tick dataset, total size, and mutable replay counter.
  - *Source Trace:* P4 — Strategy Testing Based on REAL TICKS.
- [ ] **SIM-155 — Implement chronological real-tick replay.**
  - *Technical Details:* Continue while any configured symbol has ticks; retrieve the current tick by per-symbol counter and update market state before callback execution.
  - *Source Trace:* P4 — Strategy Testing Based on REAL TICKS.
- [ ] **SIM-156 — Invoke the user strategy callback for every replay event.**
  - *Technical Details:* Provide `OnTick(ontick_func)` as the standard callback surface.
  - *Source Trace:* P4 — Strategy Testing Based on REAL TICKS.
- [ ] **SIM-157 — Provide replay progress reporting.**
  - *Technical Details:* Calculate total events across symbols and use a progress mechanism such as `tqdm` for long runs.
  - *Source Trace:* P4 — Strategy Testing Based on REAL TICKS.
- [ ] **SIM-158 — Implement the `every_tick` modelling mode.**
  - *Technical Details:* Treat it as explicitly synthetic-tick-driven rather than genuine broker-tick replay.
  - *Source Trace:* P4 — Strategy Testing Based on SIMULATED TICKS.
- [ ] **SIM-159 — Load M1 bars for synthetic-tick generation.**
  - *Technical Details:* Retrieve M1 bars for every configured symbol over the test interval.
  - *Source Trace:* P4 — Strategy Testing Based on SIMULATED TICKS.
- [ ] **SIM-160 — Implement a dedicated tick-generation component.**
  - *Technical Details:* Provide a class comparable to `TicksGen` with `generate_ticks_from_bars(bars, symbol, symbol_point, out_dir, return_df=True)`.
  - *Source Trace:* P4 — Strategy Testing Based on SIMULATED TICKS.
- [ ] **SIM-161 — Use each instrument’s point size when generating synthetic ticks.**
  - *Technical Details:* Read `symbol_info(symbol).point` before generation and keep generator rounding consistent with the instrument.
  - *Source Trace:* P4 — Strategy Testing Based on SIMULATED TICKS.
- [ ] **SIM-162 — Persist generated ticks for repeatable reuse when appropriate.**
  - *Technical Details:* Store generated datasets under a symbol-separated simulated-tick directory.
  - *Source Trace:* P4 — Strategy Testing Based on SIMULATED TICKS.
- [ ] **SIM-163 — Implement the `new_bar` modelling mode.**
  - *Technical Details:* Make it a deliberately low-fidelity mode that triggers strategy logic only at each configured-timeframe bar open.
  - *Source Trace:* P4 — Strategy Testing Based on NEW BAR.
- [ ] **SIM-164 — Load configured-timeframe bars for every symbol in new-bar mode.**
  - *Technical Details:* Store bars, size, and replay counter per symbol.
  - *Source Trace:* P4 — Strategy Testing Based on NEW BAR.
- [ ] **SIM-165 — Convert a bar to a synthetic opening tick.**
  - *Technical Details:* Implement `_bar_to_tick(symbol, bar)` using the bar open price and canonical tick schema.
  - *Source Trace:* P4 — Strategy Testing Based on NEW BAR.
- [ ] **SIM-166 — Replay bars through the common tick-update and callback path.**
  - *Technical Details:* Call `TickUpdate(symbol, current_tick)` then invoke the strategy callback; document that intra-bar movement is skipped.
  - *Source Trace:* P4 — Strategy Testing Based on NEW BAR.
- [ ] **SIM-167 — Implement the `1-minute-ohlc` modelling mode.**
  - *Technical Details:* Use M1 bars as synthetic intraday events and retain the common event processing path.
  - *Source Trace:* P4 — Strategy Testing On 1-Minute OHLC.
- [ ] **SIM-168 — Load M1 history for every configured symbol in 1-minute OHLC mode.**
  - *Technical Details:* Use the standard bar-history service and retain symbol/size/counter metadata.
  - *Source Trace:* P4 — Strategy Testing On 1-Minute OHLC.
- [ ] **SIM-169 — Replay M1 OHLC events deterministically through the bar-to-tick converter.**
  - *Technical Details:* Reuse the common callback flow and progress instrumentation.
  - *Source Trace:* P4 — Strategy Testing On 1-Minute OHLC.
- [ ] **SIM-170 — Implement `OnTick(ontick_func)` as the primary tester execution loop.**
  - *Technical Details:* Make the loop the only owner of replay progression and event sequencing.
  - *Source Trace:* P4 — Putting it All Together Inside the OnTick Function.
- [ ] **SIM-171 — Reject replay execution when tester mode is disabled.**
  - *Technical Details:* Return controlled failure/no-op when `IS_TESTER` is false rather than mixing terminal behavior into replay.
  - *Source Trace:* P4 — Putting it All Together Inside the OnTick Function.
- [ ] **SIM-172 — Select replay implementation from configured modelling mode.**
  - *Technical Details:* Support real ticks, generated ticks, new bar, and one-minute OHLC through one mode dispatch point.
  - *Source Trace:* P4 — Putting it All Together Inside the OnTick Function.
- [ ] **SIM-173 — Run account, position, and pending-order monitoring as part of every replay event.**
  - *Technical Details:* Document and consistently apply the chosen event order; do not leave monitoring responsibility to strategies.
  - *Source Trace:* P4 — Putting it All Together Inside the OnTick Function.
- [ ] **SIM-174 — Update market state before invoking strategy code.**
  - *Technical Details:* Call `TickUpdate()` before each callback so queries and orders see the current event.
  - *Source Trace:* P4 — Putting it All Together Inside the OnTick Function.
- [ ] **SIM-175 — Advance replay counters and update optional account curves during the loop.**
  - *Technical Details:* Preserve timestamps so equity/balance curves and reports can be reconstructed.
  - *Source Trace:* P4 — Putting it All Together Inside the OnTick Function.
- [ ] **SIM-176 — Implement a strategy helper that detects existing positions before entry.**
  - *Technical Details:* Query `tester.positions_get()` and filter by position type and magic number instead of examining private state.
  - *Source Trace:* P4 — Finally, Some Trading Actions in the Strategy Tester.
- [ ] **SIM-177 — Implement a standard strategy callback market-data pattern.**
  - *Technical Details:* Inside `on_tick()`, read bid/ask from `tester.symbol_info_tick(symbol)` and point size from `tester.symbol_info(symbol)`.
  - *Source Trace:* P4 — Finally, Some Trading Actions in the Strategy Tester.
- [ ] **SIM-178 — Submit market orders only when strategy position rules permit.**
  - *Technical Details:* Use `m_trade.buy(...)`/`m_trade.sell(...)` and convert SL/TP point distances to absolute price values.
  - *Source Trace:* P4 — Finally, Some Trading Actions in the Strategy Tester.

*Dependencies:* All completion gates through Phase 5.

---

# Phase 7 — Historical Queries, Reports, Visual Inspection, and Terminal-Parity Scenarios

**Objective:** Finish the single-threaded engine with auditable history APIs, reports, balance/equity evidence, visual inspection, and optional live-comparison workflows.

**Completion Gate:** A completed run produces queryable historical state and durable report artifacts; visual tools consume canonical state only; terminal comparison remains explicit and isolated.

- [ ] **SIM-179 — Implement `history_orders_total(date_from, date_to)`.**
  - *Technical Details:* Count historical orders inside the requested interval using the immutable order ledger.
  - *Source Trace:* P2 — history_orders_total and history_orders_get.
- [ ] **SIM-180 — Implement `history_orders_get(date_from, date_to, group=None, ticket=None, position=None)`.**
  - *Technical Details:* Support date-range, symbol-group, order-ticket, and position-ticket filtering and preserve order-to-position linkage.
  - *Source Trace:* P2 — history_orders_total and history_orders_get.
- [ ] **SIM-181 — Implement `deals_total(date_from, date_to)`.**
  - *Technical Details:* Count immutable deal history within the requested interval.
  - *Source Trace:* P2 — deals_total and history_deals_get.
- [ ] **SIM-182 — Implement `history_deals_get(date_from, date_to, group=None, ticket=None, position=None)`.**
  - *Technical Details:* Support date, symbol group, deal ticket, and position ticket filters in tester mode and delegate to MT5 in terminal mode.
  - *Source Trace:* P2 — deals_total and history_deals_get.
- [ ] **SIM-183 — Build an HTML tester-report template.**
  - *Technical Details:* Include separate order and deal tables with timestamps, tickets, symbol, type/direction, volume, prices, SL/TP, state, costs, profit, comment, and balance data.
  - *Source Trace:* P4 — Generating Strategy Tester Reports.
- [ ] **SIM-184 — Implement report generation from immutable historical containers.**
  - *Technical Details:* Provide a method comparable to `__GenerateTesterReport(output_file='Tester report.html')` and render historical orders/deals into rows.
  - *Source Trace:* P4 — Generating Strategy Tester Reports.
- [ ] **SIM-185 — Create an initial balance deal at tester initialization.**
  - *Technical Details:* Implement `__make_balance_deal(time)` using `DEAL_TYPE_BALANCE` and append it as the first historical deal.
  - *Source Trace:* P4 — Generating Strategy Tester Reports.
- [ ] **SIM-186 — Calculate tester performance statistics from closed deals.**
  - *Technical Details:* Calculate wins/losses, long/short results, streaks, gross P/L, drawdown, recovery factor, Sharpe, Z-score, AHPR, GHPR, linear-regression statistics, total trades, and total deals.
  - *Source Trace:* P4 — Generating Strategy Tester Reports.
- [ ] **SIM-187 — Sample account curves at a configurable interval.**
  - *Technical Details:* Implement `__curves_update(time)` and avoid writing a data point for every event unless explicitly configured.
  - *Source Trace:* P4 — Generating Strategy Tester Reports.
- [ ] **SIM-188 — Generate balance and equity chart artifacts.**
  - *Technical Details:* Implement `_plot_tester_curves(output_path)` with Matplotlib, save an image, and embed/reference it in the report.
  - *Source Trace:* P4 — Generating Strategy Tester Reports.
- [ ] **SIM-189 — Build a lightweight runtime inspection GUI.**
  - *Technical Details:* Use `tkinter`/`ttk` or an equivalent thin UI; keep business logic entirely out of the UI layer.
  - *Source Trace:* P1 — Realtime Simulations GUI Application.
- [ ] **SIM-190 — Render current account information in the GUI.**
  - *Technical Details:* Show balance, equity, margin, free margin, margin level, and floating P/L.
  - *Source Trace:* P1 — Realtime Simulations GUI Application.
- [ ] **SIM-191 — Render active positions and pending orders in separate GUI tables.**
  - *Technical Details:* Positions: ID, symbol, time, direction, volume, open/current price, SL/TP, swap, profit, comment. Orders: identity, trigger price, exits, expiry, and metadata.
  - *Source Trace:* P1 — Realtime Simulations GUI Application.
- [ ] **SIM-192 — Refresh GUI views only from canonical runtime state.**
  - *Technical Details:* Treat the UI as a ledger consumer; do not duplicate monitoring, valuation, or execution logic in widgets.
  - *Source Trace:* P1 — Realtime Simulations GUI Application.
- [ ] **SIM-193 — Implement explicit live-comparison simulation scenarios.**
  - *Technical Details:* After confirmed terminal initialization, instantiate comparable simulator/CTrade contexts and run account, position, pending-order, and order monitoring for parity observation.
  - *Source Trace:* P1 — RealTime Trade Simulation in Python.

*Dependencies:* All completion gates through Phase 6.

---

# Phase 8 — Multi-Symbol, Multi-Timeframe, Concurrent Replay, and Performance Controls

**Objective:** Scale the finished engine to multi-instrument/multi-timeframe strategies with preloaded histories, controlled concurrency, synchronized shared account state, and efficient bar-driven calculations.

**Completion Gate:** Multiple symbols and timeframes can be tested concurrently without race conditions, duplicate history fetches, or unnecessary per-tick indicator recomputation.

- [ ] **SIM-194 — Treat the primary tester timeframe as insufficient for multi-timeframe strategy requirements.**
  - *Technical Details:* Allow strategies to request bars for configured timeframes such as M15, H1, H4, and D1 through the same rate APIs.
  - *Source Trace:* P5 — The Problem with a Multi-timeframe Approach.
- [ ] **SIM-195 — Preload/synchronize every required symbol and timeframe before test execution.**
  - *Technical Details:* Do not fetch unprepared timeframe data opportunistically in the middle of replay.
  - *Source Trace:* P5 — The Problem with a Multi-timeframe Approach.
- [ ] **SIM-196 — Define controlled behavior for unavailable symbols or timeframes.**
  - *Technical Details:* Return an explicit absence/error rather than silently mixing live terminal data with replay data.
  - *Source Trace:* P5 — The Problem with a Multi-timeframe Approach.
- [ ] **SIM-197 — Implement a concurrent synthetic-tick generation worker where needed.**
  - *Technical Details:* Generate ticks from M1 bars and instrument point size using the same canonical schema as other market events.
  - *Source Trace:* P5 — Extracting Data Directly from MetaTrader 5.
- [ ] **SIM-198 — Use `ThreadPoolExecutor` for I/O-bound historical synchronization.**
  - *Technical Details:* Submit one task per configured symbol and collect completed futures via `as_completed`.
  - *Source Trace:* P5 — Extracting Data Directly from MetaTrader 5.
- [ ] **SIM-199 — Isolate historical-data failures per symbol.**
  - *Technical Details:* Log failed fetches without discarding successfully synchronized data for other instruments.
  - *Source Trace:* P5 — Extracting Data Directly from MetaTrader 5.
- [ ] **SIM-200 — Implement a per-symbol event worker.**
  - *Technical Details:* Provide a method comparable to `__ontick_symbol(symbol, modelling, ontick_func)` that owns only that symbol’s event stream.
  - *Source Trace:* P5 — Multithreaded Instruments Handling.
- [ ] **SIM-201 — Assign one worker thread per configured instrument.**
  - *Technical Details:* Each worker processes only its symbol’s tick/bar stream and calls the user callback with `ontick_func(symbol)`.
  - *Source Trace:* P5 — Multithreaded Instruments Handling.
- [ ] **SIM-202 — Treat account state and global ledgers as shared resources.**
  - *Technical Details:* Balance, equity, free margin, margin level, deals, orders, positions, and global counters require synchronized access.
  - *Source Trace:* P5 — Multithreaded Instruments Handling.
- [ ] **SIM-203 — Guard shared engine mutations with a critical-section lock.**
  - *Technical Details:* Protect `TickUpdate`, strategy execution, account/position/order monitoring, curve updates, and global index increments using an `_engine_lock`-style primitive.
  - *Source Trace:* P5 — Multithreaded Instruments Handling.
- [ ] **SIM-204 — Limit monitoring work to the active symbol when safe.**
  - *Technical Details:* Monitor positions/orders only when relevant active state exists for the current symbol, while preserving correct portfolio-wide account valuation.
  - *Source Trace:* P5 — Multithreaded Instruments Handling.
- [ ] **SIM-205 — Normalize mixed tick representations in multi-symbol replay.**
  - *Technical Details:* Accept dictionary and tuple ticks, convert tuples to canonical records, and log/skip unknown representations deterministically.
  - *Source Trace:* P5 — Multithreaded Instruments Handling.
- [ ] **SIM-206 — Classify historical query APIs as performance-sensitive operations.**
  - *Technical Details:* Treat all `copy_rates_*` and `copy_ticks_*` functions as I/O-sensitive because they read Parquet history.
  - *Source Trace:* P5 — Addressing Performance Issues Further.
- [ ] **SIM-207 — Prevent full-window historical queries on every tick.**
  - *Technical Details:* Avoid repeatedly fetching multi-timeframe data and recalculating identical indicators for each market event.
  - *Source Trace:* P5 — Addressing Performance Issues Further.
- [ ] **SIM-208 — Implement a reusable new-bar detector.**
  - *Technical Details:* Provide `is_newbar(current_time, tf) -> bool` based on tester current time and timeframe boundaries.
  - *Source Trace:* P5 — Addressing Performance Issues Further.
- [ ] **SIM-209 — Calculate bar-based indicators only on new-bar events.**
  - *Technical Details:* Fetch the needed rate window and compute indicators once per relevant bar transition rather than every tick.
  - *Source Trace:* P5 — Addressing Performance Issues Further.
- [ ] **SIM-210 — Retain tick-level position/order/account monitoring when required.**
  - *Technical Details:* Separate indicator computation frequency from execution-risk monitoring frequency.
  - *Source Trace:* P5 — Addressing Performance Issues Further.
- [ ] **SIM-211 — Declare all tradable instruments in tester configuration before initialization.**
  - *Technical Details:* Use the configuration `symbols` list as the complete trading universe for the run.
  - *Source Trace:* P5 — A Fully Functional Multi-Currency Trading Robot.
- [ ] **SIM-212 — Create one `CTrade` instance per configured symbol.**
  - *Technical Details:* Use a symbol-keyed dictionary; configure shared magic/deviation values and each symbol’s filling policy.
  - *Source Trace:* P5 — A Fully Functional Multi-Currency Trading Robot.
- [ ] **SIM-213 — Implement a symbol-aware strategy callback.**
  - *Technical Details:* Provide `on_tick_multicurrency(symbol)` and read current market state using `tester.symbol_info_tick(symbol)`.
  - *Source Trace:* P5 — A Fully Functional Multi-Currency Trading Robot.
- [ ] **SIM-214 — Gate multi-timeframe strategy logic through new-bar detection.**
  - *Technical Details:* Call `is_newbar(tester.current_time, timeframe)` before requesting history or recalculating indicators.
  - *Source Trace:* P5 — A Fully Functional Multi-Currency Trading Robot.
- [ ] **SIM-215 — Retrieve rolling rates windows for indicator calculations.**
  - *Technical Details:* Use `copy_rates_from_pos(symbol, timeframe, start_pos=0, count=20)` and normalize returned data into a DataFrame/series as needed.
  - *Source Trace:* P5 — A Fully Functional Multi-Currency Trading Robot.
- [ ] **SIM-216 — Implement the example 10-period SMA reversal strategy as an integration test.**
  - *Technical Details:* Calculate SMA from closes, compare current price to SMA, and open/reverse directional positions subject to the public position-management rules.
  - *Source Trace:* P5 — A Fully Functional Multi-Currency Trading Robot.
- [ ] **SIM-217 — Run the multi-symbol strategy through the parallel Tester event loop.**
  - *Technical Details:* Pass the symbol-aware callback into the thread-safe parallel `OnTick` implementation.
  - *Source Trace:* P5 — A Fully Functional Multi-Currency Trading Robot.

*Dependencies:* All completion gates through Phase 7.

---

# Audit Ledger

## Source-Part Reconciliation

| Source | Original Tasks | Reordered Destination |
|---|---:|---|
| Part 01 — Trade Simulator | 61 | Phases 1, 3, 4, 5, and 7 |
| Part 02 — Bars, Ticks, and MT5-Compatible Overloads | 53 | Phases 1, 2, 3, and 7 |
| Part 03 — MT5-Like Trading Operations | 29 | Phases 1, 4, 5, and 6 |
| Part 04 — Tester 101 | 42 | Phases 1, 6, and 7 |
| Part 05 — Multi-Symbols and Timeframes | 32 | Phases 1, 2, and 8 |
| **Total** | **217** | **Phases 1–8** |

## Source-Heading Coverage Ledger

This ledger makes the preservation audit explicit. Counts are the atomic task counts from the previous extraction; destination phases show where each article heading is implemented in the build-once order.

| Part | Original Requirement Category | Tasks | Destination Phase(s) |
|---|---|---:|---|
| P1 | Trading Simulator 101 | 4 | 1 |
| P1 | Calculating Profits/Losses Made By a Position | 2 | 3 |
| P1 | Simulating a Position | 4 | 3 |
| P1 | Trade Validations | 6 | 4 |
| P1 | Modifying Positions | 3 | 5 |
| P1 | Monitoring Positions | 3 | 5 |
| P1 | Market’s Pending Orders | 7 | 4 |
| P1 | Deleting Pending Orders | 3 | 5 |
| P1 | Modifying Pending Orders | 4 | 4 |
| P1 | Monitoring Pending Orders | 5 | 5 |
| P1 | Monitoring the Account | 4 | 3 |
| P1 | RealTime Trade Simulation in Python | 4 | 1, 6, 7 |
| P1 | Realtime Simulations GUI Application | 4 | 7 |
| P1 | Managing and Controlling Positions and Orders Externally | 3 | 3 |
| P1 | Working with Deals | 5 | 1, 3 |
| P2 | Handling MetaTrader 5 Historical Ticks | 6 | 2 |
| P2 | Handling MetaTrader 5 Historical Bars | 5 | 2 |
| P2 | Overloading MetaTrader 5 Functions | 4 | 1, 2 |
| P2 | symbol_info_tick | 4 | 2 |
| P2 | symbol_info | 3 | 2 |
| P2 | copy_rates_from, copy_rates_from_pos, and copy_rates_range | 5 | 2 |
| P2 | copy_ticks_from and copy_ticks_range | 4 | 2 |
| P2 | orders_total and orders_get | 4 | 1, 3 |
| P2 | positions_total and positions_get | 3 | 1, 3 |
| P2 | history_orders_total and history_orders_get | 4 | 1, 7 |
| P2 | deals_total and history_deals_get | 3 | 7 |
| P2 | account_info | 4 | 1, 3 |
| P2 | order_calc_profit and order_calc_margin | 4 | 3 |
| P3 | The order_send Method | 4 | 1, 4 |
| P3 | Trade Validation Class | 6 | 4 |
| P3 | All Validators Inside order_send | 5 | 4 |
| P3 | The CTrade Class Inside a Simulator | 5 | 5 |
| P3 | Performing Trading Actions in a Simulator | 5 | 6 |
| P3 | Managing Orders and Positions in a Simulator | 4 | 5 |
| P4 | From Simulator to Tester | 3 | 1 |
| P4 | Tester Configuration and Initialization | 5 | 1 |
| P4 | Strategy Testing Based on REAL TICKS | 5 | 6 |
| P4 | Strategy Testing Based on SIMULATED TICKS | 5 | 6 |
| P4 | Strategy Testing Based on NEW BAR | 4 | 6 |
| P4 | Strategy Testing On 1-Minute OHLC | 3 | 6 |
| P4 | Putting it All Together Inside the OnTick Function | 5 | 6 |
| P4 | Finally, Some Trading Actions in the Strategy Tester | 6 | 6 |
| P4 | Generating Strategy Tester Reports | 6 | 7 |
| P5 | Multi-Timeframe Data Handling | 5 | 1 |
| P5 | The Problem with a Multi-timeframe Approach | 3 | 8 |
| P5 | Extracting Data Directly from MetaTrader 5 | 6 | 2, 8 |
| P5 | Multithreaded Instruments Handling | 6 | 8 |
| P5 | Addressing Performance Issues Further | 5 | 8 |
| P5 | A Fully Functional Multi-Currency Trading Robot | 7 | 8 |
| **All source headings** |  | **217** | **Complete** |

## Final Reconciliation

- **Original extracted task count:** 217
- **Reordered build-plan task count:** 217
- **Difference:** 0
- **Coverage result:** Every extracted requirement is represented once in the phased plan; tutorial-driven revisits are collapsed into the earliest phase where the final form should be built.
