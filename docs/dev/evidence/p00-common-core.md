# P00 common-core observations and blockers

Status: static body-derived observations; no runtime parity or common-core translation.
Reference cohort label 144.2953; installed product build/activation unverified.
Inspected at 2026-10-06T15:07:57.025762+00:00; source HEAD `7c4436185f74b5e615c4a35160e60b6a902029c7`.

## Exact source provenance

Four donor archives were fingerprinted and inspected with javap -c -p. Their
locations/fingerprints appear in the current ledger. JrtFileSystemProvider was
re-inspected using an explicit archive-entry URI after a system classpath lookup
selected a different platform class. Its actual donor class SHA-256 is
`6e91de56a9f0254674687f9fbe6fbdea3deb985af9dd84881bf6f486dac05cac`.
Proprietary bytecode/decompiled output is not retained. No donor executable ran.

## Behavioral paraphrases

Paraphrases below come from `javap -c -p` bodies, not roadmap FR seeds. Exact
bytecode offsets will be retained in new evidence; proprietary text will not.

- `AbstractUIWebServer` constructor sets instance state, reads `SSLUse` with string
  default `false`, and passes it to Java Boolean parsing (offsets 13-26).
- `start()` loads handlers, sets the handler list, obtains a token, and emits a
  DEBUG event containing that token before reading `WebServerPort` with string
  default `-1`. Integer parsing is signed Java int; the read/parse block catches
  `Exception` and emits INFO (offsets 0-88). Do not infer AppSettings precedence.
- A positive port makes one explicit `startServer` call. Otherwise it tries
  integral TCP ports 8080 through 8090 inclusive, in ascending order, stopping at
  the first success. Failed starts attempt stop, swallow stop exceptions, then
  warn and advance. Exhaustion raises an exception (offsets 89-232). These units
  are TCP port numbers; no numerical rounding or tolerance applies.
- After server startup it logs success, sets `WebServerPortUsed`, sets
  `BrowserToken` as strings, saves settings, then calls `serverStarted(port)`
  (offsets 233-330). Saving internals and startup caller ownership are unavailable.
- Handler assembly branches on `MainApp.checkProduct("QDM")`; non-QDM resource
  assembly includes user extension roots. Product checks and license/activation
  semantics are missing. Presence/hidden navigation flags are not activation.
- `SQPluginManager.initForProduct(product)` delegates with a null second argument.
  The two-argument body constructs JSPF manager/information/utility state, loads
  `internal/plugins`, then `user/extend/Plugins`, then assigns product state
  (offsets 0-66). Folder loading and filtering need their own complete body trace
  before P02 implementation; no Python registry translation is authorized here.
- `JobEngine(int)` creates a jobs list, replaces a nonpositive worker count by
  `CpuInfo.getAvailableProcessors()`, then creates a fixed thread pool (0-31).
  CPU calculation/defaults cannot be guessed from this caller.
- `JrtFileSystemProvider.newFileSystem(uri, map)` checks nonnull map, permission,
  and URI, then branches on `java.home`; the alternate-runtime branch requires
  its `lib/jrt-fs.jar`, copies the map and removes `java.home`, constructs a loader,
  and delegates to a reflected provider. Missing files/reflection failures become
  IO errors. This is JVM infrastructure; no host filesystem algorithm is inferred.

Observed donor token logging and swallowed shutdown exceptions conflict with
repository redaction/non-silent failure authority. P00 records those conflicts;
it implements neither behavior. A future translating plan must obtain an explicit
decision on each affected operation before execution.

## Responsibilities and unresolved closure

MainApp owns referenced settings/product/data-path access; AppSettings owns the
referenced get/set/save contract. Their implementation owner archive is unavailable.
CpuInfo calculations, SQLib loader packaging, startup callers, settings precedence,
license/activation checks, loading internals and failure policies remain unresolved.
These responsibility labels describe call-site obligations, not an implemented
Python interface. Host/resource/discovery translations need their own approvals.

182 classes in 58 archives reference MainApp/AppSettings in their classfile
constant pools. The table below is a structural consumer index beyond the 667 seeds.
It does not claim method-body closure or runtime activation. Deeper callees remain
uninspected until feature-scoped research. Exact equality applies to port/count/
order facts; no rounding, floating tolerance or financial formula is inferred.

## Consumer index

