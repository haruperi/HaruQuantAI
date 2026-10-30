# Workspace source reassessment: AppDataManager through AppBuilder

Date: 2026-10-30. Scope: all complete-contribution orders formerly based only on frontend/carrier presence in files 03–08. Existing readiness remains authoritative unless an explicit READY suborder below replaces a bounded part. This inventory does not authorize unreviewed bulk ports.

## Source authority

All source locators below now use the consolidated `DONOR_REFERENCE_ROOT/` tree:
libraries in `internal/libs`, plugin implementations and assets in `internal/plugins`,
extensions in `internal/extend`, templates in `internal/ctemplate` or `internal/extend/Code`,
and web resources in `internal/web`. Temporary decompilation folders are no longer required.

Availability counts, method discovery and no-match findings below are retained from the
original audit, before consolidation. Consult [the current manifest](donor-source-manifest.json)
for copied Java files. A previous no-match result is not a claim that the copied tree lacks
that module. Behavioral findings and work-order gates remain unchanged by this path cleanup.
Original carrier provenance does not establish parity across builds.

## AppDataManager

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/AppDataManager`.

- `DONOR_REFERENCE_ROOT/internal/plugins/AppDataManager/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ConnectionLiveTest

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ConnectionLiveTest`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ConnectionMT4

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ConnectionMT4`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ConnectionTest

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ConnectionTest`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CryptoExchangeBinance

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinance`.


Available recovered primary Java files: **1**.
- `DONOR_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinance/Binance/CryptoExchangeBinancePlugin.java`: `getName()`, `getSymbols()`, `clone()`, `download()`, `availableTimeframes()`, `convertTimeframe(String tf)`, `checkSymbolExists(String symbol)`, `getSymbolInfo(String symbol)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CryptoExchangeBinanceCoinM

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinanceCoinM`.


Available recovered primary Java files: **1**.
- `DONOR_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinanceCoinM/BinanceCoinM/CryptoExchangeBinanceCoinMPlugin.java`: `getName()`, `getSymbols()`, `clone()`, `download()`, `availableTimeframes()`, `convertTimeframe(String tf)`, `checkSymbolExists(String symbol)`, `getSymbolInfo(String symbol)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CryptoExchangeBinanceUsdtM

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinanceUsdtM`.


Available recovered primary Java files: **1**.
- `DONOR_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinanceUsdtM/BinanceUsdtM/CryptoExchangeBinanceUsdtMPlugin.java`: `getName()`, `getSymbols()`, `clone()`, `download()`, `availableTimeframes()`, `convertTimeframe(String tf)`, `checkSymbolExists(String symbol)`, `getSymbolInfo(String symbol)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CryptoExchangeBitfinex

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CryptoExchangeBitfinex`.


Available recovered primary Java files: **1**.
- `DONOR_REFERENCE_ROOT/internal/plugins/CryptoExchangeBitfinex/Bitfinex/CryptoExchangeBitfinexPlugin.java`: `getName()`, `getSymbols()`, `clone()`, `download()`, `availableTimeframes()`, `convertTimeframe(String tf)`, `checkSymbolExists(String symbol)`, `getSymbolInfo(String symbol)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CryptoExchangeCoinbasePro

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CryptoExchangeCoinbasePro`.


Available recovered primary Java files: **1**.
- `DONOR_REFERENCE_ROOT/internal/plugins/CryptoExchangeCoinbasePro/CoinbasePro/CryptoExchangeCoinbaseProPlugin.java`: `getName()`, `getSymbols()`, `clone()`, `download()`, `availableTimeframes()`, `convertTimeframe(String tf)`, `checkSymbolExists(String symbol)`, `getSymbolInfo(String symbol)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CryptoExchangePoloniex

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CryptoExchangePoloniex`.


Available recovered primary Java files: **1**.
- `DONOR_REFERENCE_ROOT/internal/plugins/CryptoExchangePoloniex/Poloniex/CryptoExchangePoloniexPlugin.java`: `getName()`, `getSymbols()`, `clone()`, `download()`, `availableTimeframes()`, `convertTimeframe(String tf)`, `checkSymbolExists(String symbol)`, `getSymbolInfo(String symbol)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataManagerActions

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerActions`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerActions/brData/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerActions/brDataUpdate/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerActions/cloneToTimezone/CloneToTimezoneCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerActions/cloneToTimezone/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerActions/delete/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerActions/exportToCsv/ExportToCsvCtrl.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerActions/exportToCsv/ExportToCsvService.js`: `/data/exportToCsv`, `/data/exportToCsvDeleteFileFormat`, `/data/exportToCsvLoadSettings`, `/data/exportToCsvSaveAsFileFormat`, `/data/exportToCsvSaveFileFormat`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerActions/exportToMT4/ExportToMT4Service.js`: `/data/exportToMT4`, `/data/exportToMT4Action`, `/data/exportToMT4GetDataFolder`, `/data/exportToMT4GetServerNames`, `/data/exportToMT4LoadProperties`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerActions/exportToMT5/ExportToMT5Service.js`: `/data/exportToMT5`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataManagerBasket

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBasket`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBasket/actions/add/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBasket/actions/editStocks/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBasket/actions/updateData/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBasket/controllers/BasketsCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBasket/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBasket/service/BasketService.js`: `saveBasket(details, callback)`, `removeBaskets(baskets)`, `import(data)`, `updateData(data)`, `export(data)`, `listStocks(data, callback)`, `editStocks(data, callback)`, `saveXml(data)`, `loadXml(data)`.

Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBasket/Basket/BasketServlet.java`: `run()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBasket/Basket/BasketServletPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBasket/service/BasketService.js`: `/basketOfStocks/delete`, `/basketOfStocks/editStocks`, `/basketOfStocks/export`, `/basketOfStocks/import`, `/basketOfStocks/listStocks`, `/basketOfStocks/loadXml`, `/basketOfStocks/save`, `/basketOfStocks/saveXml`, `/basketOfStocks/updateData`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataManagerBroker

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBroker`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBroker/actions/add/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBroker/actions/editStocks/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBroker/actions/importInstruments/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBroker/actions/importSessions/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBroker/actions/updateData/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBroker/controllers/BrokersCtrl.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **3**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBroker/Broker/BrokerServlet.java`: `run()`, `run()`, `run()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBroker/Broker/BrokerServletPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBroker/Broker/BrokerXmlImporter.java`: `importSessions(String file, List<String> names)`, `importInstruments(String file, List<String> names)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerBroker/service/BrokerService.js`: `/brokers/delete`, `/brokers/editStocks`, `/brokers/export`, `/brokers/import`, `/brokers/importGetOverview`, `/brokers/importSessionInstrument`, `/brokers/listStocks`, `/brokers/loadXml`, `/brokers/save`, `/brokers/saveXml`, `/brokers/updateData`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataManagerConnections

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerConnections`.


Available recovered primary Java files: **3**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerConnections/Connections/ConnectionInfoSender.java`: `getInstance()`, `start()`, `stop()`, `getData()`, `resetLastData()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerConnections/Connections/ConnectionServlet.java`: `getInstance()`, `onList()`, `isConnectionActive(String connName)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerConnections/Connections/ConnectionServletPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataManagerCustomData

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/add/CustomDataAddCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/add/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/cot/CustomDataCotCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/cot/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/DMCustomDataCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/DMCustomDataService.js`: `add(data, callback)`, `edit(data, callback)`, `updateCot(callback)`, `clearData(data)`, `removeData(data)`, `importGetInfo()`, `import(config)`, `importAction(data, action)`, `importGetOverview(params)`, `importSaveNewDataFormat(params)`, `importUpdateDataFormat(params, callback)`, `importDeleteDataFormat(formatName, callback)`.

