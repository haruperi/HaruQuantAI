# MetaTrader 4 — export engine

> Exports a generated strategy as an MQL4 Expert Advisor (`*.mq4`) for MetaTrader 4.

## What it produces

- **Output:** an MQL4 **Expert Advisor** — the source code of a runnable MT4 EA.
- **File extension:** `.mq4`.
- **Where to place it:** save into the MetaTrader data folder under
  `{MetaTrader Data Folder}/MQL4/Experts`, where MetaEditor can compile it and MT4 can run it.
- **Engine id:** `mt4`. Registered name: *Expert Advisor for MetaTrader4 (\*.MQ4)*.

## Templates

The engine lives in `internal/extend/Code/MetaTrader4/` as a set of **FreeMarker** templates.

- **`Main.tpl`** — entry template. Opens with the metadata header (name, `id=mt4`,
  `extension=mq4`), `<#include>`s the `.inc` section files, then emits the EA: parameters →
  indicator handles → the `OnBarUpdate`/tick loop → entry/exit rules → money management → ATM exits.
- **`.inc` section files** — `mt4Parameters.inc`, `mt4Blocks.inc`, plus the shared Functions /
  Size / TradingOptions / ATM / MoneyManagement sections.
- **Runtime libraries shipped with the export:** `SQ.mqh` (the EA runtime — `sqADX`,
  `sqOpenOrder`, …) and `OrderReliable.mqh` (reliable order sending).
- **`blocks/`** — **one `.tpl` per building block** (~579 block templates), e.g. `ADX.tpl`,
  `ATR.tpl`. This is where each block's XML turns into MQL4 code.
- **Sub-folders:** `CustomFunctions/`, `ExitMethods/`, `MoneyManagement/`, `TradingOptions/`,
  `blocks/`.

## How a strategy is rendered

A generated strategy is an engine-neutral **XML rule tree**. To export it, SQX feeds that XML to
FreeMarker: `Main.tpl` renders the file skeleton, and for **each `<Block>`** in the XML it invokes
the matching `blocks/<Block>.tpl`, which emits the MQL4 expression (often a call into `SQ.mqh`).
Templates use helpers such as `getOptions("StrategyName"|"Version"|"Date")`,
`getRulesCountForEvent("OnBarUpdate")`, `<@printBacktestInfo/>` and
`<@printBlockChild block "#Param#" shift />` to recursively render nested child parameters.

Every building block exists in **two** places: its **logic** as a Java snippet in
`internal/extend/Snippets/SQ/Blocks/` (used for backtesting/evaluation) and its **rendering** as one
`.tpl` per engine in `MetaTrader4/blocks/`. A block that has no MT4 `.tpl` cannot be exported to MT4.

## Notes & limitations

- Produces MQL4 source only; compilation to a runnable `.ex4` happens in MetaEditor / MT4.
- MT4 and MT5 are separate engines with separate template folders — an EA built here is MQL4 and
  will not compile in MT5.
- The MT4 export path supports an optional broker-protection lock inserted into `OnTick()` (checks
  the account company/server) when a broker is configured.

## Related

- [Export engines index](README.md)
- Sibling engines: [MetaTrader 5](metatrader5.md) · [JForex](jforex.md) ·
  [EasyLanguage](easylanguage.md) · [PseudoCode](pseudocode.md)
- How the strategy XML is produced: [../algowizard/xml-generation.md](../algowizard/xml-generation.md)
- The block catalog & parameters: [../algowizard/config-xml.md](../algowizard/config-xml.md)
- Export developer architecture: [../../onboard/12-export/](../../onboard/12-export/README.md)
