# Formula snippets — full catalog

> Reference enumeration of the built-in **Formula** blocks used to compute close sizes, entry
> prices, ranges, SL/PT range levels, and position sizes inside strategy building blocks.

## How the set is assembled

Each formula is a snippet class extending `SQ.Internal.FormulaBlock` (position-size formulas
extend `SQ.Internal.MMFormulaBlock`), annotated with `@Formula(order=…, name=…, formula=…)`. The
`formula` attribute names the **group** the block belongs to — `CloseSize`, `Price`, `Range`,
`RangeLevel`, `SLPT`, `Size` — which corresponds one-to-one to a snippet subfolder under
`work_directory/StrategyQuant/internal/extend/Snippets/SQ/Formulas/`. Within a group, blocks are
listed in the picker ordered by `order` (ascending). `noneValue=true` marks the "no value" choice
for that group; `priceLevel=true` marks a block that resolves to an absolute price level rather
than an offset; `@IgnoreInBuilder` hides a block from the random Builder generator (still usable
manually). `RangeLevel` and `SLPT` blocks additionally carry `@SLPTValue(SLPTValues.X)` on their
`@Parameter` fields, tagging which field represents the ATR multiple / ATR period / pips value /
percent value for cross-block introspection (e.g. by `CBlockNegater`).

Each block implements `evaluateFormula(StrategyBase strategy, String symbol, double price, int
direction)`, returning the computed value; `Size` formulas instead implement `computeSize(...)`.

## CloseSize

What fraction/amount of an open position a close/exit action closes.

| Display name | Class | Order | Description |
|---|---|---|---|
| Full position | `FullPosition` | 100 | Closes the entire position. `evaluateFormula` always returns `0` (the "close full size" sentinel). No parameters. |

## Price

Used where an entry/exit action needs an explicit price expression.

| Display name | Class | Order | Description |
|---|---|---|---|
| Use formula | `UseFormula` | 400 | Evaluates an arbitrary nested block (`Value`) and returns it as the price. `priceLevel=true`. Auto-detects at runtime whether `Value` returns a boolean (via its `BuildingBlock.returnType()`) to decide `isBooleanValue()`. |

**Parameters — Use formula**