Available recovered primary Java files: **5**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/CustomData/CustomDataServlet.java`: `importCot(CotData cotData)`, `compare(CotRecord record1, CotRecord record2)`, `createCotValuesObject(String cotKey)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/CustomData/CustomDataServletPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/CustomData/job/CustomDataCsvLoader.java`: `readData()`, `restart()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/CustomData/job/CustomDataImporter.java`: `performImport(IProgressListener listener, CustomDataInfo dataInfo, ImportDataInfo importInfo)`, `getTempFileName(String fileName)`, `countRows(String importFileName)`, `cancel()`, `isCanceled()`, `pause()`, `restart()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/CustomData/job/CustomDataImporterJob.java`: `call()`, `messageReceived(GridMessage message)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/DMCustomDataService.js`: `/customdata/add`, `/customdata/clear`, `/customdata/edit`, `/customdata/importAction`, `/customdata/importDeleteDataFormat`, `/customdata/importUpdateDataFormat`, `/customdata/load`, `/customdata/recognizeFromFile`, `/customdata/remove`, `/customdata/save`, `/customdata/updateCot`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataManagerData

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData/DMDataCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData/DMDataService.js`: `listConnections(dataDetails)`, `cloneToTimezone(data, callOnSuccess)`, `cloneToTimezoneAction(symbol, action)`, `checkQualitySummary(symbol, timeframe, session, callOnSuccess)`, `getIndexForDate(symbol, timeframe, session, date, callOnSuccess)`, `editData(dataDetails)`, `saveDataChanges(data, callOnSuccess)`, `clearData(data)`, `cancelDataOperation()`, `removeData(data)`, `loadChartData(params, callback)`, `showData(data)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData/module.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **29**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData/Data/csvexport/CsvExporter.java`: `exportData(IProgressListener listener, String connection, String symbol, String timeframe, String session, String filePath, long fromDate, long toDate, Format format, String targetTimezone)`, `pause()`, `restart()`, `cancel()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData/Data/csvexport/CsvExportJob.java`: `call()`, `messageReceived(GridMessage message)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData/Data/csvexport/format/Format.java`: `toJson()`, `setFromXML(Element element)`, `getXML()`, `withIncludeHeader(boolean includeHeader)`, `printHeader()`, `printData(String symbol, VersatileData data, int decimals)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData/Data/csvexport/format/Formats.java`: `get()`, `toJson()`, `findByName(String name)`, `parseCustomFormat(String name, String header, String items, boolean includeHeader)`, `updateFormat(String fileFormat, String header, String items, boolean includeHeader)`, `addFormat(String name, String header, String items, boolean includeHeader)`, `deleteFormat(String fileFormat)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData/Data/csvexport/items/AbstractItem.java`: `toJson()`, `format(String key, String format)`, `printValue(String var1, VersatileData var2, int var3)`, `clone()`, `setFormat(String format)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData/Data/csvexport/items/AskPrice.java`: `printValue(String symbol, VersatileData data, int decimals)`, `clone()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData/Data/csvexport/items/BidPrice.java`: `printValue(String symbol, VersatileData data, int decimals)`, `clone()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData/Data/csvexport/items/ClosePrice.java`: `printValue(String symbol, VersatileData data, int decimals)`, `clone()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerData/DMDataService.js`: `/connections/listConnections`, `/data/cancelDataOperation`, `/data/checkQualitySummary`, `/data/clearData`, `/data/cloneToTimezone`, `/data/cloneToTimezoneAction`, `/data/editData`, `/data/getIndexForDate`, `/data/load`, `/data/pauseAll`, `/data/removeData`, `/data/resumeAll`, `/data/save`, `/data/saveDataChanges`, `/data/stopAll`, `/data/updateAll`, `/data/updateSelected`, `data/reviewChart`, `data/showData`, `dataSourceDukascopy/getParallelDownload`, `dataSourceDukascopy/setParallelDownload`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataManagerHelp

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerHelp`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerHelp/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataManagerHome

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerHome`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerHome/DMHomeCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerHome/DMHomeService.js`: `link(callOnSuccess)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerHome/module.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerHome/Home/HomeServlet.java`: class declaration / fields.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerHome/Home/HomeServletPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerHome/DMHomeService.js`: `/main/appconfig`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataManagerInstruments

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerInstruments`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/actions/add/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/actions/clone/CloneInstrumentCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/actions/clone/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/actions/massEdit/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/controllers/InstrumentsCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerInstruments/services/InstrumentService.js`: `/instruments/addInstrument`, `/instruments/clone`, `/instruments/load`, `/instruments/removeInstrument`, `/instruments/save`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataManagerLog

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerLog`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerLog/DMDataLogCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerLog/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataManagerSessions

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerSessions`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerSessions/actions/add/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerSessions/actions/clone/CloneSessionCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerSessions/actions/clone/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerSessions/controllers/SessionsCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerSessions/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerSessions/services/SessionService.js`: `addSession(template)`, `removeSession(names)`, `updateSession(template)`, `save(data)`, `load(data)`, `clone(data, callback)`.

Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerSessions/Sessions/SessionsServlet.java`: `run()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerSessions/Sessions/SessionsServletPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataManagerSessions/services/SessionService.js`: `/sessions/clone`, `/sessions/load`, `/sessions/removeSession`, `/sessions/save`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataSourceCrypto

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceCrypto`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/add/addPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/add/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/DataSourceCryptoService.js`: `getExchanges(callback)`, `getSymbols(exchange, callback)`, `add(data, callback)`, `addCancel()`, `importData(data)`, `importDataAction(symbol, action)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/import/importPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/import/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/module.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/Crypto/DataSourceCryptoPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/Crypto/DataSourceCryptoServlet.java`: `run()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/DataSourceCryptoService.js`: `/dataSourceCrypto/add`, `/dataSourceCrypto/addCancel`, `/dataSourceCrypto/getExchanges`, `/dataSourceCrypto/getSymbols`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataSourceDarwinex

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/add/addPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/add/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/DarwinexService.js`: `loadAvailableSymbols(data, callOnSuccess)`, `importData(data, callOnSuccess)`, `importDataCancel()`, `importDataAction(symbol, action)`, `getData()`, `getSymbolInfo(symbol)`, `addData(postfix, symbols, broker, instruments)`, `dataCancel()`, `downloadData(data)`, `downloadDataAction(symbol, action)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/disclaimer/darwinexDisclaimerCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/disclaimer/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/download/downloadPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **5**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/Darwinex/DarwinexDataManager.java`: `get()`, `getAvailableDataList()`, `suggestSymbols(String symbol)`, `getAvailableDataInfo(String symbol)`, `addData(String symbol, String postfix, int broker, String requiredInstrumentIdent)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/Darwinex/DarwinexPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/Darwinex/DarwinexServlet.java`: `run()`, `run()`, `run()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/Darwinex/importdata/DarwinexImport.java`: `get()`, `stop(String symbol)`, `pause(String symbol)`, `restart(String symbol)`, `importData(ImportInfo importInfo, String path, DataManagerProgressListener listener)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/Darwinex/importdata/DarwinexImportJob.java`: `messageReceived(GridMessage message)`, `setProgressListener(DataManagerProgressListener progressListener)`, `call()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/DarwinexService.js`: `/darwinex/importDataCancel`, `darwinex/importData`, `darwinex/importDataAction`, `darwinex/importDataCancel`, `darwinex/importLoadAvailableSymbols`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataSourceDukascopy

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/add/addPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/add/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/disclaimer/dukascopyDataDisclaimerCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/disclaimer/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/DukascopyService.js`: `getData()`, `getSymbolInfo(symbol)`, `addData(postfix, symbols, dataType, broker, instruments)`, `addCancel()`, `importData(data)`, `importDataAction(symbol, action)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/import/importPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **4**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/Dukascopy/DukasExport.java`: `getDateFrom()`, `setDateFrom(long dateFrom)`, `getDateTo()`, `setDateTo(long dateTo)`, `getTargetFolder()`, `setTargetFolder(String targetFolder)`, `getSymbol()`, `setSymbol(String symbol)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/Dukascopy/DukasServlet.java`: `run()`, `run()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/Dukascopy/DukasServletPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/Dukascopy/LastSymbolDates.java`: class declaration / fields.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/DukascopyService.js`: `/dataSourceDukascopy/addCancel`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataSourceFiles

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/add/DataSourceFilesAddCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/add/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/appImport/DataSourceFilesAppImportCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/appImport/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/DataSourceFilesService.js`: `add(dataDetails)`, `importGetInfo()`, `import(config)`, `importAction(symbol, action)`, `importGetOverview(params)`, `importSaveNewDataFormat(params)`, `importUpdateDataFormat(params, callback)`, `importDeleteDataFormat(formatName, callback)`, `massImport(params, callback)`, `appImport(params, callback)`, `cancelAppImport(params, callback)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/import/DataSourceFilesImportCtrl.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **8**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/Files/DataSourceFilesPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/Files/DataSourceFilesServlet.java`: class declaration / fields.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/Files/job/DataAppImporterJob.java`: `call()`, `validate()`, `messageReceived(GridMessage message)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/Files/job/DataImporter.java`: `performImport(IProgressListener listener, DataInfo dataInfo, ImportDataInfo importInfo)`, `setProgress(int curRecord, int estimatedRecordsTotal)`, `cancel()`, `isCanceled()`, `pause()`, `restart()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/Files/job/DataImporterJob.java`: `call()`, `messageReceived(GridMessage message)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/Files/job/DataMassImporter.java`: `cancel()`, `isCanceled()`, `performImport()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/Files/job/DataMassImporterChildrenJob.java`: `call()`, `messageReceived(GridMessage message)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/Files/job/DataMassImporterMasterJob.java`: `hasFilesToImport()`, `updateProgress(String message)`, `accept(File arg0)`, `call()`, `messageReceived(GridMessage message)`, `messageReceived(GridMessage message)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceFiles/DataSourceFilesService.js`: `/dataSourceFiles/add`, `/dataSourceFiles/appImport`, `/dataSourceFiles/cancelAppImport`, `/dataSourceFiles/importAction`, `/dataSourceFiles/importDeleteDataFormat`, `/dataSourceFiles/importUpdateDataFormat`, `/dataSourceFiles/massImport`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataSourceMt5Api

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/import/DataSourceMt5ApiImportCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/import/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/module.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/Mt5Api/DataSourceMt5ApiPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `call(String methodName, Object ... parameters)`, `getHandler()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/Mt5Api/DataSourceMt5ApiServlet.java`: `compare(JSONObject o1, JSONObject o2)`, `run()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/DataSourceMt5Api.js`: `dataSourceMt5Api/importData`, `dataSourceMt5Api/importDataAction`, `dataSourceMt5Api/loadAvailableSymbols`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataSourceSQEquityData

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/add/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/add/SQEquityDataAddCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/SQEquityDataService.js`: `getExchanges()`, `add(data, callback)`, `addCancel()`, `lookup(data, callback)`, `update()`, `verifySubscription(callOnSucces)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/update/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/update/SQEquityDataUpdateCtrl.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/SQEquityData/SQEquityDataPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/SQEquityData/SQEquityDataServlet.java`: `run()`, `getTickStep(TickerDto ticker)`, `getTickSize(TickerDto ticker)`, `getPointValue(TickerDto ticker)`, `getInstrumentType(TickerDto ticker)`, `getDescriptions(TickerDto ticker)`, `getOrderSizeMultiplier(TickerDto ticker)`, `getOrderSizeStep(TickerDto ticker)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/SQEquityDataService.js`: `/sqEquityData/add`, `/sqEquityData/addCancel`, `/sqEquityData/getExchanges`, `/sqEquityData/lookup`, `/sqEquityData/update`, `/sqEquityData/verifySubscription`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataSourceSQFuturesData

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/add/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/add/SQFuturesDataAddCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/SQFuturesDataService.js`: `getExchanges()`, `add(data, callback)`, `addCancel()`, `lookup(data, callback)`, `update()`, `updateBr()`, `verifySubscription(callOnSucces)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/update/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/update/SQFuturesDataUpdateCtrl.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/SQFuturesData/SQFuturesDataPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/SQFuturesData/SQFuturesDataServlet.java`: `run()`, `getTickStep(TickerDto ticker)`, `getTickSize(TickerDto ticker)`, `getPointValue(TickerDto ticker)`, `getInstrumentType(TickerDto ticker)`, `getDescriptions(TickerDto ticker)`, `getOrderSizeMultiplier(TickerDto ticker)`, `getOrderSizeStep(TickerDto ticker)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/SQFuturesDataService.js`: `/sqFuturesData/add`, `/sqFuturesData/addCancel`, `/sqFuturesData/getExchanges`, `/sqFuturesData/lookup`, `/sqFuturesData/update`, `/sqFuturesData/updateBr`, `/sqFuturesData/verifySubscription`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataSourceTD

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceTD`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceTD/DataSourceTDService.js`: `loadAvailableSymbols(data, callOnSuccess)`, `importData(data, callOnSuccess)`, `importDataAction(symbol, action)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceTD/import/DataSourceTDImportCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceTD/import/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceTD/module.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **4**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceTD/TD/DataSourceTDPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceTD/TD/DataSourceTDServlet.java`: class declaration / fields.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceTD/TD/job/ImportFileJob.java`: `messageReceived(GridMessage message)`, `accept(File dir, String name)`, `setProgressListener(DataManagerProgressListener progressListener)`, `call()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceTD/TD/TDDataManager.java`: `get()`, `stopTDImport(String symbol)`, `pauseTDImport(String symbol)`, `restartTDImport(String symbol)`, `importTDData(ImportInfo importInfo, String path, DataManagerProgressListener listener)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceTD/DataSourceTDService.js`: `dataSourceTD/importData`, `dataSourceTD/importDataAction`, `dataSourceTD/loadAvailableSymbols`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DataSourceYahoo

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceYahoo`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/add/addPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/add/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/download/downloadPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/download/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/YahooService.js`: `add(data, callOnSuccess)`, `addCancel()`, `importData(data)`, `importDataAction(symbol, action)`.

