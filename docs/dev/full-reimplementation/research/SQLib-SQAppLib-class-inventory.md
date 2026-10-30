# SQLib and supplied SQAppLib counterpart: class inventory

Generated from local donor JAR central directories on 2026-10-30. This is research for selecting capabilities, not an implementation work order. No donor source bodies are included.

## Provenance and scope

Direct Java context now lives in `DONOR_REFERENCE_ROOT/internal/libs/lib/` and
`DONOR_REFERENCE_ROOT/internal/libs/tradinglib/`. All class links point to the copied
Java file. Nested/anonymous class entries link to their enclosing source file.

The original compiled-entry counts and archive SHA-256 values below are historical
inventory metadata, not hashes of these source folders. They do not authenticate the
original encrypted build-145 carrier mapping. Names/package membership were observed;
selection recommendations remain design guidance rather than accepted implementation.

## Selection guide

| Reference | Capability to consider | Representative types | Suggested placement |
|---|---|---|---|
| SQLib | Settings and typed values | SettingsMap, ValuesMap, ParametrizationSettings | Core settings/contracts; adapt to Python |
| SQLib | Time and date handling | SQTime, TimePeriod, TimePeriods, DateTimeParser, DateFormats | Core utilities where required |
| SQLib | Deterministic random generation | IRandomGenerator, MTRandom, MersenneTwisterFast, MersenneTwisterRng | Core RNG contract; choose algorithms explicitly |
| SQLib | Extension discovery | CustomClassesLoader, CustomClassesLoaderCache, CustomClassesReg, ICustomClasses | Core extension registry; replace Java loading machinery |
| SQLib | Resource and cancellation contracts | MemoryInfo, CpuInfo, MemoryUsageChecker, IStopPauseStatus, TaskStoppedException | Retain existing host/jobs equivalents where suitable |
| SQLib | Persistence and packaging helpers | XMLUtil, Zipper, Unzipper, FileLoader, DirectoryHash | Use standard libraries; compatibility adapters only where needed |
| SQLib | Desktop UI, Java compiler, licensing, branding, updates, QDM | app, jxbrowser, snippets.compile, security, whitelabel, updates, qdm packages | Defer or omit from AppCore unless a specific requirement needs them |
| SQTradingLib | Strategy contracts and execution state | StrategyBase, IBlock, BuildingBlock, Indicator, Order, OrdersList, LiveOrderObj, MarketData | Core contracts/runtime; concrete indicators in extensions |
| SQTradingLib | Backtesting and simulation | BacktestRunner, BacktestSettings, SQBacktester, BacktestDataFeed, AbstractTradingSimulator | Core engine; select required platform execution semantics |
| SQTradingLib | Results and statistics | Result, ResultsGroup, SQStats, StatsKey, StatsComputer | Core result model/statistics; verify formulas individually |
| SQTradingLib | Conditions and filters | Condition, Conditions, ConditionsChecker, NumericValue | Core condition model; workspace-specific policy outside Core |
| SQTradingLib | Storage and databanks | SQFileManager, Databank, DatabankRecords, ResultsMap | Core persistence contracts; workspace orchestration separately |
| SQTradingLib | Strategy generation | StrategyGenerator, GeneratorBase, GPEngine, GPGenerationalEngine, EvolutionPipeline | Shared research engine if selected; builder orchestration in workspace |
| SQTradingLib | Optimization and walk-forward | OptimizationEngine, OptimizationEngineSimple, OptimizationEngineWF, SequentialOptimizationEngine | Shared compute engine if selected |
| SQTradingLib | Robustness and portfolio research | MonteCarloManipulation, MonteCarloRetest, WhatIf; correlation, robustnesstests, portfolioMaster packages | Select separately; concrete variants in extensions/workspaces |
| SQTradingLib | Project control, UI, data providers, stock picker, Java integration | project, equitychart, stockchart, propertygrid, dukascopy, yahoo, engine.stockpicker, talib packages | Separate workspace/adapter choices; do not import wholesale into Core |

## Important source corrections

- Inspected `SettingsMap.java`: it extends `ValuesMap`, adds defaults, XML naming, cloning and typed static getters. It does not itself establish SQLite persistence, revision locking or atomic patch transactions.
- Inspected `CustomClassesLoader.java`: it discovers classes under an `SQ.<name>` package through a cache and Java class loader. This alone does not establish a Python reload contract.

## Complete inventory

### SQLib

- Direct source folder: `DONOR_REFERENCE_ROOT/internal/libs/lib`
- Historical archive SHA-256: `40be384480b4ae8c062fec8be37e657579e31c0750730949c086eac58de6c849`
- Compiled entries: **254**; entries without `$`: **223**; nested/anonymous entries: **31**.
- Available Java source files: **223**.
- Signatures: [API dump](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/signatures/SQLib_signatures.txt)

#### com.strategyquant.allTimeStats (2)

- [AllTimeStats](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/allTimeStats/AllTimeStats.java)
- [AllTimeStatsTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/allTimeStats/AllTimeStatsTypes.java)

#### com.strategyquant.lib (18)

- [ElementComparatorByAttribute](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/ElementComparatorByAttribute.java)
- [HistoryDataLoader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/HistoryDataLoader.java)
- [HistoryDataNotAvailableExeption](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/HistoryDataNotAvailableExeption.java)
- [HistoryOHLCData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/HistoryOHLCData.java)
- [IRandomGenerator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/IRandomGenerator.java)
- [IStopPauseStatus](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/IStopPauseStatus.java)
- [L](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L.java)
- [MemoryInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/MemoryInfo.java)
- [ProcessPriorityAdjuster](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/ProcessPriorityAdjuster.java)
- [SQTime](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/SQTime.java)
- [SQUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/SQUtils.java)
- [SettingsMap](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/SettingsMap.java)
- [TaskStoppedException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/TaskStoppedException.java)
- [TimePeriod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/TimePeriod.java)
- [TimePeriods](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/TimePeriods.java)
- [ValuesMap](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/ValuesMap.java)
- [XMLUtil](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/XMLUtil.java)
- [package-info](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/package-info.java) — package metadata

#### com.strategyquant.lib.L88OaFjjon (19)

- [CwkMCS2pCb](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/CwkMCS2pCb.java)
- [DVGBR8rirw](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/DVGBR8rirw.java)
- [DcOjahK4ng](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/DcOjahK4ng.java)
- [DqO7PIpn7z](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/DqO7PIpn7z.java)
- [Eob3xULZVY](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/Eob3xULZVY.java)
- [G8SyrBEfO8](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/G8SyrBEfO8.java)
- [G8SyrBEfO8$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/G8SyrBEfO8.java) — nested/anonymous
- [KIozbup0X4](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/KIozbup0X4.java)
- [Lewgre21g](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/Lewgre21g.java)
- [Lewgre21g$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/Lewgre21g.java) — nested/anonymous
- [Tu5UdlpFO9](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/Tu5UdlpFO9.java)
- [V571hfnsHw](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/V571hfnsHw.java)
- [V7hkcR2dQd](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/V7hkcR2dQd.java)
- [WbwPVQGc2h](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/WbwPVQGc2h.java)
- [YbM3Hb5g8g](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/YbM3Hb5g8g.java)
- [YbM3Hb5g8g$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/YbM3Hb5g8g.java) — nested/anonymous
- [YbM3Hb5g8g$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/YbM3Hb5g8g.java) — nested/anonymous
- [YbM3Hb5g8g$3](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/YbM3Hb5g8g.java) — nested/anonymous
- [YbM3Hb5g8g$4](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/L88OaFjjon/YbM3Hb5g8g.java) — nested/anonymous

#### com.strategyquant.lib.app (13)

- [AppSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/AppSettings.java)
- [AppSettingsConst](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/AppSettingsConst.java)
- [AppSplash](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/AppSplash.java)
- [AppSplash$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/AppSplash.java) — nested/anonymous
- [IMainApp](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/IMainApp.java)
- [IMainFrame](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/IMainFrame.java)
- [IMainWindow](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/IMainWindow.java)
- [ISQStatusBar](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/ISQStatusBar.java)
- [LastUsedDirectory](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/LastUsedDirectory.java)
- [LauncherConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/LauncherConfig.java)
- [LicenseInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/LicenseInfo.java)
- [MainApp](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/MainApp.java)
- [SQSplashScreen](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/SQSplashScreen.java)

#### com.strategyquant.lib.app.impl (3)

- [IConsoleImpl](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/impl/IConsoleImpl.java)
- [MainAppSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/impl/MainAppSettings.java)
- [MainAppStandardImpl](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/impl/MainAppStandardImpl.java)

#### com.strategyquant.lib.app.webserver (9)

- [AbstractTextServlet](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/webserver/AbstractTextServlet.java)
- [HttpTextServlet](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/webserver/HttpTextServlet.java)
- [MainAppHttpHandler](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/webserver/MainAppHttpHandler.java)
- [MainAppHttpHandler$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/webserver/MainAppHttpHandler.java) — nested/anonymous
- [MainAppWebServer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/webserver/MainAppWebServer.java)
- [MainAppWebSocket](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/webserver/MainAppWebSocket.java)
- [MainAppWebSocket$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/webserver/MainAppWebSocket.java) — nested/anonymous
- [MainAppWebSocket$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/webserver/MainAppWebSocket.java) — nested/anonymous
- [MainAppWebSocketServlet](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/app/webserver/MainAppWebSocketServlet.java)

#### com.strategyquant.lib.classInfo (5)

- [ClassHelper](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/classInfo/ClassHelper.java)
- [ClazzInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/classInfo/ClazzInfo.java)
- [ClazzInfo$MethodInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/classInfo/ClazzInfo.java) — nested/anonymous
- [ClazzInfo$ParamInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/classInfo/ClazzInfo.java) — nested/anonymous
- [CodeInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/classInfo/CodeInfo.java)

#### com.strategyquant.lib.constants (3)

- [ProgressType](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/constants/ProgressType.java)
- [SQConst](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/constants/SQConst.java)
- [SQPaths](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/constants/SQPaths.java)

#### com.strategyquant.lib.crypting (3)

- [AESCrypterDecrypter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/AESCrypterDecrypter.java)
- [DecryptException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/DecryptException.java)
- [SQDecoderEncoder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/SQDecoderEncoder.java)

#### com.strategyquant.lib.crypting.codec (4)

- [Decoder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/Decoder.java)
- [DecoderException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/DecoderException.java)
- [Encoder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/Encoder.java)
- [EncoderException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/EncoderException.java)

#### com.strategyquant.lib.crypting.codec.binary (9)

- [Base64](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/binary/Base64.java)
- [Base64InputStream](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/binary/Base64InputStream.java)
- [Base64OutputStream](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/binary/Base64OutputStream.java)
- [BaseNCodec](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/binary/BaseNCodec.java)
- [BaseNCodec$Context](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/binary/BaseNCodec.java) — nested/anonymous
- [BaseNCodecInputStream](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/binary/BaseNCodecInputStream.java)
- [BaseNCodecOutputStream](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/binary/BaseNCodecOutputStream.java)
- [BinaryCodec](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/binary/BinaryCodec.java)
- [StringUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/crypting/codec/binary/StringUtils.java)

#### com.strategyquant.lib.customization (1)

- [Customization](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/customization/Customization.java)

#### com.strategyquant.lib.db (1)

- [DbBase](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/db/DbBase.java)

#### com.strategyquant.lib.debugging (3)

- [DuplicateLogFilter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/debugging/DuplicateLogFilter.java)
- [MessageConsole](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/debugging/MessageConsole.java)
- [MessageConsole$ConsoleOutputStream](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/debugging/MessageConsole.java) — nested/anonymous

#### com.strategyquant.lib.exception (2)

- [ISQException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/exception/ISQException.java)
- [SQException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/exception/SQException.java)

#### com.strategyquant.lib.historyData (6)