| Name | Type | Notes |
|---|---|---|
| `Value` | `IBlock` | Nested block whose evaluated result is used as the price; no numeric bounds (it's a block reference, not a scalar). |

## Range

Generic distance/range value (in price or pips), independent of direction — used e.g. for
indicator ranges.

| Display name | Class | Order | Description |
|---|---|---|---|
| None | `None` | 100 | No range defined; returns `Order.NOT_DEFINED`. `noneValue=true`. No parameters. |
| Fixed value (in pips) | `FixedValue` | 200 | Fixed pip distance, converted to real price via `strategy.convertPipsToRealPrice`. |
| ATR-based value | `ATRBasedValue` | 300 | Distance = `Value * ATR(AtrPeriod)`. Supports Stockpicker mode (via TALib ATR) and normal chart mode (cached ATR). |
| Range in pips | `PriceRange` | 500 | Evaluates a nested block (`Value`) in pips. `@IgnoreInBuilder`. |

**Parameters — Fixed value (in pips)**

| Name | Type | Default | Min | Max | Step | Builder min/max | Postfix |
|---|---|---|---|---|---|---|---|
| `Value` | double | 50 | 1 | 9999999 | 1 | 5 / 100 (step 1) | pips |

**Parameters — ATR-based value**

| Name | Type | Default | Min | Max | Step | Builder min/max | Postfix |
|---|---|---|---|---|---|---|---|
| `Value` | double | 1 | 0.01 | 9999 | 0.1 | 1 / 5 | `* ATR(` |
| `AtrPeriod` | int | 20 | 1 | 9999 | 5 | — | `)` |

**Parameters — Range in pips**

| Name | Type | Notes |
|---|---|---|
| `Value` | `IBlock` | Nested block evaluated in pips; postfix `pips`. |

## RangeLevel

Like `Range`, but resolves to an absolute price level relative to the order's `price` and
`direction` (used for entry range boundaries / trailing-style levels). Fields are additionally
tagged with `@SLPTValue` for cross-block value introspection.

| Display name | Class | Order | Description |
|---|---|---|---|
| None | `None` | 100 | No level defined; returns `Order.NOT_DEFINED`. `noneValue=true`. No parameters. |
| Fixed value (in pips) | `FixedValue` | 200 | `price ∓ pips` (subtracted for Long, added for Short), tagged `@SLPTValue(ValueInPips)`. |
| ATR-based value | `ATRBasedValue` | 300 | `price ∓ (Value * ATR(AtrPeriod))`; tagged `@SLPTValue(ATRMultiple)` / `@SLPTValue(ATRPeriod)`. |
| Range in pips | `PriceRange` | 500 | Evaluates a nested block (pips), then applies it against `price` by direction. `@IgnoreInBuilder`. |
| Price level | `PriceLevel` | 700 | Evaluates a nested block (`Value`) directly as the absolute price level. |

**Parameters — Fixed value (in pips)**

| Name | Type | Default | Min | Max | Step | Builder min/max | Postfix | SLPTValue tag |
|---|---|---|---|---|---|---|---|---|
| `Value` | double | 50 | 1 | 9999999 | 1 | 5 / 500 | pips | `ValueInPips` |

**Parameters — ATR-based value**

| Name | Type | Default | Min | Max | Step | Builder min/max | Postfix | SLPTValue tag |
|---|---|---|---|---|---|---|---|---|
| `Value` | double | 1 | 0.01 | 9999 | 0.1 | 1 / 5 | `* ATR(` | `ATRMultiple` |
| `AtrPeriod` | int | 20 | 1 | 9999 | 5 | — | `)` | `ATRPeriod` |

**Parameters — Range in pips / Price level**

| Name | Type | Notes |
|---|---|---|
| `Value` | `IBlock` | Nested block; `PriceRange` postfix `pips`, `PriceLevel` no postfix (absolute price). |

## SLPT

Stop-Loss / Profit-Target level formulas. Resolve to an absolute price level relative to the
order's open `price` and `direction`.

| Display name | Class | Order | Description |
|---|---|---|---|
| None | `None` | 100 | No SL/PT defined; returns `Order.NOT_DEFINED`. `noneValue=true`. No parameters. |
| Fixed value (in pips) | `FixedValue` | 300 | `price ± pips` by direction; tagged `@SLPTValue(ValueInPips)`. |
| Percent value | `PctValue` | 300 | `price ± (price/100 * Value%)` by direction; tagged `@SLPTValue(ValueInPct)`. |
| ATR-based value | `ATRBasedValue` | 400 | `price ± (Value * ATR(AtrPeriod))` by direction; tagged `@SLPTValue(ATRMultiple)` / `@SLPTValue(ATRPeriod)`. Supports Stockpicker mode. |
| Value from formula (in pips) | `ValueFromFormula` | 600 | Evaluates a nested block in pips, then applies by direction. `@IgnoreInBuilder`. |
| Price level | `PriceLevel` | 700 | Evaluates a nested block (`Value`) directly as the absolute price level. |

**Parameters — Fixed value (in pips)**

| Name | Type | Default | Min | Max | Step | Builder min/max | Postfix | SLPTValue tag |
|---|---|---|---|---|---|---|---|---|
| `Value` | double | 50 | 1 | 9999999 | 1 | 5 / 500 | pips | `ValueInPips` |

**Parameters — Percent value**

| Name | Type | Default | Min | Max | Step | Builder min/max | Postfix | SLPTValue tag |
|---|---|---|---|---|---|---|---|---|
| `Value` | double | 5 | 1 | 99 | 0.1 | 5 / 50 | % | `ValueInPct` |

**Parameters — ATR-based value**

| Name | Type | Default | Min | Max | Step | Builder min/max | Postfix | SLPTValue tag |
|---|---|---|---|---|---|---|---|---|
| `Value` | double | 1 | 0.01 | 9999 | 0.1 | 1 / 5 | `* ATR(` | `ATRMultiple` |
| `AtrPeriod` | int | 20 | 1 | 9999 | 5 | — | `)` | `ATRPeriod` |

**Parameters — Value from formula / Price level**

| Name | Type | Notes |
|---|---|---|
| `Value` | `IBlock` | Nested block; `ValueFromFormula` interprets the result as pips, `PriceLevel` as an absolute price. |

## Size

Position-size formulas; extend `MMFormulaBlock` and implement `computeSize(...)` instead of
`evaluateFormula(...)`.

| Display name | Class | Order | Description |
|---|---|---|---|
| Define own size | `DefineOwnSize` | 100 | Fixed, user-entered position size. `@IgnoreInBuilder`. |
| Use global Money Management | `UseGlobalMM` | 200 | Delegates sizing to the project's configured Money Management method (`strategy.getGlobalMMMethod()` or the settings' `MoneyManagement`), defaulting to size `1` if none is set. No parameters. |

**Parameters — Define own size**

| Name | Type | Default | Min | Max |
|---|---|---|---|---|
| `Value` | double | 0.1 | 0.01 | 999999999 |

## Related

- Databank columns / stats metrics reference: [`../stats-metrics.md`](../stats-metrics.md)
- Snippets hub: [`README.md`](README.md)
- Source: `work_directory/StrategyQuant/internal/extend/Snippets/SQ/Formulas/`
