# Export Engines (Target Platforms) — Detailed Reference

A generated strategy is an engine-neutral **XML rule tree**. To run it on a real trading platform,
StrategyQuant X **generates source code** for that platform from the XML. Each **target engine**
(MetaTrader 4, MetaTrader 5, JForex, Tradestation/MultiCharts EasyLanguage, PseudoCode) has its own
folder of **FreeMarker templates** under `work_directory/StrategyQuant/internal/extend/Code/<Engine>/`.

This is separate from the *trading engine* a strategy is built for (see
[../algowizard/engines-and-platforms.md](../algowizard/engines-and-platforms.md)): here we mean the
**code-export** targets — what platform a finished strategy can be exported to and traded on.

Parent: [Overview index](../README.md) · related: [Export developer docs](../../onboard/12-export/README.md)

## Available export engines

Each folder's `Main.tpl` carries a metadata header (`<name>`, `<id>`, `<extension>`) that registers
the generator with SQX.

| Engine | Output | Extension | Templates folder | Page |
|--------|--------|-----------|------------------|------|
| **MetaTrader 4** | MQL4 Expert Advisor | `.mq4` | `internal/extend/Code/MetaTrader4/` | [metatrader4.md](metatrader4.md) |
| **MetaTrader 5** | MQL5 Expert Advisor | `.mq5` | `internal/extend/Code/MetaTrader5/` | [metatrader5.md](metatrader5.md) |
| **JForex** | JForex strategy (Java) | `.java` | `internal/extend/Code/JForex/` | [jforex.md](jforex.md) |
| **EasyLanguage** | Tradestation / MultiCharts code | `.el` | `internal/extend/Code/EasyLanguage/` | [easylanguage.md](easylanguage.md) |
| **PseudoCode** | Human-readable pseudo code | `.txt` | `internal/extend/Code/PseudoCode/` | [pseudocode.md](pseudocode.md) |

> `internal/extend/Code/global/globalFunctions.inc` holds macros shared by all engines.
> NinjaTrader 8 export exists as an as-built extension — see the developer docs
> [../../onboard/12-export/06-ninjatrader.md](../../onboard/12-export/06-ninjatrader.md).

## How code generation works (FreeMarker)

Every engine folder follows the same layout, driven by **FreeMarker** (`.tpl` / `.inc`):

- **`Main.tpl`** — the entry template. Starts with a metadata header comment, `<#include>`s the
  engine's `.inc` files, then emits the platform file (parameters, indicator handles, the
  `OnBarUpdate`/tick loop, entry/exit rules, money management, ATM exits).
- **`.inc` files** — shared sections: `Functions.inc`, `Parameters.inc` (`mt4Parameters.inc`, …),
  `Blocks.inc` (`mt4Blocks.inc`, …), `Size.inc`, `TradingOptions.inc`, `ATM.inc`,
  `MoneyManagement.inc`.
- **`blocks/`** — **one `.tpl` per building block** (e.g. `ADX.tpl`, `MathAbs` → `MathAbs.tpl`).
  This is where a block's XML is turned into platform code. Example (an MT4 block template):
  ```
  MathAbs(<@printBlockChild block "#Value#" shift />)
  ```
  `<@printBlockChild ...>` recursively renders a block's child (e.g. its `#Value#` param), so nested
  block trees render into nested platform expressions.
- **Sub-folders** `ExitMethods/`, `MoneyManagement/`, `TradingOptions/`, `CustomFunctions/` — per-topic
  template fragments.

The FreeMarker data model exposes helpers the templates call: `getOptions("StrategyName"|"Version"|
"Date")`, `getRulesCountForEvent("OnBarUpdate")`, `<@printBacktestInfo/>`, `<@printBlockChild/>`, etc.

### The block-template ↔ Java-snippet pairing

Every building block therefore exists in **two** places:

1. Its **logic** — an annotated Java **snippet** in
   `internal/extend/Snippets/SQ/Blocks/.../<Block>.java` (used for backtesting/evaluation).
2. Its **rendering** — one **`.tpl` per engine** in `internal/extend/Code/<Engine>/blocks/<Block>.tpl`
   (used to emit that block as platform source).

So adding a fully-exportable block means adding the snippet **and** a block template in each engine
that should support it. Blocks without a template for a given engine cannot be exported to it.

## COT markets as inputs

A strategy that reads COT data (COT blocks or COT custom-data values) exports every COT market it
uses as a string input: `COTSymbol1`, `COTSymbol2`, ..., numbered in the order the markets first
appear in the strategy. Each input defaults to the market SQX resolved at export, and the trader can
type any other COT market in the platform. The code builds the COT identifier from the input and the
period, e.g. `COTSymbol1 + "_52W"`. Blocks that read the same market share one input; a VIX Proxy
block without a symbol reads `VX`.

