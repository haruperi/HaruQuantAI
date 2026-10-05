# Results: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppResults.jar](AppResults.md) | 1 | `com.strategyquant.plugin.App.impl.Results` |
| [DashboardResults.jar](DashboardResults.md) | 2 | `com.strategyquant.plugin.Dashboard.impl.Results` |
| [DatabankFilterByCorrelation.jar](DatabankFilterByCorrelation.md) | 2 | `com.strategyquant.plugin.Databank.impl.FilterByCorrelation` |
| [DatabankRename.jar](DatabankRename.md) | 2 | `com.strategyquant.plugin.Databank.impl.Rename` |
| [EquityChartBenchmark.jar](EquityChartBenchmark.md) | 3 | `com.strategyquant.plugin.EquityChart.impl.Benchmark` |
| [EquityChartDailyChart.jar](EquityChartDailyChart.md) | 1 | `com.strategyquant.plugin.EquityChart.impl.DailyChart` |
| [EquityChartDrawdown.jar](EquityChartDrawdown.md) | 1 | `com.strategyquant.plugin.EquityChart.impl.Drawdown` |
| [EquityChartVolatility.jar](EquityChartVolatility.md) | 1 | `com.strategyquant.plugin.EquityChart.impl.Volatility` |
| [EquityChartVolume.jar](EquityChartVolume.md) | 1 | `com.strategyquant.plugin.EquityChart.impl.Volume` |
| [ResultsChart.jar](ResultsChart.md) | 2 | `com.strategyquant.plugin.Results.impl.Chart` |
| [ResultsDatabankActions.jar](ResultsDatabankActions.md) | 3 | `com.strategyquant.plugin.Results.impl.DatabankActions` |
| [ResultsDatabankViews.jar](ResultsDatabankViews.md) | 2 | `com.strategyquant.plugin.Results.impl.DatabankViews` |
| [ResultsEquityChart.jar](ResultsEquityChart.md) | 2 | `com.strategyquant.plugin.Results.impl.EquityChart` |
| [ResultsExplore.jar](ResultsExplore.md) | 2 | `com.strategyquant.plugin.Results.impl.Explore` |
| [ResultsOptimizationProfile.jar](ResultsOptimizationProfile.md) | 12 | `com.strategyquant.plugin.Results.impl.OptimizationProfile`, `com.strategyquant.plugin.Results.impl.OptimizationProfile.charts`, `com.strategyquant.plugin.Results.impl.OptimizationProfile.results` |
| [ResultsOverview.jar](ResultsOverview.md) | 2 | `com.strategyquant.plugin.Results.impl.Overview` |
| [ResultsPlugins.jar](ResultsPlugins.md) | 2 | `com.strategyquant.plugin.Results.impl.Plugins` |
| [ResultsPortfolioCorrelation.jar](ResultsPortfolioCorrelation.md) | 13 | `com.strategyquant.plugin.Results.impl.PortfolioCorrelation`, `com.strategyquant.plugin.Results.impl.PortfolioCorrelation.correlation`, `com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades` |
| [ResultsProfileChart.jar](ResultsProfileChart.md) | 2 | `com.strategyquant.plugin.Results.impl.ProfileChart` |
| [ResultsRobustnessTests.jar](ResultsRobustnessTests.md) | 7 | `com.strategyquant.plugin.Results.impl.RobustnessTests`, `com.strategyquant.plugin.Results.impl.RobustnessTests.views` |
| [ResultsSPOverview.jar](ResultsSPOverview.md) | 5 | `com.strategyquant.plugin.Results.impl.SPOverview` |
| [ResultsSequentialOptimization.jar](ResultsSequentialOptimization.md) | 2 | `com.strategyquant.plugin.Results.impl.SequentialOptimization` |
| [ResultsSourceCode.jar](ResultsSourceCode.md) | 2 | `com.strategyquant.plugin.Results.impl.SourceCode` |
| [ResultsStockpicker.jar](ResultsStockpicker.md) | 2 | `com.strategyquant.plugin.Results.impl.Stockpicker` |
| [ResultsStrategyConfig.jar](ResultsStrategyConfig.md) | 2 | `com.strategyquant.plugin.Results.impl.StrategyConfig` |
| [ResultsSysParamPermutation.jar](ResultsSysParamPermutation.md) | 2 | `com.strategyquant.plugin.Results.impl.SysParamPermutation` |
| [ResultsTradeAnalysis.jar](ResultsTradeAnalysis.md) | 3 | `com.strategyquant.plugin.Results.impl.TradeAnalysis` |
| [ResultsTradeList.jar](ResultsTradeList.md) | 2 | `com.strategyquant.plugin.Results.impl.TradeList` |
| [ResultsTradelistViews.jar](ResultsTradelistViews.md) | 2 | `com.strategyquant.plugin.Results.impl.TradelistViews` |
| [ResultsWalkForward.jar](ResultsWalkForward.md) | 5 | `com.strategyquant.plugin.Results.impl.WalkForward`, `com.strategyquant.plugin.Results.impl.WalkForward.views` |

## Workspace registration evidence

- Observed NavigationPlugin in `SQX_REFERENCE_ROOT/internal/plugins/AppResults/module.js`: title `Results`, app code `RESULTS`, hidden registration `True`. SHA-256 `42cc52c94aa2d7254ce4daea288a0ada674237c2c3ce562a4a953ec16b799607`; inspected 2026-10-05 by direct text, at NavigationPlugin object. Registration does not prove runtime/license availability.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQDataLib.jar](../Shared/SQDataLib.md) - `Shared`.
- [SQPluginLib.jar](../Shared/SQPluginLib.md) - `Shared`.
- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.
- [SQWebGUILib.jar](../Shared/SQWebGUILib.md) - `Shared`.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