- [CdnUrlGenerator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/historyData/CdnUrlGenerator.java)
- [DataSources](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/historyData/DataSources.java)
- [HistoryDataChecker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/historyData/HistoryDataChecker.java)
- [HistoryDataConsts](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/historyData/HistoryDataConsts.java)
- [HistoryDataSubscription](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/historyData/HistoryDataSubscription.java)
- [ICryptable](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/historyData/ICryptable.java)

#### com.strategyquant.lib.hw (5)

- [HardwareInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/hw/HardwareInfo.java)
- [HardwareInfoLin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/hw/HardwareInfoLin.java)
- [HardwareInfoMac](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/hw/HardwareInfoMac.java)
- [HardwareInfoWin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/hw/HardwareInfoWin.java)
- [OperatingSystem](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/hw/OperatingSystem.java)

#### com.strategyquant.lib.jxbrowser (1)

- [JxBrowser](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/jxbrowser/JxBrowser.java)

#### com.strategyquant.lib.language (1)

- [LFileGen](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/language/LFileGen.java)

#### com.strategyquant.lib.memory (6)

- [CpuInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/memory/CpuInfo.java)
- [MemoryUsageChecker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/memory/MemoryUsageChecker.java)
- [MemoryUsageChecker$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/memory/MemoryUsageChecker.java) — nested/anonymous
- [OffHeapMemory](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/memory/OffHeapMemory.java)
- [OffHeapMemory$OffHeapObject](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/memory/OffHeapMemory.java) — nested/anonymous
- [SQMemoryProtectionError](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/memory/SQMemoryProtectionError.java)

#### com.strategyquant.lib.offheap (2)

- [IOffHeapCallback](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/offheap/IOffHeapCallback.java)
- [OffHeapStats](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/offheap/OffHeapStats.java)

#### com.strategyquant.lib.plugins.compile (1)

- [PluginCompiler](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/plugins/compile/PluginCompiler.java)

#### com.strategyquant.lib.pp (2)

- [MultiPartSender](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/pp/MultiPartSender.java)
- [ProjectPanel](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/pp/ProjectPanel.java)

#### com.strategyquant.lib.random (3)

- [MTRandom](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/random/MTRandom.java)
- [MersenneTwisterFast](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/random/MersenneTwisterFast.java)
- [MersenneTwisterRng](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/random/MersenneTwisterRng.java)

#### com.strategyquant.lib.report (3)

- [OpsgenieReporter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/report/OpsgenieReporter.java)
- [OpsgenieReporter$Priority](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/report/OpsgenieReporter.java) — nested/anonymous
- [OpsgenieReporter$Version](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/report/OpsgenieReporter.java) — nested/anonymous

#### com.strategyquant.lib.settings (3)

- [IXMLAble](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/settings/IXMLAble.java)
- [ParametrizationSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/settings/ParametrizationSettings.java)
- [ValuesMapKeys](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/settings/ValuesMapKeys.java)

#### com.strategyquant.lib.snippets (14)

- [CustomClasses](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/CustomClasses.java)
- [CustomClassesLoader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/CustomClassesLoader.java)
- [CustomClassesLoaderCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/CustomClassesLoaderCache.java)
- [CustomClassesLoaderException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/CustomClassesLoaderException.java)
- [CustomClassesReg](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/CustomClassesReg.java)
- [ICustomClasses](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/ICustomClasses.java)
- [NonexistingCustomClassException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/NonexistingCustomClassException.java)
- [ProtectedSnippets](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/ProtectedSnippets.java)
- [ProtectedSnippetsException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/ProtectedSnippetsException.java)
- [SnippetsCompiler](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/SnippetsCompiler.java)
- [SnippetsCompilerException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/SnippetsCompilerException.java)
- [SnippetsCompilerUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/SnippetsCompilerUtils.java)
- [SnippetsUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/SnippetsUtils.java)
- [SnippetsUtilsException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/SnippetsUtilsException.java)

#### com.strategyquant.lib.snippets.compile (14)

- [AutoImport](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/AutoImport.java)
- [CompilationConst](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/CompilationConst.java)
- [CompilationMessage](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/CompilationMessage.java)
- [CompilationResult](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/CompilationResult.java)
- [CompilationUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/CompilationUtils.java)
- [Compiler](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/Compiler.java)
- [CompilerBulk](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/CompilerBulk.java)
- [ICompilationListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/ICompilationListener.java)
- [MissingImport](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/MissingImport.java)
- [SQStructure](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/SQStructure.java)
- [SnippetsDb](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/SnippetsDb.java)
- [SnippetsHash](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/SnippetsHash.java)
- [SnippetsHashException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/SnippetsHashException.java)
- [SourceFile](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/SourceFile.java)

#### com.strategyquant.lib.snippets.compile.inMemory (1)

- [InMemoryJavaCompiler](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/inMemory/InMemoryJavaCompiler.java)

#### com.strategyquant.lib.snippets.compile.indicators (6)

- [IndicatorBase](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/indicators/IndicatorBase.java)
- [IndicatorParam](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/indicators/IndicatorParam.java)
- [IndicatorParser](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/indicators/IndicatorParser.java)
- [IndicatorParserException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/indicators/IndicatorParserException.java)
- [IndicatorsBuilder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/indicators/IndicatorsBuilder.java)
- [IndicatorsConst](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/indicators/IndicatorsConst.java)

#### com.strategyquant.lib.snippets.compile.jar (5)

- [CustomClassloaderJavaFileManagerJ10](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/jar/CustomClassloaderJavaFileManagerJ10.java)
- [CustomJavaFileObject](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/jar/CustomJavaFileObject.java)
- [JarCompiler](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/jar/JarCompiler.java)
- [JarCompiler$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/jar/JarCompiler.java) — nested/anonymous
- [SecuredClassLoder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/snippets/compile/jar/SecuredClassLoder.java)

#### com.strategyquant.lib.sourcecode (11)

- [CheckMacroExistsMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sourcecode/CheckMacroExistsMethod.java)
- [CodeGenerationException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sourcecode/CodeGenerationException.java)
- [ComparatorStringLength](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sourcecode/ComparatorStringLength.java)
- [ConditionsFixer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sourcecode/ConditionsFixer.java)
- [ConditionsFixerDirective](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sourcecode/ConditionsFixerDirective.java)
- [CustomBlocksAnalyzer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sourcecode/CustomBlocksAnalyzer.java)
- [ListFilesMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sourcecode/ListFilesMethod.java)
- [SourceCodeGenerator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sourcecode/SourceCodeGenerator.java)
- [SourceCodeGenerators](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sourcecode/SourceCodeGenerators.java)
- [VarAndIndex](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sourcecode/VarAndIndex.java)
- [XMLIndicatorsAnalyzer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sourcecode/XMLIndicatorsAnalyzer.java)

#### com.strategyquant.lib.sqxbusiness (8)

- [BuildData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sqxbusiness/BuildData.java)
- [EAOption](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sqxbusiness/EAOption.java)
- [MQLMarketBuildResult](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sqxbusiness/MQLMarketBuildResult.java)
- [MQLMarketBuildSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sqxbusiness/MQLMarketBuildSettings.java)
- [MQLMarketBuilder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sqxbusiness/MQLMarketBuilder.java)
- [MQLMarketConst](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sqxbusiness/MQLMarketConst.java)
- [MQLMarketLoggable](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sqxbusiness/MQLMarketLoggable.java)
- [SQXBusinessMainSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/sqxbusiness/SQXBusinessMainSettings.java)

#### com.strategyquant.lib.tempfiles (2)

- [TempFilesManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/tempfiles/TempFilesManager.java)
- [TempFilesManager$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/tempfiles/TempFilesManager.java) — nested/anonymous

#### com.strategyquant.lib.time (3)

- [DateFormats](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/time/DateFormats.java)
- [DateTimeParser](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/time/DateTimeParser.java)
- [SQTimeOld](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/time/SQTimeOld.java)

#### com.strategyquant.lib.updates (1)

- [SQUpdaterRunner](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/updates/SQUpdaterRunner.java)

#### com.strategyquant.lib.utils (32)

- [ComponentResizer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/ComponentResizer.java)
- [DirectoryHash](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/DirectoryHash.java)
- [DirectoryHash$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/DirectoryHash.java) — nested/anonymous
- [EmailSender](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/EmailSender.java)
- [FileLoader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/FileLoader.java)
- [FullData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/FullData.java)
- [GCChecker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/GCChecker.java)
- [IProgressListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/IProgressListener.java)
- [ISQCloneable](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/ISQCloneable.java)
- [IUniqueNameChecker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/IUniqueNameChecker.java)
- [JsonCreator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/JsonCreator.java)
- [LimitedList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/LimitedList.java)
- [OSUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/OSUtils.java)
- [Pair](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/Pair.java)
- [SQFileChooserFactory](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/SQFileChooserFactory.java)
- [SQFileChooserFactory$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/SQFileChooserFactory.java) — nested/anonymous
- [SQFileChooserFactory$ISQFileChooser](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/SQFileChooserFactory.java) — nested/anonymous
- [SQFileChooserFactory$JFileChooserPersisterImpl](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/SQFileChooserFactory.java) — nested/anonymous
- [SQFileChooserFactory$JFileChooserPersisterImpl$OnChooserClosing](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/SQFileChooserFactory.java) — nested/anonymous
- [SQFileChooserFactory$JFileChooserPersisterImpl$OnViewTypeChanged](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/SQFileChooserFactory.java) — nested/anonymous
- [SQFileChooserFactory$JFileChooserPersisterImpl$SortOrderInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/SQFileChooserFactory.java) — nested/anonymous
- [SQFileChooserFactory$JFileChooserPersisterImpl$SortOrderInfo$ColumnSortInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/SQFileChooserFactory.java) — nested/anonymous
- [SQUUID](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/SQUUID.java)
- [StringComparator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/StringComparator.java)
- [StringOutputStream](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/StringOutputStream.java)
- [SwingUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/SwingUtils.java)
- [TimeLocalObjects](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/TimeLocalObjects.java)
- [UnremovableArrayList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/UnremovableArrayList.java)
- [UnremovableArrayList$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/UnremovableArrayList.java) — nested/anonymous
- [Unzipper](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/Unzipper.java)
- [WizardConfigWorker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/WizardConfigWorker.java)
- [Zipper](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/Zipper.java)

#### com.strategyquant.lib.utils.mousehook (4)

- [IMouseHookListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/mousehook/IMouseHookListener.java)
- [MouseHook](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/mousehook/MouseHook.java)
- [MouseHook$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/mousehook/MouseHook.java) — nested/anonymous
- [MouseHookAdapter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/mousehook/MouseHookAdapter.java)

#### com.strategyquant.lib.utils.network (5)

- [DataDownloader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/network/DataDownloader.java)
- [HttpUtil](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/network/HttpUtil.java)
- [HttpUtil$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/network/HttpUtil.java) — nested/anonymous
- [IDataDownloader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/network/IDataDownloader.java)
- [IHttpRequestListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/utils/network/IHttpRequestListener.java)

#### com.strategyquant.lib.volumeProfile (2)

- [VolumeProfileBlocks](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/volumeProfile/VolumeProfileBlocks.java)
- [VolumeProfileSubscription](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/volumeProfile/VolumeProfileSubscription.java)

#### com.strategyquant.lib.whitelabel (2)

- [AbstractBroker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/whitelabel/AbstractBroker.java)
- [Brokers](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/whitelabel/Brokers.java)

#### com.strategyquant.lib.whitelabel.broker (2)

- [BlackwellBroker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/whitelabel/broker/BlackwellBroker.java)
- [RoboForexBroker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/whitelabel/broker/RoboForexBroker.java)

#### com.strategyquant.model (1)

- [IdName](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/model/IdName.java)

#### com.strategyquant.qdm (3)

- [QDM](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/qdm/QDM.java)
- [QDMDb](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/qdm/QDMDb.java)
- [QDMStats](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/qdm/QDMStats.java)

#### com.strategyquant.qdm.activity (2)

- [QDMActivity](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/qdm/activity/QDMActivity.java)
- [QDMActivityTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/qdm/activity/QDMActivityTypes.java)

