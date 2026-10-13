# Trading options — field reference (for UI tests)

> Exact controls, `ng-model` bindings and defaults for the Trading options settings tab, extracted from the web plugin source.

Source: `internal/plugins/SettingsOptions/` (`views/options.html`, `OptionsCtrl.js`, `OptionsService.js`,
`module.js`). Tab is registered as `SettingsTab` id `20`, `testId: 'settings-tab-opt'`, `dataItem:
'settings-options'`, `configElemName: 'Options'`, task: `Build,Retest,Optimize,AutomaticRetest,NeuralNetworkTrainer`.

**The list of trading-option METHODS (the parameters strategies can turn on) is cataloged in
[`../../snippets/trading-options.md`](../../snippets/trading-options.md) — link there for the full
parameter tables of `DontTradeOnWeekends`, `ExitAtEndOfDay`, `ExitOnFriday`, `LimitTimeRange`,
`MaxDistanceFromMarket`, `MaxTradesPerDay`, `MinMaxSLPT`, `UseInitialSLPT`.** This page documents only the
tab's own UI (the "Use custom trading options" switch) and the **8 built-in `TradingOption` classes that
the snippets catalog explicitly excludes** (`SessionOption`, `ReservedBars`, `StoreChartData`,
`RealisticGapsHandling`, `StockpickerOptions`, `BrokerOption`, `MarketOpenSession`, `LimitOver`) — all of
these live outside the extensible `TradingOptions` snippet directory but render in the same property grid.

## Tab chrome

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Use custom trading options | `config.useCustomSettings` | checkbox, `data-testid="settings-opt-custom-switch"` | `false` | Only shown when `isAutoRetestTask` (task type `AutomaticRetest`). Persisted as `Options[customSettings]` attribute; irrelevant for Build/Optimize/Retest. |
| Build and Trading Options | `config.propertyGridInstance` (`<property-grid id="btPropertyGrid">`) | dynamic property grid, `data-testid="settings-opt-grid-btn"` | — | Populated from backend `options/list`: every `TradingOption` snippet (see linked catalog) plus the 8 built-ins below, all rendered as one flat list of controls (checkboxes / time pickers / spinners / selects), grouped by each field's own `category`. Field visibility is toggled dynamically by engine (see notes per field below) and, for Stockpicker/Single-asset, only `Picker*` fields + `StoreChartData` + `LimitOver` are shown — everything else is hidden. |

## Built-in options not covered by the snippets catalog

Source: `projects/libs/SQAppLib/src/com/strategyquant/tradinglib/options/parameters/*.java`.

### Session (`SessionOption`)

| Parameter | Default | Category | Editor | ForEngine | Meaning |
|---|---|---|---|---|---|
| Session (`Session`) | `"No Session"` | Session | Selection (dynamic — one option per session defined in Data Manager) | `MC,TS,NT` | Trading session for futures/equities intraday trading; no effect in MT4/5. In the UI, hidden and forced to `"No Session"` unless the current engine is Tradestation, MultiCharts or NinjaTrader8 (`SESSION_AND_WARMUP_ENGINE_KEYS` in `OptionsCtrl.js`). The chosen session is written onto every chart setup and honoured by the backtest and by AlgoWizard backtests (`Engines.hasSessionOption`). |

### MarketOpenSession (`MarketOpenSession`)

| Parameter | Default | Category | Editor | ForEngine | Meaning |
|---|---|---|---|---|---|
| MarketOpenSession (`MarketOpenSession`) | `"No Session"` | Session | Selection (dynamic — one option per session) | `MT5` | Session used to determine market-open behavior in MT5. Hidden and forced to `"No Session"` unless the engine starts with `MetaTrader5`. On symbol change for an MT5 engine, `OptionsService.presetMarketOpenSession` auto-picks a matching session by instrument name/description. |

### Reserved bars (`ReservedBars`)

| Parameter | Default | Category | ForEngine | Meaning |
|---|---|---|---|---|
| Reserved bars (`ReservedBars`) | `50` (int) | Reserved bars | `MC,TS,NT` | Bars held in reserve before trading starts; should exceed any indicator period used by the strategy. Hidden and forced to `50` unless engine is Tradestation, MultiCharts or NinjaTrader8. Two effects, both gated by `Engines.hasReservedBarsOption`: the backtest starting bar is pushed forward by this many bars (`TradingSetup`), and a strategy whose greatest indicator period reaches it is dismissed (`BacktestRunner`). **On NinjaTrader only** it is also exported, as `BarsRequiredToTrade` in the generated NinjaScript; on TS/MC it stays advisory and the user mirrors it by hand. |

