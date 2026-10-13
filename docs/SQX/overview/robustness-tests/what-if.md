# What If simulations — robustness test

> Fast cross-check that applies "what if" scenarios (trade only certain days/hours, drop best trades, ...) to the existing trades.

## What it does

What If is a quick, simple cross-check that applies scenarios to the list of orders produced by the
standard backtest. Example scenarios:

- *What if the strategy trades only on certain days of the week, or certain hours of the day?*
- *What if we omit the 5% most profitable trades?*

Each selected scenario is applied to the existing trade list — for instance, "Trade only in days →
Tuesday, Wednesday, Thursday" filters out every trade not opened on those days. It does **not**
re-backtest the strategy; it reuses the trades from the main backtest, which is why it is very fast.
(The idea comes from the QuantAnalyzer product.)

## What weakness it exposes

**Over-dependence on favorable assumptions.** It reveals strategies that only look good because of a
few outsized trades, or because they happen to trade at specific times. If performance collapses when
the best trades are removed or trading is restricted to fewer days/hours, the edge is fragile and
narrowly dependent.

## How to configure it

- Choose one or more **What If scenarios** to apply to the strategy results (similar in style to
  Monte Carlo scenario selection).
- Optionally enable **automatic filtering** with a limit — e.g. require the What If simulation's Net
  Profit to be at least 80% of the normal backtest's Net Profit — to drop strategies that fall below
  it.
- As a cross-check it can **filter** in the Builder or **annotate** results in the Retester.

## How to read the result

- Running a What If simulation creates a new result that can be viewed in the equity chart, overview,
  or list of trades, alongside the original backtest for comparison.
- A scenario result close to the original backtest means the strategy is robust to that assumption; a
  large drop means the strategy is significantly worse under the scenario and should be treated with
  caution (or filtered out).

## Related

- Sibling: [Monte Carlo — trade manipulation](monte-carlo-trade-manipulation.md) (also reuses existing trades) · [Higher precision](higher-precision.md)
- [Cross-checks settings](../settings/cross-checks.md)
- [Retester](../retester.md) · [Retest strategies task](../tasks/retest-strategies.md)
- [Robustness Tests results tab](../results-tabs/robustness-tests.md)
- [Concepts](../concepts.md)
