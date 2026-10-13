# Source Code — Results tab

> View and export the selected strategy's generated source code for your target trading platform.

## What it shows

The Source Code tab generates ready-to-use source code for the selected strategy. For every
strategy you open, StrategyQuant X emits the code in the format you choose, so you can read the
logic, run it on a live platform, or trade it manually. Supported outputs are:

- **Pseudo Code** — human-readable pseudo code of the strategy. Shows the strategy logic and can
  be used as a reference for manual trading.
- **Expert Advisor for MetaTrader 4** — the EA code for MetaTrader 4. Save it to the
  MetaTrader `experts` directory to run the EA in MT4.
- **Expert Advisor for MetaTrader 5** — the EA code for MetaTrader 5, used the same way in MT5.
- **EasyLanguage for TradeStation / MultiCharts** — code for the TradeStation platform, which
  can also be compiled in MultiCharts.
- **Strategy XML** — the strategy definition in XML format.

## How it works

The tab is served by the `SourceCode` plugin at `/sourcecode/`. Like every Results tab, it
obtains the strategy's locked `ResultsGroup` through an `IResultsGroupProvider`
(`DatabankResultsGroupProvider`) and generates the requested code from the strategy's structure.
The chosen output format drives which code template is applied to produce the final source.

## Options & settings

- **Output format** — Pseudo Code, MetaTrader 4 EA, MetaTrader 5 EA, EasyLanguage
  (TradeStation / MultiCharts), or Strategy XML.
- **Parameter variables** — control how strategy parameters (periods, numbers, etc.) are
  generated. They can be left as plain numbers, or parametrized so they become configurable
  inputs in your trading platform.
- **MM (Money Management) used** — generate the code either with the Money Management that was
  used in the last strategy test, or choose a different MM.

## Related

- Parent overview: [../results-databank.md](../results-databank.md)
- Sibling tabs: [overview.md](overview.md), [strategy-config.md](strategy-config.md),
  [equity-chart.md](equity-chart.md), [trade-list.md](trade-list.md)
- Developer detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
- Servlet endpoint: `/sourcecode/`