### Store Chart Data (`StoreChartData`)

| Parameter | Default | Category | ForEngine | Meaning |
|---|---|---|---|---|
| Store Chart Data (`StoreChartData`, boolean) | `false` | Build options | all | Also saves full chart data with the backtest result, for later visual review (Results → Trades on chart). Always visible (not engine-gated), including for Stockpicker/Single-asset. |

### Realistic Gaps Handling (`RealisticGapsHandling`)

| Parameter | Default | Category | ForEngine | Meaning |
|---|---|---|---|---|
| Realistic Gaps Handling (`RealisticGapsHandling`, boolean) | `false` | Trading options | `MT4,MT5` | MT4/5-only: fills Stop/Limit orders at the price *after* a gap (as in real trading) instead of at the desired price. Hidden and forced to `false` unless the engine is MetaTrader4 or MetaTrader5 (`REALISTIC_GAPS_ENGINE_KEYS` in `OptionsCtrl.js`): JForex fills at the real price anyway and the bar-close engines (Tradestation, MultiCharts, NinjaTrader8) never read the option. |

### Stockpicker (`StockpickerOptions`) — Stockpicker/Single-asset only

| Parameter | Default | Min | Max | Category | Editor | ForEngine | Meaning |
|---|---|---|---|---|---|---|---|
| Entry type (`PickerEntryType`) | `5` | — | — | Stockpicker | Selection: `Randomly generated=0, From strategy=1, On Bar Open=5, On Bar Close=10, Before Bar Open=15` | `SP,SA` | When the entry condition is checked. In a **Build** task the `From strategy` option is removed from the list; in other tasks the `Randomly generated` option is removed. |
| Exit type (`PickerExitType`) | `5` | — | — | Stockpicker | same option set as Entry type | `SP,SA` | When the exit condition is checked. Same Build-vs-other-task option filtering as Entry type. |
| Exit End Of Day Long (`PickerEndOfDayLong`) | `5` | — | — | Stockpicker | Selection: `Randomly generated=0, From strategy=1, Yes=5, No=10` | `SP,SA` | Whether end-of-day close for long positions is at real day close or next market open. Same Build-vs-other-task option filtering. |
| Exit End Of Day Short (`PickerEndOfDayShort`) | `5` | — | — | Stockpicker | same option set as above | `SP,SA` | Same, for short positions. |
| Max Open Positions Long (`PickerMaxOpenPositionsLong`) | `8` | 0 | 500 | Stockpicker | spinner | `SP` | Max concurrently open long stock positions; `0` defers to the strategy's own value. Hidden for the Single-asset engine (`STOCKPICKER_ONLY_KEYS` in `OptionsCtrl.js`): a single-asset strategy holds at most one position per direction, the engine uses 1 whatever is stored. |
| Max Open Positions Short (`PickerMaxOpenPositionsShort`) | `8` | 0 | 500 | Stockpicker | spinner | `SP` | Same, for short positions. |
| Store Stockpicker Logs (`PickerStoreLogs`, boolean) | `false` | — | — | Stockpicker | checkbox | `SP,SA` | Store stockpicker logs in the backtest result. |
| Allow Better Limit Fill (`PickerAllowBetterLimitFill`, boolean) | `false` | — | — | Stockpicker | checkbox | `SP,SA` | Fills limit orders at a better market price when available. |

### Broker (`BrokerOption`) — Stockpicker only

| Parameter | Default | Category | Editor | ForEngine | Meaning |
|---|---|---|---|---|---|
| Broker (`PickerBroker`) | `BrokerManager.NO_BROKER` ("no broker" sentinel) | Stockpicker | Selection (dynamic — one option per configured broker, plus the no-broker sentinel) | `SP` | Limits the stock universe to the symbols the chosen broker offers (`PortfolioBacktester.getBrokerSymbols`). Hidden and forced to `"No filter"` for the Single-asset engine (`STOCKPICKER_ONLY_KEYS` in `OptionsCtrl.js`), which tests one given symbol. |

### Limit Over (`LimitOver`)

| Parameter | Default | Min | Max | Step | Category | ForEngine | Meaning |
|---|---|---|---|---|---|---|---|
| Limit Over (`LimitOver`) | `0` | 0 | 100 | 0.01 | Stockpicker | `SP,SA` | Limit order is filled only if price exceeds the limit by at least this many %. |

## Related

- Trading-option methods catalog: [`../../snippets/trading-options.md`](../../snippets/trading-options.md)
- Prose page: [../trading-options.md](../trading-options.md)
- Fields hub: [README.md](README.md)
