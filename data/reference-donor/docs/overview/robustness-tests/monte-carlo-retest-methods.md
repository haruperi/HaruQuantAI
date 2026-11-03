# Monte Carlo — retest methods — robustness test

> Slow Monte Carlo: each simulation is a full re-backtest with randomized parameters, history data, or start bar.

## What it does

This is the second type of Monte Carlo test. Instead of manipulating existing trades, it simulates
random changes in properties that **require the strategy to be re-tested** — such as changes in
spread, slippage, strategy parameters, or the history data. Because every simulation runs a complete
backtest, this cross-check can take a long time. (If the main backtest took 0.5 s and you run 100
simulations, expect roughly 100 × 0.5 = 50 s per strategy.)

Available methods:

- **Randomize Starting Bar** — starts the test on a different bar. A good strategy must not be
  sensitive to which bar the test begins on.
- **Randomize Strategy Parameters** — every strategy uses parameters (indicator periods, constants).
  This checks sensitivity to a small change in a parameter's value.
- **Randomize History Data** — checks the strategy's behavior when the price history is slightly
  perturbed, catching strategies that depend too heavily on the exact history data.

## What weakness it exposes

**Parameter and data sensitivity — a core form of curve-fitting.** A robust strategy should keep
working when indicator periods/constants are nudged, when the history is slightly altered, or when
the start bar shifts. Strategies that break under these small perturbations were fit to noise.

## How to configure it

- **Number of simulations** — more simulations, more significance (but more time, since each is a
  full backtest).
- **Randomize Strategy Parameters:** *Probability of change* (how likely any parameter changes) and
  *Max parameter change* (max percent change). Example: Max change 10% lets a parameter of 60 vary
  within 54–66 (±10%).
- **Randomize History Data:** *Probability of change* (per bar, chance that open/high/low/close is
  changed) and *Max price change* (a percentage of ATR). Example: if ATR is 10 pips and Max price
  change is 20%, a price can move ±2 pips.
- As a cross-check it can **filter** in the Builder or **annotate** results in the Retester.

## How to read the result

Results are reported at fixed **confidence levels only**: 50, 60, 70, 80, 90, 92, 95, 97, 98, 99,
100 — other levels produce no results. A value at the 95% confidence level means there is only a 5%
chance the metric will be worse than that value. Compare the confidence-level values against the
original strategy's metrics: small degradation across parameter/data/start-bar randomization
indicates a robust, low-sensitivity strategy.

## Related

- Sibling: [Monte Carlo — trade manipulation](monte-carlo-trade-manipulation.md) (the fast, no-backtest variant)
- [Cross-checks settings](../settings/cross-checks.md)
- [Retester](../retester.md) · [Retest strategies task](../tasks/retest-strategies.md)
- [Robustness Tests results tab](../results-tabs/robustness-tests.md)
- [Concepts](../concepts.md)
