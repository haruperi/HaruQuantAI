# OOS/IS Ratios — robustness test

> Measures how much a strategy's performance decays when it moves from in-sample to out-of-sample data.

## What it does

The OOS/IS ratio expresses the ratio between a metric measured on the Out-of-Sample period and the
same metric measured on the In-Sample period. It turns the qualitative
[IS/OOS comparison](in-sample-out-of-sample.md) into a single number per metric that quantifies the
**degree of deterioration** of the strategy on unseen data.

## What weakness it exposes

**Strategy deterioration / overfitting.** Deterioration happens when a strategy that was optimized
and fine-tuned on the IS data is applied to OOS data and performs noticeably worse. This can be
caused either by overfitting to the IS data, or by changing market conditions the strategy cannot
adapt to. The ratio makes the size of this drop-off explicit rather than leaving it to eyeballing
two equity curves.

## How to configure it

- The test relies on an IS/OOS split of the history (see [IS/OOS](in-sample-out-of-sample.md)).
- Ratios can be computed for the performance metrics of interest (the OOS value divided by the IS
  value for each metric).
- As a cross-check it can be used to **filter** (drop strategies whose decay is too large) in the
  Builder, or simply to **annotate** results in the Retester.

## How to read the result

- A ratio near 1.0 means OOS performance closely matches IS performance — little decay, a good sign
  of robustness.
- A ratio well below 1.0 means the strategy deteriorates out-of-sample — a warning of overfitting or
  poor adaptability.
- A strategy that scores well on **both** IS and OOS (ratios not far from 1) is likely more resilient
  and adaptable to changing market conditions.

## Related

- Sibling: [In-Sample / Out-of-Sample](in-sample-out-of-sample.md)
- [Cross-checks settings](../settings/cross-checks.md)
- [Retester](../retester.md) · [Retest strategies task](../tasks/retest-strategies.md)
- [Robustness Tests results tab](../results-tabs/robustness-tests.md)
- [Concepts](../concepts.md)
