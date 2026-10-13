# Money management / position sizing — full catalog

> Reference enumeration of the built-in position-sizing (money management) snippets available when
> building a strategy. This is a lookup table; for the engine legend and where these plug into a
> strategy see the [Snippets hub](README.md).

## How the set is assembled

Each position-sizing method is a snippet class extending `MoneyManagementMethod`
(`projects/libs/SQTradingLib/.../MoneyManagementMethod.java`), registered by
`MoneyManagementMethodsList` (`setDirName("MoneyManagement")`, a `CustomClasses<MoneyManagementMethod>`
loader) and loaded from the `MoneyManagement` snippet directory
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/MoneyManagement/`). The set is
**extensible** — a user snippet dropped into that directory becomes a new selectable money
management method, exactly like the built-ins below.

Each class carries `@ClassConfig(name="...", display="...")` — `name` is the label shown in the
money-management picker, `display` is a template (`#Param#` placeholders) rendered with live
parameter values wherever the chosen method needs to be summarized in the UI. Most also carry
`@Description("...")` (a similar template, used in exports/reports) and `@Help("...")` (longer,
HTML-formatted description shown as a tooltip). `@SortOrder(n)` fixes the order in the picker.
`@ForEngine("...")` restricts which trading engine(s) the method is available for — `*` means all
engines, a leading `-` excludes an engine, and bare codes restrict to only those engines (`MC` =
MultiCharts, `TS` = TradeStation, `SP` = Stockpicker, `SA` = Single-asset cloud strategy).

