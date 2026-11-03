# Strategy styles - translating intent into Builder settings

Intent (martingale, mean reversion, trend following, breakout, scalping) -> Build-task settings,
derived from the Java sources and the shipped style templates. Per-tab detail:
[`../overview/settings/`](../overview/settings/README.md); per-control XML mappings:
[`../overview/settings/fields/`](../overview/settings/fields/).

## Shipped style templates

`internal/web/BUILDER/simpleTemplates/`, each a complete Build `<Settings>` subtree:

| `strategyType` id | Style | Notes |
|---|---|---|
| `TrendFollowing` | Trend following / breakout | stop orders, with-trend signal families, H1 |
| `Mean-Reversal` | Mean reversion | counter-trend signals, reverse-at-market, D1, min 1000 trades |
| `Market` | Broad mix at market price | widest signal set |
| `Daily` | Daily strategies | nearly all blocks, robustness emphasis |
| `Fuzzy` | Fuzzy logic | `architecture="sq4fuzzy"`, 4-8 conditions |
| `DefaultForex` / `DefaultFutures` / `DefaultStockpicker` | Baseline defaults | genetic evolution, EnterAtStop only |

Servlet `Project -> applySimpleTemplate` (`projectName`, `taskName`, `strategyType`) replaces the
task's entire `<Settings>` and stamps `sampleName="<id>"` on the `<Task>`. From the AI chat: fetch
the template's sections, write them via `set_task_config`, then apply the user's deltas (MM,
timeframe, SL/PT ranges, extra blocks). Always template -> deltas, never 340 `<Block>` entries
from scratch.

## Four levers encode style

No "mean reversion" flag exists.

1. Enabled `signals` blocks (`<Blocks><BuildingBlocks><Block key="..." use="...">`). With `MarketSides type="both"` + `EntrySymmetry=true`, enabling only Down/Falling/CrossDown families makes the LONG entry fire on downward pressure (buy weakness = mean reversion), the short is its mirror; only Up/Rising/CrossUp = trend following. The shipped templates do exactly this.
2. Order types (`<Blocks><OrderTypes>`), exactly 4: `EnterAtMarket`, `EnterReverseAtMarket`, `EnterAtStop`, `EnterAtLimit`. Stop = breakout, limit = pullback/mean-reversion fills, reverse-at-market = always-in-market reversal.
3. Exits (`<Blocks><ExitTypes>`): `StopLoss.StopLoss`, `ProfitTarget.ProfitTarget`, `TrailingStop.*`, `MoveSL2BE.*`, `ExitAfterBars.ExitAfterBars`, pseudo-block `_ExitRule_` (exit on opposite signal; `use="false"` forces probability 0). ExitTypes use `probability="0-100"`, not weight.
4. Money management (`<RiskMoneyManagement>`): changes only sizing/scoring, not which strategies are generated. Martingale lives here.

## Money management methods (exact XML identity)

`<Method type="<JavaClassName>" use="true">`: first `use="true"` wins, others stay as inactive
siblings. `<Param key="...">` = Java field names. Full parameter tables:
[`../overview/snippets/money-management.md`](../overview/snippets/money-management.md).

| `type=` | Meaning | Key params (defaults) |
|---|---|---|
| `FixedSize` | neutral baseline, recommended while GENERATING | `Size` (0.1) |
| `RiskFixedBalancePct` | % risk compounding | `Risk` (5), `Decimals`, `LotsIfNoMM`, `MaxLots` |
| `RiskFixedPctOfAccount` | % risk with fixed SL assumption | + `StopLossInPips` (100) |
| `ATRRiskBasedSizing` | volatility-scaled risk | `Risk`, `ATRPeriod` (14), `ATRMult` (2.0) |
| `FixedAmount` | fixed money risk per trade | `RiskedMoney` (500) |
| `SimpleMartingaleMM` | martingale | `LotsStart` (0.1), `LotsMultiplier` (2.0), `LotsReset` (1.0 = cap, resets to start), `Decimals`, `SeparateByDirection` (true) |
| `StocksSizeByPrice` / `CryptoSizeByPrice` / `Crypto*` / `Picker*` | asset-class sizing | see snippet doc |

`SimpleMartingaleMM`: after a loss size = last size x `LotsMultiplier`; a win or exceeding
`LotsReset` resets to `LotsStart`; optionally per direction. Force-disabled on
MultiCharts/TradeStation engines; compounding distorts ranking during generation: warn the user,
set a hard `LotsReset` cap plus a `RiskManagement maxDrawdown` limit.

## Intent -> lever cheat sheet