#### com.strategyquant.qdm.banners (4)

- [Banner](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/qdm/banners/Banner.java)
- [BannerStats](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/qdm/banners/BannerStats.java)
- [BannerTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/qdm/banners/BannerTypes.java)
- [Banners](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/qdm/banners/Banners.java)

#### com.strategyquant.qdm.symbols (2)

- [SymbolStats](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/qdm/symbols/SymbolStats.java)
- [SymbolsStats](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/qdm/symbols/SymbolsStats.java)

#### com.strategyquant.security (2)

- [IDataProtector](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/security/IDataProtector.java)
- [SQDataProtector](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/lib/security/SQDataProtector.java)

### SQTradingLib

- Direct source folder: `DONOR_REFERENCE_ROOT/internal/libs/tradinglib`
- Historical archive SHA-256: `9796578273f36ced388b977bf08ff67c149a8897805b0bce00f7b8d3de6241f3`
- Compiled entries: **945**; entries without `$`: **844**; nested/anonymous entries: **101**.
- Available Java source files: **844**.
- Signatures: [API dump](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/signatures/SQTradingLib_signatures.txt)

#### com.strategyquant.indicatorTester (12)

- [CalibrationConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicatorTester/CalibrationConfig.java)
- [CalibrationData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicatorTester/CalibrationData.java)
- [CalibrationInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicatorTester/CalibrationInfo.java)
- [CalibrationRangesInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicatorTester/CalibrationRangesInfo.java)
- [IndicatorCalibrator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicatorTester/IndicatorCalibrator.java)
- [IndicatorInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicatorTester/IndicatorInfo.java)
- [IndicatorParameters](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicatorTester/IndicatorParameters.java)
- [IndicatorTestException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicatorTester/IndicatorTestException.java)
- [IndicatorTester](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicatorTester/IndicatorTester.java)
- [IndicatorTesterConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicatorTester/IndicatorTesterConfig.java)
- [IndicatorsLoader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicatorTester/IndicatorsLoader.java)
- [IndyParameter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicatorTester/IndyParameter.java)

#### com.strategyquant.tradinglib (144)

- [ATM](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ATM.java)
- [ATMExit](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ATMExit.java)
- [AbstractChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/AbstractChart.java)
- [Activator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Activator.java)
- [BadStrategyException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/BadStrategyException.java)
- [BarChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/BarChart.java)
- [BarChart$CategoryValue](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/BarChart.java) — nested/anonymous
- [Benchmark](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Benchmark.java)
- [BenchmarkResult](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/BenchmarkResult.java)
- [BlockDefinitionException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/BlockDefinitionException.java)
- [BlockSuperTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/BlockSuperTypes.java)
- [Blocks](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Blocks.java)
- [Buffer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Buffer.java)
- [BuildingBlock](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/BuildingBlock.java)
- [CategoryOrder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/CategoryOrder.java)
- [ChartData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ChartData.java)
- [ChartSetup](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ChartSetup.java)
- [ChartsConst](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ChartsConst.java)
- [Checker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Checker.java)
- [ClassConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ClassConfig.java)
- [Colors](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Colors.java)
- [CommissionsMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/CommissionsMethod.java)
- [CorrelationLib](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/CorrelationLib.java)
- [CorrelationType](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/CorrelationType.java)
- [CustomAnalysisMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/CustomAnalysisMethod.java)
- [CustomCellFormat](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/CustomCellFormat.java)
- [Databank](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Databank.java)
- [Databank$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Databank.java) — nested/anonymous
- [Databank$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Databank.java) — nested/anonymous
- [Databank$3](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Databank.java) — nested/anonymous
- [DatabankColumn](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/DatabankColumn.java)
- [DatabankColumn$Color](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/DatabankColumn.java) — nested/anonymous
- [DatabankFitness](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/DatabankFitness.java)
- [DatabankSyncTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/DatabankSyncTypes.java)
- [Description](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Description.java)
- [Directions](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Directions.java)
- [Editor](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Editor.java)
- [Editors](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Editors.java)
- [EngineChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/EngineChart.java)
- [ExitMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ExitMethod.java)
- [ExitType](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ExitType.java)
- [ExitTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ExitTypes.java)
- [FitnessCollection](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/FitnessCollection.java)
- [ForEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ForEngine.java)
- [Formula](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Formula.java)
- [GCTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/GCTypes.java)
- [GeneticInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/GeneticInfo.java)
- [Help](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Help.java)
- [IActionEventListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/IActionEventListener.java)
- [IBlock](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/IBlock.java)
- [IFitnessValue](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/IFitnessValue.java)
- [IFormula](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/IFormula.java)
- [ILiveOrder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ILiveOrder.java)
- [IParametersHelperModifier](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/IParametersHelperModifier.java)
- [IgnoreInBuilder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/IgnoreInBuilder.java)
- [Indicator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Indicator.java)
- [MT5ExtendedTemplate](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/MT5ExtendedTemplate.java)
- [MemoryCleaner](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/MemoryCleaner.java)
- [MemoryCleaner$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/MemoryCleaner.java) — nested/anonymous
- [MemoryCleaner$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/MemoryCleaner.java) — nested/anonymous
- [MoneyManagementMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/MoneyManagementMethod.java)
- [MonteCarloManipulation](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/MonteCarloManipulation.java)
- [MonteCarloRetest](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/MonteCarloRetest.java)
- [MonteCarloTestTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/MonteCarloTestTypes.java)
- [Negater](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Negater.java)
- [NegatersList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/NegatersList.java)
- [NoShift](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/NoShift.java)
- [NotFirstValue](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/NotFirstValue.java)
- [NotSupportedFor](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/NotSupportedFor.java)
- [OSUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/OSUtils.java)
- [OSUtils$Kernel32](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/OSUtils.java) — nested/anonymous
- [OSUtils$User32](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/OSUtils.java) — nested/anonymous
- [OppositeBlock](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/OppositeBlock.java)
- [Order](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Order.java)
- [OrderCloseTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/OrderCloseTypes.java)
- [OrderStatuses](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/OrderStatuses.java)
- [OrderTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/OrderTypes.java)
- [OrdersList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/OrdersList.java)
- [Output](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Output.java)
- [OverviewTemplate](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/OverviewTemplate.java)
- [Parameter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Parameter.java)
- [ParameterSet](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ParameterSet.java)
- [ParametersHelper](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ParametersHelper.java)
- [ParametersHelper$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ParametersHelper.java) — nested/anonymous
- [ParametrizationTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ParametrizationTypes.java)
- [PieChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/PieChart.java)
- [PieChart$Section](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/PieChart.java) — nested/anonymous
- [PlTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/PlTypes.java)
- [PortfolioInitialBalanceTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/PortfolioInitialBalanceTypes.java)
- [PrecachedRequest](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/PrecachedRequest.java)
- [ProjectRunInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ProjectRunInfo.java)
- [ReportGenerator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ReportGenerator.java)
- [ReportGenerator$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ReportGenerator.java) — nested/anonymous
- [Required](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Required.java)
- [Result](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Result.java)
- [ResultTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ResultTypes.java)
- [ResultsGroup](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ResultsGroup.java)
- [ResultsGroup$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ResultsGroup.java) — nested/anonymous
- [ResultsGroup$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ResultsGroup.java) — nested/anonymous
- [ReturnTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ReturnTypes.java)
- [RiskManagementMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/RiskManagementMethod.java)
- [SLPTValue](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/SLPTValue.java)
- [SLPTValues](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/SLPTValues.java)
- [SQStats](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/SQStats.java)
- [SampleTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/SampleTypes.java)
- [ScalingMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ScalingMethod.java)
- [ScatterChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ScatterChart.java)
- [SettingsKeys](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/SettingsKeys.java)
- [SortOrder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/SortOrder.java)
- [StatsDontExistException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/StatsDontExistException.java)
- [StatsKey](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/StatsKey.java)
- [StatsTypeCombination](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/StatsTypeCombination.java)
- [StrategiesActionCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/StrategiesActionCache.java)
- [StrategyBase](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/StrategyBase.java)
- [SwapMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/SwapMethod.java)
- [SwapTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/SwapTypes.java)
- [TimeDuration](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TimeDuration.java)
- [TimeDurationDay](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TimeDurationDay.java)
- [TimeDurationHour](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TimeDurationHour.java)
- [TimeDurationMin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TimeDurationMin.java)
- [TimeDurationOther](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TimeDurationOther.java)
- [TimeSeries](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TimeSeries.java)
- [TimeSeriesAreaChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TimeSeriesAreaChart.java)
- [TimeSeriesLineChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TimeSeriesLineChart.java)
- [TimeSeriesScatterChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TimeSeriesScatterChart.java)
- [TradeAnalysisChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TradeAnalysisChart.java)
- [TradeSizeSmallerThanOneException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TradeSizeSmallerThanOneException.java)
- [TradelistColumn](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TradelistColumn.java)
- [Trader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Trader.java)
- [TradingOption](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TradingOption.java)
- [TradingUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TradingUtils.java)
- [TripleSwapOptions](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/TripleSwapOptions.java)
- [ValueTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/ValueTypes.java)
- [Variable](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Variable.java)
- [Variable$AttachedField](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Variable.java) — nested/anonymous
- [Variables](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Variables.java)
- [Variables$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/Variables.java) — nested/anonymous
- [WalkForwardColumn](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/WalkForwardColumn.java)
- [WalkForwardPeriod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/WalkForwardPeriod.java)
- [WalkForwardResult](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/WalkForwardResult.java)
- [WhatIf](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/WhatIf.java)
- [XYAreaChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/XYAreaChart.java)
- [XYLineChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/XYLineChart.java)
- [package-info](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/package-info.java) — package metadata

#### com.strategyquant.tradinglib.applyMassConfig (1)

- [ApplyMassConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/applyMassConfig/ApplyMassConfig.java)

#### com.strategyquant.tradinglib.atm (5)

- [ATMConfigVerifier](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/ATMConfigVerifier.java)
- [ATMGenerateConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/ATMGenerateConfig.java)
- [ATMMoveSL2BE](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/ATMMoveSL2BE.java)
- [ATMMoveSL2BETypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/ATMMoveSL2BETypes.java)
- [ATMTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/ATMTypes.java)

#### com.strategyquant.tradinglib.atm.exits (9)

- [ATMExitLevels](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/exits/ATMExitLevels.java)
- [AbstractExitLevel](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/exits/AbstractExitLevel.java)
- [FixedProfit](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/exits/FixedProfit.java)
- [MultipleOfOriginalPT](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/exits/MultipleOfOriginalPT.java)
- [MultipleOfOriginalSL](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/exits/MultipleOfOriginalSL.java)
- [None](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/exits/None.java)
- [None$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/exits/None.java) — nested/anonymous
- [TrailingStop](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/exits/TrailingStop.java)
- [TrailingStop$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/exits/TrailingStop.java) — nested/anonymous

#### com.strategyquant.tradinglib.atm.exits.helpers (1)

- [TrailingFormula](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/exits/helpers/TrailingFormula.java)

#### com.strategyquant.tradinglib.atm.sizes (5)

- [ATMSizes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/sizes/ATMSizes.java)
- [AbstractATMPositionSize](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/sizes/AbstractATMPositionSize.java)
- [SizeAllRemaining](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/sizes/SizeAllRemaining.java)
- [SizeFixedLots](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/sizes/SizeFixedLots.java)
- [SizePercents](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/atm/sizes/SizePercents.java)

#### com.strategyquant.tradinglib.backtest (38)

