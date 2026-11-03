# Retest with higher precision — robustness test

> Re-runs the backtest on the same data at a higher precision to confirm the fast test was trustworthy.

## What it does

This test simply backtests the strategy again on the **same data**, but with a higher backtesting
precision (for example minute or real-tick precision) than the fast one used during generation.

The usual workflow is to run the main test on the fastest "Selected timeframe" precision because it
very quickly discards bad strategies (no trades, negative Net Profit). Once a profitable candidate
exists, this cross-check retests it at higher precision to confirm the result holds up under a more
exact simulation.

## What weakness it exposes

**Unreliable low-precision backtests.** A strategy that is profitable at the fast Selected-timeframe
precision can stop being profitable at higher precision, simply because the lower precision is less
exact (e.g. intrabar order of events is approximated). This test catches strategies whose apparent
edge is an artifact of the coarse simulation.

## How to configure it

- Choose the **higher precision** level to retest with (e.g. minute precision or real-tick
  precision) — higher precision is slower but more exact.
- As a cross-check it can **filter** in the Builder (drop strategies that no longer pass at higher
  precision) or **annotate** results in the Retester.

## How to read the result

- If the strategy remains profitable at the higher precision, the fast backtest was reliable for
  this strategy — a pass.
- If profitability disappears or drops sharply at higher precision, the original result was an
  artifact of low precision — a fail; discard the strategy.

## Related

- Sibling: [Multi-Market test](multi-market.md) · [What If simulations](what-if.md)
- [Cross-checks settings](../settings/cross-checks.md)
- [Retester](../retester.md) · [Retest strategies task](../tasks/retest-strategies.md)
- [Robustness Tests results tab](../results-tabs/robustness-tests.md)
- [Concepts](../concepts.md)