Available recovered primary Java files: **4**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/Yahoo/DataSourceYahooPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/Yahoo/DataSourceYahooServlet.java`: `run()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/Yahoo/YahooDataManager.java`: `get()`, `addData(String symbol, String postfix, byte dataType, String description, String exchange)`, `downloadInfo(String name)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/Yahoo/YahooSymbol.java`: class declaration / fields.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/YahooService.js`: `/dataSourceYahoo/addCancel`, `dataSourceYahoo/add`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ServletConnection

Owning order: `03-AppDataManager.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ServletConnection`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/datalib/data/DataManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## AppCodeEditor

Owning order: `04-AppCodeEditor.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/AppCodeEditor`.

- `DONOR_REFERENCE_ROOT/internal/plugins/AppCodeEditor/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/lib/snippets/SnippetsCompiler.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/indicatorTester/IndicatorCalibrator.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CodeEditorImportExport

Owning order: `04-AppCodeEditor.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/export/controllers/CEExportPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/export/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/import/controllers/CEImportCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/import/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/ImportExportService.js`: `import(files, callback)`, `export(files, targetPath, callback)`, `listFiles(filter, callback)`, `onOverwrite()`, `onOverwriteAlways()`, `onSkip()`, `onSkipAlways()`, `onCancel()`, `IDsToPaths(ids, treeObj)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/module.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **4**.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/ImportExport/ExtensionManager.java`: `install(String[] filePaths)`, `export(String[] filePaths, String targetPath)`, `overwrite()`, `overwriteAlways()`, `skip()`, `skipAlways()`, `cancelImport()`, `run()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/ImportExport/ExtensionsFileMap.java`: `generateTree(Map<String, String> sourceDirs, String filter, int startIndex)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/ImportExport/ImportExportPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/ImportExport/ImportExportServlet.java`: class declaration / fields.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/lib/snippets/SnippetsCompiler.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/indicatorTester/IndicatorCalibrator.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorImportExport/ImportExportService.js`: `/importexport/cancel`, `/importexport/export`, `/importexport/list`, `/importexport/overwrite`, `/importexport/overwriteAlways`, `/importexport/skip`, `/importexport/skipAlways`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CodeEditorIndicatorTester