- [AWProgressEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/AWProgressEngine.java)
- [AutoRetestSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/AutoRetestSettings.java)
- [AutoRetestSettings$Subchart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/AutoRetestSettings.java) — nested/anonymous
- [AutoRetestStrategyConfigModifier](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/AutoRetestStrategyConfigModifier.java)
- [BacktestConnection](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/BacktestConnection.java)
- [BacktestDataCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/BacktestDataCache.java)
- [BacktestDataFeed](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/BacktestDataFeed.java)
- [BacktestDataFeedElement](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/BacktestDataFeedElement.java)
- [BacktestDataInitializer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/BacktestDataInitializer.java)
- [BacktestDataType](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/BacktestDataType.java)
- [BacktestInitStrategy](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/BacktestInitStrategy.java)
- [BacktestModes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/BacktestModes.java)
- [BacktestRealDataStartTimeComputer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/BacktestRealDataStartTimeComputer.java)
- [BacktestTradingSetupRunnable](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/BacktestTradingSetupRunnable.java)
- [DataLoadStats](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/DataLoadStats.java)
- [FeedDataCreator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/FeedDataCreator.java)
- [HashPair](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/HashPair.java)
- [IBacktester](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/IBacktester.java)
- [IDataReadyListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/IDataReadyListener.java)
- [IFeedDataSaver](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/IFeedDataSaver.java)
- [ILoadedDataHolder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/ILoadedDataHolder.java)
- [LoadDataProgressEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/LoadDataProgressEngine.java)
- [LoadedData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/LoadedData.java)
- [LoadedDataHolderArray](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/LoadedDataHolderArray.java)
- [LoadedDataHolderArray2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/LoadedDataHolderArray2.java)
- [LoadedDataHolderFileBDF](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/LoadedDataHolderFileBDF.java)
- [LoadedDataHolderFilePlain](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/LoadedDataHolderFilePlain.java)
- [LoadedDataHolderOffheap](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/LoadedDataHolderOffheap.java)
- [LoadedDataHolderOffheap$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/LoadedDataHolderOffheap.java) — nested/anonymous
- [ResultsPanelData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/ResultsPanelData.java)
- [SQBacktester](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/SQBacktester.java)
- [SQBacktester$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/SQBacktester.java) — nested/anonymous
- [SQBacktester$JobLastEventListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/SQBacktester.java) — nested/anonymous
- [SQBacktesterJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/SQBacktesterJob.java)
- [SQBacktesterJob$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/SQBacktesterJob.java) — nested/anonymous
- [StartDataInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/StartDataInfo.java)
- [TestfilesUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/TestfilesUtils.java)
- [TradingOptionsModifier](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtest/TradingOptionsModifier.java)

#### com.strategyquant.tradinglib.backtestrunner (10)

- [BacktestResult](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtestrunner/BacktestResult.java)
- [BacktestRunner](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtestrunner/BacktestRunner.java)
- [BacktestRunner$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtestrunner/BacktestRunner.java) — nested/anonymous
- [BacktestRunner$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtestrunner/BacktestRunner.java) — nested/anonymous
- [BacktestRunner$3](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtestrunner/BacktestRunner.java) — nested/anonymous
- [BacktestSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtestrunner/BacktestSettings.java)
- [DurationStats](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtestrunner/DurationStats.java)
- [IBacktestProgressListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtestrunner/IBacktestProgressListener.java)
- [PopulationTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtestrunner/PopulationTypes.java)
- [StrategyChecker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/backtestrunner/StrategyChecker.java)

#### com.strategyquant.tradinglib.benchmark (6)

- [BenchmarkEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/benchmark/BenchmarkEngine.java)
- [BenchmarkEngine$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/benchmark/BenchmarkEngine.java) — nested/anonymous
- [BenchmarkJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/benchmark/BenchmarkJob.java)
- [BenchmarkJob2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/benchmark/BenchmarkJob2.java)
- [BenchmarkProgressEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/benchmark/BenchmarkProgressEngine.java)
- [BenchmarkResult](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/benchmark/BenchmarkResult.java)

#### com.strategyquant.tradinglib.blocks (12)

- [AnnotationHandler](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/AnnotationHandler.java)
- [AnnotationProcessor](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/AnnotationProcessor.java)
- [BlockCategoryInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/BlockCategoryInfo.java)
- [BlockComparatorByOrder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/BlockComparatorByOrder.java)
- [BlocksConfigGenerator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/BlocksConfigGenerator.java)
- [CategoryComparatorByOrder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/CategoryComparatorByOrder.java)
- [Colors](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/Colors.java)
- [CustomBlocks](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/CustomBlocks.java)
- [OppositeBlocksConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/OppositeBlocksConfig.java)
- [OutputAnnotationHandler](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/OutputAnnotationHandler.java)
- [ParameterAnnotationGenerator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/ParameterAnnotationGenerator.java)
- [ParameterAnnotationParser](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/ParameterAnnotationParser.java)

#### com.strategyquant.tradinglib.blocks.annotations (3)

- [DataSeriesChoice](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/annotations/DataSeriesChoice.java)
- [ParameterSets](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/annotations/ParameterSets.java)
- [Value](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/annotations/Value.java)

#### com.strategyquant.tradinglib.blocks.random (16)

- [BlockDefinition](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/BlockDefinition.java)
- [BlockParameter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/BlockParameter.java)
- [BlocksConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/BlocksConfig.java)
- [FormulaValue](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/FormulaValue.java)
- [ItemRandomValueRanges](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/ItemRandomValueRanges.java)
- [RandomPlaceholder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/RandomPlaceholder.java)
- [RandomValueConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/RandomValueConfig.java)
- [ReplacementBlock](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/ReplacementBlock.java)
- [ReplacementBlocks](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/ReplacementBlocks.java)
- [ReplacementChartConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/ReplacementChartConfig.java)
- [ReplacementChartsConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/ReplacementChartsConfig.java)
- [ReplacementConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/ReplacementConfig.java)
- [ReplacementParameter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/ReplacementParameter.java)
- [ReplacementParameterGroups](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/ReplacementParameterGroups.java)
- [ReplacementParameters](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/ReplacementParameters.java)
- [ReplacementsConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/blocks/random/ReplacementsConfig.java)

#### com.strategyquant.tradinglib.build (3)

- [BuildFinishedReason](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/build/BuildFinishedReason.java)
- [BuildTemplate](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/build/BuildTemplate.java)
- [BuildTemplatesManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/build/BuildTemplatesManager.java)

#### com.strategyquant.tradinglib.charts (1)

- [AbstractXYChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/charts/AbstractXYChart.java)

#### com.strategyquant.tradinglib.charts.linechart.series (4)

- [AbstractSeries](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/charts/linechart/series/AbstractSeries.java)
- [AbstractSeries$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/charts/linechart/series/AbstractSeries.java) — nested/anonymous
- [XYSeries](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/charts/linechart/series/XYSeries.java)
- [XYValue](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/charts/linechart/series/XYValue.java)

#### com.strategyquant.tradinglib.commissions (1)

- [CommissionsMethodsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/commissions/CommissionsMethodsList.java)

#### com.strategyquant.tradinglib.conditions (9)

- [ColumnConditionValue](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/conditions/ColumnConditionValue.java)
- [Condition](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/conditions/Condition.java)
- [ConditionValueTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/conditions/ConditionValueTypes.java)
- [Conditions](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/conditions/Conditions.java)
- [ConditionsChecker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/conditions/ConditionsChecker.java)
- [ConditionsTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/conditions/ConditionsTypes.java)
- [DismissStruct](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/conditions/DismissStruct.java)
- [IConditionValue](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/conditions/IConditionValue.java)
- [NumericValue](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/conditions/NumericValue.java)

#### com.strategyquant.tradinglib.connection (7)

- [Connection](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/connection/Connection.java)
- [ConnectionManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/connection/ConnectionManager.java)
- [ConnectionPluginManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/connection/ConnectionPluginManager.java)
- [ConnectionsFileManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/connection/ConnectionsFileManager.java)
- [HistoryData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/connection/HistoryData.java)
- [IConnectionListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/connection/IConnectionListener.java)
- [IDataFeed](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/connection/IDataFeed.java)

#### com.strategyquant.tradinglib.correlation (7)

- [CorrelationComputer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/correlation/CorrelationComputer.java)
- [CorrelationPeriodTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/correlation/CorrelationPeriodTypes.java)
- [CorrelationPeriods](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/correlation/CorrelationPeriods.java)
- [CorrelationSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/correlation/CorrelationSettings.java)
- [CorrelationTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/correlation/CorrelationTypes.java)
- [FitPortfolio](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/correlation/FitPortfolio.java)
- [package-info](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/correlation/package-info.java) — package metadata

#### com.strategyquant.tradinglib.crosscheck (12)

- [CrossCheckComparator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crosscheck/CrossCheckComparator.java)
- [CrossCheckConditionValue](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crosscheck/CrossCheckConditionValue.java)
- [CrossCheckDataNotExistException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crosscheck/CrossCheckDataNotExistException.java)
- [CrossCheckMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crosscheck/CrossCheckMethod.java)
- [CrossCheckRunner](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java)
- [CrossCheckTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crosscheck/CrossCheckTypes.java)
- [ICrossCheck](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crosscheck/ICrossCheck.java)
- [MCResultsComputer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crosscheck/MCResultsComputer.java)
- [MonteCarloCrossCheckMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crosscheck/MonteCarloCrossCheckMethod.java)
- [WalkForwardCrossCheckMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crosscheck/WalkForwardCrossCheckMethod.java)
- [WalkForwardCrossCheckMethod$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crosscheck/WalkForwardCrossCheckMethod.java) — nested/anonymous
- [WalkForwardCrossCheckMethod$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crosscheck/WalkForwardCrossCheckMethod.java) — nested/anonymous

#### com.strategyquant.tradinglib.crypto (1)

- [CryptoDownloadJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/crypto/CryptoDownloadJob.java)

#### com.strategyquant.tradinglib.customanalysis (2)

- [CustomAnalysisInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/customanalysis/CustomAnalysisInfo.java)
- [CustomAnalysisMethodsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/customanalysis/CustomAnalysisMethodsList.java)

#### com.strategyquant.tradinglib.dailyEquity (1)

- [DailyEquity](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dailyEquity/DailyEquity.java)

#### com.strategyquant.tradinglib.darwinex (5)

- [DarwinexDownloadJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/darwinex/DarwinexDownloadJob.java)
- [DarwinexDownloadJob$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/darwinex/DarwinexDownloadJob.java) — nested/anonymous
- [DarwinexImportManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/darwinex/DarwinexImportManager.java)
- [DarwinexImportManager$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/darwinex/DarwinexImportManager.java) — nested/anonymous
- [DarwinexImportManager$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/darwinex/DarwinexImportManager.java) — nested/anonymous

#### com.strategyquant.tradinglib.data (6)

- [AppDataImporter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/AppDataImporter.java)
- [AppDataImporter$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/AppDataImporter.java) — nested/anonymous
- [CustomDataIndyCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/CustomDataIndyCache.java)
- [CustomDataIndyMap](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/CustomDataIndyMap.java)
- [DataRanges](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/DataRanges.java)
- [TradingData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/TradingData.java)

#### com.strategyquant.tradinglib.data.download (7)

- [DownloadDispatcher](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/download/DownloadDispatcher.java)
- [DownloadDispatcher$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/download/DownloadDispatcher.java) — nested/anonymous
- [DownloadDispatcher$Details](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/download/DownloadDispatcher.java) — nested/anonymous
- [IDownloadDispatcher](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/download/IDownloadDispatcher.java)
- [NotDownloadableDataException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/download/NotDownloadableDataException.java)
- [Queue](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/download/Queue.java)
- [SpeedEvaluator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/data/download/SpeedEvaluator.java)

#### com.strategyquant.tradinglib.databank (23)