| Artifact | Consumer class | Referenced dependency | Behavior status |
| --- | --- | --- | --- |
| `internal/libs/Snippets.jar` | `SQ.Blocks.Indicators.Other.DataLoggingIndy` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/Snippets.jar` | `SQ.Internal.AbstractChart` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.basket.BasketBrokerDev` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.basket.BasketOfStocksManager` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.broker.BrokerManager` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.data.DataCloner` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.data.DataExporter` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.data.DataFolderSweeper` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.data.DataManager` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.data.DukasDataManager` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.data.imports.DataImportEngine$1` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.data.io.DataCsvLoader` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.data.io.newDataFormat.DataManipulatorNew` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.historyData.FuturesHistoryDataDao` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.indicators.CustomIndicatorFileImporter` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQDataLib.jar` | `com.strategyquant.datalib.metatrader4.Mt4Properties` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.indicatorTester.IndicatorTesterConfig` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.Blocks` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.Databank$2` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.Databank` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.MemoryCleaner$1` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.MemoryCleaner$2` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.MemoryCleaner` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.OverviewTemplate` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.Result` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.ResultsGroup` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.applyMassConfig.ApplyMassConfig` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.backtest.TestfilesUtils` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.benchmark.BenchmarkEngine` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.blocks.BlocksConfigGenerator` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.connection.ConnectionsFileManager` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.crosscheck.CrossCheckMethod` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.dailyEquity.DailyEquity` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.data.AppDataImporter` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.data.download.DownloadDispatcher` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.databank.DatabankViewsManager` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.dukascopy.CdnCache` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.dukascopy.DukascopyUtils` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.dukascopy.job.DownloadDukascopySymbolJob` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.engine.stockpicker.Stockpicker` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.engine.stockpicker.StockpickerBacktestEngine` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.engine.stockpicker.backtester.PortfolioBacktestJob` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.engine.stockpicker.backtester.PortfolioBacktester` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.engine.stockpicker.data.PickerDataLoader` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.engine.stockpicker.data.PickerDataPreloader` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.engine.stockpicker.data.additional.AdditionalDataCache` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.StockGroupsDataCache` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.file.SQFileManager` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.generator.StrategyGenerator` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.generator.StrategyImproveTemplateSQ3` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.generator.StrategyImproveTemplateSQ4` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.generator.StrategyStandardTemplateSQ3` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.generator.StrategyStandardTemplateSQ4` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.generator.StrategyStockpickerSingleAssetTemplate` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.generator.StrategyStockpickerTemplate` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.generator.StrategyTemplateGenerator` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.gp.strategies.NodeCrossover` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.historyData.DownloadEodStockHistorySymbolJob` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.historyData.DownloadHistorySymbolJob` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.historyData.HistoryDataManager` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.historyData.HttpApacheManager` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.historyData.SpecialSymbolsManager` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.mql.MQLMarketConverter` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.mt5api.Mt5ApiDownloaderJob` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.optimization.OptimizationEngineBase` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.optimization.OptimizationProfile` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.options.TradingOptions` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.performance.Performance` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.project.ProjectResources` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.project.SQLogger` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.project.SQProject` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.project.StrategiesSaver` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.project.StrategySaver` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.project.StrategyXMLModifier` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.project.bestresults.BestResultOverview` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.project.console.ConsoleImpl$1` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.project.console.ConsoleImpl` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.project.websocket.SQWebSocketManager$1` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.project.websocket.SQWebSocketManager` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.python.PythonRunner` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.results.file.FileHandler` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.simplegrid.SimpleGridEngine` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.simulator.impl.MetaTraderSimulatorHedging` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.simulator.impl.MetaTraderSimulatorNetting` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.simulator.impl.TradestationSimulator` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.stockchart.StockSaverForStockPicking` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.stockchart.StockSaverOriginalFormat` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.strategy.StrategyMerger` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.strategy.xml.SQ3StrategyConverter` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.strategy.xml.StrategyFixer` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.talib.TALibBlocks` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.talib.TALibIndicatorsCache` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.taskImpl.AbstractTask` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.task.settings.blocks.ConfigConverter` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.tradelist.TradelistViewsManager` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.util.TradingLibUtil` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQTradingLib.jar` | `com.strategyquant.tradinglib.wfo.WFOSimulationEngine` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.BrowserGUI` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.Electron` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.WebAppManager` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.init.AutoCompiler` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.license.LicenseDialog$1` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.license.LicenseDialog` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.server.AbstractUIWebServer` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.servlet.DirServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.servlet.HttpJSONServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.servlet.LanguageServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.servlet.MainServlet$1` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.servlet.MainServlet$2` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.servlet.MainServlet$3` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.servlet.MainServlet$6` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQWebGUILib.jar` | `com.strategyquant.webguilib.servlet.MainServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/libs/SQWizardBusiness.jar` | `com.strategyquant.wizard.desktop.indicators.CustomIndicatorFileImporter` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/libs/SQWizardBusiness.jar` | `com.strategyquant.wizard.desktop.loader.ErrorReportSender` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/AppCodeEditor/AppCodeEditor.jar` | `com.strategyquant.plugin.App.impl.CodeEditor.CodeEditorAppPlugin$1` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/AppDebugConsole/AppDebugConsole.jar` | `com.strategyquant.plugin.App.impl.DebugConsole.DebugConsoleAppPlugin` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/AppQuantDataManager/AppQuantDataManager.jar` | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin$1` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/AppQuantDataManager/AppQuantDataManager.jar` | `com.strategyquant.plugin.App.impl.QuantDataManager.QuantDataManagerAppPlugin` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/AppSQXBusiness/AppSQXBusiness.jar` | `com.strategyquant.plugin.App.impl.SQXBusiness.SQXBusinessServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/AppSQXHome/AppSQXHome.jar` | `com.strategyquant.plugin.App.impl.SQXHome.SQXHomeServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/CodeEditorImportExport/CodeEditorImportExport.jar` | `com.strategyquant.plugin.CodeEditor.impl.ImportExport.ExtensionManager` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/CodeEditorImportExport/CodeEditorImportExport.jar` | `com.strategyquant.plugin.CodeEditor.impl.ImportExport.ImportExportServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/ConnectionMT4/ConnectionMT4.jar` | `com.strategyquant.plugin.Connection.impl.MT4.MT4ConnectionPlugin` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DashboardResults/DashboardResults.jar` | `com.strategyquant.plugin.Dashboard.impl.Results.DashboardResultsServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/DataManagerBasket/DataManagerBasket.jar` | `com.strategyquant.plugin.DataManager.impl.Basket.BasketServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataManagerBroker/DataManagerBroker.jar` | `com.strategyquant.plugin.DataManager.impl.Broker.BrokerServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataManagerCustomData/DataManagerCustomData.jar` | `com.strategyquant.plugin.DataManager.impl.CustomData.CustomDataServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataManagerData/DataManagerData.jar` | `com.strategyquant.plugin.DataManager.impl.Data.DataServlet$4` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataManagerData/DataManagerData.jar` | `com.strategyquant.plugin.DataManager.impl.Data.DataServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/DataManagerHome/DataManagerHome.jar` | `com.strategyquant.plugin.DataManager.impl.Home.HomeServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataManagerInstruments/DataManagerInstruments.jar` | `com.strategyquant.plugin.DataManager.impl.Instruments.InstrumentsServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataSourceCrypto/DataSourceCrypto.jar` | `com.strategyquant.plugin.DataSource.impl.Crypto.DataSourceCryptoServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataSourceDarwinex/DataSourceDarwinex.jar` | `com.strategyquant.plugin.DataSource.impl.Darwinex.DarwinexDataManager` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/DataSourceDarwinex/DataSourceDarwinex.jar` | `com.strategyquant.plugin.DataSource.impl.Darwinex.DarwinexServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataSourceDarwinex/DataSourceDarwinex.jar` | `com.strategyquant.plugin.DataSource.impl.Darwinex.importdata.DarwinexImportJob` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataSourceDukascopy/DataSourceDukascopy.jar` | `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/DataSourceFiles/DataSourceFiles.jar` | `com.strategyquant.plugin.DataSource.impl.Files.DataSourceFilesServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/DataSourceFiles/DataSourceFiles.jar` | `com.strategyquant.plugin.DataSource.impl.Files.job.DataImporter` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataSourceFiles/DataSourceFiles.jar` | `com.strategyquant.plugin.DataSource.impl.Files.job.DataMassImporter` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataSourceMt5Api/DataSourceMt5Api.jar` | `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataSourceSQEquityData/DataSourceSQEquityData.jar` | `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataSourceSQFuturesData/DataSourceSQFuturesData.jar` | `com.strategyquant.plugin.DataSource.impl.SQFuturesData.SQFuturesDataServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/DataSourceYahoo/DataSourceYahoo.jar` | `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/EquityChartBenchmark/EquityChartBenchmark.jar` | `com.strategyquant.plugin.EquityChart.impl.Benchmark.Benchmark` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/HomeAbout/HomeAbout.jar` | `com.strategyquant.plugin.Home.impl.About.AboutServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/LoaderSQ3/LoaderSQ3.jar` | `com.strategyquant.plugin.Loader.impl.SQ3.SQ3FileLoaderOldXml` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/LoaderSQ4/LoaderSQ4.jar` | `com.strategyquant.plugin.Loader.impl.SQ4.SQ4LoaderPlugin` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/PortfolioComposer/PortfolioComposer.jar` | `com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/ResultsDatabankActions/ResultsDatabankActions.jar` | `com.strategyquant.plugin.Results.impl.DatabankActions.DatabankActionsServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ResultsEquityChart/ResultsEquityChart.jar` | `com.strategyquant.plugin.Results.impl.EquityChart.EquityChartServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ResultsOptimizationProfile/ResultsOptimizationProfile.jar` | `com.strategyquant.plugin.Results.impl.OptimizationProfile.OptimizationProfileServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ResultsOptimizationProfile/ResultsOptimizationProfile.jar` | `com.strategyquant.plugin.Results.impl.OptimizationProfile.results.OptResultsViewsManager` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ResultsRobustnessTests/ResultsRobustnessTests.jar` | `com.strategyquant.plugin.Results.impl.RobustnessTests.RobustnessTestsServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ResultsRobustnessTests/ResultsRobustnessTests.jar` | `com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViewsManager` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ResultsSourceCode/ResultsSourceCode.jar` | `com.strategyquant.plugin.Results.impl.SourceCode.SourceCodeServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ResultsSysParamPermutation/ResultsSysParamPermutation.jar` | `com.strategyquant.plugin.Results.impl.SysParamPermutation.SysParamPermutationServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ResultsTradeAnalysis/ResultsTradeAnalysis.jar` | `com.strategyquant.plugin.Results.impl.TradeAnalysis.TradeAnalysisServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ResultsTradeList/ResultsTradeList.jar` | `com.strategyquant.plugin.Results.impl.TradeList.TradeListServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ResultsTradelistViews/ResultsTradelistViews.jar` | `com.strategyquant.plugin.Results.impl.TradelistViews.TradelistViewsServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ResultsWalkForward/ResultsWalkForward.jar` | `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ResultsWalkForward/ResultsWalkForward.jar` | `com.strategyquant.plugin.Results.impl.WalkForward.views.WFViewsManager` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/SaverHTML/SaverHTML.jar` | `com.strategyquant.plugin.Saver.impl.HTML.HTMLReportPlugin` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/SaverPDF/SaverPDF.jar` | `com.strategyquant.plugin.Saver.impl.PDF.PDFReportPlugin` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/SaverSQ3/SaverSQ3.jar` | `com.strategyquant.plugin.Saver.impl.SQ3.SQ3FileSaver` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/SaverStrategyTrades/SaverStrategyTrades.jar` | `com.strategyquant.plugin.Saver.impl.StrategyTrades.StrategyTradesSaverPlugin` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ServletAlgoWizard/ServletAlgoWizard.jar` | `com.strategyquant.plugin.Servlet.impl.AlgoWizard.AlgoWizardServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ServletCodeEditor/ServletCodeEditor.jar` | `com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeAutoCompleteManager` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/ServletCodeEditor/ServletCodeEditor.jar` | `com.strategyquant.plugin.Servlet.impl.CodeEditor.CodeEditorServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/ServletCodeEditor/ServletCodeEditor.jar` | `com.strategyquant.plugin.Servlet.impl.CodeEditor.FileMap` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/ServletCodeEditor/ServletCodeEditor.jar` | `com.strategyquant.plugin.Servlet.impl.CodeEditor.templates.Templates` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/ServletConstants/ServletConstants.jar` | `com.strategyquant.plugin.Servlet.impl.Constants.ConstantsServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ServletProject/ServletProject.jar` | `com.strategyquant.plugin.Servlet.impl.Project.ProjectServlet` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/ServletRenameTool/ServletRenameTool.jar` | `com.strategyquant.plugin.Servlet.impl.RenameTool.RenameToolSettings` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/ServletWizard/ServletWizard.jar` | `com.strategyquant.plugin.Servlet.impl.Wizard.WizardServlet` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/SettingsCrossChecks/SettingsCrossChecks.jar` | `com.strategyquant.plugin.Settings.impl.CrossChecks.CrossChecksPlugin` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/SettingsNotification/SettingsNotification.jar` | `com.strategyquant.plugin.Settings.impl.Notification.NotificationPlugin` | `com.strategyquant.lib.app.MainApp`, `com.strategyquant.lib.app.AppSettings` | unresolved |
| `internal/plugins/SettingsWhatToBuild/SettingsWhatToBuild.jar` | `com.strategyquant.plugin.Settings.impl.WhatToBuild.WhatToBuildSettingsPlugin` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/TaskAutomaticPortfolioBuilder/TaskAutomaticPortfolioBuilder.jar` | `com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.AutomaticPortfolioBuilder` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/TaskBuild/TaskBuild.jar` | `com.strategyquant.plugin.Task.impl.Build.BuildTask` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/TaskBuild/TaskBuild.jar` | `com.strategyquant.plugin.Task.impl.Build.RandomBuildEngine` | `com.strategyquant.lib.app.MainApp` | unresolved |
| `internal/plugins/TaskOptimize/TaskOptimize.jar` | `com.strategyquant.plugin.Task.impl.Optimize.OptimizeTask` | `com.strategyquant.lib.app.MainApp` | unresolved |