Owning order: `04-AppCodeEditor.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/controllers/IndicatorTesterCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/services/IndicatorTesterService.js`: `reloadIndicators(callback)`, `getIndicators(callback)`, `addTests(indicators, xmlConfig, grid)`, `createNewConfig(config, grid, callback)`, `startTesting(xmlConfig)`, `stopTesting()`, `downloadTests(callback)`, `loadConfig(config, grid, filePath, callback)`, `reloadGrid(grid, xmlConfig)`, `updateRowStyle(grid, rowIndex)`, `formatParameters(indicatorName, parameters, shift)`, `getRawParameters(parameters)`.

Available recovered primary Java files: **5**.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/IndicatorTester/DownloadProgressPublisher.java`: `get()`, `setMessage(String message)`, `onProgress(double percent)`, `onError(String errorMsg)`, `resetLastData()`, `onStart()`, `onFinish()`, `onConfirm(String confirmMsg)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/IndicatorTester/IndicatorTesterPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/IndicatorTester/IndicatorTesterServlet.java`: `getInstance()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/IndicatorTester/IndicatorTestExecutor.java`: `get()`, `start()`, `run()`, `stop()`, `getData()`, `resetLastData()`, `getRunningStatus()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/IndicatorTester/IndicatorTestsDownloader.java`: `downloadTests(final IProgressListener listener)`, `run()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/lib/snippets/SnippetsCompiler.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/indicatorTester/IndicatorCalibrator.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/CodeEditorIndicatorTester/services/IndicatorTesterService.js`: `indyTester/addTests`, `indyTester/createNewConfig`, `indyTester/downloadTests`, `indyTester/listIndicators`, `indyTester/loadConfig`, `indyTester/saveConfig`, `indyTester/startTesting`, `indyTester/stopTesting`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ServletCodeEditor

Owning order: `04-AppCodeEditor.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/directives/bottomtabs/BottomTabsCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/directives/bottomtabs/logpane/LogPaneCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/directives/bottomtabs/searchpane/SearchPaneCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/directives/maintabs/MainTabsCtrl.js`: `add(file,
        name,
        text,
        select,
        _protected,
        dontNotifyTabsChange,
        callback)`, `getActiveTab()`, `getTabsOrig()`, `getTabs()`, `getEditors()`, `selectTab(file)`, `closeTab(file)`, `getTab(file)`, `undo()`, `redo()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/directives/righttabs/editors/EditorsCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/directives/righttabs/navigator/NavigatorCtrl.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **13**.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/CodeEditor/CodeAutoCompleteManager.java`: `getData()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/CodeEditor/CodeEditorInfoSender.java`: `getData()`, `sendData(JSONObject data)`, `resetLastData()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/CodeEditor/CodeEditorPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/CodeEditor/CodeEditorServlet.java`: `deleteRecursive(File file, List<String> deletedFiles)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/CodeEditor/CodeEditorServletException.java`: class declaration / fields.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/CodeEditor/FileMap.java`: `getCodeBlocksTypes()`, `searchForMissingTemplateFiles()`, `generateTree(Map<String, String> sourceDirs, String filter, int startIndex)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/CodeEditor/searchInFiles/SearchInFiles.java`: `search(Map<String, String> sourceDirs, String text, boolean caseSensitive, boolean regex, boolean wholeWord)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/CodeEditor/searchInFiles/SearchInFilesResult.java`: `getItems()`, `getTotalMatchesCount()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/lib/snippets/SnippetsCompiler.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/indicatorTester/IndicatorCalibrator.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ServletCodeEditor/services/CodeEditorService.js`: `codeeditor/clone`, `codeeditor/compile`, `codeeditor/compileAll`, `codeeditor/compilePlugin`, `codeeditor/createNew`, `codeeditor/createNewDir`, `codeeditor/createNewFile`, `codeeditor/createNewTemplate`, `codeeditor/delete`, `codeeditor/editorAutocomplete`, `codeeditor/findInFiles`, `codeeditor/fixImports`, `codeeditor/getContent`, `codeeditor/listCodeTypes`, `codeeditor/listIndicators`, `codeeditor/listTemplates`, `codeeditor/loadLastOpenedFiles`, `codeeditor/reload`, `codeeditor/reloadApp`, `codeeditor/rename`, `codeeditor/save`, `codeeditor/saveAs`, `codeeditor/saveLastOpenedFiles`, `codeeditor/stopCompilation`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## AppWizard

Owning order: `05-AppWizard.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/AppWizard`.

- `DONOR_REFERENCE_ROOT/internal/plugins/AppWizard/AlgoWizardService.js`: `waitForInternalEventHandlerAttached()`, `captureStrategyXML()`, `getLastBacktestID(strategyName)`, `getSymbols()`, `loadExamples(callOnSuccess)`, `loadExample(data, callOnSuccess)`, `showSuccess(message)`, `showError(message)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/AppWizard/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/business/loader/StrategyLoader.java`; `DONOR_REFERENCE_ROOT/internal/libs/business/loader/TransformEngineLoader.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/AppWizard/AlgoWizardService.js`: `/AlgoWizard/examples/examples.json`, `/algowizard/loadExample`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ServletAlgoCloud

Owning order: `05-AppWizard.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ServletAlgoCloud`.


Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletAlgoCloud/AlgoCloud/AlgoCloudServlet.java`: class declaration / fields.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletAlgoCloud/AlgoCloud/AlgoCloudServletPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/business/loader/StrategyLoader.java`; `DONOR_REFERENCE_ROOT/internal/libs/business/loader/TransformEngineLoader.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ServletAlgoWizard

Owning order: `05-AppWizard.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard`.


Available recovered primary Java files: **4**.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard/AlgoWizard/AlgoWizardBlocksTagCloud.java`: `listJSON()`, `save(String blockKey, String blockType, String blockParams)`, `_save(String blockKey, String blockType, String blockParams)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard/AlgoWizard/AlgoWizardRecentFiles.java`: `list()`, `listJSON()`, `save(String recentFile)`, `_save(String recentFile)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard/AlgoWizard/AlgoWizardServlet.java`: class declaration / fields.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletAlgoWizard/AlgoWizard/AlgoWizardServletPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/business/loader/StrategyLoader.java`; `DONOR_REFERENCE_ROOT/internal/libs/business/loader/TransformEngineLoader.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ServletConstants