- [AbstractDatabankFilter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/AbstractDatabankFilter.java)
- [AbstractDatabankFilter$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/AbstractDatabankFilter.java) — nested/anonymous
- [DatabankButton](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/DatabankButton.java)
- [DatabankButton$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/DatabankButton.java) — nested/anonymous
- [DatabankChange](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/DatabankChange.java)
- [DatabankColumnTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/DatabankColumnTypes.java)
- [DatabankColumns](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/DatabankColumns.java)
- [DatabankExport](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/DatabankExport.java)
- [DatabankRecords](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/DatabankRecords.java)
- [DatabankTableColumnEntry](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/DatabankTableColumnEntry.java)
- [DatabankTableView](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/DatabankTableView.java)
- [DatabankViewsManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/DatabankViewsManager.java)
- [DefaultDatabankFilter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/DefaultDatabankFilter.java)
- [IDatabankFilter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/IDatabankFilter.java)
- [IDatabankListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/IDatabankListener.java)
- [IProgressListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/IProgressListener.java)
- [ImproveDatabankFilter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/ImproveDatabankFilter.java)
- [OptimizeDatabankFilter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/OptimizeDatabankFilter.java)
- [RecentColumns](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/RecentColumns.java)
- [RecordNotFoundException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/RecordNotFoundException.java)
- [ResultsComparator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/ResultsComparator.java)
- [SortValuesComparator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/SortValuesComparator.java)
- [TopStrategiesData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/databank/TopStrategiesData.java)

#### com.strategyquant.tradinglib.debug (2)

- [DebugConsole](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/debug/DebugConsole.java)
- [Debugger](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/debug/Debugger.java)

#### com.strategyquant.tradinglib.dukascopy (12)

- [CdnCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/CdnCache.java)
- [CdnCache$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/CdnCache.java) — nested/anonymous
- [CdnDownloadJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/CdnDownloadJob.java)
- [CdnInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/CdnInfo.java)
- [CdnInfo$SymbolInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/CdnInfo.java) — nested/anonymous
- [DownloadResultDto](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/DownloadResultDto.java)
- [DukasImportManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/DukasImportManager.java)
- [DukasImportManager$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/DukasImportManager.java) — nested/anonymous
- [DukasImportManager$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/DukasImportManager.java) — nested/anonymous
- [DukascopyBinaryMerger](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/DukascopyBinaryMerger.java)
- [DukascopyUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/DukascopyUtils.java)
- [ImportInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/ImportInfo.java)

#### com.strategyquant.tradinglib.dukascopy.job (4)

- [DownloadDukascopySymbolJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/job/DownloadDukascopySymbolJob.java)
- [DownloadDukascopySymbolJob$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/job/DownloadDukascopySymbolJob.java) — nested/anonymous
- [DownloadRateCorrector](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/job/DownloadRateCorrector.java)
- [DownloadWithFlexibileSpeedJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/dukascopy/job/DownloadWithFlexibileSpeedJob.java)

#### com.strategyquant.tradinglib.engine (7)

- [AbstractBacktestEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/AbstractBacktestEngine.java)
- [BacktestEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/BacktestEngine.java)
- [BacktestTradingSetup](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/BacktestTradingSetup.java)
- [ChartSetups](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/ChartSetups.java)
- [TradingEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/TradingEngine.java)
- [TradingSetup](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/TradingSetup.java)
- [TradingSetupStatus](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/TradingSetupStatus.java)

#### com.strategyquant.tradinglib.engine.stockpicker (6)

- [PortfolioTrader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/PortfolioTrader.java)
- [StockBroker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/StockBroker.java)
- [Stockpicker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/Stockpicker.java)
- [StockpickerBacktestEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/StockpickerBacktestEngine.java)
- [StockpickerBacktestEngine$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/StockpickerBacktestEngine.java) — nested/anonymous
- [StockpickerBacktestEngine$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/StockpickerBacktestEngine.java) — nested/anonymous

#### com.strategyquant.tradinglib.engine.stockpicker.backtester (4)

- [BacktestData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/backtester/BacktestData.java)
- [PortfolioBacktestJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/backtester/PortfolioBacktestJob.java)
- [PortfolioBacktestJobResult](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/backtester/PortfolioBacktestJobResult.java)
- [PortfolioBacktester](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/backtester/PortfolioBacktester.java)

#### com.strategyquant.tradinglib.engine.stockpicker.backtester.log (1)

- [StockpickerLog](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/backtester/log/StockpickerLog.java)

#### com.strategyquant.tradinglib.engine.stockpicker.constants (2)

- [PickerEodTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/constants/PickerEodTypes.java)
- [PickerTriggerTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/constants/PickerTriggerTypes.java)

#### com.strategyquant.tradinglib.engine.stockpicker.data (8)

- [BarData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/BarData.java)
- [LoadedPickerData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/LoadedPickerData.java)
- [PickerDataCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/PickerDataCache.java)
- [PickerDataLoader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/PickerDataLoader.java)
- [PickerDataModifier](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/PickerDataModifier.java)
- [PickerDataPreloader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/PickerDataPreloader.java)
- [PickerDataPreloader$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/PickerDataPreloader.java) — nested/anonymous
- [PickerDataPreloaderJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/PickerDataPreloaderJob.java)

#### com.strategyquant.tradinglib.engine.stockpicker.data.additional (4)

- [AdditionalDataCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/additional/AdditionalDataCache.java)
- [AdditionalDataFile](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/additional/AdditionalDataFile.java)
- [AdditionalDataLoader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/additional/AdditionalDataLoader.java)
- [LoadedAdditionalData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/additional/LoadedAdditionalData.java)

#### com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups (6)

- [LoadedStockGroupData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/stockGroups/LoadedStockGroupData.java)
- [StockGroupDataFile](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/stockGroups/StockGroupDataFile.java)
- [StockGroupDataLoaderJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/stockGroups/StockGroupDataLoaderJob.java)
- [StockGroupsDataCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/stockGroups/StockGroupsDataCache.java)
- [StockGroupsDataLoader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/stockGroups/StockGroupsDataLoader.java)
- [StockGroupsDataLoader$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/stockGroups/StockGroupsDataLoader.java) — nested/anonymous

#### com.strategyquant.tradinglib.engine.stockpicker.data.symbols (3)

- [LoadedSymbolData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/symbols/LoadedSymbolData.java)
- [SymbolDataLoader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/symbols/SymbolDataLoader.java)
- [SymbolsDataCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/symbols/SymbolsDataCache.java)

#### com.strategyquant.tradinglib.engine.stockpicker.data.timeline (4)

- [DefaultTimeline](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/timeline/DefaultTimeline.java)
- [PickerDataTimeline](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/timeline/PickerDataTimeline.java)
- [PickerDataTimeline$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/timeline/PickerDataTimeline.java) — nested/anonymous
- [TimelineCalcJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/timeline/TimelineCalcJob.java)

#### com.strategyquant.tradinglib.engine.stockpicker.data.utils (1)

- [PickerDataUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/data/utils/PickerDataUtils.java)

#### com.strategyquant.tradinglib.engine.stockpicker.signals (2)

- [CollectedSignals](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/signals/CollectedSignals.java)
- [Signals](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/signals/Signals.java)

#### com.strategyquant.tradinglib.engine.stockpicker.signals.entry (3)

- [PickerEntrySignal](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/signals/entry/PickerEntrySignal.java)
- [PickerEntrySignalComparatorByRevScore](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/signals/entry/PickerEntrySignalComparatorByRevScore.java)
- [PickerEntrySignals](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/signals/entry/PickerEntrySignals.java)

#### com.strategyquant.tradinglib.engine.stockpicker.signals.exit (2)

- [PickerExitSignal](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/signals/exit/PickerExitSignal.java)
- [PickerExitSignals](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/engine/stockpicker/signals/exit/PickerExitSignals.java)

#### com.strategyquant.tradinglib.enginecharts (1)

- [EngineChartsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/enginecharts/EngineChartsList.java)

#### com.strategyquant.tradinglib.equitychart (25)

- [AreaFill](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/AreaFill.java)
- [BenchmarkTable](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/BenchmarkTable.java)
- [ChartDataset](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/ChartDataset.java)
- [ChartOptimalizer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/ChartOptimalizer.java)
- [ChartOptimalizer$OptimizerResult](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/ChartOptimalizer.java) — nested/anonymous
- [ChartOptimalizer$PixelGroup](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/ChartOptimalizer.java) — nested/anonymous
- [DomainAxisType](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/DomainAxisType.java)
- [Equity](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/Equity.java)
- [EquityChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/EquityChart.java)
- [EquityChartUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/EquityChartUtils.java)
- [MainChartDataset](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/MainChartDataset.java)
- [Marker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/Marker.java)
- [MaxNewHighDuration](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/MaxNewHighDuration.java)
- [Periods](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/Periods.java)
- [Points](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/Points.java)
- [SampleMarkers](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/SampleMarkers.java)
- [Stagnation](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/Stagnation.java)
- [SubChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/SubChart.java)
- [SubChartDataset](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/SubChartDataset.java)
- [Text](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/Text.java)
- [TrendLines](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/TrendLines.java)
- [WalkForward](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/WalkForward.java)
- [XYValues](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/XYValues.java)
- [YearMarkers](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/YearMarkers.java)
- [Zoom](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychart/Zoom.java)

#### com.strategyquant.tradinglib.equitychartnew.addons (1)

- [IEquityChartAddon](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/equitychartnew/addons/IEquityChartAddon.java)

#### com.strategyquant.tradinglib.event (5)

- [ITradingEvent](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/event/ITradingEvent.java)
- [ITradingEventListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/event/ITradingEventListener.java)
- [TradingEventObj](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/event/TradingEventObj.java)
- [TradingEventTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/event/TradingEventTypes.java)
- [TradingEventsArray](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/event/TradingEventsArray.java)

#### com.strategyquant.tradinglib.exception (4)

- [BacktestException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/exception/BacktestException.java)
- [StrategyProblem](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/exception/StrategyProblem.java)
- [StrategyStoppedException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/exception/StrategyStoppedException.java)
- [TaskErrorInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/exception/TaskErrorInfo.java)

#### com.strategyquant.tradinglib.exchange (4)

- [CryptoDownloadException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/exchange/CryptoDownloadException.java)
- [Exchange](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/exchange/Exchange.java)
- [IExchange](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/exchange/IExchange.java)
- [SymbolInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/exchange/SymbolInfo.java)

#### com.strategyquant.tradinglib.execution (2)

- [IExecutionEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/execution/IExecutionEngine.java)
- [ReservedBarsType](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/execution/ReservedBarsType.java)

#### com.strategyquant.tradinglib.exit (2)

- [ExitMethodsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/exit/ExitMethodsList.java)
- [TrailingStopHandler](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/exit/TrailingStopHandler.java)

#### com.strategyquant.tradinglib.explore (1)

- [Explore](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/explore/Explore.java)

#### com.strategyquant.tradinglib.file (1)

- [SQFileManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/file/SQFileManager.java)

#### com.strategyquant.tradinglib.fitnessfunction (2)

- [FitnessOptions](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/fitnessfunction/FitnessOptions.java)
- [IFitnessFunction](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/fitnessfunction/IFitnessFunction.java)

#### com.strategyquant.tradinglib.formulas (3)

- [EmptyFormula](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/formulas/EmptyFormula.java)
- [FormulaComparatorByOrder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/formulas/FormulaComparatorByOrder.java)
- [Formulas](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/formulas/Formulas.java)

#### com.strategyquant.tradinglib.generator (25)

