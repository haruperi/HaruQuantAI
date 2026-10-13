# From backtest to live trading

The [workflow](workflow.md) ends at "export the strategy". Trading it is a separate discipline
with its own failure modes — most strategies that die in production were not killed by a bad
backtest but by what happened after it.

## Forward testing is the only clean data left

By the time a strategy has been generated, filtered, retested and optimized, all of its history
has been used for selection. The one untouched sample is the future:

- Run the exported strategy on **demo or minimum size** for weeks to months (long enough for a
  meaningful number of trades — a system that trades twice a month needs a year, which is an
  argument for not building such systems as your first ones).
- Compare live trades against the backtest over the *same* period, trade by trade. Mismatches
  are usually mechanical: different data feed, timezone, symbol spec, or an indicator that
  repaints. Find those before deciding the edge is gone.
- Expect live results to be **worse than backtest** even when everything is correct — real costs,
  real fills, real latency. If the strategy is only marginally profitable in simulation, that
  margin is the first thing to disappear.

## Deploy as a portfolio member, not as a bet

A single strategy going live is a sample size of one. The portfolio is the unit that should be
sized and judged ([portfolio construction](portfolio-construction.md),
[risk and position sizing](risk-and-position-sizing.md)):

- Start each new member at reduced size and scale up only after it behaves as expected.
- Add members that are **uncorrelated** with what you already trade — a new strategy that
  duplicates existing exposure adds risk without adding diversification.
- Keep total and per-sector exposure capped so a correlated cluster cannot take the account down.

## Monitoring: distinguish a normal losing streak from a dead edge

This is the hardest judgement in systematic trading, and it must be decided **before** the
drawdown, not during it. Useful anchors:

- **Compare to the backtest's own distribution.** The Monte Carlo drawdown distribution tells
  you what a normal bad run looks like for this system. Being inside it is not evidence of
  failure; exceeding the worst simulated drawdown is.
- **Watch behaviour, not just P/L.** Trade frequency, average holding time and win rate drifting
  away from the backtest means the market regime changed or the setup broke — a more actionable
  signal than equity alone.
- **Write the retirement rule in advance**: a drawdown threshold, a number of consecutive losing
  months, or a behaviour drift. Deciding while losing money guarantees deciding badly.

Reoptimizing a struggling strategy is the tempting move and usually the wrong one — it is
fitting to the most recent noise. Whether periodic reoptimization helps at all is an empirical
question the [walk-forward tests](../overview/robustness-tests/walk-forward.md) answer *before*
deployment; if WFO said reoptimization does not help, do not start now.

## Operational risk

Automation moves risk from judgement to plumbing. The mundane failures are the common ones:
platform disconnects, VPS reboots, a terminal left running an old version of the EA, a broker
changing symbol names or specs, duplicate orders after a restart, news-time gaps hitting a
position with no stop on the server. Keep stops on the broker's side rather than in the
strategy's memory, and check that what is running is what you exported.

## Related

- [Export engines](../overview/export-engines/README.md) — MT4/MT5, TradeStation, NinjaTrader
- [Overfitting](overfitting.md) — why forward testing is the only untainted evidence
- [Risk and position sizing](risk-and-position-sizing.md) · [Portfolio construction](portfolio-construction.md)
