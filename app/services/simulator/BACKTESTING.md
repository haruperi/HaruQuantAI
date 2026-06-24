# Simple Backtesting Module

## Purpose

`haruquant.backtesting` is the first deterministic execution harness for the
JSON/Python strategy template. It allows every bundled strategy to be evaluated
on canonical OHLCV data before the full `08_simulation` module is built.

It is deliberately **bar based** and **single-symbol per run**. It is intended
for strategy development, unit tests, signal-regression checks, and early
research—not for claiming tick-accurate or broker-identical results.

```text
Historical canonical bars
    → SimpleBacktestEngine
    → MarketContext at completed-bar close
    → Strategy TradeIntent
    → Next-bar execution simulator
    → positions / pending orders / fills / equity / result ledger
```

## No-lookahead rule

At the close of bar `N`, the strategy receives only completed bars through `N`.
Any intent it emits is executed at the open of bar `N + 1`.

```text
Bar N close: strategy evaluates completed data
Bar N+1 open: queued intent is applied
Bar N+1 high/low: pending orders and existing SL/TP are evaluated
Bar N+1 close: equity marked and next strategy evaluation occurs
```

This prevents same-bar close-to-open fills and is the default contract for all
standard strategy strategies.

## Supported strategy actions

| TradeIntent | Engine behavior |
|---|---|
| `OPEN / MARKET` | Fills at next-bar bid/ask plus adverse configured slippage. |
| `OPEN / LIMIT` | Becomes a pending order; fills when side-aware OHLC reaches the limit. |
| `OPEN / STOP` | Becomes a pending order; fills when side-aware OHLC reaches the stop. |
| `CLOSE` | Closes targeted positions at next-bar executable price. |
| `PARTIAL_CLOSE` | Closes the requested aggregate quantity across target position IDs. |
| `MODIFY` | Changes SL, TP, trailing values, or clears SL/TP for targeted positions. |
| `CANCEL_PENDING` | Cancels target pending order IDs. |

It supports the controls required by the bundled MQL5 ports: separate magic
numbers, multi-position baskets, hedge positions, partial closes, SL/TP
amendments, trailing stops, pending stop/limit orders, and execution-event
reactions.

## Execution assumptions

- **Market price:** long entries use ask; short entries use bid. Long exits use
  bid; short exits use ask.
- **Spread:** `spread_points × point_size`; the input bar price is treated as a
  midpoint.
- **Slippage:** applied adversely to market orders and stop exits/fills.
- **Commissions:** `commission_per_unit` is charged on entry and exit.
- **Stop/target ambiguity:** if one OHLC bar reaches both SL and TP, configured
  `STOP_FIRST` is the conservative default. `TARGET_FIRST` exists for explicit
  sensitivity testing, not optimism.
- **Trailing stops:** a trailing level is updated after that bar's SL/TP check,
  and therefore becomes usable from the next bar. This deliberately avoids
  assuming a known favorable intra-bar path.
- **Final bar:** by default all open positions are closed at final-bar close;
  pending orders are cancelled. Set `close_open_positions_at_end=False` to
  inspect open exposure instead.
- **Execution events:** when a strategy fill occurs, its
  `evaluate_execution_event()` hook is called using the reconciled state. Any
  resulting intents are deferred to the following bar open. This enables Market
  Structure EA's OnTrade-derived pending-order workflow without same-bar path
  reuse.

## Basic use

```python
from haruquant.backtesting import BacktestConfig, SimpleBacktestEngine, load_ohlcv_csv
from haruquant.strategies import load_bundled_strategy

bars = load_ohlcv_csv("EURUSD_H1.csv")
strategy = load_bundled_strategy("naive_ma_trend")
engine = SimpleBacktestEngine(
    BacktestConfig(
        initial_balance=10_000.0,
        point_size=0.00001,
        spread_points=10.0,
        slippage_points=1.0,
        contract_size=100_000.0,
        default_quantity=0.10,
    )
)
result = engine.run(strategy, bars, symbol="EURUSD", timeframe="H1")
print(result.to_dict())
```

`load_ohlcv_csv()` expects a UTF-8 CSV containing a timezone-aware timestamp
column named `open_time`, `time`, `timestamp`, `datetime`, or `date`, together
with `open`, `high`, `low`, `close`, and optional `volume`.

## Strategies with additional requirements

### Harriet Hedging EA

Supply the H1 completed bars alongside the main M5 stream:

```python
result = engine.run(
    load_bundled_strategy("harriet_hedging_ea"),
    m5_bars,
    additional_chart_bars={"H1": h1_bars},
    chart_timeframes={"H1": "H1"},
)
```

### Market Structure EA

Supply the independently calculated, newest-first ZigZag extreme sequence at
each main-bar close. The strategy intentionally does not compute ZigZag itself.

```python
def features(index, history, as_of):
    return {"zigzag_extremes": zigzag_extremes_by_index[index]}

result = engine.run(
    load_bundled_strategy("market_structure_ea"),
    m5_bars,
    feature_provider=features,
)
```


## Result contract

`BacktestResult` returns:

- `closed_trades`: full realized trade ledger with entry/exit prices, costs,
  reasons, magic number, comment, and net P&L;
- `equity_curve`: one marked-to-market observation per completed primary bar;
- `events`: fills, modifications, cancellations, strategy diagnostics, and
  execution-reaction events;
- `open_positions` and `pending_orders`: non-empty only when final flattening
  is disabled;
- `metrics`: initial/final balance, net profit, return, win rate, gross profit,
  gross loss, profit factor, and max drawdown.

## Explicit non-goals

This is **not** yet the production simulation engine. It does not model:

- tick sequencing, order-book depth, partial market fills, queue position, or
  liquidity limits;
- latency, rejects, rate limits, broker-specific stop levels, swap/rollover,
  financing, dividends, corporate actions, or exchange fees;
- margin liquidation, cross-symbol/netting account behavior, portfolio VaR,
  correlation constraints, or prop-firm policy enforcement;
- multiple primary symbols in one run, walk-forward orchestration, optimization,
  or advanced analytics beyond the included first-pass metrics.

Those belong in HaruQuant's later `Simulation`, `Risk`, `Portfolio`, and
`Analytics` modules. The simple backtester is intentionally honest about those
boundaries.
