# Canonical trading API

This package is the only strategy-facing implementation of the eight MQL5-shaped
classes: Trade, AccountInfo, SymbolInfo, OrderInfo, HistoryOrderInfo, PositionInfo,
DealInfo and TerminalInfo. Every remote/model operation is asynchronous. Callers
use the same classes with live MT5 or local simulation.

```text
strategy -> Trading and eight async classes -> TradingBackend capability
                                             |                    |
                                         MT5Backend        SimulationBackend
                                             |                    |
                                      authenticated Bridge   local model/handlers
                                             |
                                    native MT5 C* objects
```

The API vocabulary is compatible with the standard eight classes; it does not
select brokers or contain broker-specific calculations. Object IDs and per-object
locks keep mutable selection/request/result state isolated. Backend modules own
execution, native/model state, receipts and events. Contract records and the async
protocol live in app/services/brokers/contracts.py.

## Calling code

```python
from app.services.trading import Trading


async def read_account(backend):
    async with Trading(backend) as trading:
        await trading.wait_connected(timeout=60)
        balance = await trading.account.Balance()
        await trading.symbol.Name("EURUSD")
        bid = await trading.symbol.Bid()
        return balance, bid
```

Supply MT5Backend for live MT5, or SimulationBackend with registered symbols and
externally supplied ticks for simulation. MT5Backend retains convenience members
such as backend.account, but they are instances of these same canonical classes.
There are no alternative classes/proxies folders under brokers.

Generic selected-object InfoInteger/InfoDouble/InfoString calls return
PropertyValue. AccountInfo/TerminalInfo property calls return scalars. Trade
Request/Result/CheckResult return dictionaries. Enums retain native numeric values;
seconds/milliseconds stay integer values. Symbol Name() reads the binding;
Name("EURUSD") returns a binding boolean. StoreState and void native setters return
booleans consistently across backends.

Trade methods retain the distinction between immediate dispatch and eventual
execution. Explicit arming permits mutations on the selected backend; simulated
arming grants no live authority. Native timeout/connection uncertainty retains
UNCERTAIN receipts and disarms the live bridge. Read receipts through
trading.receipt(command_id); reconcile observed state before retrying uncertain
trades. Events are backend-originated, not interchangeable proofs of complete fills.

## Simulation

```python
from datetime import UTC, datetime
from app.services.brokers.contracts import SymbolSpec
from app.services.brokers.simulator import SimulationBackend
from app.services.trading import Trading

backend = SimulationBackend()
backend.add_symbol(SymbolSpec(name="EURUSD"))
backend.feed_tick("EURUSD", bid=1.1, ask=1.1002, time=datetime(2026, 1, 1, tzinfo=UTC))
trading = Trading(backend)
# await trading.account.Balance()
```

The simulator owns margin/fills/order/position/deal state. Only feed_tick/set_clock
advance local time; strategy queries do not. Native-method handlers are private
functions and state records in brokers/_simulation_api.py, not a second public
set of eight classes. The synchronous BrokerBackend ABC describes only the
internal snapshot model; TradingBackend is the async strategy execution boundary.

The local model supports named property fields (including common native prefixes
and aliases), not numeric property IDs. Unknown/unavailable properties and
unsupported operations fail explicitly. No fabricated zero/success is returned
for missing property evidence. Simulation emits local simulation_transaction
events. It has no native request IDs, so await_request_event raises a typed
UNSUPPORTED_OPERATION error; next_event supports local events and timeouts.
Queued asynchronous trade execution via SetAsyncMode(True) is also unsupported
in the local model; the public API itself is always async.
Native FormatRequest text formatting is terminal-specific and is not byte-for-byte
identical to the simulator's JSON formatter.

A future cTrader backend implements TradingBackend and maps native operations into
this declared compatibility vocabulary. Unsupported capabilities must fail
explicitly rather than silently invent MT5 data. No cTrader backend is implemented
by this consolidation.

## Verification

```powershell
uv run pytest tests/unit/services/test_trading_api.py tests/unit/services/test_trading_backend_parity.py tests/unit/services/test_trading_simulator.py --no-cov
```

Tests exercise actual local models and bounded native transport fixtures. They do
not connect to a live terminal or certify real broker fills.


## Nineteen named usage functions