Owning order: `05-AppWizard.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ServletConstants`.


Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletConstants/Constants/ConstantsServlet.java`: `getInstance()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletConstants/Constants/ConstantsServletPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/business/loader/StrategyLoader.java`; `DONOR_REFERENCE_ROOT/internal/libs/business/loader/TransformEngineLoader.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ServletStrategy

Owning order: `05-AppWizard.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ServletStrategy`.


Available recovered primary Java files: **3**.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletStrategy/Strategy/MyStrategy.java`: `Initialize()`, `OnBarUpdate()`, `callOnInit(TradingSetup tradingSetup)`, `getATRValue(ChartData chartData, int atrPeriod, int shift)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletStrategy/Strategy/StrategyServlet.java`: `getInstance()`, `onList()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ServletStrategy/Strategy/StrategyServletPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/business/loader/StrategyLoader.java`; `DONOR_REFERENCE_ROOT/internal/libs/business/loader/TransformEngineLoader.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## AppResults

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/AppResults`.

- `DONOR_REFERENCE_ROOT/internal/plugins/AppResults/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CustomDatabankActions

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CustomDatabankActions`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CustomDatabankActions/delete/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CustomDatabankActions/moveLeft/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CustomDatabankActions/moveRight/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CustomDatabankActions/moveToPosition/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CustomDatabankActions/rename/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CustomDatabankActions/rename/RenameDatabankPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CustomResultsPluginActions

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CustomResultsPluginActions`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CustomResultsPluginActions/delete/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CustomResultsPluginActions/rename/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CustomResultsPluginActions/rename/RenameResultsPluginPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DatabankFilterByCorrelation

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DatabankFilterByCorrelation`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DatabankFilterByCorrelation/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## DatabankRename

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/DatabankRename`.

- `DONOR_REFERENCE_ROOT/internal/plugins/DatabankRename/ui/DatabankRenamePopupCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/DatabankRename/ui/module.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/DatabankRename/src/com/strategyquant/plugin/Databank/impl/Rename/DatabankRenamePlugin.java`: `getHandler()`, `getProduct()`, `getPreferredPosition()`, `initPlugin()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/DatabankRename/src/com/strategyquant/plugin/Databank/impl/Rename/DatabankRenameServlet.java`: class declaration / fields.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/DatabankRename/ui/DatabankRenamePopupCtrl.js`: `/databank/rename`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## EquityChartBenchmark

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/EquityChartBenchmark`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## EquityChartDailyChart

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/EquityChartDailyChart`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## EquityChartDrawdown

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/EquityChartDrawdown`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## EquityChartVolatility

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/EquityChartVolatility`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## EquityChartVolume

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/EquityChartVolume`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## LoaderSQ3

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/LoaderSQ3`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## LoaderSQ4

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/LoaderSQ4`.


Available recovered primary Java files: **1**.
- `DONOR_REFERENCE_ROOT/internal/plugins/LoaderSQ4/SQ4/SQ4LoaderPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getFileExtensions()`, `load(String fileName, boolean exceptionOnMissingInstrument, String missingInstrumentReplacement, String userSecretCode)`, `finishLoad(ResultsGroup result)`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsChart

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsChart`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsChart/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsChart/ResultsChartCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsChart/ResultsChartService.js`: `cancelLoading()`, `loadChartData(params)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsDatabankActions

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/clearAll/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActionsService.js`: `getSelectedStrategy()`, `getStrategyXml(data, callOnSuccess)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/delete/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/load/loadBtnCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/load/LoadPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/load/LoadService.js`: `addAlias(alias, callOnSuccess)`, `addInstrument(instrumentDetails, callOnSuccess)`, `instrumentSelected(data)`, `subscribeToProgressChannel()`.

Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActions/DatabankActionsPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `call(String methodName, Object ... parameters)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActions/DatabankActionsServlet.java`: `run()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/DatabankActionsService.js`: `resultsDatabankActions/getStrategyXml`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/load/LoadService.js`: `/instruments/addAlias`, `/instruments/addInstrument`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/retest/RetestDialogCtrl.js`: `project/retest`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/save/exportCSV/CSVExportService.js`: `resultsDatabankActions/exportDatabankToCSV`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/save/SaveButtonService.js`: `dirs/setLastFolderUsed`, `project/saveReports`, `project/saveSingleFileJava`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/sync/DatabankSyncService.js`: `project/setDatabankSynchronization`, `project/synchronizeDatabank`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/tools/compareStrategies/CompareStrategiesService.js`: `resultsDatabankActions/compareStrategies`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankActions/tools/edit/editParameters/EditParametersService.js`: `resultsDatabankActions/getStrategyParameters`, `resultsDatabankActions/setStrategyParameters`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsDatabankViews

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews/DatabankViewsCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews/DatabankViewsService.js`: `removeView(name, callback)`, `addView(viewXML, callback)`, `updateView(viewXML, callback)`, `changeView(projectName, databankName, viewName, callback)`, `getColumnText(column, direction, sampleType, resultType, chartSetup, chartSetupValue)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsDatabankViews/DatabankViewsService.js`: `/dbviews/addView`, `/dbviews/changeView`, `/dbviews/removeView`, `/dbviews/updateView`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsEquityChart

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsEquityChart`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/benchmark/BenchmarkCtrl.js`: `print(data)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/EquityChartCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/EquityChartService.js`: `print(data, callback)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/EquityChartCtrl.js`: `/main/openlink`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsEquityChart/EquityChartService.js`: `equitychart/print`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsExplore

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsExplore`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsExplore/ExploreCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsExplore/ExploreService.js`: `info(data, callOnSuccess)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsExplore/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsExplore/ExploreService.js`: `explore/info`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsOverview

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsOverview`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsOverview/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsOverview/ResultsOverviewCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsOverview/ResultsOverviewService.js`: `getOverviewContent(params)`.

Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsOverview/Overview/OverviewServlet.java`: `getTemplates()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsOverview/Overview/OverviewServletPlugin.java`: `getProduct()`, `getPreferredPosition()`, `initPlugin()`, `getHandler()`, `containsResult(ResultsGroup rg)`, `getKey()`, `getInitializationData()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsPlugins

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPlugins`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPlugins/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPlugins/PluginIframeCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPlugins/ResultsPluginsService.js`: `listPlugins(callback)`, `createPlugin(pluginName, callback)`, `renamePlugin(pluginName, newName, callback)`, `deletePlugin(pluginName, callback)`, `getStats(params, callback)`, `getOrders(params, callback)`, `getLastSettingsXml(params, callback)`, `getSourceCode(params, callback)`, `getDatabankStrategies(params, callback)`, `getStrategyStats(params, callback)`, `getStrategyOrders(params, callback)`, `getStrategyResultKeys(params, callback)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPlugins/ResultsPluginsService.js`: `resultsPlugins/candles`, `resultsPlugins/create`, `resultsPlugins/dataSymbols`, `resultsPlugins/databankStrategies`, `resultsPlugins/delete`, `resultsPlugins/list`, `resultsPlugins/orders`, `resultsPlugins/rename`, `resultsPlugins/settings`, `resultsPlugins/stats`, `resultsPlugins/strategyOrders`, `resultsPlugins/strategyResultKeys`, `resultsPlugins/strategyStats`, `sourcecode/print`, `sqai/complete`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsPortfolioCorrelation

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/PortfolioCorrelationCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/PortfolioCorrelationService.js`: `compute(data, callOnSuccess)`, `stop()`, `correlationSave(data, callOnSuccess)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/tabs/correlationMatrix/CorrelationMatrixCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/tabs/overlappingTrades/OverlappingTradesCtrl.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsPortfolioCorrelation/PortfolioCorrelationService.js`: `portfoliocorrelation/compute`, `portfoliocorrelation/correlationSave`, `portfoliocorrelation/stop`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsProfileChart

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsProfileChart`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/ProfileChartCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/ProfileChartService.js`: `getPaths(params, callback)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/ProfileChartService.js`: `profilechart/paths`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsReport

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsReport`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsReport/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsReport/ReportCtrl.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsSourceCode

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSourceCode`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/SourceCodeCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/SourceCodeService.js`: `init(data)`, `loadParamsConfig()`, `setParamsConfig()`, `print(params, callOnSuccess)`, `getDataPath(installPath, isMT4, callback)`, `saveMTPaths(brokerObj, callback)`, `saveEA(mt4)`, `saveWFCalendar(filePath)`, `getGenerator()`, `isAlgoWizardApp()`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSourceCode/SourceCodeService.js`: `sourcecode/getDataPath`, `sourcecode/print`, `sourcecode/saveEA`, `sourcecode/saveMTPaths`, `sourcecode/saveWFCalendar`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsSPOverview

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSPOverview`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/directives/spOverviewList/SPOverviewListCtrl.js`: `init()`, `print(data)`, `reset()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/directives/spOverviewStats/SPOverviewStatsCtrl.js`: `init()`, `print(data)`, `reset()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/directives/spOverviewTopChart/SPOverviewTopChartCtrl.js`: `init(color)`, `print(data)`, `reset()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/directives/spOverviewTreeMap/SPOverviewTreeMapCtrl.js`: `init()`, `print(data)`, `reset()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/SPOverviewCtrl.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsSPOverview/SPOverviewService.js`: `spoverview/print`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsStockpicker

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsStockpicker`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsStockpicker/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsStockpicker/StockpickerCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsStockpicker/StockpickerService.js`: `print(data, callOnSuccess)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsStockpicker/StockpickerService.js`: `stockpicker/print`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsStrategyConfig

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig/StrategyConfigCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig/StrategyConfigService.js`: `print(data, callback)`, `loadStrategySettings(data, callOnSuccess)`, `loadTasks(isTaskManager, projectName, callback)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsStrategyConfig/StrategyConfigService.js`: `strategyconfig/loadStrategySettings`, `strategyconfig/print`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsTradeAnalysis

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis/controllers/TradeAnalysisCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis/directives/TradeAnalysisPanelCtrl.js`: `print(data)`, `setSelectedType(type)`, `getSelectedType()`, `reset()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis/services/TradeAnalysisService.js`: `print(data, callOnSuccess)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradeAnalysis/services/TradeAnalysisService.js`: `tradeanalysis/print`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsTradeList

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradeList`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradeList/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradeList/ResultsTradelistCtrl.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsTradelistViews

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradelistViews`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradelistViews/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradelistViews/TradelistViewsCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradelistViews/TradelistViewsService.js`: `removeView(name)`, `addView(viewXML)`, `updateView(viewXML)`, `changeView(viewName)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsTradelistViews/TradelistViewsService.js`: `/tradelistviews/changeView`, `/tradelistviews/removeView`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## SaverHTML

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/SaverHTML`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## SaverPDF

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/SaverPDF`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## SaverSQ3

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/SaverSQ3`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## SaverStrategyTrades

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/SaverStrategyTrades`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ServletRenameTool

Owning order: `06-AppResults.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ServletRenameTool`.


No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/results/stats/StatsComputer.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/file/SQFileManager.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## AppRetester

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/AppRetester`.

