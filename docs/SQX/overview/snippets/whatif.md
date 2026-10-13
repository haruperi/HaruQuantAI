# What-If manipulations — full catalog (settings for UI tests)

> Reference enumeration of every built-in **What If** snippet, with the exact parameters each one
> exposes (name, default, min, max, step). This is a lookup table; for what the What If test *is*
> and how it's used see [`../robustness-tests/what-if.md`](../robustness-tests/what-if.md).

## How the set is assembled

Each What If scenario is a snippet class extending `WhatIf`
(`com.strategyquant.tradinglib.WhatIf`), implementing a single `filter(OrdersList orders)` method
that mutates/removes entries in the trade list produced by the main backtest — no re-backtest is
run. At startup `WhatIfMethodsList` loads every class found in the `WhatIf` snippet directory
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/WhatIf/`), so **the set is extensible**
— a user can drop in a new snippet and it appears in the What If picker.

Each class carries a `@ClassConfig(name=..., display=...)` annotation: `name` is the label shown in
the picker, `display` is a template (with `#ParameterName#` placeholders) used to render the
configured scenario as one line once parameter values are filled in — this is what UI tests should
match against a configured instance. `@Parameter` fields on the class are exactly the settings
exposed in the configuration UI for that scenario.

## Scenarios

| Display name | Class | Description |
|---------------|-------|--------------|
| Trade only in days | `ByDays` | Keeps only trades opened on the checked days of the week; trades opened on an unchecked day are removed. |
| Trade only in hours | `ByHours` | Keeps only trades opened in the checked hours (0–23); trades opened in an unchecked hour are removed. |
| Trade only in months | `ByMonths` | Keeps only trades opened in the checked months; trades opened in an unchecked month are removed. |
| Exclude % of trades with biggest profit | `ExcludePctTradesWithBiggestPl` | Sorts trades by P/L and removes the top `TradesPct`% with the biggest profit (balance orders are skipped, not counted). |
| Exclude % of trades with biggest loss | `ExcludePctTradesWithLowestPl` | Sorts trades by P/L and removes the bottom `TradesPct`% (the biggest losses / lowest P/L). |
| Exclude short trades | `ExcludeShortTrades` | Walks the trade list in original order and removes trades whose duration is under `Minutes` minutes, stopping once `TradesPct`% of all trades have been removed. |
| Exclude trades with biggest profit | `ExcludeTradesWithBiggestPl` | Sorts trades by P/L and removes the `Trades` trades with the biggest profit. |
| Exclude trades with lowest profit | `ExcludeTradesWithLowestPl` | Sorts trades by P/L and removes the `Trades` trades with the lowest profit (biggest losses). |
| Exclude overlapping trades | `ExludeOverlappingTrades` | Sorts trades by open time and removes any trade that opens before the previously kept trade's close time. |
| Remove balance transactions | `RemoveBalanceTransactions` | Removes all balance/deposit orders (`order.isBalanceOrder()`) from the trade list. |
| Remove pending trades | `RemovePendingTrades` | Removes all pending/unfilled orders (`order.isPendingOrder()`) from the trade list. |
| Swap | `Swap` | Adds a simulated swap/rollover cost to every trade's commission+swap field, using separate long/short swap rates (triple swap applied Wednesday at 23:00). |
| Take every second trade | `TakeEverySecondTrade` | Sorts trades by open time and removes every other trade, keeping the 1st, 3rd, 5th, ... |
| Take maximum trades per day | `TakeMaxTradesPerDay` | Sorts trades by open time and removes any trade beyond the `Trades`-th one opened on the same calendar day. |
| Use fixed lots | `UseFixedLots` | Recomputes each trade's P/L and size as if a fixed lot size (`Size`) had been used instead of the trade's original size. |

## Parameters

### Trade only in days (`ByDays`)

Seven boolean day toggles, all defaulting to `true` (checked = day is traded). No min/max/step —
boolean parameters.

| Parameter | Default |
|-----------|---------|
| Monday | true |
| Tuesday | true |
| Wednesday | true |
| Thursday | true |
| Friday | true |
| Saturday | true |
| Sunday | true |

### Trade only in hours (`ByHours`)

Twenty-four boolean hour toggles (`Hour 0` … `Hour 23`), all defaulting to `true`.