Run `uv run python -m scripts.examples.brokers` from the repository root.
Select `BROKER = "mt5"` or `"simulator"` in `scripts/examples/brokers.py`.
Only the setup factory imports providers; all example functions use `Trading`.
The current owner-selected flags are preserved. Keep `ALLOW_LIVE_TRADING = False`
for read-only MT5. Simulation runs all functions with explicitly seeded history.

The legacy seventeen-function sequence is implemented as async functions:

1. `example_01_connect`
2. `example_02_terminal`
3. `example_03_account`
4. `example_04_symbol`
5. `example_05_position`
6. `example_06_order`
7. `example_07_history_order`
8. `example_08_history_deal`
9. `example_09_open_position`
10. `example_10_calc_profit_margin`
11. `example_11_modify_position`
12. `example_12_close_partial_position`
13. `example_13_close_position`
14. `example_14_pending_orders`
15. `example_15_modify_pending_orders`
16. `example_16_delete_pending_orders`
17. `example_17_shutdown`
18. `example_18_historical_bars`
19. `example_19_tick_data`

Functions 18/19 run before function 17 so shutdown remains last. Shutdown also
runs once on failure. Each function accepts an explicit `ExampleContext` from the
script, so callers may run selected functions after connection/symbol setup.
`EXAMPLES` contains the eighteen non-shutdown functions; `run_examples` owns the
final shutdown and reports one result per function.

Each function directly calls the relevant trading class and reports its fields.
Only one small reporting helper formats the output; backend setup and the runner
handle connection ownership. Trade checks are written in the functions that need
them, and ExampleContext carries the run's owned tickets between those functions.

Position/order/history functions read at most five samples and clearly report
a preview, including empty results; the sample count is not a total account count.
Account identity, local paths, comments and arbitrary exception messages
are excluded from output. Useful financial/specification fields and up to five
bar/tick samples are displayed with their field names. Logs never contain authentication.

Live functions 9 and 11–16 require `ALLOW_LIVE_TRADING = True` and hedging mode.
The buy opens **twice VOLUME** (currently 0.02 lots); partial close removes VOLUME
(0.01), and full close removes the remainder. Lot constraints are checked before
buying. Position modification sets distant SL/TP; the pending BuyLimit is placed,
modified farther from price, then cancelled. Every mutation validates retcode and
observable state, using only tickets correlated with the run's deal/magic/symbol.
Pre-existing positions and orders are only previewed. No close-by-symbol fallback,
automatic trade retry or cleanup of unknown resources is performed. Failures can
leave resources open; inspect and reconcile them before running again.

## Historical market data

The eight native-shaped classes remain unchanged. Read-only helper functions
`get_historical_bars` and `get_ticks` and matching `Trading` methods supplement
the composition through an internal `MarketData` backend dispatch.

```python
from datetime import UTC, datetime, timedelta
from app.services.brokers.contracts import Timeframe
from app.services.trading import Trading

trading = Trading(backend)
end = datetime(2026, 10, 9, 12, 5, tzinfo=UTC)
start = end - timedelta(minutes=5)
bars = await trading.get_historical_bars("EURUSD", Timeframe.PERIOD_M1, start, end)
ticks = await trading.get_ticks("EURUSD", end - timedelta(seconds=10), end)
```

`MarketBar` and `MarketTick` are immutable contract records. Bars contain UTC
opening epoch seconds, OHLC, tick/real volume and spread. Ticks preserve epoch
milliseconds, bid/ask/last, integer/real volume and flags. Rows are chronological;
ticks sharing a millisecond retain their distinct records. Bounds are inclusive;
sub-second bar bounds are rounded inward, as are sub-millisecond tick bounds.
Aware dates are mandatory. An explicit `Timeframe` is required; CURRENT is rejected.
An explicit tick date_from must be after epoch zero because native CopyTicks treats zero specially.

A request accepts `limit` from 1 to 1000 and has a 60-second response deadline.
Oversized date spans/row counts raise `DATA_LIMIT_EXCEEDED`; narrow the interval
rather than assuming the response was silently truncated. Bar range size is
conservatively bounded using timeframe duration before native allocation. Tick
copy requests at most limit+1 rows from the start, then filters through the end.
Data availability/terminal synchronization errors raise `DATA_NOT_READY`; empty
successful intervals are reported honestly. There is no automatic history retry.
No persistence schema changes are required for market-data reads.