- `DONOR_REFERENCE_ROOT/internal/plugins/AppRetester/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CrossCheckMonteCarloManipulation

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/FitnessFunction/MCManipulationFitnessCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/FitnessFunction/MCManipulationFitnessService.js`: `list(callback)`, `getLevels(callOnSuccess)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/FitnessFunction/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/MonteCarloManipulationCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/MonteCarloManipulationService.js`: `list(callOnSuccess)`, `applySettings(settingsElem, config)`, `loadSettings(settingsElem, config)`, `getInfo(settingsElem)`, `getShortInfo(settingsElem)`, `getAverageDuration(settingsElem)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/FitnessFunction/MCManipulationFitnessService.js`: `monteCarloManipulation/fitnessGetConfidenceLevels`, `monteCarloManipulation/fitnessList`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloManipulation/MonteCarloManipulationService.js`: `monteCarloManipulation/list`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CrossCheckMonteCarloRetest

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/FitnessFunction/MCRetestFitnessCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/FitnessFunction/MCRetestFitnessService.js`: `list(callback)`, `getLevels(callOnSuccess)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/FitnessFunction/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/MonteCarloRetestCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/MonteCarloRetestService.js`: `list(callOnSuccess)`, `applySettings(settingsElem, config)`, `loadSettings(settingsElem, config)`, `getInfo(settingsElem)`, `getShortInfo(settingsElem)`, `getAverageDuration(settingsElem)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/FitnessFunction/MCRetestFitnessService.js`: `monteCarloRetest/fitnessGetConfidenceLevels`, `monteCarloRetest/fitnessList`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckMonteCarloRetest/MonteCarloRetestService.js`: `monteCarloRetest/list`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CrossCheckOptProfileSysParamPermutation

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/OptProfileSysParamPermutationCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckOptProfileSysParamPermutation/OptProfileSysParamPermutationService.js`: `applySettings(settingsElem, config)`, `loadSettings(settingsElem, config)`, `getInfo(settingsElem)`, `getShortInfo(settingsElem)`, `getAverageDuration(settingsElem)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CrossCheckRetestOnAdditionalMarkets

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/FitnessFunction/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/FitnessFunction/PortfolioFitnessCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/FitnessFunction/PortfolioFitnessService.js`: `list(callback)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/RetestOnAdditionalMarketsCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/RetestOnAdditionalMarketsService.js`: `getMainSetup()`, `applySettings(settingsElem, config)`, `loadSettings(settingsElem, config)`, `getInfo(settingsElem)`, `getShortInfo(settingsElem, dontCutSymbolNames)`, `getAverageDuration(settingsElem)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestOnAdditionalMarkets/FitnessFunction/PortfolioFitnessService.js`: `retestOnAdditionalMarkets/list`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CrossCheckRetestWithHigherPrecision

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/FitnessFunction/CCHigherPrecisionCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/FitnessFunction/CCHigherPrecisionService.js`: `list(callback)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/FitnessFunction/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/RetestWithHigherPrecisionCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/RetestWithHigherPrecisionService.js`: `loadConfig(config)`, `loadSettings(settingsElem, config)`, `applySettings(settingsElem, config)`, `getInfo(settingsElem)`, `getShortInfo(settingsElem)`, `getAverageDuration(settingsElem)`, `getSymbolData(symbol)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckRetestWithHigherPrecision/FitnessFunction/CCHigherPrecisionService.js`: `retestWithHigherPrecision/list`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CrossCheckSequentialOptimization

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/SequentialOptimizationCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckSequentialOptimization/SequentialOptimizationService.js`: `applySettings(settingsElem, config)`, `loadSettings(settingsElem, config)`, `getInfo(settingsElem)`, `getShortInfo(settingsElem)`, `getAverageDuration(settingsElem)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CrossCheckWalkForwardMatrix

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/WalkForwardMatrixCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardMatrix/WalkForwardMatrixService.js`: `applySettings(settingsElem, config)`, `loadSettings(settingsElem, config)`, `getInfo(settingsElem)`, `getShortInfo(settingsElem)`, `getAverageDuration(settingsElem)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CrossCheckWalkForwardOptimization

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/WalkForwardOptimizationCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWalkForwardOptimization/WalkForwardOptimizationService.js`: `applySettings(settingsElem, config)`, `loadSettings(settingsElem, config)`, `getInfo(settingsElem)`, `getShortInfo(settingsElem)`, `getAverageDuration(settingsElem)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## CrossCheckWhatIf

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf`.

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/WhatIfCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/WhatIfService.js`: `list(callOnSuccess)`, `applySettings(settingsElem, config)`, `loadSettings(settingsElem, config)`, `getInfo(settingsElem)`, `getShortInfo(settingsElem)`, `getAverageDuration(settingsElem)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/CrossCheckWhatIf/WhatIfService.js`: `whatIf/list`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ResultsRobustnessTests

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/directives/manageviews/ManageViewsCtrlRt.js`: `getSelectedViewName()`, `getSelectedView()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/directives/manageviews/ManageViewsService.js`: `loadViews(type, callback)`, `removeView(name, type)`, `addView(viewXML, type)`, `updateView(viewXML, type)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/directives/robustnessAnalysis/RobustnessAnalysisCtrl.js`: `print(data)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/RobustnessTestsResultsCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/services/RTService.js`: `printChart(data, callOnSuccess)`, `printConfLevels(data, callOnSuccess)`, `getMethods(data, callback)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/directives/manageviews/ManageViewsService.js`: `rtresults/viewsGetViews`, `rtresults/viewsRemoveView`.
- `DONOR_REFERENCE_ROOT/internal/plugins/ResultsRobustnessTests/services/RTService.js`: `rtresults/getMethods`, `rtresults/printChart`, `rtresults/printConfLevels`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## SettingsAutoRetestData

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData`.

- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/AutoRetestDataCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/AutoRetestDataService.js`: `loadDataConfig(forceReload)`, `changeSetupDetails(oldSymbol)`, `getSymbolDateRange(selectedSymbol)`, `correctSetupSymbolNames(setup, oldSymbolName, newSymbolName)`, `correctSubcharts()`, `saveConfig()`, `correctPrecision(precision)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsAutoRetestData/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## SettingsCrossChecks

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks`.

- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/crosscheck/CrossCheckCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossCheckAcceptanceSettingsCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossCheckAcceptanceSettingsService.js`: `getDefaultWFConditions(data, callOnSuccess)`, `getDefaultSPPConditions(callOnSuccess)`, `applySettings(acceptSettingsElem, config, crosscheckName)`, `loadSettings(acceptSettingsElem, config, crosscheckName)`, `getAcceptanceSettingsInfo(acceptSettingsElem, crosscheckName)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossChecksCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossChecksService.js`: `list(callOnSuccess, forceReload)`, `loadConfig()`, `saveConfig()`, `saveSettings(crossCheckName, settingsElem, acceptSettingsElem)`, `createElement(name)`, `getCrossChecksElem()`, `getSettingsElem(crossCheckName, settingName)`, `getAverageDuration(backtestsCount, useMainSetup, elSetups, customPrecision)`, `get(crossCheckName)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsCrossChecks/CrossCheckAcceptanceSettingsService.js`: `optProfileSysParamPerm/getDefaultSPPConditions`, `rankingsettings/getDefaultWFConditions`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## SettingsWhatToRetest

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest`.

- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/SettingsWhatToRetestCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToRetest/SettingsWhatToRetestService.js`: `loadAvailableDatabanks(callback)`, `loadSettings()`, `saveSettings()`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## TaskRetest

Owning order: `07-AppRetester.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/TaskRetest`.

- `DONOR_REFERENCE_ROOT/internal/plugins/TaskRetest/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskRetest/simpleSettings/SimpleRetestSettingsCtrl.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **2**.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskRetest/Retest/RetestJob.java`: `call()`, `messageReceived(GridMessage message)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskRetest/Retest/RetestTask.java`: `beforeStart()`, `start()`, `messageReceived(GridMessage message)`, `run()`, `onStatusChanged(int status)`, `getType()`, `getPluginFolderName()`, `getName()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/crosscheck/CrossCheckRunner.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/backtestrunner/BacktestRunner.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## AppBuilder

Owning order: `08-AppBuilder.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/AppBuilder`.

- `DONOR_REFERENCE_ROOT/internal/plugins/AppBuilder/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/gp/GPSettings.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/generator/StrategyGenerator.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## FitnessMethodStrategyResult

Owning order: `08-AppBuilder.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult`.

- `DONOR_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResultCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResultService.js`: `list(callback)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/gp/GPSettings.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/generator/StrategyGenerator.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/FitnessMethodStrategyResult/FitnessMethodStrategyResultService.js`: `fitnessMethodStrategyResult/list`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## ServletBuilder

Owning order: `08-AppBuilder.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/ServletBuilder`.

- `DONOR_REFERENCE_ROOT/internal/plugins/ServletBuilder/module.js`: registration/configuration source; no `this` method declaration matched.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/gp/GPSettings.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/generator/StrategyGenerator.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## SettingsBlocks

Owning order: `08-AppBuilder.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsBlocks`.

- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsBlocks/BlocksCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsBlocks/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsBlocks/services/BlocksService.js`: `init()`, `loadSettings(callback)`, `disableAllBlocks()`, `loadSettingsFromFile(filePath)`, `saveSettingsToFile(filePath)`, `loadCustomData(reloadGrid)`, `initOrderTypesGrid()`, `initExitTypesGrid()`, `initBlocksGrid()`, `initIndicatorsGrid()`, `initStopLimitBlocksGrid()`, `initCustomDataGrid()`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/gp/GPSettings.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/generator/StrategyGenerator.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsBlocks/services/BlocksService.js`: `blocks/list`, `blocks/loadFromFile`, `blocks/saveToFile`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## SettingsGeneticOptions

Owning order: `08-AppBuilder.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions`.

- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/SettingsGeneticOptionsCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsGeneticOptions/SettingsGeneticOptionsService.js`: `loadSettings()`, `saveSettings()`, `checkIPSettings()`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/gp/GPSettings.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/generator/StrategyGenerator.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## SettingsPartsToImprove

Owning order: `08-AppBuilder.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove`.

- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/PartsToImproveCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsPartsToImprove/PartsToImproveService.js`: `init()`, `getConditionText(condition)`, `updateMarketSides()`, `saveConfig()`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/gp/GPSettings.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/generator/StrategyGenerator.java`.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## SettingsRankings

Owning order: `08-AppBuilder.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsRankings`.

- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsRankings/FitnessFunction/FitnessFunctionCtrl.js`: `applySettings(key, settingsElem)`, `resetSettings()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsRankings/FitnessFunction/FitnessFunctionService.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsRankings/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsRankings/RankingCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsRankings/RankingService.js`: `getDefaultWFConditions(data, callOnSuccess)`, `applySettings()`, `isDatabankInput()`, `onMaxStrategiesChanged(maxRecords, callback)`, `saveConfig()`, `checkFitPortfolioSettings()`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/gp/GPSettings.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/generator/StrategyGenerator.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsRankings/RankingService.js`: `project/changeMaxRecords`, `rankingsettings/getDefaultWFConditions`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## SettingsWhatToBuild

Owning order: `08-AppBuilder.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild`.

- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/views/settings/buildMode/BuildModeCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/views/settings/buildMode/BuildModeService.js`: `loadSettings()`, `checkSettings()`, `saveSettings(whatToBuildElem)`, `resetSettings(useOldSettings)`, `getDescription()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/views/settings/buildMode/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/views/settings/conditionsAndPeriods/ConditionsAndPeriodsCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/views/settings/conditionsAndPeriods/ConditionsAndPeriodsService.js`: `loadSettings()`, `checkSettings()`, `saveSettings(whatToBuildElem)`, `resetSettings(useOldSettings)`, `getDescription(settingName)`.

No matching previously recovered primary Java directory was found for this module. The module JAR or frontend files alone do not prove a complete readable backend body.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/gp/GPSettings.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/generator/StrategyGenerator.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/SettingsWhatToBuild/WhatToBuildService.js`: `buildType/getTemplateConfig`, `buildType/listFiles`, `project/checkTemplateResources`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.

## TaskBuild

Owning order: `08-AppBuilder.md`. Current source folder: `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild`.

- `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/BuildTaskService.js`: `loadSettings()`, `calibrate(symbols, timeframes, maxSteps, engine, callback)`, `saveSettings(config)`, `getStrategyTypeInfo(strategyType)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/indicatorsCalibration/IndicatorsCalibrationPopupCtrl.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/module.js`: registration/configuration source; no `this` method declaration matched.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/simpleSettings/SimpleBuildSettingsCtrl.js`: registration/configuration source; no `this` method declaration matched.

Available recovered primary Java files: **7**.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/Build/ArtificalBuilderJob.java`: `call()`, `generateTestOrders(int size)`, `messageReceived(GridMessage message)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/Build/BuilderJob.java`: `call()`, `messageReceived(GridMessage message)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/Build/BuildStopConditionsChecker.java`: `shouldStop(Databank outputDatabank, SettingsMap settings, ProgressEngine progressEngine, ProjectRunInfo projectRunInfo)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/Build/BuildTask.java`: `beforeStart()`, `start()`, `finished(int reason)`, `getType()`, `getName()`, `clone(String projectName, ProgressEngine progressEngine)`, `getPluginFolderName()`, `getPreferredPosition()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/Build/GeneticBuildEngine.java`: `newCandidate(Node candidate)`, `evolutionMessage(GPEvolutionMessage data)`, `lastPopulation(GPEvolutionPopulationMessage data)`, `evolutionException(Serializable data)`, `finished(int reason)`, `testRun()`, `start()`, `shouldStop()`.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/Build/IBuildEngine.java`: `testRun()`, `start()`, `setFinishListener(IGPFinishedListener var1)`, `destroy()`, `getFinishSent()`, `setStrategyNamePrefix(String var1)`.
- `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/Build/RandomBuildEngine.java`: `run()`, `testRun()`, `start()`, `setFinishListener(IGPFinishedListener finishedListener)`, `onStatusChanged(int status)`, `messageReceived(GridMessage message)`, `destroy()`, `getFinishSent()`.

Shared-library context (responsibility only): `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/gp/GPSettings.java`; `DONOR_REFERENCE_ROOT/internal/libs/tradinglib/generator/StrategyGenerator.java`.

**Additional observed client action vocabulary:**

- `DONOR_REFERENCE_ROOT/internal/plugins/TaskBuild/BuildTaskService.js`: `indyTester/calibrate`.

These are literal client request actions; omitted HTTP method arguments use BackendService defaults and are not inferred here. A forwarded `data`/`details` object is not yet a typed schema.

**Remaining release gate:** reconcile the actual plugin methods and frontend consumers into explicit Python request/result models; select persistence/error/cancellation semantics and add deterministic success and failure fixtures. External connector contracts additionally need an offline transport adapter and response fixtures; discovery of source is not proof that the historical remote endpoint is operational.


## Extension and export category reassessment

These source counts are observed files, not completed implementation contracts. Concrete parameter/formula review must be separate from directory availability. Existing per-definition ID lists remain the scope checklist.

| Owning document | Category | Readable primary path | Java definitions / template files |
|---|---|---|---:|
| `04-AppCodeEditor.md` | `Blocks` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Blocks` | 670 |
| `04-AppCodeEditor.md` | `Calculators` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Calculators` | 7 |
| `04-AppCodeEditor.md` | `ExitMethods` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/ExitMethods` | 5 |
| `04-AppCodeEditor.md` | `Functions` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Functions` | 4 |
| `04-AppCodeEditor.md` | `Internal` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Internal` | 35 |
| `04-AppCodeEditor.md` | `MoneyManagement` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/MoneyManagement` | 12 |
| `04-AppCodeEditor.md` | `RiskManagement` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/RiskManagement` | 1 |
| `04-AppCodeEditor.md` | `TALibIndicators` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/TALibIndicators` | 1 |
| `04-AppCodeEditor.md` | `Trading` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Trading` | 6 |
| `04-AppCodeEditor.md` | `TradingOptions` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/TradingOptions` | 8 |
| `04-AppCodeEditor.md` | `Utils` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Utils` | 1 |
| `05-AppWizard.md` | `EasyLanguage` | `DONOR_REFERENCE_ROOT/internal/extend/Code/EasyLanguage` | 694 |
| `05-AppWizard.md` | `JForex` | `DONOR_REFERENCE_ROOT/internal/extend/Code/JForex` | 602 |
| `05-AppWizard.md` | `MetaTrader4` | `DONOR_REFERENCE_ROOT/internal/extend/Code/MetaTrader4` | 748 |
| `05-AppWizard.md` | `MetaTrader5` | `DONOR_REFERENCE_ROOT/internal/extend/Code/MetaTrader5` | 745 |
| `05-AppWizard.md` | `NinjaTrader` | `DONOR_REFERENCE_ROOT/internal/extend/Code/NinjaTrader` | 698 |
| `05-AppWizard.md` | `PseudoCode` | `DONOR_REFERENCE_ROOT/internal/extend/Code/PseudoCode` | 867 |
| `06-AppResults.md` | `Columns` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Columns` | 160 |
| `06-AppResults.md` | `CustomAnalysis` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/CustomAnalysis` | 2 |
| `06-AppResults.md` | `EngineCharts` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/EngineCharts` | 14 |
| `06-AppResults.md` | `Stats` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Stats` | 7 |
| `07-AppRetester.md` | `Checker` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Checker` | 3 |
| `07-AppRetester.md` | `MonteCarlo` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/MonteCarlo` | 14 |
| `07-AppRetester.md` | `TradeAnalysis` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/TradeAnalysis` | 27 |
| `07-AppRetester.md` | `WhatIf` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/WhatIf` | 15 |
| `08-AppBuilder.md` | `Formulas` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Formulas` | 19 |
| `08-AppBuilder.md` | `Internal` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Internal` | 35 |
| `08-AppBuilder.md` | `Negater` | `DONOR_REFERENCE_ROOT/internal/extend/Snippets/SQ/Negater` | 15 |
