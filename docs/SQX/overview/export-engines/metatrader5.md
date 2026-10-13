# MetaTrader 5 — export engine

> Exports a generated strategy as an MQL5 Expert Advisor (`*.mq5`) for MetaTrader 5.

## What it produces

- **Output:** an MQL5 **Expert Advisor** — the source code of a runnable MT5 EA.
- **File extension:** `.mq5`.
- **Where to place it:** save into the MetaTrader 5 data folder (the `MQL5/Experts` directory),
  where MetaEditor can compile it and MT5 can run it.
- **Engine id:** `mt5`. Registered name: *Expert Advisor for MetaTrader5 (\*.MQ5)*.

## Templates

The engine lives in `internal/extend/Code/MetaTrader5/` as a set of **FreeMarker** templates.

- **`Main.tpl`** — entry template. Opens with the metadata header (name, `id=mt5`,
  `extension=mq5`), `<#include>`s the `.inc` section files, then emits the EA: parameters →
  indicator handles → the `OnBarUpdate`/tick loop → entry/exit rules → money management → ATM exits.
- **`.inc` section files** — `mt5Parameters.inc`, `mt5Blocks.inc`, `mt5Size.inc`, plus the shared
  Functions / TradingOptions / ATM / MoneyManagement sections.
- **Runtime library shipped with the export:** `SQ.mqh` (the EA runtime library).
- **`blocks/`** — **one `.tpl` per building block** (~581 block templates), e.g. `ADX.tpl`,
  `ATR.tpl`. This is where each block's XML turns into MQL5 code.
- **Sub-folders:** `CustomFunctions/`, `ExitMethods/`, `MoneyManagement/`, `TradingOptions/`,
  `blocks/`.

## How a strategy is rendered

A generated strategy is an engine-neutral **XML rule tree**. To export it, SQX feeds that XML to
FreeMarker: `Main.tpl` renders the file skeleton, and for **each `<Block>`** in the XML it invokes
the matching `blocks/<Block>.tpl`, which emits the MQL5 expression (often a call into `SQ.mqh`).
Templates use helpers such as `getOptions("StrategyName"|"Version"|"Date")`,
`getRulesCountForEvent("OnBarUpdate")`, `<@printBacktestInfo/>` and
`<@printBlockChild block "#Param#" shift />` to recursively render nested child parameters.

Every building block exists in **two** places: its **logic** as a Java snippet in
`internal/extend/Snippets/SQ/Blocks/` (used for backtesting/evaluation) and its **rendering** as one
`.tpl` per engine in `MetaTrader5/blocks/`. A block that has no MT5 `.tpl` cannot be exported to MT5.

## Notes & limitations

- Produces MQL5 source only; compilation to a runnable `.ex5` happens in MetaEditor / MT5.
- MQL5 differs from MQL4 (indicator handles, order model), so MT5 is its own engine folder with its
  own macros — an MT4 EA is not an MT5 EA.
- The MT5 export path supports an optional broker-protection lock inserted into `OnTick()` (checks
  the account company/server) when a broker is configured.
- A MetaTrader5 (Brazil) variant is added dynamically only for the Brazilian edition.

## Related

- [Export engines index](README.md)
- Sibling engines: [MetaTrader 4](metatrader4.md) · [JForex](jforex.md) ·
  [EasyLanguage](easylanguage.md) · [PseudoCode](pseudocode.md)
- How the strategy XML is produced: [../algowizard/xml-generation.md](../algowizard/xml-generation.md)
- The block catalog & parameters: [../algowizard/config-xml.md](../algowizard/config-xml.md)
- Export developer architecture: [../../onboard/12-export/](../../onboard/12-export/README.md)
