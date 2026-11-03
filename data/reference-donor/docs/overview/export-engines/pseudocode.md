# PseudoCode — export engine

> Exports a generated strategy as human-readable pseudo code (`*.txt`) for reading and verifying its
> logic — not for live trading.

## What it produces

- **Output:** a **human-readable pseudo-code** description of the strategy's logic.
- **File extension:** `.txt`.
- Registered name: *Pseudo Code (\*.TXT)*.
- **Purpose:** good for **reading and verifying** what a strategy actually does — its entry/exit
  rules, indicators and parameters — in plain, platform-neutral text. It is **not** runnable and
  **not** meant for live trading.

## Templates

The engine lives in `internal/extend/Code/PseudoCode/` as a set of **FreeMarker** templates.

- **`Main.tpl`** — entry template. Opens with the metadata header (name, `extension=txt`),
  `<#include>`s the `.inc` section files, then emits the readable description: parameters →
  indicators → entry/exit rules → money management → ATM exits.
- **`.inc` section files** — `BuildingBlocks.inc`, `pseudoBlocks.inc`, `pseudoParameters.inc`, plus
  the shared section files.
- **Example strategies:** `Example.xml` and `Example2.xml` ship alongside the templates.
- **`blocks/`** — **one `.tpl` per building block** (~749 block templates — the widest block
  coverage of any engine), e.g. `ADX.tpl`, `ATR.tpl`. This is where each block's XML turns into a
  readable expression.
- **Sub-folders:** `ExitMethods/`, `MoneyManagement/`, `TradingOptions/`, `blocks/`.

## How a strategy is rendered

A generated strategy is an engine-neutral **XML rule tree**. To export it, SQX feeds that XML to
FreeMarker: `Main.tpl` renders the file skeleton, and for **each `<Block>`** in the XML it invokes
the matching `blocks/<Block>.tpl`, which emits the readable pseudo-code expression. Templates use
helpers such as `getOptions("StrategyName"|"Version"|"Date")`,
`getRulesCountForEvent("OnBarUpdate")`, `<@printBacktestInfo/>` and
`<@printBlockChild block "#Param#" shift />` to recursively render nested child parameters.

Every building block exists in **two** places: its **logic** as a Java snippet in
`internal/extend/Snippets/SQ/Blocks/` (used for backtesting/evaluation) and its **rendering** as one
`.tpl` per engine in `PseudoCode/blocks/`. A block that has no PseudoCode `.tpl` cannot be rendered
into pseudo code.

## Notes & limitations

- **Read-only / not tradable.** The `.txt` output describes the strategy for a human to read and
  verify; there is nothing to compile or run on a trading platform.
- Because it only has to render text (no platform runtime, order model or broker lock), it can cover
  the largest set of blocks (~749 templates), so it is a good way to inspect a strategy that other
  engines cannot fully export.

## Related

- [Export engines index](README.md)
- Sibling engines: [MetaTrader 4](metatrader4.md) · [MetaTrader 5](metatrader5.md) ·
  [JForex](jforex.md) · [EasyLanguage](easylanguage.md)
- How the strategy XML is produced: [../algowizard/xml-generation.md](../algowizard/xml-generation.md)
- The block catalog & parameters: [../algowizard/config-xml.md](../algowizard/config-xml.md)
- Export developer architecture: [../../onboard/12-export/](../../onboard/12-export/README.md)
