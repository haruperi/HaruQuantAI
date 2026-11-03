# Stockpicker & Single-asset engines in SQX

The SQX side of AlgoCloud: the two backtest engines, how strategies are generated for them, and
what differs in their Build settings. Code-derived (paths/classes below). The deepest developer
write-up of the engine internals is [`../onboard/11-misc/01-stockpicker.md`](../onboard/11-misc/01-stockpicker.md)
— this page is the knowledge-base view and links rather than duplicates.

## Engine identity

`Engines.java` (`SQAppLib …/simulator/`):

| Name string (= identifier in `Data/Setup/@engine`) | UI label | Key |
|---|---|---|
| `Stockpicker` | AlgoCloud Stockpicker | `SP` |
| `Single-asset cloud strategy` | AlgoCloud Single-asset | `SA` |

`Engines.isAWCloudEngine()` groups them; the display name IS the identifier (a rename must touch
every UI reference — source comment warns about this).

## How the engine works (one paragraph)

Both engines run the **same** `StockpickerBacktestEngine` (`engine/stockpicker/`, ~10k LOC across
49 files) — a signal-based **two-phase portfolio backtester** (AmiBroker-style, per its own
comment): phase 1 fans out per symbol and collects `PickerEntrySignal`/`PickerExitSignal` with a
**position score**; phase 2 walks the merged daily timeline sequentially, ranks entry candidates
by score (`PickerEntrySignalComparatorByRevScore`), fills free slots up to
`MaxOpenPositionsLong/Short`, and executes through `StockBroker` with intra-bar tick order:
exit/entry Before Bar Open → On Bar Open → On Bar Close. Main chart **must be a stock-group
alias** (`[Name]` / `[[Name]]`); additional charts only D1/W/M; results are forced to D1 and gain
extra stats (`maxDailyDD(Pct)`, open-drawdown variants).

**Single-asset = a Stockpicker over a one-element basket**: `BacktestRunner` wraps the symbol as
`"[SYMBOL]"` via `createTempStockGroup(...)`, and `MaxOpenPositions` is forced to 1/1. The
strategy XML marks the engines with `Strategy/@pickerEditor="true"` (+ `@singleAsset="true"` for
SA).

## Strategy generation (Builder)

