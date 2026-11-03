# The cross-check funnel: filtering strategies by increasing cost

How SQX applies robustness tests *economically* — the vendor-recommended funnel mapped to
the UI our [catalog](../ui/README.md) drives. Full per-check detail:
[`overview/settings/cross-checks.md`](../overview/settings/cross-checks.md) and
[`overview/robustness-tests/`](../overview/robustness-tests/README.md); vocabulary:
[`overview/concepts.md`](../overview/concepts.md).

## Why a funnel

A bare backtest of a generated strategy takes ~0.2 s; the same strategy with heavy cross-checks
can take 10–200 s (a Monte Carlo retest with 100 simulations = 100 × the backtest time).
Applying every test to every candidate would waste almost all compute on junk. SQX therefore
runs cross-checks **in order, cheapest first, dismissing on first failure** — a strategy that
fails cross-check 1 never reaches cross-check 2.

Cross-checks are grouped by cost: **Basic → Standard → Extensive**. You choose how deep the
funnel goes; each stage has its own *filter* (acceptance criteria) that decides pass/dismiss.

## The recommended funnel (official)

1. **Generate + first filters** — build at the fastest test precision (*Selected timeframe*);
   dismiss immediately on Custom Conditions (too few trades, low Net profit, weak Profit
   Factor / Return-DD / **SQN** — System Quality Number).
2. **Retest with higher precision** — re-run on minute or real-tick data; kills strategies
   whose edge was an artifact of coarse simulation.
3. **Monte Carlo trades manipulation** — hundreds of equity curves by reshuffling/skipping
   trades; kills luck-of-sequence equity curves. Cheap (no re-backtest).
4. **Retest on additional markets** — not profitable on related symbols/TFs → out.
5. *(optional)* **Monte Carlo retest methods** — each simulation is a full backtest with
   perturbed indicator parameters, spread/slippage or history data; the deepest and most
   expensive stage.

Survivors land in the databank with "quite good confidence" of robustness; walk-forward
(WFO / WF Matrix) then answers the *reoptimization* question separately
([workflow](workflow.md) Step 3).

## The precision ladder

The same economics apply to backtest precision: generate at **Selected timeframe** precision
(fast, approximate), promote survivors to **M1 close** and finally **real tick** precision.
The higher-precision cross-check is exactly this promotion automated. Never trust a
fill-sensitive style (mean reversion, breakout) at coarse precision only.

## Builder vs Retester roles

- In the **Builder**, cross-checks *filter* — every generated strategy passes through the
  funnel and failures are dismissed automatically.
- In the **Retester**, cross-checks *annotate* — they run on demand without dismissal (or
  with, if you configure acceptance), which is why the standard pattern is **build fast with
  a short funnel, then batch the heavy tests in the Retester** on the small survivor set
  (see [Retester overview](../overview/retester.md)).

## Practical defaults for the styles in this KB

- All styles: higher-precision retest + MC trades manipulation are near-free insurance —
  keep them in the build funnel (`builder.settings.cc.higher-precision.toggle`,
  `builder.settings.cc.mc-manipulation.toggle`).
- [Mean reversion](mean-reversion.md) / [breakout](breakout.md): add MC **retest** with
  spread/slippage perturbation early — these styles die by fills.
- [Momentum/trend](momentum-trend.md): additional-markets is the key stage — a trend edge
  that only exists on one symbol is suspect.