- [BlockSettingsConverter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/BlockSettingsConverter.java)
- [Checkers](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/Checkers.java)
- [CheckersList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/CheckersList.java)
- [EmptyStrategy](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/EmptyStrategy.java)
- [GenerateException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/GenerateException.java)
- [GeneratorBase](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/GeneratorBase.java)
- [IStrategyTemplate](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/IStrategyTemplate.java)
- [NegaterComparatorByOrder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/NegaterComparatorByOrder.java)
- [Negaters](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/Negaters.java)
- [RandomAndOr](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/RandomAndOr.java)
- [RandomAndOrList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/RandomAndOrList.java)
- [RulePart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/RulePart.java)
- [RuleType](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/RuleType.java)
- [StrategyGenerator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/StrategyGenerator.java)
- [StrategyGeneratorCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/StrategyGeneratorCache.java)
- [StrategyImproveTemplateSQ3](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/StrategyImproveTemplateSQ3.java)
- [StrategyImproveTemplateSQ4](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/StrategyImproveTemplateSQ4.java)
- [StrategyStandardTemplateSQ3](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/StrategyStandardTemplateSQ3.java)
- [StrategyStandardTemplateSQ4](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/StrategyStandardTemplateSQ4.java)
- [StrategyStandardTemplateSQ4Fuzzy](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/StrategyStandardTemplateSQ4Fuzzy.java)
- [StrategyStockpickerSingleAssetTemplate](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/StrategyStockpickerSingleAssetTemplate.java)
- [StrategyStockpickerTemplate](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/StrategyStockpickerTemplate.java)
- [StrategyTemplateGenerator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/StrategyTemplateGenerator.java)
- [StrategyTemplateNotFoundException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/StrategyTemplateNotFoundException.java)
- [StrategyWithVariables](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/generator/StrategyWithVariables.java)

#### com.strategyquant.tradinglib.gp (29)

- [AbstractCrossover](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/AbstractCrossover.java)
- [AbstractFactory](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/AbstractFactory.java)
- [EvolutionPipeline](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/EvolutionPipeline.java)
- [FitnessCollectionData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/FitnessCollectionData.java)
- [GPConstants](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPConstants.java)
- [GPEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPEngine.java)
- [GPEvaluationJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPEvaluationJob.java)
- [GPEvolutionMessage](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPEvolutionMessage.java)
- [GPEvolutionPopulationMessage](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPEvolutionPopulationMessage.java)
- [GPFitnessComparator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPFitnessComparator.java)
- [GPFitnessEvolution](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPFitnessEvolution.java)
- [GPFitnessEvolutionData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPFitnessEvolutionData.java)
- [GPGenerationTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPGenerationTypes.java)
- [GPGenerationalEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPGenerationalEngine.java)
- [GPGenerationalEngine$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPGenerationalEngine.java) — nested/anonymous
- [GPIDs](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPIDs.java)
- [GPIslandJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPIslandJob.java)
- [GPMessages](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPMessages.java)
- [GPSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/GPSettings.java)
- [IEvolutionaryOperator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/IEvolutionaryOperator.java)
- [IFitnessEvaluator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/IFitnessEvaluator.java)
- [IGPEvolutionMessagesListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/IGPEvolutionMessagesListener.java)
- [IGPFinishedListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/IGPFinishedListener.java)
- [IGPNode](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/IGPNode.java)
- [ISelectionStrategy](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/ISelectionStrategy.java)
- [IStopConditionsChecker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/IStopConditionsChecker.java)
- [RouletteWheelSelection](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/RouletteWheelSelection.java)
- [SelectedBlockGroups](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/SelectedBlockGroups.java)
- [TournamentSelection](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/TournamentSelection.java)

#### com.strategyquant.tradinglib.gp.strategies (15)

- [BacktestEvaluator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/BacktestEvaluator.java)
- [BuildSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/BuildSettings.java)
- [FixCustomBlocks](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/FixCustomBlocks.java)
- [FixNonRandomBlocks](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/FixNonRandomBlocks.java)
- [FixNumberOfExitTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/FixNumberOfExitTypes.java)
- [FixStockpickerBlocks](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/FixStockpickerBlocks.java)
- [FixUnusedDependentFormulas](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/FixUnusedDependentFormulas.java)
- [GenEvoChecker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/GenEvoChecker.java)
- [GeneratedObject](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/GeneratedObject.java)
- [GeneratedObjectsMap](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/GeneratedObjectsMap.java)
- [Node](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/Node.java)
- [NodeCrossover](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/NodeCrossover.java)
- [NodeElement](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/NodeElement.java)
- [NodeFactory](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/NodeFactory.java)
- [NodeMutation](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gp/strategies/NodeMutation.java)

#### com.strategyquant.tradinglib.gui (2)

- [IInitAfterGUILoad](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gui/IInitAfterGUILoad.java)
- [InitAfterGUILoad](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/gui/InitAfterGUILoad.java)

#### com.strategyquant.tradinglib.historyData (17)

- [DownloadEodStockHistorySymbolJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/DownloadEodStockHistorySymbolJob.java)
- [DownloadEodStockHistorySymbolJob$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/DownloadEodStockHistorySymbolJob.java) — nested/anonymous
- [DownloadHistorySymbolJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/DownloadHistorySymbolJob.java)
- [DownloadHistorySymbolJob$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/DownloadHistorySymbolJob.java) — nested/anonymous
- [DownloadMessageHandler](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/DownloadMessageHandler.java)
- [EodHistoryDataCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/EodHistoryDataCache.java)
- [HistoryDataCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/HistoryDataCache.java)
- [HistoryDataDownloadUrls](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/HistoryDataDownloadUrls.java)
- [HistoryDataManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/HistoryDataManager.java)
- [HistoryDataManager$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/HistoryDataManager.java) — nested/anonymous
- [HistoryDataManager$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/HistoryDataManager.java) — nested/anonymous
- [HistoryDataManager$3](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/HistoryDataManager.java) — nested/anonymous
- [HttpApacheManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/HttpApacheManager.java)
- [HttpApacheManager$HttpException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/HttpApacheManager.java) — nested/anonymous
- [MarketDtoToJsonTransformer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/MarketDtoToJsonTransformer.java)
- [SpecialSymbolsManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/SpecialSymbolsManager.java)
- [TickerDtoToJsonTransformer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/historyData/TickerDtoToJsonTransformer.java)

#### com.strategyquant.tradinglib.indicator (6)

- [IIndicatorsHolder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicator/IIndicatorsHolder.java)
- [IndicatorBase](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicator/IndicatorBase.java)
- [IndicatorBase$DataSeriesSet](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicator/IndicatorBase.java) — nested/anonymous
- [IndicatorsCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicator/IndicatorsCache.java)
- [IndicatorsObj](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicator/IndicatorsObj.java)
- [Inputs](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/indicator/Inputs.java)

#### com.strategyquant.tradinglib.jobs (1)

- [SimpleDownloadJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/jobs/SimpleDownloadJob.java)

#### com.strategyquant.tradinglib.miniequitychart (1)

- [MiniEquityChartComputer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/miniequitychart/MiniEquityChartComputer.java)

#### com.strategyquant.tradinglib.moneymanagement (2)

- [MMComparatorByOrder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/moneymanagement/MMComparatorByOrder.java)
- [MoneyManagementMethodsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/moneymanagement/MoneyManagementMethodsList.java)

#### com.strategyquant.tradinglib.montecarlo.manipulation (1)

- [MonteCarloManipulationList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/montecarlo/manipulation/MonteCarloManipulationList.java)

#### com.strategyquant.tradinglib.montecarlo.retest (1)

- [MonteCarloRetestList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/montecarlo/retest/MonteCarloRetestList.java)

#### com.strategyquant.tradinglib.mql (1)

- [MQLMarketConverter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/mql/MQLMarketConverter.java)

#### com.strategyquant.tradinglib.mt4 (4)

- [Mt4Exporter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/mt4/Mt4Exporter.java)
- [Mt4Exporter$Exporter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/mt4/Mt4Exporter.java) — nested/anonymous
- [Mt4Exporter$FxtExporter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/mt4/Mt4Exporter.java) — nested/anonymous
- [Mt4Exporter$HstExporter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/mt4/Mt4Exporter.java) — nested/anonymous

#### com.strategyquant.tradinglib.mt5api (6)

- [Mt5ApiDownloaderJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/mt5api/Mt5ApiDownloaderJob.java)
- [Mt5ApiDownloaderJob$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/mt5api/Mt5ApiDownloaderJob.java) — nested/anonymous
- [Mt5ApiImportInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/mt5api/Mt5ApiImportInfo.java)
- [Mt5ApiManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/mt5api/Mt5ApiManager.java)
- [Mt5ApiManager$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/mt5api/Mt5ApiManager.java) — nested/anonymous
- [Mt5ApiManager$Source](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/mt5api/Mt5ApiManager.java) — nested/anonymous

#### com.strategyquant.tradinglib.optimization (55)

- [BadOptimizationParamsException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/BadOptimizationParamsException.java)
- [FitnessMetricComparator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/FitnessMetricComparator.java)
- [IEngineLogListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/IEngineLogListener.java)
- [INewResultListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/INewResultListener.java)
- [ISequentialOptimizationCompleteListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/ISequentialOptimizationCompleteListener.java)
- [IStepsListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/IStepsListener.java)
- [IStrategyModifier](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/IStrategyModifier.java)
- [MetricForFitness](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/MetricForFitness.java)
- [NonexistingVariableException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/NonexistingVariableException.java)
- [NotEnoughSpaceException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/NotEnoughSpaceException.java)
- [OptProfileChecksLevels](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptProfileChecksLevels.java)
- [OptimizationConst](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationConst.java)
- [OptimizationEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationEngine.java)
- [OptimizationEngineBase](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationEngineBase.java)
- [OptimizationEngineSimple](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationEngineSimple.java)
- [OptimizationEngineSimple$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationEngineSimple.java) — nested/anonymous
- [OptimizationEngineSimple$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationEngineSimple.java) — nested/anonymous
- [OptimizationEngineWF](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationEngineWF.java)
- [OptimizationEngineWF$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationEngineWF.java) — nested/anonymous
- [OptimizationException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationException.java)
- [OptimizationIndexes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationIndexes.java)
- [OptimizationIndexesCrossover](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationIndexesCrossover.java)
- [OptimizationIndexesFactory](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationIndexesFactory.java)
- [OptimizationIndexesMutation](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationIndexesMutation.java)
- [OptimizationMethods](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationMethods.java)
- [OptimizationParams](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationParams.java)
- [OptimizationProfile](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationProfile.java)
- [OptimizationSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationSettings.java)
- [OptimizationTestJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationTestJob.java)
- [OptimizationTestResult](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationTestResult.java)
- [OptimizationTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizationTypes.java)
- [OptimizerBacktestEvaluator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OptimizerBacktestEvaluator.java)
- [OrdersIndexComparator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/OrdersIndexComparator.java)
- [Parameter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/Parameter.java)
- [ParametersSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/ParametersSettings.java)
- [PopulationGenerations](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/PopulationGenerations.java)
- [SequentialOptimizationEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/SequentialOptimizationEngine.java)
- [SequentialOptimizationEngine$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/SequentialOptimizationEngine.java) — nested/anonymous
- [SequentialOptimizationJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/SequentialOptimizationJob.java)
- [SequentialOptimizationSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/SequentialOptimizationSettings.java)
- [StandardFitnessComparator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/StandardFitnessComparator.java)
- [StrategyHelper](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/StrategyHelper.java)
- [StrategyParamData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/StrategyParamData.java)
- [SysParamPermutationsCharts](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/SysParamPermutationsCharts.java)
- [SysParamPermutationsTable](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/SysParamPermutationsTable.java)
- [VariantComparatorByName](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/VariantComparatorByName.java)
- [WFOptJobResult](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/WFOptJobResult.java)
- [WFSimulationJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/WFSimulationJob.java)
- [WFSimulationJobResult](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/WFSimulationJobResult.java)
- [WalkForwardColumns](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/WalkForwardColumns.java)
- [WalkForwardMatrixResult](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/WalkForwardMatrixResult.java)
- [WalkForwardParametersStability](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/WalkForwardParametersStability.java)
- [WalkForwardScore](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/WalkForwardScore.java)
- [WalkForwardStability](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/WalkForwardStability.java)
- [package-info](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/optimization/package-info.java) — package metadata

#### com.strategyquant.tradinglib.options (2)

- [TradingOptions](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/options/TradingOptions.java)
- [TradingOptionsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/options/TradingOptionsList.java)

#### com.strategyquant.tradinglib.options.parameters (8)