| Parameter | Default |
|-----------|---------|
| Hour 0 | true |
| Hour 1 | true |
| Hour 2 | true |
| Hour 3 | true |
| Hour 4 | true |
| Hour 5 | true |
| Hour 6 | true |
| Hour 7 | true |
| Hour 8 | true |
| Hour 9 | true |
| Hour 10 | true |
| Hour 11 | true |
| Hour 12 | true |
| Hour 13 | true |
| Hour 14 | true |
| Hour 15 | true |
| Hour 16 | true |
| Hour 17 | true |
| Hour 18 | true |
| Hour 19 | true |
| Hour 20 | true |
| Hour 21 | true |
| Hour 22 | true |
| Hour 23 | true |

### Trade only in months (`ByMonths`)

Twelve boolean month toggles (January … December), all defaulting to `true`.

| Parameter | Default |
|-----------|---------|
| January | true |
| February | true |
| March | true |
| April | true |
| May | true |
| June | true |
| July | true |
| August | true |
| September | true |
| October | true |
| November | true |
| December | true |

### Exclude % of trades with biggest profit (`ExcludePctTradesWithBiggestPl`)

Display template: `Exclude #TradesPct#% trades with biggest profit`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| % Trades (`TradesPct`) | 5 | 1 | 100 | 1 | Percentage of trades to remove, taken from the top of the profit-sorted list. |

### Exclude % of trades with biggest loss (`ExcludePctTradesWithLowestPl`)

Display template: `Exclude #TradesPct#% trades with biggest loss`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| % Trades (`TradesPct`) | 5 | 1 | 100 | 1 | Percentage of trades to remove, taken from the bottom of the profit-sorted list. |

### Exclude short trades (`ExcludeShortTrades`)

Display template: `Exclude #TradesPct#% trades which takes less than #Minutes# minutes`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| % Trades (`TradesPct`) | 5 | 1 | 100 | 1 | Cap on how many trades (as % of all trades) may be removed. |
| Minutes (`Minutes`) | 10 | 1 | 100000 | 1 | Duration threshold in minutes; trades shorter than this are candidates for removal. |

### Exclude trades with biggest profit (`ExcludeTradesWithBiggestPl`)

Display template: `Exclude #Trades# trades with biggest profit`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Trades (`Trades`) | 2 | 1 | 10000 | 1 | Number of highest-profit trades to remove. |

### Exclude trades with lowest profit (`ExcludeTradesWithLowestPl`)

Display template: `Exclude #Trades# trades with lowest profit`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Trades (`Trades`) | 2 | 1 | 10000 | 1 | Number of lowest-profit (worst) trades to remove. |

### Exclude overlapping trades (`ExludeOverlappingTrades`)

No parameters.

### Remove balance transactions (`RemoveBalanceTransactions`)

No parameters.

### Remove pending trades (`RemovePendingTrades`)

No parameters.

### Swap (`Swap`)

Display template: `Swap (Long: #swapLongInput#,Short: #swapShortInput#)`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| SwapDev Long (`swapLongInput`) | 10 | -1000 | 1000 | 0.01 | Swap rate applied to long trades. |
| SwapDev Short (`swapShortInput`) | -10 | -1000 | 1000 | 0.01 | Swap rate applied to short trades. |

### Take every second trade (`TakeEverySecondTrade`)

No parameters.

### Take maximum trades per day (`TakeMaxTradesPerDay`)

Display template: `Take maximum #Trades# trades per day`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Trades (`Trades`) | 2 | 1 | 10000 | 1 | Maximum number of trades kept per calendar day; extra trades on the same day are removed. |

### Use fixed lots (`UseFixedLots`)

Display template: `Use #Size# fixed lots`

| Parameter | Default | Min | Max | Step | Meaning |
|-----------|---------|-----|-----|------|---------|
| Size (`Size`) | 0.1 | 0.01 | 100 | 0.1 | Fixed lot size substituted for every trade's original size; P/L is rescaled proportionally. |

## Related

- [What If simulations — robustness test](../robustness-tests/what-if.md)
- [Monte Carlo randomization methods catalog](monte-carlo.md)
- [Snippets hub](README.md)
- [Cross-checks settings](../settings/cross-checks.md)
