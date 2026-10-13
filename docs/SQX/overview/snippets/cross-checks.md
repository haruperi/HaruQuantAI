# Cross-checks — full catalog (settings for UI tests)

> Reference enumeration of every built-in **cross-check** (robustness test run per strategy during
> Build, or on demand in the Retester), with its identity (name/tier/behavior flags) and every
> setting it exposes. This is a lookup table; for what cross-checks *are* and how they're used see
> [`../settings/cross-checks.md`](../settings/cross-checks.md) and
> [`../robustness-tests/README.md`](../robustness-tests/README.md).

## How the set is assembled

Each cross-check is a class under
`com.strategyquant.plugin.CrossCheck.impl.<Name>` extending `CrossCheckMethod`
(`com.strategyquant.tradinglib.crosscheck.CrossCheckMethod`, which implements `ICrossCheck`) and
carrying a JSPF `@PluginImplementation` annotation, so — unlike the What If / Monte Carlo
*snippet* families — **the set of 9 cross-checks itself is fixed** (not user-extensible); only the
settings inside each one are configurable. The 9 classes live one per subfolder under
`projects/libs/Plugins/src/com/strategyquant/plugin/CrossCheck/impl/`.

Two of the nine extend a shared intermediate base instead of `CrossCheckMethod` directly:

