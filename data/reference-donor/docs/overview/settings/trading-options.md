# Trading options — Builder settings panel
> Sets the trading-behaviour and backtest-engine rules every generated strategy must obey — session and time filters, end-of-day/week exits, trade limits, SL/PT caps and realistic fill handling.

**Field-level controls (for UI tests):** [fields/trading-options.md](fields/trading-options.md)

## What it configures

This panel specifies properties that apply to all generated strategies and to how the
backtesting engine simulates them. It governs *when* a strategy is allowed to trade (session,
time range, end-of-day/Friday exits), *how many* trades it can take, hard limits on Stop Loss
and Profit Target sizes, and a few engine-level realism settings. These rules are enforced on
every candidate during generation and carried into the exported strategy.

## Main options

- **Exit At End Of Day / Exit On Friday** — close all open positions at a specified time at
  the end of each day or at the end of the week (Friday), so no positions are held overnight
  or over the weekend.
- **Limit Time Range** (Time Range From / To, Exit At End Of Range) — restrict the hours in
  which the strategy checks for entry signals. With **Exit At End Of Range** enabled, open
  positions are also closed at the end of the range; without it, no new trades open outside
  the range but existing positions stay open.
- **Maximum Trades Per Day** — cap the number of trades the strategy may take in a single day.
- **Minimum / Maximum SL & PT** — hard lower/upper bounds on Stop Loss and Profit Target
  (`0` = unlimited). Whatever value the strategy computes is clipped to stay within this range.
- **Session** — the trading session used for futures/equities intraday trading. Sessions
  themselves are created and managed in the **Data Manager**.
- **Reserved bars** — number of bars reserved before trading begins; must be larger than the
  period of any indicator the strategy uses (so indicators are fully "warmed up").
- **Realistic gaps handling** (MT4 / MT5 only) — fill Stop/Limit orders at the price *after* a
  gap, as in real live trading, instead of at the desired order price the way the MetaTrader
  backtester does. More realistic, but results may then differ from a native MetaTrader backtest.
- **Store Chart Data** — also save the full chart data for the backtest, so the strategy can
  later be reviewed visually with all indicators and orders drawn on the chart (via
  **Results → Trades on chart**).

## How it affects generation

These options constrain the trading behaviour of every candidate, so they shape both what
gets generated and how each backtest is scored. Session, time-range and end-of-day/Friday
rules bound *when* trades happen; max trades per day and the SL/PT caps bound *how much* risk
and activity a strategy can express, keeping generated strategies within limits that match
how you intend to trade them. Reserved bars and realistic gaps handling affect backtest
correctness and realism, while Store Chart Data only adds review information (at the cost of
larger stored results) and does not change results.

## Related

- Parent: [../builder.md](../builder.md)
- Concepts (backtest, orders and exits): [../concepts.md](../concepts.md)
- Sibling panels: [what-to-build.md](what-to-build.md) · [data.md](data.md) · [money-management.md](money-management.md) · [cross-checks.md](cross-checks.md)
- Data Manager (where sessions are defined): [../data-manager.md](../data-manager.md)
- Developer detail: [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md)