- [BrokerOption](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/options/parameters/BrokerOption.java)
- [LimitOver](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/options/parameters/LimitOver.java)
- [MarketOpenSession](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/options/parameters/MarketOpenSession.java)
- [RealisticGapsHandling](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/options/parameters/RealisticGapsHandling.java)
- [ReservedBars](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/options/parameters/ReservedBars.java)
- [SessionOption](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/options/parameters/SessionOption.java)
- [StockpickerOptions](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/options/parameters/StockpickerOptions.java)
- [StoreChartData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/options/parameters/StoreChartData.java)

#### com.strategyquant.tradinglib.order (5)

- [ILiveOrdersList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/order/ILiveOrdersList.java)
- [IOrderListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/order/IOrderListener.java)
- [LiveOrdersListObj](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/order/LiveOrdersListObj.java)
- [LiveOrdersListObj$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/order/LiveOrdersListObj.java) — nested/anonymous
- [LiveOrdersListObj$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/order/LiveOrdersListObj.java) — nested/anonymous

#### com.strategyquant.tradinglib.performance (1)

- [Performance](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/performance/Performance.java)

#### com.strategyquant.tradinglib.plugindef.app (1)

- [IAppPlugin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/plugindef/app/IAppPlugin.java)

#### com.strategyquant.tradinglib.plugindef.connection (1)

- [IConnectionPlugin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/plugindef/connection/IConnectionPlugin.java)

#### com.strategyquant.tradinglib.portfolioMaster (4)

- [PortfolioMasterFitness](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/portfolioMaster/PortfolioMasterFitness.java)
- [PortfolioMasterFitnessList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/portfolioMaster/PortfolioMasterFitnessList.java)
- [PortfolioMasterSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/portfolioMaster/PortfolioMasterSettings.java)
- [PortfolioMasterUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/portfolioMaster/PortfolioMasterUtils.java)

#### com.strategyquant.tradinglib.project (55)

- [ChartSetupException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ChartSetupException.java)
- [ComplexDurationStats](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ComplexDurationStats.java)
- [CustomConfigs](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/CustomConfigs.java)
- [DatabankPositionComparator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/DatabankPositionComparator.java)
- [Databanks](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/Databanks.java)
- [Databanks$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/Databanks.java) — nested/anonymous
- [DefaultProjectConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/DefaultProjectConfig.java)
- [EngineCharts](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/EngineCharts.java)
- [FitnessEvolution](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/FitnessEvolution.java)
- [FitnessEvolution$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/FitnessEvolution.java) — nested/anonymous
- [FitnessEvolution$DatabankChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/FitnessEvolution.java) — nested/anonymous
- [FitnessEvolution$IslandChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/FitnessEvolution.java) — nested/anonymous
- [FitnessEvolution$IslandCharts](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/FitnessEvolution.java) — nested/anonymous
- [GoToTaskException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/GoToTaskException.java)
- [GridProject](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/GridProject.java)
- [GridProject$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/GridProject.java) — nested/anonymous
- [ILastEventListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ILastEventListener.java)
- [IProgressStatusListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/IProgressStatusListener.java)
- [IProject](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/IProject.java)
- [IProjectCondition](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/IProjectCondition.java)
- [IProjectsListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/IProjectsListener.java)
- [ProgressEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProgressEngine.java)
- [ProjectConditionField](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectConditionField.java)
- [ProjectConditions](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectConditions.java)
- [ProjectConfigHelper](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectConfigHelper.java)
- [ProjectConfigHelper$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectConfigHelper.java) — nested/anonymous
- [ProjectCustomResources](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectCustomResources.java)
- [ProjectEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectEngine.java)
- [ProjectException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectException.java)
- [ProjectGlobalLog](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectGlobalLog.java)
- [ProjectLog](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectLog.java)
- [ProjectNameComparator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectNameComparator.java)
- [ProjectProgress](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectProgress.java)
- [ProjectProgressInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectProgressInfo.java)
- [ProjectResources](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectResources.java)
- [ProjectResources$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectResources.java) — nested/anonymous
- [ProjectResources$2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectResources.java) — nested/anonymous
- [ProjectResources$CloneInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectResources.java) — nested/anonymous
- [ProjectStatusListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ProjectStatusListener.java)
- [RandomGroups](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/RandomGroups.java)
- [ResourcesCustomBlocks](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ResourcesCustomBlocks.java)
- [ResourcesRandomGroups](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/ResourcesRandomGroups.java)
- [RunningStatusBase](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/RunningStatusBase.java)
- [SQLogger](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/SQLogger.java)
- [SQProject](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/SQProject.java)
- [SQProject$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/SQProject.java) — nested/anonymous
- [StopPauseEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/StopPauseEngine.java)
- [StrategiesSaver](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/StrategiesSaver.java)
- [StrategiesSaver$StrategySavedListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/StrategiesSaver.java) — nested/anonymous
- [StrategySaver](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/StrategySaver.java)
- [StrategyXMLModifier](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/StrategyXMLModifier.java)
- [TaskStat](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/TaskStat.java)
- [TaskStats](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/TaskStats.java)
- [UserConfirm](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/UserConfirm.java)
- [UserConfirm$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/UserConfirm.java) — nested/anonymous

#### com.strategyquant.tradinglib.project.bestresults (3)

- [BestResultMiniChart](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/bestresults/BestResultMiniChart.java)
- [BestResultOverview](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/bestresults/BestResultOverview.java)
- [BestResults](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/bestresults/BestResults.java)

#### com.strategyquant.tradinglib.project.console (4)

- [CLILogger](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/console/CLILogger.java)
- [ConsoleImpl](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/console/ConsoleImpl.java)
- [ConsoleImpl$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/console/ConsoleImpl.java) — nested/anonymous
- [SQConsole](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/console/SQConsole.java)

#### com.strategyquant.tradinglib.project.mcp (1)

- [MCPTools](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/mcp/MCPTools.java)

#### com.strategyquant.tradinglib.project.websocket (21)

- [DataManagerAddProgressSender](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/DataManagerAddProgressSender.java)
- [DataManagerConfirm](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/DataManagerConfirm.java)
- [DataManagerConfirm$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/DataManagerConfirm.java) — nested/anonymous
- [DataManagerCustomDataProgress](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/DataManagerCustomDataProgress.java)
- [DataManagerDataProgress](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/DataManagerDataProgress.java)
- [DataManagerProgressListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/DataManagerProgressListener.java)
- [DataManagerSaveProgreessSender](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/DataManagerSaveProgreessSender.java)
- [DataToSend](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/DataToSend.java)
- [DataUpdateTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/DataUpdateTypes.java)
- [MultiProgressListener](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/MultiProgressListener.java)
- [MultiProgressPublisher](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/MultiProgressPublisher.java)
- [ProjectDataPublisher](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/ProjectDataPublisher.java)
- [ProjectFeeds](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/ProjectFeeds.java)
- [SQWebSocket](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/SQWebSocket.java)
- [SQWebSocketManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/SQWebSocketManager.java)
- [SQWebSocketManager$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/SQWebSocketManager.java) — nested/anonymous
- [SynchronizedWebSocketPublisher](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/SynchronizedWebSocketPublisher.java)
- [WSDataObjects](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/WSDataObjects.java)
- [WebSocketConst](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/WebSocketConst.java)
- [WebSocketNotification](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/WebSocketNotification.java)
- [WebSocketPublisher](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/WebSocketPublisher.java)

#### com.strategyquant.tradinglib.project.websocket.channels (2)

- [IProjectChannel](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/channels/IProjectChannel.java)
- [ProjectChannels](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/channels/ProjectChannels.java)

#### com.strategyquant.tradinglib.project.websocket.channels.impl (6)

- [BestResultsChannel](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/channels/impl/BestResultsChannel.java)
- [DatabankChannel](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/channels/impl/DatabankChannel.java)
- [EngineChannel](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/channels/impl/EngineChannel.java)
- [EngineChartsChannel](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/channels/impl/EngineChartsChannel.java)
- [LogChannel](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/channels/impl/LogChannel.java)
- [ProgressChannel](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/project/websocket/channels/impl/ProgressChannel.java)

#### com.strategyquant.tradinglib.propertygrid (10)

- [IPGParameter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/propertygrid/IPGParameter.java)
- [PGBooleanParameter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/propertygrid/PGBooleanParameter.java)
- [PGComboParameter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/propertygrid/PGComboParameter.java)
- [PGDoubleParameter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/propertygrid/PGDoubleParameter.java)
- [PGIntParameter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/propertygrid/PGIntParameter.java)
- [PGStringParameter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/propertygrid/PGStringParameter.java)
- [PGTimeParameter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/propertygrid/PGTimeParameter.java)
- [ParameterDoesntExistException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/propertygrid/ParameterDoesntExistException.java)
- [ParametersTableItem](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/propertygrid/ParametersTableItem.java)
- [ParametersTableItemProperties](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/propertygrid/ParametersTableItemProperties.java)

#### com.strategyquant.tradinglib.python (3)

- [PythonRunner](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/python/PythonRunner.java)
- [PythonRunner$ProgressCallback](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/python/PythonRunner.java) — nested/anonymous
- [PythonRunner$ProgressCallbackAdapter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/python/PythonRunner.java) — nested/anonymous

#### com.strategyquant.tradinglib.quality (4)

- [DataProblemEvaluator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/quality/DataProblemEvaluator.java)
- [DataProblemEvaluator$ProblemKind](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/quality/DataProblemEvaluator.java) — nested/anonymous
- [QualityChecker](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/quality/QualityChecker.java)
- [QualityChecker$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/quality/QualityChecker.java) — nested/anonymous

#### com.strategyquant.tradinglib.results (14)

- [AbstractBacktestPlugin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/AbstractBacktestPlugin.java)
- [AbstractResultsPlugin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/AbstractResultsPlugin.java)
- [DatabankResultsGroupProvider](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/DatabankResultsGroupProvider.java)
- [FingerprintsMap](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/FingerprintsMap.java)
- [IBacktestPlugin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/IBacktestPlugin.java)
- [IResultPlugin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/IResultPlugin.java)
- [IResultsGroupProvider](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/IResultsGroupProvider.java)
- [ResultsMap](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/ResultsMap.java)
- [SpecialValues](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/SpecialValues.java)
- [StatsKeyCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/StatsKeyCache.java)
- [StatsKeyCache$StatInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/StatsKeyCache.java) — nested/anonymous
- [StrategyFingerprint](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/StrategyFingerprint.java)
- [SymbolInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/SymbolInfo.java)
- [SymbolsMap](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/SymbolsMap.java)

#### com.strategyquant.tradinglib.results.file (6)

- [FileHandler](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/file/FileHandler.java)
- [FileHandlerVariables](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/file/FileHandlerVariables.java)
- [ILoaderPlugin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/file/ILoaderPlugin.java)
- [ISaverPlugin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/file/ISaverPlugin.java)
- [MissingInstrumentException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/file/MissingInstrumentException.java)
- [SQ3Settings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/file/SQ3Settings.java)

#### com.strategyquant.tradinglib.results.overview (1)

- [OverviewTemplates](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/overview/OverviewTemplates.java)

#### com.strategyquant.tradinglib.results.stats (3)

- [ChartValue](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/ChartValue.java)
- [StatsComputer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/StatsComputer.java)
- [TradingPeriodTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/TradingPeriodTypes.java)

#### com.strategyquant.tradinglib.results.stats.comparator (4)

- [OrderComparatorByCloseTime](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/comparator/OrderComparatorByCloseTime.java)
- [OrderComparatorByOpenTime](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/comparator/OrderComparatorByOpenTime.java)
- [OrderComparatorByOpenTime2](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/comparator/OrderComparatorByOpenTime2.java)
- [OrderComparatorByTicket](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/comparator/OrderComparatorByTicket.java)

#### com.strategyquant.tradinglib.results.stats.computer (2)

- [IOrderComputer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/computer/IOrderComputer.java)
- [OrderPLComputer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/computer/OrderPLComputer.java)