- **`MonteCarloCrossCheckMethod`** — `MonteCarloManipulationPlugin` and `MonteCarloRetestPlugin`.
  Adds confidence-level statistics (`ConfidenceLevels = {50,60,70,80,90,92,95,97,98,99,100}`),
  `IFitnessFunction` support (a strategy can be ranked by a chosen confidence level's stats), and
  save/load of simulation data to the result jar.
- **`WalkForwardCrossCheckMethod`** — `OptProfileSysParamPermutation`, `SequentialOptimization`,
  `WalkForwardMatrix`, `WalkForwardOptimization`. Runs the check through an `OptimizationEngine`,
  and unless a subclass overrides them, contributes the defaults `getType()` = EXTENSIVE,
  `getNumberOfSimulations()` = 0, `doesRetest()` = true, `doesForEverySetup()` = false,
  `doesCreateSubjobs()` = true, and a `WhatToParametrize` settings block (documented once below,
  since all four share it verbatim).

Each check declares a cost **tier** via `getType()`, resolved against
`com.strategyquant.tradinglib.crosscheck.CrossCheckTypes`:

| Constant | Value |
|----------|-------|
| `BASIC` | 0 |
| `STANDARD` | 1 |
| `EXTENSIVE` | 2 |

During Build, `CrossCheckComparator` (`com.strategyquant.tradinglib.crosscheck.CrossCheckComparator`)
sorts the enabled checks by **`(getType(), getPreferredPosition())` ascending** — tier first,
`getPreferredPosition()` only as a tiebreaker within the same tier — and they run in that order as
a funnel: a strategy dismissed by an earlier (cheaper) check never reaches a later (pricier) one.
In the Retester the same checks run for information (or still filter, depending on task config) —
see [`../retester.md`](../retester.md).

Every check reads a generic **`AcceptanceSettings/Conditions`** list via
`CrossCheckMethod.readConditions()` / evaluates it via `checkConditions()` — this is the pass/fail
condition builder shared by (almost) all cross-checks. Two exceptions worth knowing for UI tests:
`SequentialOptimization` overrides `checkConditions()` to unconditionally `return true` — its
Conditions list is present in the XML (via `fixSettings`) but is **not** evaluated as a filter,
pass/fail instead comes from its own `PctToPass` / `ResultsCount` / `StabilityRange` settings; and
`RetestOnAdditionalMarkets` overrides `checkConditions()` to route through a per-market
`Check`/`MinConditions`/`MinMarkets` evaluation instead of the plain generic one.

`doesForEverySetup()` returns `false` on all 9 classes (as of this reading) — none of them
auto-repeats via that flag; `RetestOnAdditionalMarkets` instead loops over its own configured list
of additional chart setups internally.

### Shared: the `WhatToParametrize` block

Read by `WalkForwardCrossCheckMethod.readWhatToParametrize(Element)` and used identically by
**Opt. Profile / SPP**, **Sequential Optimization**, **Walk-Forward Optimization**, and
**Walk-Forward Matrix** (documented once here instead of 4×):

| Setting | Controls | Default |
|---------|----------|---------|
| `Recommended` | Boolean. If true, uses SQX's recommended parameter set (`ParametrizationTypes.ParamTypeRecommended`) and forces symmetric long/short parameters, ignoring every checkbox below. | `true` |
| `Periods` | Boolean. Include Period-type parameters (only read when `Recommended=false`). | `false` |
| `Shifts` | Boolean. Include Shift-type parameters. | `false` |
| `Constants` | Boolean. Include Constant-type parameters. | `false` |
| `OtherParams` | Boolean. Include Other-Param-type parameters. | `false` |
| `ExitParamsUsed` | Boolean. Include used Exit parameters. | `false` |
| `ExitParamsUnused` | Boolean. Include unused Exit parameters. | `false` |
| `BooleanParams` | Boolean. Include Boolean-type parameters. | `false` |
| `TradingOptions` | Boolean. Include Trading-Options-type parameters. | `false` |
| `EntryParams` | Boolean. Include Entry-level parameters. | `false` |
| `EntryLogic` | Boolean. Include Entry-logic parameters. | `false` |
| `symmetricVariables` | Boolean (element presence, via `XMLUtil.elementIs`). If true, long/short parameter pairs are optimized symmetrically. | not set (only meaningful when `Recommended=false`) |

Parameters actually placed into the optimization run are then built by
`initializeParams(strategy, distributionUp, distributionDown, maxSteps)`, which additionally
excludes any variable named `Magic*`, `*EntrySignal*`, `*ExitSignal*`, `*ReplaceExistingOrders*`,
or of internal type String — regardless of the `WhatToParametrize` selection above.

## Summary table

Ordered by actual funnel order (`getType()` then `getPreferredPosition()`), matching execution
order during Build.

| # | Short name | Full name | Class | Tier | Position | Retests? | Subjobs? | # Simulations | Purpose |
|---|------------|-----------|-------|------|----------|----------|----------|----------------|---------|
| 1 | What If | What If simulations | `WhatIfPlugin` | Basic | 220 | No | No | 0 (fixed) | Filters the existing trade list under What-If scenarios (days/hours traded, fixed lots, swap, etc.) without re-backtesting. |
| 2 | MC trades | Monte Carlo trades manipulation | `MonteCarloManipulationPlugin` | Basic | 230 | No | No | `NumberOfSimulations` (default 10) | Fast Monte Carlo: reorders/skips/degrades existing trades to test luck vs. edge and drawdown range. |
| 3 | Higher backtest precis. | Higher backtest precision | `RetestWithHigherPrecision` | Basic | 300 | Yes | No | 1 (fixed) | Re-backtests once at a higher test precision to confirm the fast-precision result was reliable. |
| 4 | Add. markets | Backtests on additional markets | `RetestOnAdditionalMarkets` | Standard | 210 | Yes | No | = number of configured additional chart setups | Re-backtests the strategy on other symbols/timeframes to check it isn't curve-fit to one market. |
| 5 | MC retest | Monte Carlo retest methods | `MonteCarloRetestPlugin` | Standard | 240 | Yes | Yes | `NumberOfSimulations` (default 10) | Slow Monte Carlo: each simulation is a full re-backtest with perturbed spread/parameters/history/starting bar. |
| 6 | Sequential Optimization | Sequential Optimization | `SequentialOptimization` | Standard | 300 | Yes | Yes | 0 (fixed) | Sequentially optimizes the strategy and looks for a stable parameter area. |
| 7 | Opt. Profile / SPP | Opt. Profile / Sys. Param. Permutation | `OptProfileSysParamPermutation` | Extensive | 260 | Yes | Yes | 0 (fixed) | Optimizes the strategy and evaluates the resulting Optimization Profile / Sys. Param. Permutation table against profitability/distribution checks. |
| 8 | WF optim. | Walk-Forward Optimization | `WalkForwardOptimization` | Extensive | 270 | Yes | Yes | 0 (fixed) | Runs a single Walk-Forward Optimization and filters on the % of WF steps that pass. |
| 9 | WF matrix | Walk-Forward Matrix | `WalkForwardMatrix` | Extensive | 280 | Yes | Yes | 0 (fixed) | Runs a matrix of Walk-Forward Optimizations (varying the two WF period parameters) and filters on the stable-area grid. |

Note: `RetestWithHigherPrecision` and `SequentialOptimization` both declare `getPreferredPosition()
== 300`; they never collide in the actual run order because they sit in different tiers (Basic vs.
Standard), so the tier comparison alone separates them.

## What If simulations (`WhatIfPlugin`)

Package: `com.strategyquant.plugin.CrossCheck.impl.WhatIf` · setting name: `WhatIf` · tier: Basic ·
preferred position: 220.

> This cross check allows you to apply various What-If scenarios to the list of orders, for
> example what if the strategy trades only on particular days. It creates simulations by filtering
> the existing orders from the main backtest, it doesn't retest the strategies again.

Behavior flags: `getNumberOfSimulations()` = 0 (fixed); `doesRetest()` = false; `doesForEverySetup()`
= false; `doesCreateSubjobs()` = false; `disabledForSpecialTrial()` = true — `runTest()` calls
`checkSpecialTrialLimitation()` first, so this check is unavailable on a Special Trial license.
Results are written to a fixed sub-result key `CrossCheck_WhatIf`.

This check delegates its actual per-scenario parameters to the **What If snippet catalog** — see
[`whatif.md`](whatif.md) for every scenario and its settings.

| Setting | Controls | Default |
|---------|----------|---------|
| `Methods` (`SettingsKeys.WhatIfMethods`) | List of configured What-If snippet instances (see [`whatif.md`](whatif.md)); applied in order to a clone of the full-sample order list. | empty list |
| `AcceptanceSettings/Conditions` | Generic pass/fail condition list (shared mechanism, see above). | empty |

## Monte Carlo trades manipulation (`MonteCarloManipulationPlugin`)

Package: `com.strategyquant.plugin.CrossCheck.impl.MonteCarloManipulation` · setting name:
`MonteCarloManipulation` · tier: Basic · extends `MonteCarloCrossCheckMethod`.

> This cross check uses Monte Carlo method to perform various simulations of resulting equity
> curve by manipulating the order of the trades. It allows you to quickly assess how much the
> good results are dependent on order of the trades.

Behavior flags: `getNumberOfSimulations()` = the configured `NumberOfSimulations` (dynamic);
`doesRetest()` = false; `doesForEverySetup()` = false; `doesCreateSubjobs()` = false (inherited).

Delegates its per-method parameters to the **Monte Carlo snippet catalog** — "Trade manipulation"
section of [`monte-carlo.md`](monte-carlo.md).

| Setting | Controls | Default |
|---------|----------|---------|
| `MCUseFullSample` | Boolean. If true, simulations manipulate the Full Sample order set instead of just In-Sample. | `false` |
| `NumberOfSimulations` (`SettingsKeys.RTNumberOfSimulations`) | Number of Monte Carlo simulation runs performed. | `10` |
| `Methods` (`SettingsKeys.MonteCarloMethods`) | List of configured Monte Carlo *manipulation* snippet instances (see [`monte-carlo.md`](monte-carlo.md)), applied in sequence to each simulated copy of the trade list. | empty list |
| `AcceptanceSettings/Conditions` | Generic pass/fail condition list. | empty |

## Higher backtest precision (`RetestWithHigherPrecision`)

Package: `com.strategyquant.plugin.CrossCheck.impl.RetestWithHigherPrecision` · setting name:
`RetestWithHigherPrecision` · tier: Basic · extends `CrossCheckMethod` directly, also implements
`IFitnessFunction`.

> This cross checks retests the strategy with higher test precision. It can be used if you are
> using the lowest 'Selected timeframe' precision in the main backtest to quickly find and
> evaluate the valid strategies. You can then use this cross check to retest the strategy with
> higher precision to see if it performs in a same way with higher precision backtesting.

Behavior flags: `getNumberOfSimulations()` = 1 (fixed — a single higher-precision re-backtest);
`doesRetest()` = true; `doesForEverySetup()` = false; `doesCreateSubjobs()` = false. Results are
written to a fixed sub-result key `CrossCheck_HigherPrecision`.

| Setting | Controls | Default |
|---------|----------|---------|
| `Precision` (`SettingsKeys.BacktestPrecision`) | Integer backtest-precision constant (see `Precisions`, e.g. Selected timeframe / 1-minute / real ticks) used for the retest. Parsed with `Integer.parseInt`; if the element is missing or unparsable, falls back to `Precisions.SelectedTF`. | `Precisions.SelectedTF` (on missing/invalid value) |
| `Spread` (`SettingsKeys.BacktestSpread`) | Double spread override applied to the main chart and every subchart sharing the main symbol. If the `Spread` element is present, its parsed value is used; if absent, `1` is stored (the `-2.0` sentinel checked in `runTest()` for "no override" is effectively never persisted by `readSettings`, so a spread override is applied in practice). | `1` (if element missing) |
| `AcceptanceSettings/Conditions` | Generic pass/fail condition list. | empty |

## Backtests on additional markets (`RetestOnAdditionalMarkets`)

Package: `com.strategyquant.plugin.CrossCheck.impl.RetestOnAdditionalMarkets` · setting name:
`RetestOnAdditionalMarkets` · tier: Standard · extends `CrossCheckMethod` directly, also
implements `IFitnessFunction`.

> This cross check retest the strategy on multiple additional markets (symbols). It allows you to
> compare the performance on multiple symbols, ideally you want to find the strategy that will
> work on multiple markets.

Behavior flags: `getNumberOfSimulations()` = the number of configured additional chart setups (0
if none — in which case `runTest()` is a no-op that returns `true`); `doesRetest()` = true;
`doesForEverySetup()` = false; `doesCreateSubjobs()` = false. `readSettings()` throws if zero
additional setups are configured ("No additional setups defined").

Top-level acceptance settings:

| Setting | Controls | Default |
|---------|----------|---------|
| `AcceptanceSettings/Check` | String `"all"` or `"markets"`. When `"markets"`, filtering switches from the plain generic Conditions evaluation to a per-market pass-count evaluation (`ConditionsCheckAdditionalMarkets` = value equals `"markets"`). | `"all"` |
| `AcceptanceSettings/MinConditions` | Minimum number of enabled, cross-check-scoped conditions a given market must satisfy to count as "passed" for that market. Only used when `Check="markets"`. | `0` |
| `AcceptanceSettings/MinMarkets` | Minimum number of markets that must reach `MinConditions` for the strategy to survive. Only used when `Check="markets"`. | `0` |
| `AcceptanceSettings/Conditions` | Generic pass/fail condition list (used directly when `Check="all"`). | empty |

Per-market setup — the user adds any number of `Settings/Setups/Setup` entries; each is read via
`ProjectConfigHelper` helpers with **no code-level default** (the UI always writes every attribute
when a setup is added):

| Field | Controls |
|-------|----------|
| Chart `symbol` / `timeframe` / `session` | The additional market's symbol, timeframe, and trading session. |
| Setup `dateFrom` / `dateTo` | Requested history range for the additional-market backtest; clamped to the data's actual available range (`checkHistoryFrom`/`checkHistoryTo`). |
| `MainTestValues/dates` (`useMainTestDates`) | `"true"`/`"false"` string. If `"true"`, the main backtest's own date range is used instead of this setup's `dateFrom`/`dateTo`. |
| Setup `testPrecision` | Backtest precision for this additional-market retest. |
| Chart `spread` | Spread applied on this market. |
| Setup `slippage` | Slippage applied on this market. |
| Setup `minDist` | Minimum distance from price (for stop/limit orders) on this market. |
| Commission method (via `getCommissionsMethod`) | Commission model applied on this market. |
| Swap method (via `getSwapMethod`) | Swap/rollover model applied on this market. |
| Additional `Chart` children (subcharts) | Extra symbols in the same multi-chart setup, mirroring the main setup's subchart count. |

## Monte Carlo retest methods (`MonteCarloRetestPlugin`)

Package: `com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest` · setting name:
`MonteCarloRetest` · tier: Standard · extends `MonteCarloCrossCheckMethod`.

> This cross check uses Monte Carlo methods that perform simulations that require retesting the
> strategy - using different spread, parameters or history data. Note that it is slow, strategy
> will have to be retested multiple times, depending on your number of simulations.

Behavior flags: `getNumberOfSimulations()` = the configured `NumberOfSimulations` (dynamic);
`doesRetest()` = true; `doesForEverySetup()` = false; `doesCreateSubjobs()` = true (overridden —
each simulation runs as an `MCRetestJob` grid subjob via `SimpleGridEngine`).

Delegates its per-method parameters to the **Monte Carlo snippet catalog** — "Data / retest
randomization" section of [`monte-carlo.md`](monte-carlo.md).

| Setting | Controls | Default |
|---------|----------|---------|
| `MCUseFullSample` | Boolean. If true, retests the Full Sample instead of just In-Sample. | `false` |
| `NumberOfSimulations` (`SettingsKeys.RTNumberOfSimulations`) | Number of Monte Carlo re-backtests performed. | `10` |
| `Methods` (`SettingsKeys.MonteCarloMethods`) | List of configured Monte Carlo *retest* snippet instances (see [`monte-carlo.md`](monte-carlo.md)). | empty list |
| `MCBacktestPrecision` | Backtest precision override for the MC retest simulations; `-1` means "same as main chart" (printed as such), otherwise a `Precisions` constant. | `-1` (same as main chart) |
| `AcceptanceSettings/Conditions` | Generic pass/fail condition list. | empty |

## Sequential Optimization (`SequentialOptimization`)

Package: `com.strategyquant.plugin.CrossCheck.impl.SequentialOptimization` · setting name:
`SequentialOptimization` · tier: Standard (`getType()` overridden to return
`CrossCheckTypes.STANDARD`, instead of the `WalkForwardCrossCheckMethod` default of `EXTENSIVE`)
· extends `WalkForwardCrossCheckMethod` (constructed with task name
`SequentialOptimization_CrossCheck`), also implements `ILastEventListener`.

> This cross check performs sequential optimization of the strategy and finds stable parameters.

Behavior flags: `getNumberOfSimulations()` = 0 (inherited); `doesRetest()` = true (inherited);
`doesForEverySetup()` = false (inherited); `doesCreateSubjobs()` = true (overridden explicitly, same
value as the inherited default); `disabledForSpecialTrial()` = true (overridden) and `runTest()`
also calls `checkSpecialTrialLimitation()` directly. **`checkConditions()` is overridden to always
return `true`** — the generic `AcceptanceSettings/Conditions` list is present in the XML (via
`fixSettings`) but is not evaluated; pass/fail is instead decided by the optimization engine using
`PctToPass` / `ResultsCount` / `StabilityRange` below. Results land in a fixed sub-result key
`CrossCheck_SequentialOptimization`.

Also reads the shared `WhatToParametrize` block — see the shared section above.

| Setting | Controls | Default |
|---------|----------|---------|
| `Settings/ParameterSettings/DistributionUp` | % up-distribution used to build each parameter's optimization range. | `50` |
| `Settings/ParameterSettings/DistributionDown` | % down-distribution used to build each parameter's optimization range. | `50` |
| `Settings/ParameterSettings/Steps` | Max number of optimization steps per parameter. | `50` |
| `Settings/ParameterSettings/ApplyToStrategy` | Boolean. If true, the optimized/stable parameter values are written back onto the strategy (`rg.mainResult().addStrategy(...)`). | `false` |
| `AcceptanceSettings/PctToPass` | % of parameter combinations around the found optimum that must still perform acceptably for the area to count as "stable". | `80` |
| `AcceptanceSettings/ResultsCount` | Number of stable-area results required to pass. | `5` |
| `AcceptanceSettings/StabilityRange` | % range around the optimum considered part of the same stable area. | `30` |

## Opt. Profile / Sys. Param. Permutation (`OptProfileSysParamPermutation`)

Package: `com.strategyquant.plugin.CrossCheck.impl.OptProfileSysParamPermutation` · setting name:
`OptProfileSysParamPermutation` (class simple name) · tier: Extensive · extends
`WalkForwardCrossCheckMethod` (task name `OptProfileSysParamPermutation_CrossCheck`).

> This cross check performs optimization of the strategy and then evaluates its Optimization
> profile - see the conditions in filter.

Behavior flags: `getNumberOfSimulations()` = 0 (overridden, same as inherited default);
`doesRetest()` = true (overridden, same as default); `doesForEverySetup()` = false (overridden,
same as default); `doesCreateSubjobs()` = true (inherited). After the inherited
`WalkForwardCrossCheckMethod.runTest()` runs a **Sequential**-type `OptimizationEngine` pass
(`prepareSettings` fixes `optimizationType = OptimizationTypes.Sequential`,
`optimizationMethod = OptimizationMethods.Automatic`), `runTest()` additionally calls
`checkOptimizationProfileConditions(rg)`, which is a **second filter layer** evaluating the
resulting `OptimizationProfile` against the four `Eval*Check` toggles and their thresholds below —
on top of (not instead of) the generic Conditions list.

Also reads the shared `WhatToParametrize` block — see the shared section above.

| Setting | Controls | Default |
|---------|----------|---------|
| `Settings/MaxTests` | Cap on the number of optimization backtests run to build the Sys. Param. Permutation table (`optimizationSettings.maxOptimizationBacktests`). | `100` |
| `Settings/DistributionUp` | % up-distribution used to build each parameter's optimization range. | `100` |
| `Settings/DistributionDown` | % down-distribution used to build each parameter's optimization range. | `100` |
| `Settings/Steps` | Max number of optimization steps per parameter (`maxSteps`). | `25` |
| `AcceptanceSettings/EvalProfitOptCheck` | Boolean. Enables the "% of profitable optimizations" check. | `true` |
| `AcceptanceSettings/EvalAvgProfitCheck` | Boolean. Enables the "average profit" check. | `true` |
| `AcceptanceSettings/EvalUniformDistrCheck` | Boolean. Enables the "uniform distribution of profitable results" check. | `true` |
| `AcceptanceSettings/EvalTopProfitCheck` | Boolean. Enables the "top-profit standard deviation" check. | `true` |
| `AcceptanceSettings/ProfitOptPct` | Minimum % of optimization runs that must be profitable (used when `EvalProfitOptCheck`). | `30` |
| `AcceptanceSettings/AvgProfit` | Minimum average-profit threshold across optimization runs (used when `EvalAvgProfitCheck`). | `0` |
| `AcceptanceSettings/UniformDistrChanges` | Max allowed number of direction changes in the profit-vs-parameter distribution (used when `EvalUniformDistrCheck`). | `5` |
| `AcceptanceSettings/StdevAvgProfit` | Max standard deviation (double, in multiples of average profit) allowed among the top-profit results (used when `EvalTopProfitCheck`). | `1` |
| `AcceptanceSettings/Conditions` | Generic pass/fail condition list — still evaluated (inherited `checkConditions()` is not overridden here). | empty |

## Walk-Forward Optimization (`WalkForwardOptimization`)

Package: `com.strategyquant.plugin.CrossCheck.impl.WalkForwardOptimization` · setting name:
`WalkForwardOptimization` (inherited class simple name) · tier: Extensive (inherited) · extends
`WalkForwardCrossCheckMethod` (task name `WalkForwardOptimization_CrossCheck`).

> This cross check performs Walk-Forward Optimization of the strategy using the settings below.
> Be aware that WF optimization is very slow, it requires repeated backtests of the strategy in
> different time ranges and using different parameter values.

Behavior flags: all inherited from `WalkForwardCrossCheckMethod` (0 simulations, retests, not
per-setup, creates subjobs); `disabledForSpecialTrial()` = true (overridden) and `runTest()` calls
`checkSpecialTrialLimitation()` before delegating to the inherited implementation.

Also reads the shared `WhatToParametrize` block — see the shared section above.

| Setting | Controls | Default |
|---------|----------|---------|
| `Settings/WalkForward@type` | WF type: `0` = Simulated IS / Simulated OOS (fastest), `1` = Simulated IS / Exact OOS (slower), `2` = Exact IS / Exact OOS (slow). | `1` |
| `Settings/WalkForward@period` | Period unit for the two Param values below: `10` = Percent, `20` = Days, `30` = Bars. | `10` (Percent) |
| `Settings/WalkForward@optimization` | `15` = Floating WF window, `25` = Fixed WF window. | `15` (Floating) |
| `Settings/WalkForward@distributionUp` | % up-distribution used to build each parameter's optimization range. | `30` |
| `Settings/WalkForward@distributionDown` | % down-distribution used to build each parameter's optimization range. | `30` |
| `Settings/WalkForward@maxSteps` | Max number of optimization steps per parameter. | `10` |
| `Settings/WalkForward/Param1@value` | Percent mode: % Out-of-Sample. Days/Bars mode: In-Sample period length. | `20` |
| `Settings/WalkForward/Param2@value` | Percent mode: number of WF runs. Days/Bars mode: Out-of-Sample period length. | `10` |
| `Settings/MaxTests` | Cap on optimization backtests per WF run. | `100` |
| `AcceptanceSettings/Conditions@thresholdPct` | Minimum % of individual WF-step results that must pass for the overall WF result to pass. | `10` |
| `AcceptanceSettings/Conditions` | Generic pass/fail condition list. | empty |

## Walk-Forward Matrix (`WalkForwardMatrix`)

Package: `com.strategyquant.plugin.CrossCheck.impl.WalkForwardMatrix` · setting name:
`WalkForwardMatrix` (inherited class simple name) · tier: Extensive (inherited) · extends
`WalkForwardCrossCheckMethod` (task name `WalkForwardMatrix_CrossCheck`).

> This cross check performs Walk-Forward Matrix evaluation of the strategy using the settings
> below. Be aware that WF Matrix is extremely slow, it consists of running a number of WF
> optimizations, which themselves are very slow.

Behavior flags: all inherited from `WalkForwardCrossCheckMethod` (0 simulations, retests, not
per-setup, creates subjobs). Unlike `WalkForwardOptimization` / `SequentialOptimization` /
`WhatIfPlugin`, this class does **not** override `disabledForSpecialTrial()`, so it stays available
(`false`, the `CrossCheckMethod` default) on a Special Trial license.

Also reads the shared `WhatToParametrize` block — see the shared section above.

| Setting | Controls | Default |
|---------|----------|---------|
| `Settings/WalkForward@type` | WF type: `0`/`1`/`2` as above. | `1` |
| `Settings/WalkForward@period` | Period unit: `10` Percent / `20` Days / `30` Bars. | `10` (Percent) |
| `Settings/WalkForward@optimization` | `15` Floating / `25` Fixed. | `15` (Floating) |
| `Settings/WalkForward@distributionUp` | % up-distribution per parameter. | `30` |
| `Settings/WalkForward@distributionDown` | % down-distribution per parameter. | `30` |
| `Settings/WalkForward@maxSteps` | Max optimization steps per parameter. | `10` |
| `Settings/WalkForward/Param1@start` / `@stop` / `@step` | Matrix range for the Param1 axis (Percent mode: % Out-of-Sample; Days/Bars mode: In-Sample period length). | `10` / `40` / `10` |
| `Settings/WalkForward/Param2@start` / `@stop` / `@step` | Matrix range for the Param2 axis (Percent mode: number of WF runs; Days/Bars mode: Out-of-Sample period length). | `10` / `20` / `5` |
| `Settings/MaxTests` | Cap on optimization backtests per WF matrix cell. | `100` |
| `AcceptanceSettings/Conditions@thresholdPct` | Minimum % of matrix cells that must pass. | `80` |
| `AcceptanceSettings/Conditions@robCombRows` | Rows required in the stable-area grid (Param1-axis span). | `3` |
| `AcceptanceSettings/Conditions@robCombCols` | Columns required in the stable-area grid (Param2-axis span). | `3` |
| `AcceptanceSettings/Conditions@robMinComb` | Minimum number of passing matrix cells (combinations) within the stable area. | `7` |
| `AcceptanceSettings/Conditions` | Generic pass/fail condition list. | empty |

## Related

- [Cross-checks settings tab (prose)](../settings/cross-checks.md)
- [Robustness tests / cross-checks — detailed reference hub](../robustness-tests/README.md)
- [Retester](../retester.md)
- [What-If manipulations catalog](whatif.md)
- [Monte Carlo randomization methods catalog](monte-carlo.md)
- [Snippets hub](README.md)