`StrategyTemplateGenerator` routes `engine=Stockpicker` → `StrategyStockpickerTemplate`,
`Single-asset` → `StrategyStockpickerSingleAssetTemplate` (which only adds `singleAsset="true"` —
its rule-building code is an identical copy of the parent's). Skeletons come from
`internal/ctemplate/build/sp/*.xml`. A generated stockpicker strategy = 4 rules:

1. `Rule "Long" type="StockpickerEntryExit"` — entry conditions, order (Market/Stop/Limit),
   exits (incl. `atEndOfDay`),
2. `Rule "Short"` — symmetric via negation/opposite action,
3. + 4. `Rule "Position Score Long|Short" type="StockpickerPS"` — assigns `#PositionScore#`
   (a **randomly generated value formula**, identification `RandomPSValue`) and
   `#MaxOpenPositions#` (default 6). For single-asset these rules are emitted but **inert**
   (`StockpickerPS` early-returns).

Post-generation, `StockpickerGenFixer` applies the `StockpickerOptions` values: entry/exit
triggers (`BeforeBarOpen|OnBarOpen|OnBarClose`, `0` = random), end-of-day exits, max open
positions. `improve` mode is **not implemented** for SP/SA (throws).

## `task_stockpicker.xml` — what differs from forex

(`internal/plugins/TaskBuild/task_stockpicker.xml`; same section set as forex.)

- **Data**: `engine="Stockpicker"`, ONE `<Chart symbol="[[S&P 100 limited]]" timeframe="D1">` —
  the universe is a group alias, not a symbol list. Commissions `Method type="Stockpicker"`
  (`Commission` $/share, `MinPerOrder`, `MaxPerOrder` with money/equity types).
- **Options**: 7 `className="StockpickerOptions"` params — `PickerEntryType`/`PickerExitType`
  (0=random, 1=from strategy, 5=OnBarOpen, 10=OnBarClose, 15=BeforeBarOpen),
  `PickerEndOfDayLong/Short` (5=Yes, 10=No), `PickerMaxOpenPositionsLong/Short` (8),
  `PickerStoreLogs`. Related SP-only options: `BrokerOption` (filter the universe to a broker's
  symbols), `LimitOver` (limit fills only when price exceeds the limit by ≥ X %).
- **ExitTypes**: both `_ExitRule_` AND **`_ExitEOD_`** `use="true"` — `_ExitEOD_` exists only in
  the stockpicker defaults.
- **OrderTypes**: Market/Stop/Limit all enabled; `EnterReverseAtMarket` absent.
- **Money management**: `PickerRiskFixedPctOfAccount` (`Risk` 10 %) active; `PickerFixedAmount`
  is the other picker method. Both `@ForEngine("SP,SA")`, sized per position and **divided by max
  positions**, with fractional-share params. `InitialCapital` 100000.
- **SLPT**: SL/PT not required (vs forex all-required). Genetic defaults smaller (50/50, 1 island).

## Data side — universes

`BasketOfStocksManager` (`SQDataLib …/basket/`, SQLite `STOCK_GROUP`/`STOCK`): groups of
`StockDto{ticker, dateFrom, dateTo}` (dated membership = survivorship-bias control, matching the
AlgoCloud concept). Group alias in the data table = `[Name]`; `basketId ≥ 0` system group,
`< 0` custom. Bundled sample universe: `[[S&P 100 limited]]` (update-locked). Loading goes
through `PickerDataCache`/preloaders; `SettingsKeys.BrokerSymbols` is the AlgoCloud-side symbol
override consumed on backtest nodes.

## `@ForEngine` gating

Snippets/options/blocks carry `@ForEngine("SP,SA")` (allow) or `"*,-SP,-SA"` (deny) — substring
semantics, `-X` wins; see [`../onboard/12-export/07-forengine.md`](../onboard/12-export/07-forengine.md).
SP/SA-positive snippets: the two Picker MM methods, `StockpickerOptions`, `LimitOver`,
`BrokerOption` (SP only), and the week-of-month bar blocks.

## Known quirks (flagged during this mapping, 2026-08-07)

1. `StrategyStockpickerSingleAssetTemplate` duplicates the parent's private methods verbatim —
   only `singleAsset="true"` differs; the inert Position Score rules still ship in SA XML
   (⚠ `docs/overview/algowizard/engine-single-asset.md` describes SA XML without them).
2. `AlgoWizardServlet`'s MM gate compares `mmEngine.equals("SP,SA")` literally instead of
   `checkEngine()` — an MM annotated `@ForEngine("SP")` alone would be rejected for both engines.
3. `StockpickerBacktestEngine.getEngineId()`/`getGlobalATR()` are TODO stubs returning 0.
4. The `@ForEngine` census table in `07-forengine.md` is stale (NT was added to 70 sites since).

## Where to read more

- **What a cloud strategy can actually express** (the capability matrix, the engine clock, value
  arithmetic, and the measured translation gaps):
  [`../strategy-authoring/`](../strategy-authoring/README.md)
- Engine internals & class map: [`../onboard/11-misc/01-stockpicker.md`](../onboard/11-misc/01-stockpicker.md)
- AlgoWizard editor view of both engines: [`../overview/algowizard/engine-stockpicker.md`](../overview/algowizard/engine-stockpicker.md),
  [`engine-single-asset.md`](../overview/algowizard/engine-single-asset.md)
- Trading-option fields: [`../overview/settings/fields/trading-options.md`](../overview/settings/fields/trading-options.md)
- Picker MM: [`../overview/snippets/money-management.md`](../overview/snippets/money-management.md)
- The platform this all serves: [platform.md](platform.md)