#### com.strategyquant.tradinglib.results.stats.type (4)

- [IStatsType](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/type/IStatsType.java)
- [StatsTypeDirection](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/type/StatsTypeDirection.java)
- [StatsTypePL](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/type/StatsTypePL.java)
- [StatsTypeSample](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/results/stats/type/StatsTypeSample.java)

#### com.strategyquant.tradinglib.riskmanagement (1)

- [RiskManagementMethodsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/riskmanagement/RiskManagementMethodsList.java)

#### com.strategyquant.tradinglib.robustnesstests (10)

- [DataModifierCallback](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/robustnesstests/DataModifierCallback.java)
- [FitnessData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/robustnesstests/FitnessData.java)
- [MCSimulations](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/robustnesstests/MCSimulations.java)
- [RobustnessOrdersValues](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/robustnesstests/RobustnessOrdersValues.java)
- [RobustnessResultComparator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/robustnesstests/RobustnessResultComparator.java)
- [RobustnessResults](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/robustnesstests/RobustnessResults.java)
- [RobustnessTestMethod](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/robustnesstests/RobustnessTestMethod.java)
- [RobustnessTestMethodsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/robustnesstests/RobustnessTestMethodsList.java)
- [SequentialOptimizationResults](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/robustnesstests/SequentialOptimizationResults.java)
- [package-info](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/robustnesstests/package-info.java) — package metadata

#### com.strategyquant.tradinglib.scaling (1)

- [ScalingMethodsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/scaling/ScalingMethodsList.java)

#### com.strategyquant.tradinglib.servlet (1)

- [IServletPlugin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/servlet/IServletPlugin.java)

#### com.strategyquant.tradinglib.setup (4)

- [BarUpdateInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/setup/BarUpdateInfo.java)
- [Portfolio](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/setup/Portfolio.java)
- [Portfolio$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/setup/Portfolio.java) — nested/anonymous
- [TradingSetupRunnable](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/setup/TradingSetupRunnable.java)

#### com.strategyquant.tradinglib.simplegrid (2)

- [SimpleGridEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simplegrid/SimpleGridEngine.java)
- [SimpleGridEngine$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simplegrid/SimpleGridEngine.java) — nested/anonymous

#### com.strategyquant.tradinglib.simulator (2)

- [Engines](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/Engines.java)
- [ITradingSimulator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/ITradingSimulator.java)

#### com.strategyquant.tradinglib.simulator.impl (13)

- [AbstractTradingSimulator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/AbstractTradingSimulator.java)
- [JForexSimulator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/JForexSimulator.java)
- [MarketPriceHolder](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/MarketPriceHolder.java)
- [MarketPriceHolder$TwoTickEvents](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/MarketPriceHolder.java) — nested/anonymous
- [MetaTrader4Simulator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/MetaTrader4Simulator.java)
- [MetaTrader5SimulatorHedging](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/MetaTrader5SimulatorHedging.java)
- [MetaTrader5SimulatorNetting](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/MetaTrader5SimulatorNetting.java)
- [MetaTraderSimulatorHedging](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/MetaTraderSimulatorHedging.java)
- [MetaTraderSimulatorNetting](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/MetaTraderSimulatorNetting.java)
- [MultiChartsSimulator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/MultiChartsSimulator.java)
- [OrderExecutionTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/OrderExecutionTypes.java)
- [TraderSimulators](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/TraderSimulators.java)
- [TradestationSimulator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/simulator/impl/TradestationSimulator.java)

#### com.strategyquant.tradinglib.stockchart (15)

- [ChartKind](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/ChartKind.java)
- [Indicator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/Indicator.java)
- [IndicatorDisplayFormatter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/IndicatorDisplayFormatter.java)
- [IndicatorLevel](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/IndicatorLevel.java)
- [IndicatorLine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/IndicatorLine.java)
- [PreviewCaption](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/PreviewCaption.java)
- [StockChartData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/StockChartData.java)
- [StockData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/StockData.java)
- [StockDataUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/StockDataUtils.java)
- [StockLoader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/StockLoader.java)
- [StockLoader$ChartInfo](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/StockLoader.java) — nested/anonymous
- [StockLoaderForStockPicking](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/StockLoaderForStockPicking.java)
- [StockSaverForStockPicking](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/StockSaverForStockPicking.java)
- [StockSaverOriginalFormat](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/StockSaverOriginalFormat.java)
- [Trade](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/stockchart/Trade.java)

#### com.strategyquant.tradinglib.strategy (19)

- [DataItemsGenerator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/DataItemsGenerator.java)
- [EmptyMarketData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/EmptyMarketData.java)
- [LiveOrderObj](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/LiveOrderObj.java)
- [LiveOrdersCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/LiveOrdersCache.java)
- [MarketData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/MarketData.java)
- [OrderActions](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/OrderActions.java)
- [OrderErrors](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/OrderErrors.java)
- [OutOfSample](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/OutOfSample.java)
- [PreparedChartData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/PreparedChartData.java)
- [SimpleStrategyTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/SimpleStrategyTypes.java)
- [SourceCode](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/SourceCode.java)
- [StrategiesList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/StrategiesList.java)
- [StrategyLoader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/StrategyLoader.java)
- [StrategyMerger](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/StrategyMerger.java)
- [SyncType](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/SyncType.java)
- [TraderUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/TraderUtils.java)
- [UpdateEvents](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/UpdateEvents.java)
- [WorkingStatus](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/WorkingStatus.java)
- [WorstDailyEquity](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/WorstDailyEquity.java)

#### com.strategyquant.tradinglib.strategy.xml (4)

- [SQ3StrategyConverter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/xml/SQ3StrategyConverter.java)
- [StrategyFixer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/xml/StrategyFixer.java)
- [StrategyFixerWizardOld](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/xml/StrategyFixerWizardOld.java)
- [XmlStrategyException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategy/xml/XmlStrategyException.java)

#### com.strategyquant.tradinglib.strategyConfig (1)

- [StrategyConfig](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/strategyConfig/StrategyConfig.java)

#### com.strategyquant.tradinglib.swap (1)

- [SwapCalculator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/swap/SwapCalculator.java)

#### com.strategyquant.tradinglib.table (2)

- [TableColumn](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/table/TableColumn.java)
- [TradelistOrdersComparator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/table/TradelistOrdersComparator.java)

#### com.strategyquant.tradinglib.talib (7)

- [TALibBlocks](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/TALibBlocks.java)
- [TALibCustomIndicator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/TALibCustomIndicator.java)
- [TALibCustomIndicatorsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/TALibCustomIndicatorsList.java)
- [TALibIndicator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/TALibIndicator.java)
- [TALibIndicators](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/TALibIndicators.java)
- [TALibIndicatorsCache](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/TALibIndicatorsCache.java)
- [TALibIndicatorsTest](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/TALibIndicatorsTest.java)

#### com.strategyquant.tradinglib.talib.reflection (12)

- [DoubleArray](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/reflection/DoubleArray.java)
- [TALibConst](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/reflection/TALibConst.java)
- [TALibFunction](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/reflection/TALibFunction.java)
- [TALibFunction$DoubleParams](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/reflection/TALibFunction.java) — nested/anonymous
- [TALibFunction$IntegerParams](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/reflection/TALibFunction.java) — nested/anonymous
- [TALibFunction$Param](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/reflection/TALibFunction.java) — nested/anonymous
- [TALibFunctionCalculator](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/reflection/TALibFunctionCalculator.java)
- [TALibFunctions](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/reflection/TALibFunctions.java)
- [TALibSwitchGenApp](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/reflection/TALibSwitchGenApp.java)
- [TALibTestApp](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/reflection/TALibTestApp.java)
- [TALibXmlGenApp](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/reflection/TALibXmlGenApp.java)
- [TALibXmlGenApp$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/talib/reflection/TALibXmlGenApp.java) — nested/anonymous

#### com.strategyquant.tradinglib.task.settings (4)

- [IChangeSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/IChangeSettings.java)
- [ISettingTabPlugin](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/ISettingTabPlugin.java)
- [SettingError](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/SettingError.java)
- [TaskSettingsData](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/TaskSettingsData.java)

#### com.strategyquant.tradinglib.task.settings.blocks (5)

- [BlocksList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/blocks/BlocksList.java)
- [ConfigConverter](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/blocks/ConfigConverter.java)
- [ConfigVerifier](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/blocks/ConfigVerifier.java)
- [ConfigVerifier$1](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/blocks/ConfigVerifier.java) — nested/anonymous
- [ConfigVerifier$BlocksExists](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/blocks/ConfigVerifier.java) — nested/anonymous

#### com.strategyquant.tradinglib.task.settings.buildmode (4)

- [BuildMode](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/buildmode/BuildMode.java)
- [GenerationTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/buildmode/GenerationTypes.java)
- [JSONAble](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/buildmode/JSONAble.java)
- [StopConditionTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/buildmode/StopConditionTypes.java)

#### com.strategyquant.tradinglib.task.settings.buildtype (6)

- [BuildType](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/buildtype/BuildType.java)
- [ChartSettings](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/buildtype/ChartSettings.java)
- [ImproveTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/buildtype/ImproveTypes.java)
- [StrategyArchitectures](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/buildtype/StrategyArchitectures.java)
- [StrategyDirections](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/buildtype/StrategyDirections.java)
- [StrategyTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/buildtype/StrategyTypes.java)

#### com.strategyquant.tradinglib.task.settings.partstoimprove (2)

- [ImproveActionTypes](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/partstoimprove/ImproveActionTypes.java)
- [PartsToImprove](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/task/settings/partstoimprove/PartsToImprove.java)

#### com.strategyquant.tradinglib.taskImpl (3)

- [AbstractTask](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/taskImpl/AbstractTask.java)
- [ISQTask](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/taskImpl/ISQTask.java)
- [TaskException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/taskImpl/TaskException.java)

#### com.strategyquant.tradinglib.tasks (1)

- [HelpTexts](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/tasks/HelpTexts.java)

#### com.strategyquant.tradinglib.tradeanalysis (1)

- [TradeAnalysisChartsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/tradeanalysis/TradeAnalysisChartsList.java)

#### com.strategyquant.tradinglib.tradelist (6)

- [Tradelist](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/tradelist/Tradelist.java)
- [TradelistColumnsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/tradelist/TradelistColumnsList.java)
- [TradelistExport](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/tradelist/TradelistExport.java)
- [TradelistTableColumnEntry](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/tradelist/TradelistTableColumnEntry.java)
- [TradelistTableView](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/tradelist/TradelistTableView.java)
- [TradelistViewsManager](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/tradelist/TradelistViewsManager.java)

#### com.strategyquant.tradinglib.transfomer (1)

- [AbstractDtoToJsonTransformer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/transfomer/AbstractDtoToJsonTransformer.java)

#### com.strategyquant.tradinglib.util (5)

- [ResultComparatorByName](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/util/ResultComparatorByName.java)
- [ResultComparatorByNetProfit](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/util/ResultComparatorByNetProfit.java)
- [RngUtils](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/util/RngUtils.java)
- [StockpickerGenFixer](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/util/StockpickerGenFixer.java)
- [TradingLibUtil](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/util/TradingLibUtil.java)

#### com.strategyquant.tradinglib.wfo (4)

- [EvolutionException](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/wfo/EvolutionException.java)
- [SimulationOrdersList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/wfo/SimulationOrdersList.java)
- [WFOSimulationEngine](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/wfo/WFOSimulationEngine.java)
- [WFVariant](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/wfo/WFVariant.java)

#### com.strategyquant.tradinglib.whatif (1)

- [WhatIfMethodsList](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/whatif/WhatIfMethodsList.java)

#### com.strategyquant.tradinglib.yahoo (3)

- [YahooDownloadJob](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/yahoo/YahooDownloadJob.java)
- [YahooDownloader](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/yahoo/YahooDownloader.java)
- [YahooHelper](C:/Users/rharu/AppDev/HaruQuantAI/data/reference-donor/internal/libs/tradinglib/yahoo/YahooHelper.java)
