# Shared trading API

Import `Trading`, `Trade`, and information proxies from `app.workspace.trading`.
The former `app.include.trading` module and include-level trading exports have
been removed. Contracts, enums, and the `TradingBackend` protocol remain in
`app.include` so foundational modules do not depend on workspaces.

`api.py` composes the eight interfaces and delegates lifecycle, receipts, and
backend events. `base.py` handles serialized proxy calls, snapshot conversion, request normalization,
wire serialization, and typed execution/check result conversion.
`trade.py`, `account.py`, `symbol.py`, `positions.py`, `orders.py`, `history.py`,
and `terminal.py` own their respective public interfaces. Missing result codes decode as errors.

Strategies use the same facade and requests with MetaTrader, cTrader, or the
simulator. Inject the backend; this package does not construct broker clients.
Broker transport, authentication, execution, and simulation fills stay in
`app.workspace.brokers`. Generic MQL-style adaptation resides in
`brokers/trading_dispatch.py`, with selection and request/result state isolated
by proxy object ID. Async typed collection getters are supported, as are symbol,
ticket, position, and group filters. Unsupported filters fail explicitly.

Generic dispatch enforces arming before OrderSend and records rejected receipts.
OrderCheck remains available without arming. Queued execution and native request
correlation are backend capabilities; unsupported operations raise explicitly.
Trade setters retain per-object configuration, but low-level OrderSend and
OrderCheck use the explicit TradeRequest fields, including magic, deviation,
and filling. Setters do not overwrite explicit requests. Automatic filling
selection inspects the canonical symbol specification and reports failure when
no supported mode can be selected.

Simulation time continues to advance only through caller-provided clock/ticks.
The shared API does not impose broker fill behavior or replace broker validation.

Run focused verification with:

```powershell
uv run pytest tests/workspace/trading tests/workspace/brokers tests/examples/test_brokers.py --no-cov
```

## Shared order actions

`Trade` implements the twelve entry, close, cancel, and protection operations:

| Entry | Close/cancel | Protection |
| --- | --- | --- |
| `enter_at_market` | `close_position` | `set_stop_loss` |
| `enter_at_limit` | `close_all_positions` | `set_profit_target` |
| `enter_at_stop` | `close_best_position` | |
| `enter_reverse_at_market` | `close_worst_position` | |
| | `cancel_pending_order` | |
| | `cancel_all_pending_orders` | |

```python
from app.workspace.trading import TradeFilter

result = await trading.trade.enter_at_market(
    "EURUSD", 1, 0.02, magic=42, comment="entry", sl=1.08, tp=1.14
)
scope = TradeFilter("EURUSD", magic=42, comment="entry")
results = await trading.trade.set_stop_loss(scope, 1.09)
result = await trading.trade.close_position(scope, volume=0.01)
```

Entry direction is `1` (buy) or `-1` (sell). Matching uses resolved symbol names,
direction, exact magic number, comment substring, and optional ticket. A filter
must be supplied for exits and modifications; `None` for symbol/magic means any,
and direction zero means either side. Magic zero matches zero exactly, unlike
SQX's wildcard convention. The broker contracts have no strategy-name ownership
field, so callers must assign and filter by strategy magic numbers explicitly.

Single operations return `TradeResult`, or `None` for no match/a skipped entry.
Bulk operations return an ordered list and stop at the first unsuccessful result.
Best/worst selection ranks profit plus swap and commission; ties keep backend
collection order. Close-position supports full and partial volume. Cancellation
only touches pending orders; close operations only touch positions. Protection
updates apply to matching positions and pending orders and preserve the other
protective level, pending entry price, filling, and expiry. Zero removes a level.

Entry duplicates are scoped to symbol, magic, and comment substring. By default,
a matching position blocks entry. `allow_duplicate_trades=True` permits additional
requests; netting or hedging remains a backend account behavior. Pending entries
replace matching same-direction pending orders by default; `replace_existing=False`
skips them. The candidate is checked before cancellation, so an invalid replacement
leaves its predecessor intact. Reversal closes all matching opposite positions and
verifies their absence before entering. A same-direction position blocks reversal
when duplicates are disabled. Partial or unconfirmed intermediate results stop
replacement/reversal; no request is automatically retried or rolled back.

High-level workflows are serialized per `Trade` instance. They call the existing
`OrderCheck` and `OrderSend`, accepting native check code zero and simulator DONE.
Arming is still enforced by the execution backend. Multi-request actions are not
atomic across brokers, other Trade instances, external terminals, or processes.
An exception after cancellation/closure can leave that completed change in place.