Simulation requires `seed_bar_history(symbol, timeframe, records)` and
`seed_tick_history(symbol, records)`. Missing seeded series fail explicitly;
explicitly seeded empty series return empty data. Reads do not aggregate bars,
advance time or add tick history implicitly. `feed_tick` retains its trading-model
semantics. The example factory supplies three synthetic bars and ticks; real
simulation callers supply their own historical data.

Edit `DATE_FROM`, `DATE_TO`, `TICK_DATE_FROM`, `TIMEFRAME` and `DATA_LIMIT` in the
script for your desired periods. Defaults cover five minutes of bars and ten
seconds of ticks ending at the import-time UTC minute; market closures can produce
empty history. Native historical download may require narrowing/preloading dates.

MT5 requires a rebuilt `scripts/mql5/Experts/PythonBridge.mq5` for these reads.
Copy it into the terminal, compile in MetaEditor, and reload the attached EA with
the matching token. The shared journal remains `data/database/haruquantai.db`,
using `mt5_commands`/`mt5_events`. Old EA builds fail on new read commands.


## Optional historical-read selectors

The same two functions route according to their arguments; no additional public
scenario functions are needed:

```python
# Bars from a date, moving forward through time.
bars = await trading.get_historical_bars(symbol, timeframe, date_from=start, count=100)
# Bars by native index: zero is the current, potentially unfinished bar.
bars = await trading.get_historical_bars(symbol, timeframe, start_pos=10, count=100)
# Inclusive date range (existing positional dates also work).
bars = await trading.get_historical_bars(symbol, timeframe, date_from=start, date_to=end)
# Latest bars; a date alone runs through the current UTC instant.
bars = await trading.get_historical_bars(symbol, timeframe, count=100)
bars = await trading.get_historical_bars(symbol, timeframe, date_from=start)
# Index alone returns indices start_pos through zero (chronologically).
bars = await trading.get_historical_bars(symbol, timeframe, start_pos=10)

# Ticks from a date/count, date range, latest count or date through now.
ticks = await trading.get_ticks(symbol, date_from=start, count=100)
ticks = await trading.get_ticks(symbol, date_from=start, date_to=end)
ticks = await trading.get_ticks(symbol, count=100)
ticks = await trading.get_ticks(symbol, date_from=start)
```

All rows return oldest-first. Bar index/count follows native indexing toward
older bars; date/count moves forward for both bars and ticks. Forward bar counting
is intentional: the EA uses date-to-index selection, since native CopyRates'
date/count overload counts older bars. Ticks sharing a millisecond remain distinct.

No selector/count defaults to the latest `limit` rows (1000). Explicit count asks
for up to that many available records; fewer rows near available/current history
can be valid. Date-only endpoints use one captured current UTC instant, not a
future end-of-day. Simulation also filters out seeded records after its model
clock without advancing time. Capacity remains 1000 for testing, implemented in
our code; oversized date/position ranges fail rather than silently truncate.

Reject date_from combined with start_pos, date_to without date_from, explicit
date_to combined with count, booleans/non-integer count/index, nonpositive counts
and negative/out-of-native-range indices. Existing deadlines, DTO validation,
frame limits and absence of automatic retries/saving remain unchanged.

Example functions 18 and 19 demonstrate the selectors directly. Recompile/reload
the updated EA before using the extended wire routes; deployed files are not
updated by editing repository source.


## Connection evidence in example one

Example one first awaits backend readiness, then calls `TerminalInfo.IsConnected`
and immediately reads that command's receipt. Its output shows the actual returned
boolean, probe name, command ID, resolved receipt status and send/acknowledgment/
resolution timestamps. Missing/mismatched/incomplete evidence or a false terminal
connection stops the example instead of printing a hardcoded success.

MT5 readiness means Python validated the EA hello/token and issued hello_ack. The
correlated terminal response then supplies observable two-way bridge evidence;
IsConnected also indicates the terminal's broker connection. Simulator readiness
and receipt are local model evidence and do not claim a native network handshake.
Evidence applies at that instant, not indefinitely and not as proof of trade fills.
Credentials, account identity, raw receipt metadata and private session state are
never included in this report. No EA protocol change/rebuild is needed for this
example-only evidence change.
