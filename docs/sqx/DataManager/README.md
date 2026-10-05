# DataManager: SQX JAR references

[All workspaces](../README.md)

This folder groups donor archives for research. Except for inspected App registrations, backend ownership is inferred. Shared components can be consumed by multiple workspaces; these documents do not prescribe HaruQuantAI architecture.

## Canonical JAR documents

| JAR | Class entries | Declaration families |
| --- | ---: | --- |
| [AppDataManager.jar](AppDataManager.md) | 1 | `com.strategyquant.plugin.App.impl.DataManager` |
| [CryptoExchangeBinance.jar](CryptoExchangeBinance.md) | 2 | `com.strategyquant.plugin.CryptoExchange.impl.Binance` |
| [CryptoExchangeBinanceCoinM.jar](CryptoExchangeBinanceCoinM.md) | 2 | `com.strategyquant.plugin.CryptoExchange.impl.BinanceCoinM` |
| [CryptoExchangeBinanceUsdtM.jar](CryptoExchangeBinanceUsdtM.md) | 2 | `com.strategyquant.plugin.CryptoExchange.impl.BinanceUsdtM` |
| [CryptoExchangeBitfinex.jar](CryptoExchangeBitfinex.md) | 2 | `com.strategyquant.plugin.CryptoExchange.impl.Bitfinex` |
| [CryptoExchangeCoinbasePro.jar](CryptoExchangeCoinbasePro.md) | 2 | `com.strategyquant.plugin.CryptoExchange.impl.CoinbasePro` |
| [CryptoExchangePoloniex.jar](CryptoExchangePoloniex.md) | 2 | `com.strategyquant.plugin.CryptoExchange.impl.Poloniex` |
| [DataManagerBasket.jar](DataManagerBasket.md) | 3 | `com.strategyquant.plugin.DataManager.impl.Basket` |
| [DataManagerBroker.jar](DataManagerBroker.md) | 6 | `com.strategyquant.plugin.DataManager.impl.Broker` |
| [DataManagerConnections.jar](DataManagerConnections.md) | 3 | `com.strategyquant.plugin.DataManager.impl.Connections` |
| [DataManagerCustomData.jar](DataManagerCustomData.md) | 5 | `com.strategyquant.plugin.DataManager.impl.CustomData`, `com.strategyquant.plugin.DataManager.impl.CustomData.job` |
| [DataManagerData.jar](DataManagerData.md) | 35 | `com.strategyquant.plugin.DataManager.impl.Data`, `com.strategyquant.plugin.DataManager.impl.Data.csvexport`, `com.strategyquant.plugin.DataManager.impl.Data.csvexport.format`; 2 additional packages |
| [DataManagerHome.jar](DataManagerHome.md) | 2 | `com.strategyquant.plugin.DataManager.impl.Home` |
| [DataManagerInstruments.jar](DataManagerInstruments.md) | 3 | `com.strategyquant.plugin.DataManager.impl.Instruments` |
| [DataManagerSessions.jar](DataManagerSessions.md) | 3 | `com.strategyquant.plugin.DataManager.impl.Sessions` |
| [DataSourceCrypto.jar](DataSourceCrypto.md) | 3 | `com.strategyquant.plugin.DataSource.impl.Crypto` |
| [DataSourceDarwinex.jar](DataSourceDarwinex.md) | 8 | `com.strategyquant.plugin.DataSource.impl.Darwinex`, `com.strategyquant.plugin.DataSource.impl.Darwinex.importdata` |
| [DataSourceDukascopy.jar](DataSourceDukascopy.md) | 6 | `com.strategyquant.plugin.DataSource.impl.Dukascopy` |
| [DataSourceFiles.jar](DataSourceFiles.md) | 10 | `com.strategyquant.plugin.DataSource.impl.Files`, `com.strategyquant.plugin.DataSource.impl.Files.job` |
| [DataSourceMt5Api.jar](DataSourceMt5Api.md) | 4 | `com.strategyquant.plugin.DataSource.impl.Mt5Api` |
| [DataSourceSQEquityData.jar](DataSourceSQEquityData.md) | 5 | `com.strategyquant.plugin.DataSource.impl.SQEquityData` |
| [DataSourceSQFuturesData.jar](DataSourceSQFuturesData.md) | 5 | `com.strategyquant.plugin.DataSource.impl.SQFuturesData` |
| [DataSourceTD.jar](DataSourceTD.md) | 5 | `com.strategyquant.plugin.DataSource.impl.TD`, `com.strategyquant.plugin.DataSource.impl.TD.job` |
| [DataSourceYahoo.jar](DataSourceYahoo.md) | 5 | `com.strategyquant.plugin.DataSource.impl.Yahoo` |

## Workspace registration evidence

- Observed NavigationPlugin in `SQX_REFERENCE_ROOT/internal/plugins/AppDataManager/module.js`: title `Data Manager`, app code `SQMANAGER`, hidden registration `False`. SHA-256 `84c51d70af4b2a8c0581746394b1b50d6d2ecaf2fae89cc8f8e03ab29c2eaa04`; inspected 2026-10-05 by direct text, at NavigationPlugin object. Registration does not prove runtime/license availability.

## Referenced archives outside this group

These links are supported by superclass/interface/member-type references in the inspected declarations. They are declaration dependencies, not a runtime call graph.

- [SQDataLib.jar](../Shared/SQDataLib.md) - `Shared`.
- [SQGridLib2.jar](../Shared/SQGridLib2.md) - `Shared`.
- [SQPluginLib.jar](../Shared/SQPluginLib.md) - `Shared`.
- [SQTradingLib.jar](../Shared/SQTradingLib.md) - `Shared`.
- [SQWebGUILib.jar](../Shared/SQWebGUILib.md) - `Shared`.

## Limits

No method bodies, algorithms, event order, failure behavior or parity are established by a class diagram. Exact behavior needs separate donor inspection and isolated runtime fixtures. Source locators and fingerprints are in each archive document; no ledger IDs are allocated while the authoritative ledger/schema are absent.
