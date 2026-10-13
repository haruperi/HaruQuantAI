# Data — field reference (for UI tests)

> Exact controls, `ng-model` bindings and defaults for the Data settings tab, extracted from the web plugin source.

Source: `internal/plugins/SettingsData/` (`views/data.html`, `DataCtrl.js`, `DataService.js`,
`ComplexitiesService.js`, `module.js`). Tab is registered as `SettingsTab` id `10`, `testId:
'settings-tab-data'`, `dataItem: 'settings-data'`, `configElemName: 'Data'`, task:
`Build,Optimize,Retest,NeuralNetworkTrainer`.

The template is almost entirely the shared `<chart-setup>` directive
(`internal/web/app/directives/chartSetup/`, `ChartSetup.js` / `views/chartSetup.html`) bound to
`config.setups[0]` (the main chart) plus, for non-Optimize tasks, a "Data range parts" (OOS) fieldset owned
directly by `DataCtrl`/`DataService`. `config.setups[0]` also carries additional-chart ("subchart") entries
rendered by the same `<chart-setup>` markup, one row per subchart.

## Trading engine (fieldset, in `<chart-setup>`)

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Engine | `setup.engine` | `<select>` (`ng-options`) | `"MetaTrader4"` (`Engines.list()[0]`) | Options (`constants.engineTypes`, value=name unless noted): `MetaTrader4`, `MetaTrader5 (netted)`, `MetaTrader5 (hedged)`, `Tradestation`, `MultiCharts`, `JForex`, `AlgoCloud Stockpicker` (value `Stockpicker`), `AlgoCloud Single-asset` (value `Single-asset cloud strategy`). |
| Additional charts | `additionalCharts.count` | number spinner (`sqn-spinner`) | 0 | min 0, step 1. Only shown (`showSubchartSpinner()`) for Optimize/Retest main setup, or for a Build task with strategy type `improve`/`template`. Drives how many subchart rows appear below. |

## Backtest data settings (fieldset, in `<chart-setup>`)

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Symbol / Group / Main chart | `setup.symbol` (via `<sq-data-box sq-model="setup.symbol">`) | custom searchable symbol picker (`.sq-data-box`, click-to-open dropdown with type filter buttons `All`/data-type, "Recently used" list) | — | Label text switches: "Group" when `engine == 'Stockpicker'`, "Main chart" when the setup has subcharts, otherwise "Symbol". |
| Timeframe | `setup.timeframe` (via `<timeframe-picker timeframe="setup.timeframe">`) | `<select>` of available timeframes | `"H1"` (`addDefaultMainChart` default before a symbol is chosen) | Options = `availableTimeframes` computed from the chosen symbol's stored data / min timeframe; higher TFs disabled for Stockpicker/Single-asset engines. |
| Start day | `setup.dateFrom` (via `<date-picker date="setup.dateFrom">`) | date input, format `yyyy.mm.dd` | symbol's available start date | Bounded by `symbolDateRangeFrom`/`symbolDateRangeTo`. Changing it fires `onMainDatesChange`, which reflows the OOS ranges. |
| End day | `setup.dateTo` (via `<date-picker date="setup.dateTo">`) | date input, format `yyyy.mm.dd` | symbol's available end date | Same bounds/behavior as Start day. |
| Reset dates | button, `ng-click="resetDates()"` | button | — | Resets `dateFrom`/`dateTo` to the full available range of the current symbol. |
| Available from / to | — (`symbolDateRangeFrom`, `symbolDateRangeTo`) | read-only labels | — | Informational only, not editable. |
| Subcharts N: Symbol | `subchart.symbol` (via `<sq-data-box sq-model="subchart.symbol">`, one row per `setup.subcharts[i]`) | same custom symbol picker as main Symbol | `"Same as main chart"` | Engine is hard-coded to `MetaTrader4` in the subchart data-box. |
| Subcharts N: Timeframe | `subchart.timeframe` (via `<timeframe-picker timeframe="subchart.timeframe">`) | `<select>` | `"H1"` | Custom/higher TFs disabled for Stockpicker/Single-asset engines. |

