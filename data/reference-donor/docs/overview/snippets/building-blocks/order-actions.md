# Order & Other Actions — Building Block Catalog

> Reference enumeration of the `Order` and `OtherActions` building-block snippets (opening/closing/
> modifying trades, plus misc actions like variables, drawing, logging, and email). This is a
> lookup table; for the general building-block model see [README.md](README.md).

## How this file is organized

Both folders hold **action** blocks: they extend `SQ.Internal.ActionBlock` and implement
`OnAction()` (no return value — they cause a side effect such as opening/closing an order). Source:
`work_directory/StrategyQuant/internal/extend/Snippets/SQ/Blocks/Order/` (12 files, split into
`Open/`, `Close/`, `Modify/` subfolders) and
`work_directory/StrategyQuant/internal/extend/Snippets/SQ/Blocks/OtherActions/` (8 files). There
are no abstract/internal base classes to exclude in either folder, though several `Order/Open`
classes extend each other concretely (see note below).

Most `Order` blocks share the same **order-identification parameters** used elsewhere in this
snippet set: `Symbol` (default `"Current"`), `Direction` (Long=1/Short=-1/Any=0), `MagicNumber`
(default references the `MagicNumber` variable), `Comment` (substring match). These are called out
only where a block has additional parameters worth noting.

## Order actions

### Opening orders

`EnterAtStop` extends `EnterAtMarket`; `EnterAtLimit` extends `EnterAtStop` (same parameters,
places a limit instead of a stop order); `EnterReverseAtMarket` extends `EnterAtMarket` and closes
any opposite-direction position before opening the new one.

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (MKT) Enter at market | `EnterAtMarket` | Opens an order at the current market price. | `Symbol`, `Direction` (Long=1/Short=-1), `Size` (formula, required), `MagicNumber`, `Comment`, `AllowDuplicateTrades` — bool, default false, `ExitMethods[]`. |
| (STOP) Enter at stop | `EnterAtStop` | Opens a stop order at a computed price level. | All of `EnterAtMarket` plus `Price` (formula, required), `BarsValid` — default 0, min 0, max 1000, step 1 (builder range 0-200; 0 = never expires), `Replace Existing Order` (`ReplaceExisting`) — bool, default true. |
| (LMT) Enter at limit | `EnterAtLimit` | Opens a limit order at a computed price level. | Same as `EnterAtStop` (inherited, unchanged). |
| (MKT) Enter/reverse at market | `EnterReverseAtMarket` | Opens an order at market price; if an opposite-direction order exists, closes it first. | Same as `EnterAtMarket` (inherited). |

### Closing orders

| Display name | Class | Description | Parameters |
|---|---|---|---|
| Close position (`ClosePosition`) | `ClosePosition` | Closes the first matching position, or part of it. | Order identification (incl. `Direction`) + `Size` (formula, `CloseSize`, required). |
| Close all positions (`CloseAllPositions`) | `CloseAllPositions` | Closes every position matching the criteria. | Order identification (incl. `Direction`). |
| Close most profitable position | `CloseBestPosition` | Closes the matching position with the highest current P/L. | Order identification (incl. `Direction`). |
| Close least profitable position | `CloseWorstPosition` | Closes the matching position with the lowest current P/L. | Order identification (incl. `Direction`). |
| Close pending order (`ClosePendingOrder`) | `ClosePendingOrder` | Closes the first matching pending order. | Order identification (incl. `Direction`). |
| Close all pending orders (`CloseAllPendingOrders`) | `CloseAllPendingOrders` | Closes every pending order matching the criteria. | Order identification (incl. `Direction`). |

### Modifying orders

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (SL) Set Stop Loss | `SetStopLoss` | Sets (or moves) Stop Loss to a computed level on the matching order. | Order identification (incl. `Direction`) + `StopLoss` (formula, `RangeLevel`). |
| (PT) Set Profit Target | `SetProfitTarget` | Sets (or moves) Profit Target to a computed level on the matching order. | Order identification (incl. `Direction`) + `ProfitTarget` (formula, `RangeLevel`). |

## Other actions

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (VAR) Assign variable | `AssignVariable` | Assigns a computed value (or boolean) to a strategy variable. | `Variable` — variable selection. `Value` — formula. |
| Custom action | `CustomAction` | Placeholder for a user-defined platform command (MQL command or custom function); not executed by StrategyQuant itself, only by the target platform. | `Command` — free-text editbox. |
| (v) Draw Down Arrow | `DrawDownArrow` | Draws a down arrow marker on the chart (platform-rendered; placeholder in StrategyQuant). | `Shift`. |
| (^) Draw Up Arrow | `DrawUpArrow` | Draws an up arrow marker on the chart (platform-rendered; placeholder in StrategyQuant). | `Shift`. |
| (\|) Draw Vertical Line | `DrawVerticalLine` | Draws a vertical line on the chart (platform-rendered; placeholder in StrategyQuant). | `Shift`. |
| Log to file (`LogToFile`) | `LogToFile` | Logs a message to a file under the platform's tester/experts files folder (platform-rendered; placeholder in StrategyQuant). | `Filename` — default "some_logfile.txt". `Message` — default "some message". |
| Log to journal (`LogToJournal`) | `LogToJournal` | Logs a message to the platform's Strategy Tester Journal / Experts log (platform-rendered; placeholder in StrategyQuant). | `Message` — default "some message". |
| Send email (`SendEmail`) | `SendEmail` | Sends an email via the platform's configured SMTP settings (platform-rendered; placeholder in StrategyQuant). | `EmailSubject` — default "Some subject". `Message` — default "some message". |

Note: `DrawDownArrow`, `DrawUpArrow`, `DrawVerticalLine`, `LogToFile`, `LogToJournal`,
`CustomAction`, and `SendEmail` all have an empty `OnAction()` body in the StrategyQuant Java
engine — their `@Help` text notes they are placeholders for the Wizard / for platform code
generation (e.g. MT4/MT5 export), not executed directly by the SQX simulator.

## Related

- Building blocks hub: [README.md](README.md)
- Strategy control (position/order state these actions read before acting): [`strategy-control.md`](strategy-control.md)
- Functions (formulas/values feeding `Size`, `Price`, `StopLoss`, `ProfitTarget`): [`functions.md`](functions.md)
- Comparisons (conditions that gate these actions in entry/exit rules): [`comparisons.md`](comparisons.md)
