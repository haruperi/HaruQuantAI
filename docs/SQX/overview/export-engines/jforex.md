# JForex — export engine

> Exports a generated strategy as a JForex strategy written in Java (`*.java`) for Dukascopy JForex.

## What it produces

- **Output:** a **JForex strategy** — Java source implementing the Dukascopy JForex strategy API.
- **File extension:** `.java`.
- **Engine id:** `jforex`. Registered name: *Expert Advisor for JForex (\*.java)*.

## Templates

The engine lives in `internal/extend/Code/JForex/` as a set of **FreeMarker** templates.

- **`Main.tpl`** — entry template. Opens with the metadata header (name, `id=jforex`,
  `extension=java`), `<#include>`s the `.inc` section files, then emits the strategy: parameters →
  indicators → the bar/tick event loop → entry/exit rules → money management → ATM exits.
- **`.inc` section files** — the shared Functions / Parameters / Blocks / Size / TradingOptions /
  ATM / MoneyManagement sections in JForex (Java) syntax.
- **Runtime sources shipped with the export:** `SQ.java` and `SQIndicators.java` (the Java runtime
  and indicator helpers used by the generated strategy).
- **`blocks/`** — **one `.tpl` per building block** (~534 block templates), e.g. `ADX.tpl`,
  `ATR.tpl`. This is where each block's XML turns into Java code.
- **Sub-folders:** `CustomFunctions/`, `ExitMethods/`, `MoneyManagement/`, `TradingOptions/`,
  `blocks/`.

## How a strategy is rendered

A generated strategy is an engine-neutral **XML rule tree**. To export it, SQX feeds that XML to
FreeMarker: `Main.tpl` renders the file skeleton, and for **each `<Block>`** in the XML it invokes
the matching `blocks/<Block>.tpl`, which emits the Java expression (often a call into `SQ.java` /
`SQIndicators.java`). Templates use helpers such as
`getOptions("StrategyName"|"Version"|"Date")`, `getRulesCountForEvent("OnBarUpdate")`,
`<@printBacktestInfo/>` and `<@printBlockChild block "#Param#" shift />` to recursively render
nested child parameters.

Every building block exists in **two** places: its **logic** as a Java snippet in
`internal/extend/Snippets/SQ/Blocks/` (used for backtesting/evaluation) and its **rendering** as one
`.tpl` per engine in `JForex/blocks/`. A block that has no JForex `.tpl` cannot be exported to JForex.

## Notes & limitations

- The output is Java source (the JForex strategy API), not an MQL EA — despite the "Expert Advisor"
  wording in the registered name.
- The generated `.java` is compiled and run inside the Dukascopy JForex platform, not by SQX.
- The JForex export has no MT-style broker-protection lock (that post-processing is MT4/MT5 only).

## Related

- [Export engines index](README.md)
- Sibling engines: [MetaTrader 4](metatrader4.md) · [MetaTrader 5](metatrader5.md) ·
  [EasyLanguage](easylanguage.md) · [PseudoCode](pseudocode.md)
- How the strategy XML is produced: [../algowizard/xml-generation.md](../algowizard/xml-generation.md)
- The block catalog & parameters: [../algowizard/config-xml.md](../algowizard/config-xml.md)
- Export developer architecture: [../../onboard/12-export/](../../onboard/12-export/README.md)