The magic, deviation, and filling setters supply high-level request defaults.
Explicit low-level requests remain unchanged. Without a filling override, market
orders choose supported FOK/IOC (or RETURN for non-market execution); pending orders
use RETURN. Price levels align to the symbol tick step, and volume must satisfy
symbol limits and step. Brokers remain authoritative for margin and execution.

These are independently implemented action counterparts, not the SQX builder or
engine-specific export behavior. Strategy formulas must supply evaluated volume,
price, stop, and target values; resolve Current/Any before entry. For pending expiry,
pass a timezone-aware `expiration`; a future strategy runtime must translate bar
validity into an expiry using its chart/calendar. Advanced trade management,
formula evaluation, bar callbacks, platform-specific pending-to-market fallbacks,
and exit-index bookkeeping are outside this order-action API. StrategyControl
queries are described below.


## StrategyControl queries

The 25 SQX StrategyControl counterparts are implemented on the shared interfaces:

| Interface | Queries |
| --- | --- |
| `account` | `account_balance`, `account_equity` |
| `position` | `market_position`, `market_position_is_flat`, `market_position_is_long`, `market_position_is_short`, `market_position_is_not_long`, `market_position_is_not_short` |
| `position` | `market_positions_count`, `market_position_size` |
| `position` | `open_pl_in_money`, `open_pl_in_pips`, `bars_since_order_open` |
| `position` / `order` | `order_open_price`, `order_sl`, `order_pt` (position or pending-order view respectively) |
| `order` | `pending_order_exists`, `pending_order_doesnt_exist` |
| `history_order` | `closed_pl_in_money`, `closed_pl_in_pips`, `last_order_was`, `last_order_was_not` |
| `history_order` | `bars_since_order_closed`, `trade_recently_closed`, `no_trade_recently_closed` |

All take the same `TradeFilter` used by actions. Missing prices/levels and bar
counts return -1; missing P/L, count, and volume return zero. `market_position`
returns the first matching direction (1, -1, or 0 when flat). Long/short predicates
check any matching position, so both can be true in a hedged account. Position
size is the gross sum of matching volumes, not signed net exposure. Pending
orders do not contribute to position queries.

Open money P/L sums broker-reported profit, swap, and available signed commission.
An optional `prices={symbol: price}` values positions at explicit strategy decision
prices through the existing broker profit calculation. Open pip P/L uses current
position prices unless decision prices are supplied. These queries never mutate
positions or feed ticks. Every matched symbol must have a supplied decision price;
missing prices fail rather than silently falling back. Pips use canonical
`pip_size`, falling back to `tick_size` when no pip size is configured. Pip P/L
sums directional price changes without volume weighting.

`history_order.closed_trades(scope, as_of=...)` reconstructs immutable `ClosedTrade`
records from trading deals. It includes all entries and partial exits, emitting a
completed lifecycle only when flat. Netting INOUT deals close one lifecycle and
open the next; commissions and fees split by closed/opened volume. Realized money
P/L sums reported profits, entry/exit commissions, swap, and fees; pip P/L uses
volume-weighted entry and exit prices. The filter matches original entry identity,
so manual exit comments/magic do not reassign a trade. Ticket filters refer to
position identifiers. `trades_ago=0` selects the latest completed lifecycle,
1 the previous, and so on. Cancelled or expired pending orders are excluded.
`last_order_was_not` is false when no completed trade exists.

Reconstruction requires complete entry/exit history. Orphan closes, duplicate
execution tickets, and conflicting netted ownership fail explicitly instead of
inventing a cost basis or attributing one strategy's trade to another. Backend
history limits/availability remain authoritative; these queries cannot recover
missing executions. Non-trading balance/commission account operations are excluded;
only charges attached to execution deals are attributed to trades.

Time-sensitive queries require explicit aware timestamps. Supply actual chart bar
starts oldest first to `bars_since_order_open` / `bars_since_order_closed`, plus
`as_of`; the bars must cover the event. They count strictly later bar starts and
respect session gaps, rather than dividing elapsed seconds by a timeframe.
Recent-close checks require `as_of` and, when checking the current bar, `bar_start`.
The current-minute test uses the calendar minute containing `as_of`. Repeated
queries are stable and non-consuming; `no_trade_recently_closed` is its complement.
These rules intentionally omit SQX engine-specific shortcuts and mutable scan
cursors. History queries accept `as_of` to exclude later completions; open-position
queries describe the backend's present state and are not historical reconstruction.

```python
scope = TradeFilter("EURUSD", magic=42)
flat = await trading.position.market_position_is_flat(scope)
net_open = await trading.position.open_pl_in_money(scope)
last_closed = await trading.history_order.closed_pl_in_money(scope)
recent = await trading.history_order.trade_recently_closed(
    scope, as_of=decision_time, bar_start=current_bar_start
)
```

