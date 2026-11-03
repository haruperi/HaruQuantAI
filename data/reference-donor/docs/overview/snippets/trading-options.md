# Trading options — full catalog

> Reference enumeration of the built-in trading-option snippets — session/time restrictions,
> SL/PT clamps, and other always-available toggles a strategy can turn on. This is a lookup table;
> for the engine legend see the [Snippets hub](README.md).

## How the set is assembled

Each trading option is a snippet class extending `TradingOption`
(`projects/libs/SQTradingLib/.../TradingOption.java`), registered by `TradingOptionsList`
(`setDirName("TradingOptions")`, a `CustomClasses<TradingOption>` loader) and loaded from the
`TradingOptions` snippet directory
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/TradingOptions/`). The set is
**extensible** — a user snippet dropped into that directory becomes a new option. Besides the
directory-loaded snippets, `TradingOptionsList` also registers a handful of built-in classes by
name (`SessionOption`, `ReservedBars`, `StoreChartData`, `RealisticGapsHandling`,
`StockpickerOptions`, `BrokerOption`, `MarketOpenSession`, `LimitOver`) which live outside the
snippet directory and are out of scope for this catalog.

**Annotation pattern differs from Money management / Exit methods:** none of these 8 classes carry
a class-level `@ClassConfig` — there is no picker entry or display template. Instead, **all
trading options are active simultaneously** as a flat panel of settings (checkboxes, time pickers,
spinners) grouped under `category="Trading options"`. Each `@Parameter` field carries its own
`name`, `defaultValue`, optional `minValue`/`maxValue`/`step`, `@Help("...")`, and — notably —
`@ForEngine("...")` is applied **per field**, not per class (unlike Money management/Exit methods).
Most options follow an enable-flag pattern: one boolean `@Parameter` acts as the on/off switch, and
dependent fields carry `@Activator(param="<flag name>")` so the UI enables/greys them out together.
Time-of-day fields use `@Editor(type=Editors.Time)` (HHMM integer format, e.g. `2300` = 23:00, in
the timezone of the data).

## Catalog

| Class | Enable parameter | Engines | What it does |
|-------|-------------------|---------|---------------|
| `DontTradeOnWeekends` | Don't trade on weekends | all, −SP,−SA | Stops trading from a Friday close time until a Sunday open time. |
| `ExitAtEndOfDay` | Exit At End Of Day | all, −SP,−SA | Closes all positions at a configurable end-of-day time. |
| `ExitOnFriday` | Exit On Friday | all, −SP,−SA | Closes all positions at a configurable Friday exit time. |
| `LimitTimeRange` | Limit Time Range | all, −SP,−SA | Restricts trading to a daily time window, optionally closing positions at the end of the range. |
| `MaxDistanceFromMarket` | Max distance from market | all, −SP,−SA | Cancels pending orders whose price is too far from the current market price. |
| `MaxTradesPerDay` | (always evaluated; 0 = no limit) | all, −SP,−SA | Caps the number of trades opened per day. |
| `MinMaxSLPT` | (always evaluated; 0 = no limit, per field) | all, −SP,−SA | Clamps Stop Loss / Profit Target to min/max pip distances. |
| `UseInitialSLPT` | Use initial SL & PT | MC, TS | Applies SL/PT immediately on fill instead of on the next bar. |

## Parameters

### Don't trade on weekends (`DontTradeOnWeekends`)

| Parameter | Default | Min | Max | Editor | Activator | Meaning |
|-----------|---------|-----|-----|--------|-----------|---------|
| Don't trade on weekends (`DontTradeOnWeekends`, boolean) | false | — | — | — | — | Master switch; strategy performs no operations during the weekend window. |
| Friday Close Time (`FridayCloseTime`) | 2300 | — | — | Time | `DontTradeOnWeekends` | Time (HHMM) after which trading stops on Friday. |
| Sunday Open Time (`SundayOpenTime`) | 2300 | — | — | Time | `DontTradeOnWeekends` | Time (HHMM) trading re-enables on Sunday. |

### Exit At End Of Day (`ExitAtEndOfDay`)

| Parameter | Default | Min | Max | Editor | Activator | Meaning |
|-----------|---------|-----|-----|--------|-----------|---------|
| Exit At End Of Day (`ExitAtEndOfDay`, boolean) | false | — | — | — | — | Master switch; closes all positions at end of day. |
| End Of Day Exit Time (`EODExitTime`) | 2355 | — | — | Time | `ExitAtEndOfDay` | Time (HHMM) to close all positions; `0` closes at midnight (start of the previous day). Interacts with `LimitTimeRange` if both are enabled. |

### Exit On Friday (`ExitOnFriday`)

| Parameter | Default | Min | Max | Editor | Activator | Meaning |
|-----------|---------|-----|-----|--------|-----------|---------|
| Exit On Friday (`ExitOnFriday`, boolean) | false | — | — | — | — | Master switch; closes all positions at end of week (Friday). |
| Friday Exit Time (`FridayExitTime`) | 2300 | — | — | Time | `ExitOnFriday` | Time (HHMM) on Friday to close all positions. |

### Limit Time Range (`LimitTimeRange`)

| Parameter | Default | Min | Max | Editor | Activator | Meaning |
|-----------|---------|-----|-----|--------|-----------|---------|
| Limit Time Range (`LimitTimeRange`, boolean) | false | — | — | — | — | Master switch; restricts trading (signal-taking) to a daily time window. |
| Time Range From (`SignalTimeRangeFrom`) | 0800 | — | — | Time | `LimitTimeRange` | Window start time (HHMM). |
| Time Range To (`SignalTimeRangeTo`) | 1600 | — | — | Time | `LimitTimeRange` | Window end time (HHMM). |
| Exit At End Of Range (`ExitAtEndOfRange`, boolean) | false | — | — | — | `LimitTimeRange` | If true, closes positions once the window ends. |
| Order Types To Close (`OrderTypeToExit`) | 0 | — | — | Selection: `All=0, Live only=1, Pending only=2` | `LimitTimeRange` | Which order types the end-of-range close applies to. Only takes effect when Exit At End Of Range = true. |

### Max distance from market (`MaxDistanceFromMarket`)

`isUsedInTrading()` returns `false` — this option isn't enforced by `OnBarUpdate` itself; it's read
elsewhere (order-placement logic) as a passive limit.

| Parameter | Default | Min | Max | Step | Editor | Activator | Meaning |
|-----------|---------|-----|-----|------|--------|-----------|---------|
| Max distance from market (`MaxDistanceFromMarket`, boolean) | false | — | — | — | — | — | Master switch; limits pending orders' maximum distance from the current market price. |
| Max distance percent (`MaxDistancePct`) | 6 | 0 | 1000 | 0.1 | Spinner | `MaxDistanceFromMarket` | Orders priced beyond this % distance from market are canceled. |

### Maximum Trades Per Day (`MaxTradesPerDay`)

`isUsedInTrading()` returns `true` only when the value is non-zero — there is no separate enable
flag, `0` itself means "no limit".

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Maximum Trades Per Day (`MaxTradesPerDay`) | 0 | 0 | — (unbounded) | — | Maximum trades allowed per day; `0` = no limit. |

### Min/Max SL & PT (`MinMaxSLPT`)

`isUsedInTrading()` returns `false` — this option isn't enforced by `OnBarUpdate`; the four limits
are read elsewhere when SL/PT are being set on an order. Each field carries
`@ForEngine("*,-SP,-SA")` (all engines except Stockpicker and Single-asset). No enable flag — each
of the four fields is independently active whenever it is non-zero.

| Parameter | Default | Min | Max | Meaning |
|-----------|---------|-----|-----|---------|
| Minimum SL (`MinimumSL`) | 0 | 0 | 1,000,000 | Clamps SL so it is never smaller than this (pips). `0` = no limit. |
| Maximum SL (`MaximumSL`) | 0 | 0 | 1,000,000 | Clamps SL so it is never bigger than this (pips). `0` = no limit. |
| Minimum PT (`MinimumPT`) | 0 | 0 | 1,000,000 | Clamps PT so it is never smaller than this (pips). `0` = no limit. |
| Maximum PT (`MaximumPT`) | 0 | 0 | 1,000,000 | Clamps PT so it is never bigger than this (pips). `0` = no limit. |

Legacy XML import note: `setFromParameterEl()` maps the old combined keys `MinimumSLPT` /
`MaximumSLPT` onto both the SL and PT fields at once for backward compatibility.

### Use initial SL & PT (`UseInitialSLPT`)

`@ForEngine("MC,TS,NT")` — MultiCharts, TradeStation and NinjaTrader 8; those, with EasyLanguage, are
the engines shipping `UseInitialSLPT_code.tpl`. `isUsedInTrading()` returns `false` — read elsewhere
at order-fill time.

> NinjaTrader was added by GEN-55 (2026-08-02), but the UI kept a second, hard-coded engine list that
> hid the option and forced it to `false` on NT8 until issue #162. If this value ever changes again,
> change `SESSION_AND_WARMUP_ENGINE_KEYS` in `SettingsOptions/OptionsCtrl.js` with it.

| Parameter | Default | Min | Max | Meaning |
|-----------|---------|-----|-----|---------|
| Use initial SL & PT (`UseInitialSLPT`, boolean) | false | — | — | Sets Stop Loss and Profit Target immediately once the order is filled, instead of waiting for the next bar. |

## Related

- Snippets hub: [`README.md`](README.md)
- Money management catalog: [`money-management.md`](money-management.md)
- Exit methods catalog: [`exit-methods.md`](exit-methods.md)
- Loader: `TradingOptionsList` (`projects/libs/SQTradingLib/.../options/TradingOptionsList.java`)
