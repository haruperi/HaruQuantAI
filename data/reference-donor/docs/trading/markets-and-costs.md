# Markets, data quality and trading costs

A backtest is a simulation of an instrument you did not trade, on data you did not receive, at
prices you would not have got. This page covers the assumptions that decide whether a backtest
resembles reality — the trading-side companion to the
[Data Manager](../overview/data-manager.md) and the
[Data settings panel](../overview/settings/data.md).

## What differs between instrument classes

| Class | Traded as | Cost model | Watch out for |
|---|---|---|---|
| **Forex** | CFD / spot, lots | spread + commission, swap overnight | session liquidity — spreads blow out at rollover and in Asia |
| **Indices / commodity CFDs** | CFD | spread, financing | dividend/expiry adjustments baked into the series |
| **Futures** | contracts | commission + exchange fees, tick value | continuous-contract stitching at rollover creates fake gaps |
| **Stocks / ETFs** | shares | commission, sometimes per-share | splits and dividends; survivorship bias in any basket |
| **Crypto** | spot / perp | taker fee, funding | 24/7 sessions, exchange-specific prices, short history |

The **tick value** and **contract size** are what turn a price move into money — the same 50-point
move is a different P/L on NQ, GOLD and EURUSD. Getting these wrong in the symbol setup makes
every downstream metric wrong in a way that looks plausible.

## Data quality

Downstream analysis cannot repair bad input:

- **Length and regime coverage.** You want years spanning trending, ranging and crisis regimes.
  A system built on 2021 alone has never seen a market it will meet.
- **Gaps and bad ticks.** Missing sessions and spike ticks create fake breakouts and fake
  mean-reversion snap-backs — exactly the patterns generators love to find.
- **Timezone and DST.** Session-based rules (open-range breakouts, hour filters) are meaningless
  if the data's timezone is not the one you assume; a DST shift silently moves every hour filter
  by an hour for half the year.
- **Broker differences.** Two brokers' EURUSD H1 are not the same series. A strategy that only
  works on one data source has an edge in that source, not in the market — one reason to retest
  on a second data set.

## Costs: spread, commission, slippage

Costs are subtracted per trade, so their impact scales with **trade frequency and target size**:

- A 1-pip cost on a 10-pip average winner is 10 % of the edge; on a 200-pip winner it is
  negligible. This is why cost realism matters far more for intraday/scalping systems than for
  swing systems — and why an unrealistically low spread turns losing high-frequency systems into
  apparently brilliant ones.
- **Slippage** is not symmetric in practice: stop orders and market exits fill worse than the
  simulated price, especially on breakouts and at news. Model it explicitly rather than assuming
  zero.
- **Overnight financing / swap** dominates for long-hold CFD positions and is often omitted from
  backtests entirely.
- Set costs **pessimistically**. If the edge only exists at optimistic costs, it does not exist.

## Test precision: what the simulation assumes about fills

The backtest engine has to guess what happened *inside* each bar. At the fastest precision
(*Selected timeframe*) it works from OHLC only, so intrabar order of high and low is assumed;
M1 and real-tick precision progressively remove that guesswork.

Styles differ in how much this matters:

- **[Breakout](breakout.md)** — entries are stop orders at the extreme of a bar; the coarse
  assumption is most flattering exactly here.
- **[Mean reversion](mean-reversion.md)** — limit fills near band extremes may never have been
  available at the simulated price.
- **[Momentum/trend](momentum-trend.md)** — least fill-sensitive, since entries are usually
  market orders on a confirmed move.

Rule: generate fast, then **re-verify survivors at higher precision** before believing anything
([cross-check funnel](crosscheck-funnel.md)). A large drop in performance at higher precision is
a finding, not a nuisance.

## Related

- [Data Manager](../overview/data-manager.md) · [data sources](../overview/data-sources/README.md)
- [Higher precision retest](../overview/robustness-tests/higher-precision.md)
- [Overfitting](overfitting.md) — costs and precision are common sources of fake edges