The MT5 bridge history response now includes `fee` and `time_msc`. Compile and
reload the updated `scripts/mql5/Experts/PythonBridge.mq5` to receive those fields
from the live terminal. Existing responses without them have zero fees and
second-resolution timestamp fallback. Python tests exercise typed and dictionary
responses; they do not certify a running terminal or compile the MQL5 EA.

Backends without execution history or decision-price profit calculation raise
`UNSUPPORTED_OPERATION`; an unavailable feature is not interpreted as zero P/L
or an empty trade history. cTrader currently lacks these inherited capabilities.


## Exit policies

`exits.py` provides `StopLoss`, `ProfitTarget`, `MoveSL2BE`, `TrailingStop`, and
`ExitAfterBars`, composed in an immutable `ExitPlan`. The shared facade exposes
`trading.exits`, an `ExitManager` using the same Trade and query interfaces as
strategy actions. No broker-specific implementation or background task is added.

```python
from app.workspace.trading import (
    ExitAfterBars,
    ExitPlan,
    MoveSL2BE,
    ProfitTarget,
    StopLoss,
    TradeFilter,
    TrailingStop,
)

await trading.exits.attach(
    TradeFilter("EURUSD", magic=42),
    ExitPlan(
        stop_loss=StopLoss(1.09),
        profit_target=ProfitTarget(1.12),
        move_sl_to_be=MoveSL2BE(activation=0.0010, offset=0.0001),
        trailing_stop=TrailingStop(distance=0.0005, activation=0.0015),
        exit_after_bars=ExitAfterBars(10),
    ),
)
outcomes = await trading.exits.evaluate(
    as_of=decision_time,
    prices={"EURUSD": decision_price},
    bar_times={"EURUSD": chart_bar_starts},
)
```

The strategy runtime calls `attach` after fills and `evaluate` on its chosen bar
or tick events. Attach selects currently filled positions, never pending orders.
Use entry `sl`/`tp` fields for initial protections when submitting an entry; exit
policies update filled positions during explicit evaluations. Formula evaluation
belongs to the strategy runtime: supply evaluated absolute SL/PT prices and
price-distance activation, offset, and trailing values. Pip counts must first
be converted to price units. Break-even refers to entry plus the configured
offset, without estimating commissions or swap. Netting uses the current weighted
entry price exposed by PositionInfo, not a separate last-entry price.

State is isolated by ticket, stable identifier, symbol, magic, side, and opening
time. Reattaching an existing lifecycle updates its plan while retaining favorable
prices and activation state. Closed, missing, or reversed lifecycles are pruned;
new fills require attachment. State is in memory and is not restored automatically
after process restart. `detach(ticket)` removes policy state but cannot cancel an
already dispatched request.

A due bar exit takes precedence over stop/target changes. Bar counts use actual
chart starts and explicit aware evaluation time, including session gaps. Zero
exit bars disables that policy. Stop-loss, break-even, and trailing candidates
are combined into one most-protective valid stop; stops are tightened rather than
removed or loosened. Trailing uses favorable decision-price extrema after its
activation gate. Target changes preserve the stop. Prices align to the symbol's
tick grid and respect the quoted side, stops distance, and freeze distance;
ineligible levels are skipped, and brokers still perform final validation.
Policy changes affect positions only, even when pending orders share a numeric
ticket. `Trade.set_stop_loss(..., tighten_only=True)` rechecks protection under
the Trade workflow lock; unchanged/tighter existing stops return NO_CHANGES
without dispatch. This is not an atomic guarantee against other terminals or
independent Trade instances modifying the account.

`evaluate` returns `ExitOutcome` records for requested actions. It uses the
position's current liquidation price unless a complete per-symbol decision-price
mapping is supplied. Bar-count exits additionally require chart starts covering
each entry. Repeating an evaluation timestamp does not resend actions; backward
timestamps are rejected. `market_open=False` skips evaluation without consuming
the event. The caller owns market-session scheduling and clock progression.

Rejected, partial, unconfirmed, or exceptional execution blocks that lifecycle;
inspect `trading.exits.blocked_tickets`, reconcile broker state, then explicitly
call `resume(ticket)` before a later event. Positive broker results are checked
against the resulting position state. There are no automatic retries or rollback,
and actions across multiple positions or the SL/PT pair are not transactional.
The simulator retains actual stop triggering and fill behavior; this manager
only makes shared decisions and submits the existing trade operations. SQX
formula engines, platform-specific export quirks, and event registration are
not reproduced by a second simulator-only exit implementation.
