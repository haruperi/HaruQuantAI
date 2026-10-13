# Monte Carlo — trade manipulation — robustness test

> Fast Monte Carlo: reshuffle and drop trades from the existing backtest to see if the equity curve was luck or edge.

## What it does

This cross-check runs a number of simulations where, in each simulation, the **existing trades** from
the main backtest are manipulated — reshuffled, some omitted, and so on. It does **not** run new
backtests; it works purely on the list of trades already produced, which makes it very fast.

The two manipulations available:

- **Randomize Trades Order** — randomly shuffles the order of the trades. This does not change the
  final Net Profit, but it is very useful for studying the range of Drawdowns that can result from a
  different order of the same trades.
- **Skip Trades randomly (Randomly Skip Trades)** — randomly skips trades with a given probability.
  In real trading you can miss a trade due to a platform/internet failure, or simply because you
  paused trading. This shows what the equity curve might look like if some trades are missed.

## What weakness it exposes

**Reliance on luck and fragility of the equity curve.** It reveals whether the strategy's result
depended on one particular lucky ordering of trades, and how badly the strategy degrades (especially
Drawdown) if some trades are not executed. A strategy whose profit collapses when a few trades are
skipped is fragile.

## How to configure it

- Choose which manipulation(s) to apply (Randomize Trades Order, Skip Trades randomly).
- **Number of simulations** — more simulations give greater statistical significance (e.g. 100).
- For skipping, a **probability** controls how likely each trade is to be skipped.
- As a cross-check it can **filter** in the Builder or **annotate** results in the Retester.

## How to read the result

The test outputs an equity chart for each simulation run plus a table of metrics at fixed
**confidence levels**. The first row shows the original strategy's values for comparison; the
remaining rows show values at each confidence level.

A value at the 80% confidence level means there is a 20% chance the metric (Net Profit, Drawdown,
etc.) will be worse than that value; at 95% there is only a 5% chance of a worse outcome. For
example, skipping 10% of trades might drop Net Profit from $6,990 to $3,943 and raise Max Drawdown
from 6.97% to 11.36% at the 95% level. Because simulations are random, the exact numbers differ
slightly on each run; more simulations mean more significance.

## Related

- Sibling: [Monte Carlo — retest methods](monte-carlo-retest-methods.md) (the slow, re-backtesting variant) · [What If simulations](what-if.md)
- [Cross-checks settings](../settings/cross-checks.md)
- [Retester](../retester.md) · [Retest strategies task](../tasks/retest-strategies.md)
- [Robustness Tests results tab](../results-tabs/robustness-tests.md)
- [Concepts](../concepts.md)
