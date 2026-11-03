# Custom Analysis — Results feature

> Run your own computations, metrics and filters on generated strategies and whole databanks.

## What it shows

Custom Analysis lets you perform your own analysis of the generated / retested / optimized
strategies and of whole databanks. It is an addition on top of all the metrics and filtering
that StrategyQuant X already does, so you can plug in custom logic. It can be used to:

- compute new metrics that cross the boundaries of a single backtest or cross check,
- implement new metrics that are shown in the databank,
- filter strategies (by returning `false`),
- call external programs (for example in Python) to perform additional analysis.

## How it works

Custom analysis classes and methods are implemented as a **snippet**, with a simple contract —
only three methods are used. There are two types:

- **Per strategy** — runs after the complete backtests and cross checks finish and *before* the
  strategy is saved into the databank. It can inspect all backtest and cross-check results and
  compute useful information. It can also act as a filter: if the method returns `false`, the
  strategy is optionally not saved into the databank (depending on whether custom-analysis
  filtering is turned on in the UI).
- **Per databank** — runs on the whole databank. It receives the array of all strategies in the
  databank and can compute anything across them: compare values between strategies, run counts
  and statistics, and even remove strategies from the databank. This type can be used only in a
  custom project, via the **Custom analysis task**.

## Options & settings

- **Per-strategy configuration** — configured in the **Ranking** tab of Builder / Retester /
  Optimizer projects. Enabling **Filter** there also dismisses strategies according to the
  result of the custom-analysis method.
- **Custom analysis task** — used in a custom project. It has four configurable slots, letting
  you choose the Source and Target databank and then chain four methods in order: per-strategy
  analysis, per-databank analysis, per-strategy analysis, per-databank analysis. This ordering
  lets you run the per-strategy pass first, then the per-databank pass, and repeat.

## Related

- Parent overview: [../results-databank.md](../results-databank.md)
- Sibling tabs: [overview.md](overview.md), [trade-analysis.md](trade-analysis.md)
- Developer detail: [../../onboard/08-results/](../../onboard/08-results/README.md)

> Custom Analysis is a snippet-based feature configured in project settings (Ranking tab /
> Custom analysis task); it is not a dedicated Results servlet tab.
