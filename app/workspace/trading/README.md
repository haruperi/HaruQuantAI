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

## Canonical strategy operations

Strategy operations now live in `app/include/blocks/order` and
`app/include/blocks/strategy_control`. The old lowercase helper methods and
workspace exports of `TradeFilter` / `ClosedTrade` have been removed.
Import each operation from its owning module:

```python
from app.include.blocks.order.open.enter_at_market import enter_at_market
from app.include.blocks.order.close.close_best_position import close_best_position
from app.include.blocks.order.types import TradeFilter
from app.include.blocks.strategy_control.market_positions_count import (
    market_positions_count,
)

await enter_at_market(trading, "EURUSD", 1, 0.02, magic=42)
scope = TradeFilter("EURUSD", magic=42)
count = await market_positions_count(trading, scope)
result = await close_best_position(trading, scope)
```

`Trading` structurally implements the foundational `TradingRuntime` protocol.
Blocks own filtering, ranking, duplicate policies, reversal, replacement, P/L
aggregation, history reconstruction, and chart-bar predicates. No include module
imports workspace trading or broker implementations. Package initializers do not
load sibling blocks; each file is independently discoverable.

`Trade` retains raw request/result APIs and concrete execution primitives:
`prepare_entry_request`, `send_checked`, `close(position, volume)`, `cancel(order)`,
and `modify_protection(item, sl=..., tp=...)`. These operate on explicit requests
or selected snapshots. They do not select the best/worst position or execute a
strategy predicate. Symbol normalization, volume constraints, filling selection,
request checking and broker submission remain here. Blocks share the executor's
`operation_lock` to serialize complete workflows.

The 12 order and 25 state-query blocks, donor mappings, explicit semantics and
qualification limits are documented in `docs/dev/trading-block-migration.md`.


## Exit policies

`exits.py` provides `StopLoss`, `ProfitTarget`, `MoveSL2BE`, `TrailingStop`, and
`ExitAfterBars`, composed in an immutable `ExitPlan`. The shared facade exposes
`trading.exits`, an `ExitManager` using the same Trade and query interfaces as
strategy actions. No broker-specific implementation or background task is added.

```python
from app.include.blocks.order.types import TradeFilter
from app.workspace.trading import (
    ExitAfterBars,
    ExitPlan,
    MoveSL2BE,
    ProfitTarget,
    StopLoss,
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