Configurable settings are declared as `@Parameter` fields — `name` (label), `defaultValue`,
`minValue`, `maxValue`, `step`, and `category` (grouping tab within the method's settings panel).
Each parameter typically also carries `@Help("...")` with a one-line description.

## Catalog

| Display name | Class | Engines | Description |
|---------------|-------|---------|--------------|
| Fixed size | `FixedSize` | all, −SP,−SA | No money management — strategy trades a fixed number of lots. |
| Fixed amount | `FixedAmount` | all, −SP,−SA | Risks a fixed $ amount per trade (no compounding); size derived from the order's Stop Loss distance. |
| Risk fixed % balance | `RiskFixedBalancePct` | all, −SP,−SA | Risks a fixed % of account **balance** per trade. |
| Risk fixed % of account | `RiskFixedPctOfAccount` | all, −SP,−SA | Risks a fixed % of account **equity** per trade; falls back to a predefined SL in pips if the order has none. |
| ATR Risk-Based Sizing | `ATRRiskBasedSizing` | all, −SP,−SA | Risks a fixed % of equity per trade, with stop distance derived from ATR volatility instead of the order's SL. |
| Simple Martingale MM | `SimpleMartingaleMM` | all, −SP,−SA | Experimental: multiplies the last trade's size after a loss, resets to the starting size after a profit. |
| Crypto fixed amount | `CryptoFixedAmount` | all, −SP,−SA | Spends a fixed $ amount per trade; size = money / open price (no Stop Loss involved). |
| Crypto fixed % balance | `CryptoFixedBalancePct` | all, −SP,−SA | Spends a fixed % of account balance per trade; size = money / open price. |
| Crypto size by price | `CryptoSizeByPrice` | all, −SP,−SA | Size = account balance (or initial capital) / asset price, capped at a maximum size. |
| Stocks size by price | `StocksSizeByPrice` | all, −SP,−SA | Size = account balance (or initial capital) / stock price, capped at a maximum size; always rounded to whole shares. |
| Fixed amount (Stockpicker) | `PickerFixedAmount` | SP, SA | Allocates a fixed $ amount, split across the maximum allowed open positions. |
| Risk fixed % of account (Stockpicker) | `PickerRiskFixedPctOfAccount` | SP, SA | Allocates a fixed % of account equity, split across the maximum allowed open positions. |

## Fixed-size / fixed-amount

### Fixed size (`FixedSize`)

No money management — trades a constant number of lots every time.

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Order size (`Size`) | 0.1 | 0.01 | 1,000,000 | 0.1 | Order size (number of lots for forex). |

### Fixed amount (`FixedAmount`)

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| RiskedMoney | 500 | 1 | 1,000,000 | 100 | Risk in $ per trade. |
| Size Decimals | 1 | 0 | 6 | 1 | Rounding decimals for order size (2 = microlots, 1 = mini lots, 0 = stocks/futures). |
| Size if no MM (`LotsIfNoMM`) | 0.1 | 0 | 1,000,000,000 | 0.1 | Lots traded if MM is disabled or computed size is 0. |
| Maximum lots (`MaxLots`) | 0.5 | 0.01 | 1,000,000,000 | 0.1 | Largest lot size allowed. |

## Risk-based (% of account)

### Risk fixed % balance (`RiskFixedBalancePct`)

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Risk in % (`Risk`) | 5 | 0.1 | 100,000 | 0.1 | % of account **balance** risked per trade. |
| Size Decimals | 1 | 0 | 6 | 1 | Rounding decimals for order size. |
| Size if no MM (`LotsIfNoMM`) | 1 | 0 | 1,000,000,000 | 0.1 | Lots traded if MM disabled or computed size is 0. |
| Maximum lots (`MaxLots`) | 5 | 0.01 | 1,000,000,000 | 0.1 | Largest lot size allowed. |

### Risk fixed % of account (`RiskFixedPctOfAccount`)

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Risk in % (`Risk`) | 5 | 0.1 | 100,000 | 0.1 | % of account **equity** risked per trade. |
| Size Decimals | 1 | 0 | 6 | 1 | Rounding decimals for order size. |
| StopLoss in pips (`StopLossInPips`) | 100 | 0 | 1,000,000 | 10 | Fallback SL (in pips) used to size the trade when the order has no SL. |
| Size if no MM (`LotsIfNoMM`) | 1 | 0 | 1,000,000,000 | 0.1 | Lots traded if MM disabled or computed size is 0. |
| Maximum lots (`MaxLots`) | 5 | 0.01 | 1,000,000,000 | 0.1 | Largest lot size allowed. |

### ATR Risk-Based Sizing (`ATRRiskBasedSizing`)

| Parameter | Default | Min | Max | Step | Category | Meaning |
|-----------|---------|-----|-----|------|----------|---------|
| Risk in % (`Risk`) | 2 | 0.1 | 100,000 | 0.1 | Risk | % of account equity risked per trade. |
| ATR Period | 14 | 2 | 480 | 1 | ATR | ATR lookback period. |
| ATR Multiplier (`ATRMult`) | 2.0 | 0.1 | 10 | 0.1 | ATR | ATR multiple used as the stop distance. |
| Size Decimals | 1 | 0 | 6 | 1 | Default | Rounding decimals for order size. |
| Size if no MM (`LotsIfNoMM`) | 1 | 0 | 1,000,000,000 | 0.1 | Lots | Lots traded if computed size is 0 or MM disabled. |
| Maximum lots (`MaxLots`) | 5 | 0.01 | 1,000,000,000 | 0.1 | Lots | Largest lot size allowed. |

## Martingale

### Simple Martingale MM (`SimpleMartingaleMM`)

Experimental. Multiplies the previous trade's size by a multiplier after a loss; resets to the
starting size after a profit or once the size exceeds the reset threshold.

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Starting lots (`LotsStart`) | 0.1 | 0.01 | — (unbounded) | — | Size used at the start / after a reset. |
| Lots multiplier (`LotsMultiplier`) | 2.0 | 0.01 | — (unbounded) | — | Multiplier applied to the previous order's size after a loss. |
| Maximum Lots (reset) (`LotsReset`) | 1.0 | 0.01 | — (unbounded) | — | If the computed size exceeds this, resets back to Starting lots. |
| Size Decimals | 1 | 0 | 6 | 1 | Rounding decimals for order size. |
| Separate MM by direction? (`SeparateByDirection`) | true (boolean) | — | — | — | If true, tracks Martingale state independently for Buy vs. Sell orders. |

## Crypto

### Crypto fixed amount (`CryptoFixedAmount`)

> Available on every desktop engine. It was MultiCharts-only until 2026: the annotation was widened by
> `GEN-56` and the matching guard inside `computeTradeSize` removed by `GEN-85`, once the export
> templates existed for EasyLanguage, MetaTrader 4/5, JForex and NinjaTrader. Verified against a real
> NinjaTrader at 100 % size parity.

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| RiskedMoney | 500 | 1 | 1,000,000 | 100 | Risk in $ per trade; size = money / open price. |
| Size Decimals | 1 | 0 | 6 | 1 | Rounding decimals applied before multiplying. |

### Crypto fixed % balance (`CryptoFixedBalancePct`)

> Available on every desktop engine — same history as `CryptoFixedAmount` above.

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Risk in % (`Risk`) | 5 | 0.1 | 100,000 | 0.1 | % of account balance risked per trade. |
| Size Decimals | 1 | 0 | 6 | 1 | Rounding decimals for order size. |

### Crypto size by price (`CryptoSizeByPrice`)

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Use account balance (`UseAccountBalance`) | true (boolean) | — | — | — | If true, sizes off current account balance; otherwise off initial capital. |
| Maximum size (`MaxSize`) | 100 | 0.01 | 1,000,000,000 | 0.1 | Largest size allowed. |
| Size Decimals | 4 | 0 | 12 | 1 | Rounding decimals (2 = microlots, 1 = mini lots, 0 = stocks/futures). |

## Stocks

### Stocks size by price (`StocksSizeByPrice`)

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Use account balance (`UseAccountBalance`) | true (boolean) | — | — | — | If true, sizes off current account balance; otherwise off initial capital. |
| Maximum size (`MaxSize`) | 100 | 0.01 | 1,000,000,000 | 0.1 | Largest size allowed. |

No "Size Decimals" parameter — trade size is always rounded to whole shares (decimals hardcoded to 0).

## Stockpicker (portfolio) sizing

Available only for the Stockpicker (`SP`) and Single-asset cloud strategy (`SA`) engines; size is
split across `maxPos` (maximum allowed open positions).

### Fixed amount (Stockpicker) (`PickerFixedAmount`)

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| RiskedMoney | 10,000 | 1 | 1,000,000 | 100 | $ amount allocated to the strategy (split across max positions). |
| Allow fractional shares (`AllowFractionalShares`) | false (boolean) | — | — | — | Allows trading fractional shares (broker/stock dependent). |
| Fractional decimal numbers (`FractionalDecimalNumbers`) | 4 | 0 | 12 | 1 | Decimal places used when rounding fractional share size. |
| Fractional step (`FractionalStep`) | 0.01 | 0 | 1 | 0.01 | Step size fractional shares are rounded to. |

### Risk fixed % of account (Stockpicker) (`PickerRiskFixedPctOfAccount`)

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Risk in % (`Risk`) | 10 | 0.1 | 100 | 0.1 | % of account equity allocated to the strategy (split across max positions). |
| Allow fractional shares (`AllowFractionalShares`) | false (boolean) | — | — | — | Allows trading fractional shares (broker/stock dependent). |
| Fractional decimal numbers (`FractionalDecimalNumbers`) | 4 | 0 | 12 | 1 | Decimal places used when rounding fractional share size. |
| Fractional step (`FractionalStep`) | 0.01 | 0 | 1 | 0.01 | Step size fractional shares are rounded to. |

## Related

- Snippets hub: [`README.md`](README.md)
- Exit methods catalog: [`exit-methods.md`](exit-methods.md)
- Trading options catalog: [`trading-options.md`](trading-options.md)
- Loader: `MoneyManagementMethodsList` (`projects/libs/SQTradingLib/.../moneymanagement/MoneyManagementMethodsList.java`)