At start-up the strategy checks that the COT data file of each input exists and refuses to trade
otherwise, naming the input and the market (`COTSymbol2: COT symbol 'XYZ' does not exist ...`):

| Engine | Inputs | Check |
|--------|--------|-------|
| MetaTrader 4 / 5 | `extern` / `input string COTSymbolN` | `sqCOTCheckSymbols` asks the COT reader (`COT_IsAvailable`) for `<market>_52W`: in `OnInit` when the data is there (a missing market raises an alert and `INIT_FAILED`), otherwise on the first tick after the data arrives (alert, and the strategy opens no trades) |
| NinjaTrader 8 | `[NinjaScriptProperty] string COTSymbolN` in the "COT Data" group | `State.Historical` looks for `<market>_52W.bin` or `.csv` in the folder the `SqCOT` indicator reads and throws |
| EasyLanguage | `COTSymbolN("ES")` inputs | On the last bar of the chart `SQ_COT_GetValue(<market>_52W)` returns -1 only without a data file; the strategy raises a run-time error |

COT values read through the MetaTrader `sqCOTData()` runtime are not checked this way: that runtime
downloads its own data and alerts on a market the server does not know.

Every engine also gives the strategy a `COTLicenseCode` input. With the license filled in, the
strategy gets the COT data itself when it is missing or older than 7 days; with an empty license it
only reports missing or old data. The platform's own COT downloader still works as well.

| Engine | How the strategy downloads the COT data |
|--------|-----------------------------------------|
| MetaTrader 4 / 5 | `OnInit` starts the `SqCOTDownloader` EA on a chart of its own and hands it the license; until the data is loaded the strategy opens no new trades, and a failed download shows its cause in one alert; see [MetaTrader COT data](#metatrader-cot-data) |
| EasyLanguage | `SQ_COT_EnsureData` on the first bar and once a day: MultiCharts through the DLL, TradeStation through PowerShell in the background; see [easylanguage.md](easylanguage.md#cot-commitments-of-traders-blocks) |
| NinjaTrader 8 | `State.DataLoaded` starts the `SqCOTDownloader` indicator with the license; once a day in real time the strategy lets it download again |

The shared FreeMarker code is `internal/extend/Code/global/cotSymbols.inc`; each `Main.tpl` calls
`cotCollectSymbols` before it prints inputs or blocks. NinjaTrader exports no COT custom-data values,
so only its COT blocks get inputs.

In NinjaTrader `COTLicenseCode` is the last input of the "COT Data" group. The indicator downloads
into `Documents\NinjaTrader 8\SqCOT` in its own `DataLoaded`, which NinjaTrader runs after the
strategy's; that is why the check for the data files runs in `State.Historical`.

### MetaTrader COT data

- **Data:** `MQL4|MQL5\Files\SqCOT\*.csv`, read by the `SqCOT` indicator and the strategy. After each
  successful download the downloader copies the CSV files into `Common\Files\SqCOT`. The readers use
  the terminal's own folder first, then `Common\Files\SqCOT`.
- **`version.txt`:** the time of the last successful download (`yyyy.mm.dd hh:mi`). Older than 7 days
  means old data: the strategy keeps trading and starts the downloader. A change makes the `SqCOT`
  indicator reload within a minute.
- **`status.txt`** (local): the result of the last download - code, time, message. The strategy
  alerts once per cause.
- **`Common\Files\SqCOT\license.txt`:** the license handed to the downloader.
- **Global variable `SqCOT_DownloaderHeartbeat`:** a running downloader. At most one downloader runs
  per terminal. Without a license and without a running downloader the strategy only reports.
- **Strategy Tester:** no download. The strategy reads `Files\SqCOT` of the tester, then
  `Common\Files\SqCOT`; without data it stops at start with a message that names the folder.
- **Requirements:** Allow WebRequest for `https://cdn.strategyquantcdn.com`, Allow DLL imports,
  AutoTrading / Algo Trading, the `SqCOTDownloader` template in the templates folder.

## Adding / extending an engine

A new target engine is a new folder under `internal/extend/Code/` with its own `Main.tpl` (metadata
header) + `.inc` files + `blocks/`. Developer walkthrough:
[../../onboard/12-export/05-adding-a-platform.md](../../onboard/12-export/05-adding-a-platform.md).

## Related

- How the strategy XML that feeds these templates is produced: [../algowizard/xml-generation.md](../algowizard/xml-generation.md)
- The block catalog & parameters: [../algowizard/config-xml.md](../algowizard/config-xml.md)
- Export developer architecture (SourceCodeGenerators, FreeMarker pipeline): [../../onboard/12-export/](../../onboard/12-export/README.md)
