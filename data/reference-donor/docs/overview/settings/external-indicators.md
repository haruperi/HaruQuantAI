# External indicators — Building blocks deep dive
> Import indicator values computed in your trading platform as data, so SQ X can use an indicator it does not natively support.

**Field-level controls (for UI tests):** [fields/external-indicators.md](fields/external-indicators.md)

**Applies to:** Build — defined in Data Manager, then selectable in the Builder's Building blocks. Available from Build 127.

> Note: this feature was previously called **Custom Data Indicators**; it was renamed **External
> indicators** in later builds.

## What it configures

If you want to use an indicator that SQ X does not yet support, you have two options: implement it in
Java in the CodeEditor (works like any native indicator, but needs programming), or **import the
indicator as data**. This page covers the second option: you compute the indicator's values in your
trading platform (MetaTrader, TradeStation, …), export them, and import them into SQ X, which then
uses the values without knowing how they were computed.

> Important limitation: the imported values are valid **only for the symbol and timeframe** they were
> computed on. To use the indicator on another symbol or timeframe you must re-export the data. The
> values are computed in your trading platform, not in SQ, so both SQ and the platform must use the
> **same history data** for results to match.

## Main options

Defined in **Data manager → External indicators → Add new**:

- **Name** — a unique name (no special characters). Good practice: include the symbol and timeframe,
  e.g. `RVI_EURUSD_H1`.
- **Return type** — how SQ matches the indicator to other blocks (so it compares price with price, not
  price with a CCI value). One of:
  - **Number** — like CCI, RSI, MACD.
  - **Price** — value is a price, like a moving average or Bollinger Bands.
  - **Price range** — value is a price difference/range, like ATR.
  - **Signal** — use the indicator as a custom signal block (e.g. candle patterns, custom rules).
  - Rule of thumb: if the indicator draws on the price chart it is Price; if it draws in a separate
    window it is Number (except range indicators like ATR).
- **Indicator values (lines)** — the output values the indicator produces, defined in the same order
  as in the indicator. For each line you can optionally specify the **source code per platform**
  (MT4, MT5, EasyLanguage) — not required for SQ to use the values, but required for SQ to generate
  strategy source code for that platform. You only need code for the platforms you use. For
  MetaTrader the code looks like `iCustom(NULL, 0, "RVI", 10, 0, #Shift#)` — the `#Shift#` constant is
  replaced by the block's actual Shift during code generation (MT5 handles shift differently and does
  not need it computed).
- **Import indicator data** — after defining the indicator, import the exported values from a file and
  map the file columns to **Value1**, **Value2**, … The definition alone cannot be used until data is
  imported.

The values are exported from the platform using a helper (for MetaTrader, the
`SqIndicatorValuesExportEA` Expert Advisor, shipped in SQ's `custom_indicators` folder), which you
edit to point at your indicator and run via the platform's Strategy Tester.

## How it affects generation

Once data is imported, the external indicator appears in **Builder → Settings → Building blocks** and
is combined into strategies like any other block, and SQ can generate valid platform code for it.
Because the values are tied to one timeframe, the indicator only shows up when the matching timeframe
is selected in **Settings → Data** — switching timeframe hides indicators imported for a different
one.

## Related

- Settings index: [README.md](README.md)
- Parent panel: [building-blocks.md](building-blocks.md)
- Where indicators are imported: [../data-manager.md](../data-manager.md)
- Matching timeframe: [data.md](data.md)
- Concepts (indicator, building block, source-code generation): [../concepts.md](../concepts.md)
- Developer detail: [../../onboard/04-builder/05-blocks-catalog.md](../../onboard/04-builder/05-blocks-catalog.md)