| Intent | Levers |
|---|---|
| Martingale | `SimpleMartingaleMM use=true` (+ params), other Methods `use=false`; keep `<RiskManagement maxDrawdown>`; warn about ranking distortion + MC/TS engines; consider `MaxTradesPerDay` and `_ExitRule_` off. |
| Mean reversion | template `Mean-Reversal`, or: only `*Falling/*Lower/*CrossDown/*ChangesDown` + BB/KC "closes above upper / below lower" signals; `EnterAtMarket` + `EnterReverseAtMarket` (optionally `EnterAtLimit`); `_ExitRule_ use=true`; PT < SL. |
| Trend following | template `TrendFollowing`, or: only `*Rising/*Higher/*CrossUp` + MACD/ADX/DI/Aroon/LinReg families; `TrailingStop use=true`; PT >> SL or `PTRequired=false`. |
| Breakout | TrendFollowing base + OrderTypes only `EnterAtStop use=true`; enable `stopLimitBlocks` (`Stop/Limit Price Levels.Highest/Lowest/...`, `Stop/Limit Price Ranges.ATR/BarRange/...`); breakout signals (`IchimokuKumoBreakout*`, `KCBarClosesAboveUpper`, `BBBarClosesAbove*`). |
| Scalping / intraday | `Data/Setups/Setup/Chart@timeframe` M1-M15; small `MinSLInPips/MaxSLInPips`; `Options`: `LimitTimeRange`, `ExitAtEndOfDay=true`, `MaxTradesPerDay`; Rankings: raise the `NumberOfTrades >` filter. |
| Swing / daily | template `Daily`; H4/D1; wide ATR-based SL; `ExitAfterBars` prob 100. |
| Long-only / short-only | `WhatToBuild/MarketSides@type` = `long` / `short` (symmetry flags read only when `both`). |
| Fuzzy / many conditions | `StrategyType@architecture="sq4fuzzy"`, `RulesComplexity minConditions>=4`, `minTrue/maxTrue`. |

## Relevant XML sections

- `<WhatToBuild>`: `<StrategyType type="simple|multi-tf|template|improve" architecture="sq4|sq4fuzzy|sq3">`, `<MarketSides type="both|long|short">` + `EntrySymmetry`/`ExitSymmetry`, `<RulesComplexity>` (min/maxConditions, period/shift ranges), `<SLPTOptions>` (`SLRequired`, `PTRequired`, `SLATR/SLFixedPips/SLPercent`, `MinSLInPips`/`MaxSLInPips`, PT mirrors; PT ranges are overwritten from SL when `SeparatedSettings=false`), `<BuildMode generationType="random-generation|genetic-evolution">` (+ `PopulationSize`, `MaxGenerations`, `Islands`, ...).
- `<Blocks>`: `<BuildingBlocks>` (`Block key=<class or dotted family>`, `use`, `weight`, `category="signals|indicators|stopLimitBlocks"`; per-`Param` `generation="random|fixed"`, negative min/max sentinels = inherit the global period/shift/SL/PT range), `<OrderTypes>`, `<ExitTypes>` (probability), `<Calibration>`.
- `<Options><BuildTradingOptions><Params>`: flat `<Param key= className=>` list, all active at once: `ExitAtEndOfDay`/`EODExitTime`, `ExitOnFriday`, `LimitTimeRange` + range, `MaxTradesPerDay`, `MinimumSLPT`/`MaximumSLPT`, `Session`. No max-open-trades setting exists; nearest levers are `#AllowDuplicateTrades#` per order type and `MaxTradesPerDay`.
- `<Rankings>`: `<FitnessCriteria method="ComputeFromStrategyResult"><Settings><Ranking type="ReturnDDRatio"/>`, `<Conditions>` (databank-column comparisons, e.g. `NumberOfTrades > 100`), `<StopCondition type="never|passed-count|databank-full|time-limit">`.
- `<Data>`: `<Setups><Setup dateFrom= dateTo= engine=...><Chart symbol= timeframe= spread=/>`, `<OutOfSample><Range dateFrom= dateTo=/>`.

## Blocks

- `category="signals"` blocks are pre-combined conditions (indicator + comparison in one class: `RSICrossUp`, `MARising`, ...); `category="indicators"` + operator blocks (`CrossesAbove`, `IsRising`, ...) belong to the old `sq3` architecture and ship disabled everywhere.
- Every condition class declares an `@OppositeBlock` for symmetry; override via `user/settings/OppositeBlocks.csv`.
- Catalog: [`../overview/snippets/building-blocks/`](../overview/snippets/building-blocks/README.md) (52 indicator families, ~400 blocks).
