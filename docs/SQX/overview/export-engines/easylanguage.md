# EasyLanguage — export engine

> Exports a generated strategy as EasyLanguage code (`*.el`) for Tradestation and MultiCharts.

## What it produces

- **Output:** **EasyLanguage** code for **Tradestation** and **MultiCharts** (both use the same
  EasyLanguage export).
- **File extension:** `.el`.
- Registered name: *EasyLanguage for Tradestation / MultiCharts (\*.el)*.

## Templates

The engine lives in `internal/extend/Code/EasyLanguage/` as a set of **FreeMarker** templates.

- **`Main.tpl`** — entry template. Opens with the metadata header (name, `extension=el`),
  `<#include>`s the `.inc` section files, then emits the strategy: parameters → indicators →
  the bar loop → entry/exit rules → money management → ATM exits.
- **`.inc` section files** — `Functions.inc`, `Parameters.inc`, `Blocks.inc`, `Size.inc`, plus the
  shared TradingOptions / ATM / MoneyManagement sections in EasyLanguage syntax.
- **`blocks/`** — **one `.tpl` per building block** (~544 block templates), e.g. `ADX.tpl`,
  `ATR.tpl`. This is where each block's XML turns into EasyLanguage code (often a `SQ_…` function
  call).
- **Sub-folders:** `ExitMethods/`, `MoneyManagement/`, `TradingOptions/`, `blocks/`.

## How a strategy is rendered

A generated strategy is an engine-neutral **XML rule tree**. To export it, SQX feeds that XML to
FreeMarker: `Main.tpl` renders the file skeleton, and for **each `<Block>`** in the XML it invokes
the matching `blocks/<Block>.tpl`, which emits the EasyLanguage expression. Templates use helpers
such as `getOptions("StrategyName"|"Version"|"Date")`, `getRulesCountForEvent("OnBarUpdate")`,
`<@printBacktestInfo/>` and `<@printBlockChild block "#Param#" shift />` to recursively render
nested child parameters.

Every building block exists in **two** places: its **logic** as a Java snippet in
`internal/extend/Snippets/SQ/Blocks/` (used for backtesting/evaluation) and its **rendering** as one
`.tpl` per engine in `EasyLanguage/blocks/`. A block that has no EasyLanguage `.tpl` cannot be
exported to EasyLanguage.

## COT (Commitments of Traders) blocks

COT blocks and COT custom-data values export as calls to the `SQ_COT_*` functions of the platform
package, for example `SQ_COT_GetValue(COTSymbol1 + "_52W", 0, 0, "")`. The COT market is an input
(`COTSymbol1("ES")`), one per market; see [COT markets as inputs](README.md#cot-markets-as-inputs).

- **Arguments of `SQ_COT_GetValue`:** COT identifier (`<market>_52W` or `<market>_156W`), field
  (0 = cpihedg, 1 = ctihedg, 2 = cpispec, 3 = ctispec, 4 = cpismall), bar shift, CSV folder.
- **The `Shift` of every `SQ_COT_*` signal function is a bar shift**, as in `SQ_COT_GetValue`: the
  function evaluates the bar `Shift` bars back and steps from that bar's date by weeks of 7 days.
- **`SQ_COT_Score(market, weeks, folder)` takes weeks, not bars.** The export writes the bar shift as
  the function's history reference: `SQ_COT_Score(COTSymbol1, 4, "")[1]` is the score 4 weeks before
  the previous bar.
- **The folder is always exported empty (`""`).** Each platform package turns it into its own COT
  data folder, so the same `.el` runs on both platforms.
- **`AUTO` as the COT symbol** is the COT market of the strategy's instrument (Data Manager >
  Instruments > COT); a backtest writes the resolved market into the strategy before export.
- COT custom-data values get their EasyLanguage code from
  `CustomDataServlet.createCotValuesObject`.

| | MultiCharts | TradeStation (9.5 and 10) |
|---|---|---|
| Package | `custom_indicators/Tradestation/SQ_MC.pla`, plus `SQ_COT_DownloaderLib_MC.dll` and `SQ_COT_Managed.dll` from `DLL (Multicharts only)/` copied into the MultiCharts program folder | `custom_indicators/Tradestation/SQ.ELD` |
| Reading COT data | The functions call the DLL | EasyLanguage reads the CSV files directly |
| Empty folder means | `C:\ProgramData\TS Support\MultiCharts64\SQ_COT\`, created by the DLL | `C:\SQ_COT\`, created by the download script of `SQ_COT_EnsureData` |
| Downloading COT data | The strategy itself, with its `COTLicenseCode` input: `SQ_COT_EnsureData` calls the DLL and returns when the data is there | The strategy itself, with its `COTLicenseCode` input: `SQ_COT_EnsureData` starts PowerShell, which downloads in the background |

A strategy that reads COT data gets a `COTLicenseCode("")` input and calls
`SQ_COT_EnsureData(COTLicenseCode, "")` before its rules: on the first bar, then once a day on the
last bar of the chart. Both versions download from `https://cdn.strategyquantcdn.com/cot.php` when
the data is missing or older than 7 days and return at once otherwise; with an empty license they
only print a message when the data is missing or old. The `SQ_COT_Downloader` indicator still works
on both platforms.

- **MultiCharts** calls `MC_COT_EnsureData` of the DLL, which downloads and extracts the data
  before it returns.
- **TradeStation** writes `SqCOT_EnsureData.ps1` into the COT folder and starts it, the same
  download as the `SQ_COT_Downloader` indicator; it takes a few minutes. When the COT folder does
  not exist, the script goes into `C:\Users\Public\` and creates the folder first. Without any COT data the
  strategy stops at once with "COT data download started. Turn the strategy on again in a few
  minutes."; with old data it keeps running, and `SQ_COT_GetValue` reloads its files on the last bar
  when `version.txt` changes. The script writes `version.txt` (the date as `1YYMMDD`) at the end,
  `download_running.txt` marks a download in progress for up to 10 minutes, and
  `download_error.txt` keeps the server's answer to a failed download, which the next start shows.

In TradeStation the other COT functions call `SQ_COT_GetValue` with a chart date as the third
argument; the TradeStation version treats a value below 10000 as a bar shift and a larger value as
a chart date.

## Notes & limitations

- One export target serves **two platforms** — Tradestation and MultiCharts — since both consume
  EasyLanguage; the generated `.el` is imported and compiled inside those platforms.
- Unlike the MetaTrader engines, EasyLanguage has no `CustomFunctions/` sub-folder and no
  MT-style broker-protection lock.

## Related

- [Export engines index](README.md)
- Sibling engines: [MetaTrader 4](metatrader4.md) · [MetaTrader 5](metatrader5.md) ·
  [JForex](jforex.md) · [PseudoCode](pseudocode.md)
- How the strategy XML is produced: [../algowizard/xml-generation.md](../algowizard/xml-generation.md)
- The block catalog & parameters: [../algowizard/config-xml.md](../algowizard/config-xml.md)
- Export developer architecture: [../../onboard/12-export/](../../onboard/12-export/README.md)