## Test parameters (fieldset, in `<chart-setup>`)

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Precision | `setup.precision` | `<select>` (`ng-options`) | `1` (`Selected timeframe only (fastest)`) | Options (`constants.precisions`, filtered by symbol's timeframe / engine): `1` = "Selected timeframe only (fastest)", `2` = "1 minute data tick simulation (slow)", `3` = "Real Tick - custom spread (slowest)", `4` = "Real Tick - real spread (slowest)". For Tradestation/MultiCharts only option `1` is offered. |
| Commisions & swap | — (opens modal, see below) | button (gear icon) + read-only summary label | — | Opens the "Commission & swap settings" modal. |
| Spread | `setup.spread` | number spinner | 0 (or the instrument's `defaultSpread` when the symbol changes) | Hidden for Stockpicker/Single-asset engines; hidden when `precision == 4` (Real Tick — real spread, since real spread is used instead). Unit: pips. |
| Slippage | `setup.slippage` | number spinner | 0 (or the instrument's `defaultSlippage` when the symbol changes) | Label reads "Slippage / Spread" for Stockpicker/Single-asset. Unit: pips, except "$ per trade" for Tradestation/MultiCharts. |
| Min. distance | `setup.minDistance` | number spinner | 0 | Hidden for Tradestation/MultiCharts (saved as `0` for those engines regardless of the field). Unit: pips. Minimum distance from current price for a Stop/Limit pending order. |

### Commission & swap settings (modal, opened from Test parameters)

| Label | Config key | Type | Default | Options / notes |
|---|---|---|---|---|
| Commission method + params | `setup.commissions` (XML string; edited via `<multi-property-grid instance="commPGInstance">`) | dynamic property grid, method picker + per-method parameter fields | method `None` | Method list comes from backend `constants/listCommissionMethods`; out of scope for this table (dynamic, backend-driven method catalog, not a fixed set of named controls). |
| Use (swap) | `config.useSwap` (`<swap-settings sq-model="setup.swap">`) | checkbox | `false` | Master switch for the swap block; the four fields below are disabled when off. |
| Swap type | `config.swapType` | `<select>` | `"money"` | Options (`swapTypes`): `money` ($ per day), `percent` (% per year), `points` (points per day). |
| Long | `config.swapLong` | number spinner, `updateOn: 'blur'` | 0 | Step 0.1. Unit label follows `swapType` ($ per day / % per year / points per day). |
| Short | `config.swapShort` | number spinner, `updateOn: 'blur'` | 0 | Step 0.1. Same unit behavior as Long. |
| Triple swap on | `config.tripleSwapOn` | `<select>` | `"WEDNESDAY"` | Options (`tripleSwapOptions`): `MONDAY`, `TUESDAY`, `WEDNESDAY`, `THURSDAY`, `FRIDAY`, `NEVER`. |
| Rollout hour | `config.rolloutHour` (`<time-spinner>`) | time spinner (HH:MM) | `"23:00"` | min 0, max 86340 sec, step 1800 sec (30 min). Stored and read strictly as `HH:MM`, the only form the engine's `SwapMethod` parses; a stored value in any other form (e.g. a bare `0`) is shown and re-saved as 23:00, the value the engine applies to it. |

## Data range parts (fieldset — hidden for the Optimize task, `enableOOSSettings`)

| Label | Config key / handler | Type | Default | Options / notes |
|---|---|---|---|---|
| What is it? | — | external link | — | Opens `strategyquant.com/article/training-validation-test-periods`. |
| Most used configs — preset 1 | `setSampleConfig(1)` | button, `data-testid="settings-data-oos-preset-1-btn"` | — | IST 50% / ISV 20% / OOS 30%. |
| Most used configs — preset 2 | `setSampleConfig(2)` | button, `data-testid="settings-data-oos-preset-2-btn"` | — | OOS 30% / ISV 20% / IST 50%. |
| Most used configs — preset 3 | `setSampleConfig(3)` | button, `data-testid="settings-data-oos-preset-3-btn"` | — | IST 20% / ISV 20% / OOS 10% / IST 20% / ISV 20% / OOS 10%. |
| Most used configs — preset 4 | `setSampleConfig(4)` | button, `data-testid="settings-data-oos-preset-4-btn"` | — | 10× alternating IST/ISV (3.5% each) then OOS 30%. |
| Most used configs — preset 5 | `setSampleConfig(5)` | button, `data-testid="settings-data-oos-preset-5-btn"` | — | 10× alternating IST/OOS (5% each), 20 segments total. |
| Show/Hide chart | `config.oosGraphShown` | toggle link + graph widget `#dataOOSComponent` (elessar range-slider component), `data-testid="settings-data-oos-graph-toggle"` | `false` | Draws OOS-range distribution against equity/price data of the symbol. |
| OOS range row: type | `range.type` (per `config.oosRanges[i]`, via `<oos-range>` → internal `<select>`) | `<select>` | `"oos"` for a newly added range | Options (`$scope.types`): `isv` = "In sample - Validation" (label `ISV`), `oos` = "Out of sample - Test" (label `OOS`), `notrade` = "No trade" (label `NoTrade`). Note: In-Sample **Training** (IST) is not a selectable range type — it is the implicit background/default region not covered by any explicit range. |
| OOS range row: Start | `range.dateFrom` (via nested `<date-picker>`) | date input, format `yyyy.mm.dd` | — | Bounded by the main chart's date range (`oosBounds`). |
| OOS range row: End | `range.dateTo` (via nested `<date-picker>`) | date input, format `yyyy.mm.dd` | — | Bounded by the main chart's date range. |
| OOS range row: remove | `onRemove(index)` (`.sq-oos-btn-close`) | button | — | Removes that range from `config.oosRanges`. |
| OOS range row: % label | — (`oosPercents[$index]`) | read-only label | — | Percentage of the total date range this part covers. |
| Add new part | `addOOSRange()` | link/button | — | Adds a new `oos`-type range in the largest available free space (must be >10% of total range, else shows an error). |

## Related

- Prose page: [../data.md](../data.md)
- Fields hub: [README.md](README.md)
