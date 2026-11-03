# Exit methods — full catalog

> Reference enumeration of the built-in exit-method snippets a strategy's Exit block can use
> (Stop Loss, Profit Target, Trailing Stop, Move SL to Break Even, Exit After Bars). This is a
> lookup table; for the engine legend see the [Snippets hub](README.md).

## How the set is assembled

Each exit method is a snippet class extending `ExitMethod`
(`projects/libs/SQTradingLib/.../ExitMethod.java`), registered by `ExitMethodsList`
(`setDirName("ExitMethods")`) and loaded from the `ExitMethods` snippet directory
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/ExitMethods/`). The set is
**extensible** — a user snippet dropped into that directory becomes a new selectable exit block.

Each class carries `@ClassConfig(name="...")` (the label shown in the exit-method picker) and
`@SortOrder(n)`. Some also carry `@ForEngine("...")` at the class level restricting which trading
engine(s) the method is available for (`*` = all engines, a leading `-` excludes an engine; `SP` =
Stockpicker, `SA` = Single-asset cloud strategy).

Unlike money-management snippets, most exit-method parameters are **formula-typed**
(`IFormula`, `@Editor(type=Editors.Formula, formulaName="...")`) rather than plain numeric
`@Parameter` ranges — the value is a Range/RangeLevel/SLPT formula (fixed pips, ATR-based,
indicator-based, etc.) built in the Formula editor, not a min/max/step spinner. `ExitAfterBars` is
the exception, using a plain numeric parameter. `@ExitType(...)` marks which built-in exit slot
(StopLoss, ProfitTarget, ExitAfterBars) the parameter feeds. `showIfDefault=false` means the field
is hidden in the UI while left at its default (unset) value.

## Catalog

| Display name | Class | Engines | Sort order | What it does |
|---------------|-------|---------|------------|--------------|
| Stop Loss | `StopLoss` | all | 100 | Sets/maintains the order's Stop Loss from a Range/SLPT formula. |
| Profit Target | `ProfitTarget` | all | 200 | Sets/maintains the order's Profit Target from a Range/SLPT formula. |
| Move SL to BE | `MoveSL2BE` | all, −SP,−SA | 300 | Moves the Stop Loss to break-even (+ optional offset) once a trigger level is reached. |
| Trailing Stop | `TrailingStop` | all, −SP,−SA | 400 | Trails the Stop Loss behind price once an activation level is reached. |
| Exit After Bars | `ExitAfterBars` | all | 500 | Closes the trade automatically after a fixed number of bars in trade. |

## Parameters

### Stop Loss (`StopLoss`)

No class-level `@ForEngine` restriction (available on all engines).

| Parameter | Type | Category | Editor | Meaning |
|-----------|------|----------|--------|---------|
| StopLoss | `IFormula` | Basic | Formula (`SLPT`) | Stop-loss distance/level formula. `showIfDefault=false`; tagged `@ExitType(ExitTypes.StopLoss)`. No numeric min/max/step — value is built in the Formula editor. |

No plain-numeric parameters; no `@Help` text on the field.

### Profit Target (`ProfitTarget`)

No class-level `@ForEngine` restriction (available on all engines).

| Parameter | Type | Category | Editor | Meaning |
|-----------|------|----------|--------|---------|
| ProfitTarget | `IFormula` | Basic | Formula (`SLPT`) | Profit-target distance/level formula. `showIfDefault=false`; tagged `@ExitType(ExitTypes.ProfitTarget)`. No numeric min/max/step. |

No plain-numeric parameters; no `@Help` text on the field.

### Move SL to BE (`MoveSL2BE`)

`@ForEngine("*,-SP,-SA")` — all engines except Stockpicker and Single-asset.

| Parameter | Type | Category | Editor | Meaning |
|-----------|------|----------|--------|---------|
| Move SL to BE (`MoveSL2BE`) | `IFormula` | Advanced | Formula (`RangeLevel`) | Level at which the Stop Loss is moved to break-even. Default `SQ.Formulas.RangeLevel.None` (disabled); `showIfDefault=false`. Help: "Move StopLoss to Break Even". |
| SL to BE - Add pips (`SL2BEAddPips`) | `IFormula` | Advanced | Formula (`Range`) | Extra offset (in pips) added to the break-even level. `showIfDefault=false`. No `@Help` text. |

No plain-numeric min/max/step parameters — both fields are Formula-typed.

### Trailing Stop (`TrailingStop`)

`@ForEngine("*,-SP,-SA")` — all engines except Stockpicker and Single-asset.

| Parameter | Type | Category | Editor | Meaning |
|-----------|------|----------|--------|---------|
| Trailing Stop (`TrailingStop`) | `IFormula` | Advanced | Formula (`RangeLevel`) | Trailing distance formula. `showIfDefault=false`. No `@Help` text. |
| TS Activation Level (`TrailingActivation`) | `IFormula` | Advanced | Formula (`Range`) | Profit level (in the Range formula) that must be reached before trailing starts. `showIfDefault=false`. No `@Help` text. |

No plain-numeric min/max/step parameters — both fields are Formula-typed.

### Exit After Bars (`ExitAfterBars`)

No class-level `@ForEngine` restriction (available on all engines).

| Parameter | Default | Min | Max | Builder Min | Builder Max | Step | Meaning |
|-----------|---------|-----|-----|-------------|-------------|------|---------|
| ExitAfterBars | 0 | 0 | 99,999 | 5 | 500 | 1 | Number of bars after which the trade is automatically closed. `category="Advanced"`, `showIfDefault=false`; tagged `@ExitType(ExitTypes.ExitAfterBars)`. `builderMinValue`/`builderMaxValue` set the range the strategy Builder/Optimizer samples from, distinct from the hard `minValue`/`maxValue` bounds. |

## Related

- Snippets hub: [`README.md`](README.md)
- Money management catalog: [`money-management.md`](money-management.md)
- Trading options catalog: [`trading-options.md`](trading-options.md)
- Loader: `ExitMethodsList` (`projects/libs/SQTradingLib/.../exit/ExitMethodsList.java`)
