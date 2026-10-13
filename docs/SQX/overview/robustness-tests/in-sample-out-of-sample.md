# In-Sample / Out-of-Sample (IS/OOS) — robustness test

> The most basic robustness test: does the strategy still work on data it was never built on?

## What it does

Historical data is split into two segments. The **In-Sample (IS)** part is the data used to
develop, evolve and optimize the strategy — its parameters, rules and indicators are all fine-tuned
against it. The **Out-of-Sample (OOS)** part is a separate, unseen segment that is held back and
never used during generation or optimization.

Because the OOS segment is "unknown" to the strategy, its performance there is an unbiased estimate
of how the strategy generalizes. When genetic evolution is used, the strategy is evolved only on the
IS part, so the OOS part is available as an honest forward check.

## What weakness it exposes

**Overfitting (curve-fitting).** A strategy that has been over-optimized to the exact quirks of the
IS data will look excellent in-sample but fall apart on the OOS segment. Comparing the two equity
curves reveals this immediately: a robust strategy keeps performing on the blue (OOS) part, while a
curve-fit one flatlines or reverses there.

## How to configure it

- **IS/OOS split** — set how much of the history is reserved as Out-of-Sample. The IS portion is
  used for development/optimization; the OOS portion is held back for validation.
- The split is defined with the data range for the backtest, so the OOS segment is contiguous with
  and follows the IS segment in time.

## How to read the result

- Compare performance metrics on IS vs OOS. A strategy that performs well on **both** is less likely
  to be overfit and more likely to hold up in live trading.
- Strong IS but weak/negative OOS is a red flag for curve-fitting or an idea that only fit noise.
- Consistent OOS performance adds confidence that the underlying trading idea is genuinely sound and
  not the product of chance. To quantify how much decays, see the sibling
  [OOS/IS ratios](oos-is-ratios.md) test.

## Related

- [Cross-checks settings](../settings/cross-checks.md)
- [Retester](../retester.md) · [Retest strategies task](../tasks/retest-strategies.md)
- [Robustness Tests results tab](../results-tabs/robustness-tests.md)
- Sibling: [OOS/IS ratios](oos-is-ratios.md) · [Walk-Forward](walk-forward.md)
- [Concepts](../concepts.md)
